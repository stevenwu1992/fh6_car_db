/**
 * 管理员密码登录 + 分级标签读写（Cloudflare Worker + D1）
 *
 * 与 server/server.mjs 同一套语义：
 *   - 独立 cookie fh6_admin，SameSite=Strict，默认 12 小时
 *   - 只写 admin_sessions，不动 users.is_admin
 *   - 单 IP 5 次失败锁 15 分钟
 *
 * 端点：
 *   POST /auth/admin/login   { password }
 *   POST /auth/admin/logout
 *   GET  /auth/admin/session
 *   GET  /api/tiers          公开读
 *   PUT  /api/tiers/:carId   仅管理员
 */

const COOKIE = "fh6_admin";
const TTL_HOURS = 12;

const enc = new TextEncoder();

const json = (code, body, extra = {}) =>
  new Response(JSON.stringify(body), {
    status: code,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });

const now = () => Math.floor(Date.now() / 1000);

const b64url = bytes =>
  btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

async function sha256hex(s) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(String(s)));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}

// 两侧都先 sha256，长度固定，比较走异或累加，不泄露长度与内容
function eqHash(a, b) {
  if (a.length !== b.length) return false;
  let x = 0;
  for (let i = 0; i < a.length; i++) x |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return x === 0;
}

// 支持把密码以 PBKDF2 哈希形式放在 wrangler [vars]（明文无需进控制台）
const unb64 = s => {
  let t = s.replace(/-/g, "+").replace(/_/g, "/");
  while (t.length % 4) t += "=";
  return Uint8Array.from(atob(t), c => c.charCodeAt(0));
};

async function verifyPbkdf2(pw, stored) {
  const [algo, iterStr, saltB64, hashB64] = String(stored).split("$");
  if (algo !== "pbkdf2") return false;
  const key = await crypto.subtle.importKey("raw", enc.encode(String(pw)), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt: unb64(saltB64), iterations: Number(iterStr) }, key, 256);
  return eqHash(b64url(new Uint8Array(bits)), hashB64);
}

function readCookie(request, name) {
  for (const part of (request.headers.get("cookie") || "").split(";")) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i).trim() === name) return decodeURIComponent(part.slice(i + 1).trim());
  }
  return null;
}

const cookieHeader = (val, maxAge) =>
  `${COOKIE}=${encodeURIComponent(val)}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${maxAge}; Secure`;

/* ---------- 会话 ---------- */
export async function adminValid(request, env) {
  const t = readCookie(request, COOKIE);
  if (!t) return false;
  const h = await sha256hex(t);
  const row = await env.DB.prepare("SELECT expires_at, role FROM admin_sessions WHERE token_hash=?").bind(h).first();
  if (!row) return false;
  if (row.expires_at <= now()) {
    await env.DB.prepare("DELETE FROM admin_sessions WHERE token_hash=?").bind(h).run();
    return false;
  }
  return row.role || "full";   // 'full' | 'drift'
}

async function issue(request, env, role) {
  const token = b64url(crypto.getRandomValues(new Uint8Array(32)));
  const ttl = TTL_HOURS * 3600;
  const t = now();
  await env.DB.prepare(
    "INSERT INTO admin_sessions(token_hash,created_at,expires_at,ip_hash,ua_hash,role) VALUES(?,?,?,?,?,?)"
  ).bind(await sha256hex(token), t, t + ttl,
         await sha256hex(request.headers.get("cf-connecting-ip") || ""),
         await sha256hex(request.headers.get("user-agent") || ""), role).run();
  await env.DB.prepare("DELETE FROM admin_sessions WHERE expires_at <= ?").bind(t).run();
  return { token, ttl };
}

async function rateLimit(env, bucket, limit, windowSec) {
  const t = now();
  const row = await env.DB.prepare("SELECT window_start,count FROM auth_rate_limits WHERE bucket=?").bind(bucket).first();
  if (!row || t - row.window_start >= windowSec) {
    await env.DB.prepare(
      "INSERT INTO auth_rate_limits(bucket,window_start,count) VALUES(?,?,1) ON CONFLICT(bucket) DO UPDATE SET window_start=?,count=1"
    ).bind(bucket, t, t).run();
    return true;
  }
  if (row.count >= limit) return false;
  await env.DB.prepare("UPDATE auth_rate_limits SET count=count+1 WHERE bucket=?").bind(bucket).run();
  return true;
}

/* ---------- 写操作来源校验 ---------- */
function badOrigin(request, url) {
  const o = request.headers.get("origin");
  return !o || o !== url.origin;
}

/* ---------- 分级 ---------- */
const CAR_RE = /^\d{1,6}$/;
const SHARE_RE = /^\d{9}$/;
const TIER_GROUPS = [
  "R 998公路", "S2 900公路", "S1 800公路", "S1 800泥地", "S1 800越野",
  "A 700公路", "A 700泥地", "A 700越野", "B 600公路", "B 600泥地", "B 600越野",
  "C 500公路", "C 500泥地", "漂移神车", "通用",
];
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
/* 调校发布时间只卡下界：不早于《地平线 6》发售日 2026-05-18，不设上限（允许未来日期） */
const RELEASE_DATE = "2026-05-18";
const validDate = v => {
  if (!DATE_RE.test(v)) return false;
  const d = new Date(v + "T00:00:00Z");
  if (Number.isNaN(d.getTime())) return false;
  if (d.toISOString().slice(0, 10) !== v) return false;   // 2026-02-31 这类会被顺延的日期不收
  return v >= RELEASE_DATE;
};

async function listTiers(env) {
  const rows = await env.DB.prepare(
    "SELECT car_id,race_tier,race_group,drift_tier,updated_at FROM tier_overrides"
  ).all();
  return json(200, { overrides: rows.results || [], server_time: now() });
}

async function putTier(request, env, url) {
  if (badOrigin(request, url)) return json(403, { error: "来源不被允许" });
  const role = await adminValid(request, env);
  if (!role) return json(403, { error: "需要管理员权限" });

  const carId = url.pathname.split("/")[3] || "";
  if (!CAR_RE.test(carId)) return json(400, { error: "车辆 ID 不合法" });

  const body = await request.json().catch(() => ({}));
  const driftTier = body.drift_tier ? String(body.drift_tier).slice(0, 12) : null;

  // 漂移管理员只能改漂移强度，竞速分级保持原值
  if (role !== "full") {
    const cur = await env.DB.prepare("SELECT race_tier, race_group FROM tier_overrides WHERE car_id=?").bind(carId).first();
    await env.DB.prepare(
      `INSERT INTO tier_overrides(car_id,race_tier,race_group,drift_tier,updated_by,updated_at)
       VALUES(?,?,?,?,?,?)
       ON CONFLICT(car_id) DO UPDATE SET drift_tier=excluded.drift_tier,
         updated_by=excluded.updated_by, updated_at=excluded.updated_at`
    ).bind(carId, cur?.race_tier ?? null, cur?.race_group ?? null, driftTier, "drift-admin", now()).run();
    return json(200, { ok: true, car_id: carId, role });
  }

  const raceTier = body.race_tier ? String(body.race_tier).slice(0, 12) : null;
  const raceGroup = body.race_group ? String(body.race_group).slice(0, 24) : null;

  await env.DB.prepare(
    `INSERT INTO tier_overrides(car_id,race_tier,race_group,drift_tier,updated_by,updated_at)
     VALUES(?,?,?,?,?,?)
     ON CONFLICT(car_id) DO UPDATE SET race_tier=excluded.race_tier, race_group=excluded.race_group,
       drift_tier=excluded.drift_tier, updated_by=excluded.updated_by, updated_at=excluded.updated_at`
  ).bind(carId, raceTier, raceGroup, driftTier, "admin", now()).run();

  return json(200, { ok: true, car_id: carId, role });
}

/* ---------- 登录 ---------- */
async function login(request, env, url) {
  if (badOrigin(request, url)) return json(403, { error: "来源不被允许" });
  const anyPw = env.ADMIN_PASSWORD || env.ADMIN_PASSWORD_HASH || env.DRIFT_ADMIN_PASSWORD || env.DRIFT_ADMIN_PASSWORD_HASH;
  if (!anyPw) return json(503, { error: "服务端未配置后台密码" });

  const ip = request.headers.get("cf-connecting-ip") || "0.0.0.0";
  const bucket = "admin:login:" + await sha256hex(ip);
  if (!await rateLimit(env, bucket, 5, 900)) return json(429, { error: "尝试过于频繁，请 15 分钟后再试" });
  if (!await rateLimit(env, "admin:login:global", 100, 3600)) return json(429, { error: "登录尝试过多，请稍后再试" });

  const body = await request.json().catch(() => ({}));
  const pw = String(body.password ?? "");

  const matchHash = async (h) => h ? await verifyPbkdf2(pw, h) : false;
  const matchPlain = async (p) => p ? eqHash(await sha256hex(pw), await sha256hex(p)) : false;

  let role = null;
  if (env.ADMIN_PASSWORD_HASH) { if (await matchHash(env.ADMIN_PASSWORD_HASH)) role = "full"; }
  else if (await matchPlain(env.ADMIN_PASSWORD)) role = "full";

  if (!role) {
    if (env.DRIFT_ADMIN_PASSWORD_HASH) { if (await matchHash(env.DRIFT_ADMIN_PASSWORD_HASH)) role = "drift"; }
    else if (await matchPlain(env.DRIFT_ADMIN_PASSWORD)) role = "drift";
  }

  if (!role) return json(401, { error: "密码不正确" });

  const { token, ttl } = await issue(request, env, role);
  await env.DB.prepare("DELETE FROM auth_rate_limits WHERE bucket=?").bind(bucket).run();
  return json(200, { ok: true, role, expires_at: now() + ttl }, { "set-cookie": cookieHeader(token, ttl) });
}

async function logout(request, env) {
  const t = readCookie(request, COOKIE);
  if (t) await env.DB.prepare("DELETE FROM admin_sessions WHERE token_hash=?").bind(await sha256hex(t)).run();
  return json(200, { ok: true }, { "set-cookie": cookieHeader("", 0) });
}

/* ---------- 调校管理（管理员） ---------- */
async function listTunesAdmin(env, url) {
  const carId = String(url.searchParams.get("carId") || "").trim();
  const kw = String(url.searchParams.get("q") || "").trim();
  let rows;
  if (CAR_RE.test(carId)) {
    rows = await env.DB.prepare(
      "SELECT id,car_id,share_code,author_id,tier_group,game_date,note,created_at FROM tunes WHERE car_id=? ORDER BY created_at DESC LIMIT 100"
    ).bind(carId).all();
  } else if (kw) {
    rows = await env.DB.prepare(
      `SELECT id,car_id,share_code,author_id,tier_group,game_date,note,created_at FROM tunes
       WHERE share_code LIKE ? OR author_id LIKE ? ORDER BY created_at DESC LIMIT 60`
    ).bind(`%${kw}%`, `%${kw}%`).all();
  } else {
    rows = await env.DB.prepare(
      "SELECT id,car_id,share_code,author_id,tier_group,game_date,note,created_at FROM tunes ORDER BY created_at DESC LIMIT 60"
    ).all();
  }
  return json(200, { tunes: rows.results || [] });
}

async function updateTune(request, env, url) {
  if (badOrigin(request, url)) return json(403, { error: "来源不被允许" });
  if (!await adminValid(request, env)) return json(403, { error: "需要管理员权限" });
  const id = url.pathname.split("/")[4] || "";
  const row = await env.DB.prepare("SELECT id, car_id FROM tunes WHERE id=?").bind(id).first();
  if (!row) return json(404, { error: "调校不存在" });

  const b = await request.json().catch(() => ({}));
  const shareCode = String(b.share_code ?? "").replace(/\D/g, "");
  const authorId = String(b.author_id ?? "").replace(/\s+/g, " ").trim();
  const tierGroup = String(b.tier_group ?? "").trim();
  const gameDate = String(b.game_date ?? "").trim();
  const note = String(b.note ?? "").replace(/[\u0000-\u001f]/g, " ").trim();

  if (!SHARE_RE.test(shareCode)) return json(400, { error: "分享码必须是 9 位数字" });
  if (Array.from(authorId).length < 2 || Array.from(authorId).length > 32) return json(400, { error: "作者 ID 需 2–32 字" });
  if (!TIER_GROUPS.includes(tierGroup)) return json(400, { error: "分级不合法" });
  if (gameDate && !validDate(gameDate)) return json(400, { error: "发布时间格式应为 YYYY-MM-DD，且不早于 2026-05-18" });
  if (Array.from(note).length > 100) return json(400, { error: "说明最多 100 字" });

  await env.DB.prepare(
    "UPDATE tunes SET share_code=?, author_id=?, tier_group=?, game_date=?, note=?, updated_at=? WHERE id=?"
  ).bind(shareCode, authorId, tierGroup.slice(0, 24), gameDate, note, now(), id).run();
  return json(200, { ok: true, id });
}

async function deleteTune(request, env, url) {
  if (badOrigin(request, url)) return json(403, { error: "来源不被允许" });
  if (!await adminValid(request, env)) return json(403, { error: "需要管理员权限" });
  const id = url.pathname.split("/")[4] || "";
  await env.DB.prepare("DELETE FROM tunes WHERE id=?").bind(id).run();
  return json(200, { ok: true, id });
}

/* ---------- 批量导入（管理员） ---------- */
/* 每行：车辆ID, 分享码, 作者ID, 分级, 发布日期, 说明；逐行校验并回显失败原因 */
async function bulkImport(request, env, url) {
  if (badOrigin(request, url)) return json(403, { error: "来源不被允许" });
  if (!await adminValid(request, env)) return json(403, { error: "需要管理员权限" });

  const body = await request.json().catch(() => ({}));
  const rows = Array.isArray(body.rows) ? body.rows.slice(0, 500) : [];
  if (!rows.length) return json(400, { error: "没有可导入的行" });

  const t = now();
  const ok = [], bad = [];
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i] || {};
    const carId = String(r.car_id ?? "").trim();
    const code = String(r.share_code ?? "").replace(/\D/g, "");
    const author = String(r.author_id ?? "").replace(/\s+/g, " ").trim();
    const tier = String(r.tier_group ?? "").trim();
    const date = String(r.game_date ?? "").trim();
    const note = String(r.note ?? "").replace(/[\u0000-\u001f]/g, " ").trim().slice(0, 100);
    const why =
      !CAR_RE.test(carId) ? "车辆ID不合法" :
      !SHARE_RE.test(code) ? "分享码非 9 位数字" :
      (Array.from(author).length < 2 || Array.from(author).length > 32) ? "作者ID需 2–32 字" :
      !TIER_GROUPS.includes(tier) ? "分级不在允许列表" :
      (date && !validDate(date)) ? "日期格式不正确" : "";
    if (why) { bad.push({ line: i + 1, why }); continue; }

    const dup = await env.DB.prepare("SELECT 1 x FROM tunes WHERE car_id=? AND share_code=?").bind(carId, code).first();
    if (dup) { bad.push({ line: i + 1, why: "已存在同名分享码" }); continue; }

    await env.DB.prepare(
      `INSERT INTO tunes(id,user_id,car_id,share_code,author_id,tier_group,game_date,note,payload,created_at,updated_at)
       VALUES(?,?,?,?,?,?,?,?,?,?,?)`
    ).bind("t_" + crypto.randomUUID().replace(/-/g, "").slice(0, 16),
           "admin", carId, code, author, tier, date, note, "{}", t, t).run();
    ok.push(code);
  }
  return json(200, { imported: ok.length, failed: bad.length, errors: bad.slice(0, 50) });
}

/* ---------- 路由 ---------- */
export async function routeAdmin(request, env, url) {
  const p = url.pathname;
  const m = request.method;

  if (p === "/auth/admin/login" && m === "POST") return login(request, env, url);
  if (p === "/auth/admin/logout" && m === "POST") return logout(request, env);
  if (p === "/auth/admin/session" && m === "GET") {
    const role = await adminValid(request, env);
    return role ? json(200, { ok: true, role }) : json(401, { error: "未登录" });
  }

  if (p === "/api/tiers" && m === "GET") return listTiers(env);
  if (p.startsWith("/api/tiers/") && m === "PUT") return putTier(request, env, url);

  if (p === "/api/admin/tunes" && m === "GET") {
    if (!await adminValid(request, env)) return json(403, { error: "需要管理员权限" });
    return listTunesAdmin(env, url);
  }
  if (p === "/api/admin/tunes/bulk" && m === "POST") return bulkImport(request, env, url);
  if (p.startsWith("/api/admin/tunes/") && m === "PUT") return updateTune(request, env, url);
  if (p.startsWith("/api/admin/tunes/") && m === "DELETE") return deleteTune(request, env, url);

  return null;
}
