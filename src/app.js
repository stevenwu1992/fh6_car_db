/**
 * 玩家数据接口：收藏 / 评分 / 调校（Cloudflare Worker + D1）
 *
 * 契约来自 web_template.py 的实际调用，不要随意改字段名：
 *   GET    /api/garage                → { garage:[{car_id,state}], ratings:[{car_id,score}] }
 *   PUT    /api/garage/:carId  {state} → { ok }
 *   DELETE /api/garage/:carId          → { ok }
 *   PUT    /api/ratings/:carId  {score} → { ok, votes, avg }
 *   GET    /api/stats?ids=1,2,3        → { stats:{ "1":{fav,votes,avg} } }
 *   GET    /api/tunes?carId=123        → { tunes:[...] }
 *   POST   /api/tunes                  → { id, ... }
 */

import { currentUser } from "./auth.js";

const json = (code, body) =>
  new Response(JSON.stringify(body), {
    status: code,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

const now = () => Math.floor(Date.now() / 1000);
const CAR_RE = /^\d{1,6}$/;
const STATES = new Set(["owned", "favorite", "wishlist"]);
const TIER_GROUPS = [
  "R 998公路", "S2 900公路", "S1 800公路", "S1 800泥地", "S1 800越野",
  "A 700公路", "A 700泥地", "A 700越野", "B 600公路", "B 600泥地", "B 600越野",
  "C 500公路", "C 500泥地", "漂移神车", "通用",
];
const SHARE_RE = /^\d{9}$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
/* 游戏内调校发布时间：只收 YYYY-MM-DD，且不能晚于今天 */
/* 调校发布时间：介于《地平线 6》发售日 2026-05-18 与今天之间（含两端），不接受未来日期。
   服务器按 UTC 计时，"今天"统一按东八区算，避免凌晨上传被误判成未来。 */
const RELEASE_DATE = "2026-05-18";
const todayCST = () => new Date(Date.now() + 8 * 3600 * 1000).toISOString().slice(0, 10);
const validDate = v => {
  if (!DATE_RE.test(v)) return false;
  const d = new Date(v + "T00:00:00Z");
  if (Number.isNaN(d.getTime())) return false;
  if (d.toISOString().slice(0, 10) !== v) return false;   // 2026-02-31 这类会被顺延的日期不收
  return v >= RELEASE_DATE && v <= todayCST();
};
const cjkLen = v => Array.from(String(v ?? "")).length;

const carIdOf = url => (url.pathname.split("/")[3] || "");

/* 写操作要求：已登录 + 同源 */
function guardWrite(request, url, u) {
  const o = request.headers.get("origin");
  if (!o || o !== url.origin) return json(403, { error: "来源不被允许" });
  if (!u || !u.id) return json(401, { error: "请先登录" });
  return null;
}

/* ---------- 收藏 ---------- */
async function listGarage(env, u) {
  if (!u || !u.id) {
    return json(200, { garage: [], ratings: [], logged_in: false });
  }
  const g = await env.DB.prepare("SELECT car_id, state FROM garage WHERE user_id=?").bind(u.id).all();
  const r = await env.DB.prepare("SELECT car_id, score FROM ratings WHERE user_id=?").bind(u.id).all();
  return json(200, {
    garage: (g.results || []).map(x => ({ car_id: x.car_id, state: x.state })),
    ratings: (r.results || []).map(x => ({ car_id: x.car_id, score: x.score })),
    logged_in: true,
  });
}

async function putGarage(request, env, url, u) {
  const bad = guardWrite(request, url, u);
  if (bad) return bad;
  const carId = carIdOf(url);
  if (!CAR_RE.test(carId)) return json(400, { error: "车辆 ID 不合法" });

  const body = await request.json().catch(() => ({}));
  const state = String(body.state || "favorite");
  if (!STATES.has(state)) return json(400, { error: "状态不合法" });

  await env.DB.prepare(
    `INSERT INTO garage(user_id,car_id,state,updated_at) VALUES(?,?,?,?)
     ON CONFLICT(user_id,car_id) DO UPDATE SET state=excluded.state, updated_at=excluded.updated_at`
  ).bind(u.id, carId, state, now()).run();
  return json(200, { ok: true, car_id: carId, state });
}

async function delGarage(request, env, url, u) {
  const bad = guardWrite(request, url, u);
  if (bad) return bad;
  const carId = carIdOf(url);
  if (!CAR_RE.test(carId)) return json(400, { error: "车辆 ID 不合法" });
  await env.DB.prepare("DELETE FROM garage WHERE user_id=? AND car_id=?").bind(u.id, carId).run();
  return json(200, { ok: true, car_id: carId });
}

/* ---------- 评分 ---------- */
async function putRating(request, env, url, u) {
  const bad = guardWrite(request, url, u);
  if (bad) return bad;
  const carId = carIdOf(url);
  if (!CAR_RE.test(carId)) return json(400, { error: "车辆 ID 不合法" });

  const body = await request.json().catch(() => ({}));
  const score = Number(body.score);
  if (!Number.isInteger(score) || score < 1 || score > 5) return json(400, { error: "评分需为 1–5" });

  await env.DB.prepare(
    `INSERT INTO ratings(user_id,car_id,score,updated_at) VALUES(?,?,?,?)
     ON CONFLICT(user_id,car_id) DO UPDATE SET score=excluded.score, updated_at=excluded.updated_at`
  ).bind(u.id, carId, score, now()).run();

  const agg = await env.DB.prepare(
    "SELECT COUNT(*) v, AVG(score) a FROM ratings WHERE car_id=?"
  ).bind(carId).first();
  return json(200, { ok: true, votes: agg?.v ?? 0, avg: Number((agg?.a ?? 0).toFixed(2)) });
}

/* ---------- 汇总统计（收藏数 / 评分人数与均分） ---------- */
async function stats(env, url) {
  const ids = (url.searchParams.get("ids") || "").split(",").map(s => s.trim()).filter(s => CAR_RE.test(s)).slice(0, 300);
  if (!ids.length) return json(200, { stats: {} });

  const ph = ids.map(() => "?").join(",");
  const fav = await env.DB.prepare(
    `SELECT car_id, COUNT(*) n FROM garage WHERE state='favorite' AND car_id IN (${ph}) GROUP BY car_id`
  ).bind(...ids).all();
  const rat = await env.DB.prepare(
    `SELECT car_id, COUNT(*) v, AVG(score) a FROM ratings WHERE car_id IN (${ph}) GROUP BY car_id`
  ).bind(...ids).all();

  const out = {};
  for (const r of fav.results || []) out[r.car_id] = { fav: r.n, votes: 0, avg: 0 };
  for (const r of rat.results || []) {
    const o = out[r.car_id] || { fav: 0, votes: 0, avg: 0 };
    o.votes = r.v; o.avg = Number((r.a ?? 0).toFixed(2));
    out[r.car_id] = o;
  }
  return json(200, { stats: out });
}

/* ---------- 调校 ---------- */
async function listTunes(env, url, u) {
  const carId = String(url.searchParams.get("carId") || "");
  if (!CAR_RE.test(carId)) return json(400, { error: "车辆 ID 不合法" });
  const sort = url.searchParams.get("sort") === "likes" ? "likes" : "time";
  const cols = `t.id, t.car_id, t.share_code, t.author_id, t.tier_group, t.game_date,
                t.note, t.created_at,
                (SELECT COUNT(*) FROM tune_likes l WHERE l.tune_id=t.id) likes,
                EXISTS(SELECT 1 FROM tune_likes l2 WHERE l2.tune_id=t.id AND l2.user_id=?) mine`;
  const order = sort === "likes"
    ? "likes DESC, t.created_at DESC"
    : "COALESCE(NULLIF(t.game_date,''), date(t.created_at,'unixepoch')) DESC, t.created_at DESC";
  const rows = await env.DB.prepare(
    `SELECT ${cols} FROM tunes t WHERE t.car_id=? ORDER BY ${order} LIMIT 200`
  ).bind(u?.id ?? "", carId).all();
  return json(200, {
    tunes: (rows.results || []).map(r => ({ ...r, mine: !!r.mine })),
    sort,
  });
}

/* 点赞：登录用户一人一条调校只记一次，再点取消 */
async function toggleLike(request, env, url, u) {
  const bad = guardWrite(request, url, u);
  if (bad) return bad;
  const id = url.pathname.split("/")[3] || "";
  if (!id) return json(400, { error: "调校 ID 不合法" });
  const tune = await env.DB.prepare("SELECT id FROM tunes WHERE id=?").bind(id).first();
  if (!tune) return json(404, { error: "调校不存在" });

  // 同一用户 10 分钟最多 60 次
  const t = now();
  const bucket = "like:" + u.id;
  const rl = await env.DB.prepare("SELECT window_start,count FROM auth_rate_limits WHERE bucket=?").bind(bucket).first();
  if (rl && t - rl.window_start < 600) {
    if (rl.count >= 60) return json(429, { error: "操作过于频繁" });
    await env.DB.prepare("UPDATE auth_rate_limits SET count=count+1 WHERE bucket=?").bind(bucket).run();
  } else {
    await env.DB.prepare(
      "INSERT INTO auth_rate_limits(bucket,window_start,count) VALUES(?,?,1) ON CONFLICT(bucket) DO UPDATE SET window_start=?,count=1"
    ).bind(bucket, t, t).run();
  }

  const had = await env.DB.prepare("SELECT 1 x FROM tune_likes WHERE tune_id=? AND user_id=?").bind(id, u.id).first();
  if (had) {
    await env.DB.prepare("DELETE FROM tune_likes WHERE tune_id=? AND user_id=?").bind(id, u.id).run();
  } else {
    await env.DB.prepare("INSERT INTO tune_likes(tune_id,user_id,created_at) VALUES(?,?,?)").bind(id, u.id, t).run();
  }
  const n = await env.DB.prepare("SELECT COUNT(*) n FROM tune_likes WHERE tune_id=?").bind(id).first();
  return json(200, { id, liked: !had, likes: n?.n ?? 0 });
}

async function postTune(request, env, url, u) {
  const bad = guardWrite(request, url, u);
  if (bad) return bad;

  // 同一用户 1 小时最多 10 条
  const t = now();
  const bucket = "tune:" + u.id;
  const rl = await env.DB.prepare("SELECT window_start,count FROM auth_rate_limits WHERE bucket=?").bind(bucket).first();
  if (rl && t - rl.window_start < 3600) {
    if (rl.count >= 10) return json(429, { error: "上传过于频繁" });
    await env.DB.prepare("UPDATE auth_rate_limits SET count=count+1 WHERE bucket=?").bind(bucket).run();
  } else {
    await env.DB.prepare(
      "INSERT INTO auth_rate_limits(bucket,window_start,count) VALUES(?,?,1) ON CONFLICT(bucket) DO UPDATE SET window_start=?,count=1"
    ).bind(bucket, t, t).run();
  }

  const b = await request.json().catch(() => ({}));
  const carId = String(b.car_id ?? "").trim();
  const shareCode = String(b.share_code ?? "").trim();
  const authorId = String(b.author_id ?? "").replace(/\s+/g, " ").trim();
  const tierGroup = String(b.tier_group ?? "").trim();
  const gameDate = String(b.game_date ?? "").trim();
  const note = String(b.note ?? "").replace(/[\u0000-\u001f]/g, " ").trim();

  if (!CAR_RE.test(carId)) return json(400, { error: "车辆 ID 不合法" });
  if (!SHARE_RE.test(shareCode)) return json(400, { error: "分享码必须是 9 位数字" });
  if (cjkLen(authorId) < 2 || cjkLen(authorId) > 32) return json(400, { error: "请填写 2–32 字的作者 ID" });
  if (!TIER_GROUPS.includes(tierGroup)) return json(400, { error: "分级不合法" });
  if (gameDate && !validDate(gameDate)) return json(400, { error: "发布时间格式应为 YYYY-MM-DD，且介于 2026-05-18 与今天之间" });
  if (cjkLen(note) > 100) return json(400, { error: "说明最多 100 个字符" });

  const dup = await env.DB.prepare("SELECT id FROM tunes WHERE car_id=? AND share_code=?").bind(carId, shareCode).first();
  if (dup) return json(409, { error: "这台车已收录过该分享码" });

  const id = "t_" + crypto.randomUUID().replace(/-/g, "").slice(0, 16);
  await env.DB.prepare(
    `INSERT INTO tunes(id,user_id,car_id,share_code,author_id,tier_group,game_date,note,payload,created_at,updated_at)
     VALUES(?,?,?,?,?,?,?,?,?,?,?)`
  ).bind(id, u.id, carId, shareCode, authorId, tierGroup, gameDate, note, JSON.stringify(b.payload ?? {}), t, t).run();

  return json(200, { id, car_id: carId, share_code: shareCode, game_date: gameDate });
}

/* ---------- 路由 ---------- */
export async function routeApp(request, env, url) {
  const p = url.pathname;
  const m = request.method;

  if (!p.startsWith("/api/")) return null;

  if (p === "/api/garage" && m === "GET") {
    return listGarage(env, await currentUser(request, env));
  }
  if (p.startsWith("/api/garage/") && (m === "PUT" || m === "DELETE")) {
    const u = await currentUser(request, env);
    return m === "PUT" ? putGarage(request, env, url, u) : delGarage(request, env, url, u);
  }

  if (p.startsWith("/api/ratings/") && m === "PUT") {
    return putRating(request, env, url, await currentUser(request, env));
  }
  if (p.startsWith("/api/ratings/") && m === "DELETE") {
    const u = await currentUser(request, env);
    const bad = guardWrite(request, url, u);
    if (bad) return bad;
    const carId = carIdOf(url);
    if (!CAR_RE.test(carId)) return json(400, { error: "车辆 ID 不合法" });
    await env.DB.prepare("DELETE FROM ratings WHERE user_id=? AND car_id=?").bind(u.id, carId).run();
    const agg = await env.DB.prepare("SELECT COUNT(*) v, AVG(score) a FROM ratings WHERE car_id=?").bind(carId).first();
    return json(200, { ok: true, votes: agg?.v ?? 0, avg: Number((agg?.a ?? 0).toFixed(2)) });
  }

  if (p === "/api/stats" && m === "GET") return stats(env, url);

  if (p === "/api/tunes" && m === "GET") {
    return listTunes(env, url, await currentUser(request, env));
  }
  if (p === "/api/tunes" && m === "POST") {
    return postTune(request, env, url, await currentUser(request, env));
  }
  if (p.startsWith("/api/tunes/") && p.endsWith("/like") && m === "POST") {
    return toggleLike(request, env, url, await currentUser(request, env));
  }
  if (p.startsWith("/api/tunes/") && m === "DELETE") {
    const u = await currentUser(request, env);
    const bad = guardWrite(request, url, u);
    if (bad) return bad;
    const id = p.split("/")[3] || "";
    const row = await env.DB.prepare("SELECT user_id FROM tunes WHERE id=?").bind(id).first();
    if (!row) return json(404, { error: "调校不存在" });
    if (row.user_id !== u.id) return json(403, { error: "只能删除自己上传的调校" });
    await env.DB.prepare("DELETE FROM tunes WHERE id=?").bind(id).run();
    return json(200, { ok: true });
  }

  return null;
}
