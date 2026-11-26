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
  const row = await env.DB.prepare("SELECT expires_at FROM admin_sessions WHERE token_hash=?").bind(h).first();
  if (!row) return false;
  if (row.expires_at <= now()) {
    await env.DB.prepare("DELETE FROM admin_sessions WHERE token_hash=?").bind(h).run();
    return false;
  }
  return true;
}

async function issue(request, env) {
  const token = b64url(crypto.getRandomValues(new Uint8Array(32)));
  const ttl = TTL_HOURS * 3600;
  const t = now();
  await env.DB.prepare(
    "INSERT INTO admin_sessions(token_hash,created_at,expires_at,ip_hash,ua_hash) VALUES(?,?,?,?,?)"
  ).bind(await sha256hex(token), t, t + ttl,
         await sha256hex(request.headers.get("cf-connecting-ip") || ""),
         await sha256hex(request.headers.get("user-agent") || "")).run();
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

async function listTiers(env) {
  const rows = await env.DB.prepare(
    "SELECT car_id,race_tier,race_group,drift_tier,updated_at FROM tier_overrides"
  ).all();
  return json(200, { overrides: rows.results || [], server_time: now() });
}

async function putTier(request, env, url) {
  if (badOrigin(request, url)) return json(403, { error: "来源不被允许" });
  if (!await adminValid(request, env)) return json(403, { error: "需要管理员权限" });

  const carId = url.pathname.split("/")[3] || "";
  if (!CAR_RE.test(carId)) return json(400, { error: "车辆 ID 不合法" });

  const body = await request.json().catch(() => ({}));
  const raceTier = body.race_tier ? String(body.race_tier).slice(0, 12) : null;
  const raceGroup = body.race_group ? String(body.race_group).slice(0, 24) : null;
  const driftTier = body.drift_tier ? String(body.drift_tier).slice(0, 12) : null;

  await env.DB.prepare(
    `INSERT INTO tier_overrides(car_id,race_tier,race_group,drift_tier,updated_by,updated_at)
     VALUES(?,?,?,?,?,?)
     ON CONFLICT(car_id) DO UPDATE SET race_tier=excluded.race_tier, race_group=excluded.race_group,
       drift_tier=excluded.drift_tier, updated_by=excluded.updated_by, updated_at=excluded.updated_at`
  ).bind(carId, raceTier, raceGroup, driftTier, "admin", now()).run();

  return json(200, { ok: true, car_id: carId });
}

/* ---------- 登录 ---------- */
async function login(request, env, url) {
  if (badOrigin(request, url)) return json(403, { error: "来源不被允许" });
  if (!env.ADMIN_PASSWORD && !env.ADMIN_PASSWORD_HASH) {
    return json(503, { error: "服务端未配置 ADMIN_PASSWORD" });
  }

  const ip = request.headers.get("cf-connecting-ip") || "0.0.0.0";
  const bucket = "admin:login:" + await sha256hex(ip);
  if (!await rateLimit(env, bucket, 5, 900)) return json(429, { error: "尝试过于频繁，请 15 分钟后再试" });
  if (!await rateLimit(env, "admin:login:global", 100, 3600)) return json(429, { error: "登录尝试过多，请稍后再试" });

  const body = await request.json().catch(() => ({}));
  const pw = String(body.password ?? "");
  const ok = env.ADMIN_PASSWORD
    ? eqHash(await sha256hex(pw), await sha256hex(env.ADMIN_PASSWORD))
    : await verifyPbkdf2(pw, env.ADMIN_PASSWORD_HASH);
  if (!ok) return json(401, { error: "密码不正确" });

  const { token, ttl } = await issue(request, env);
  await env.DB.prepare("DELETE FROM auth_rate_limits WHERE bucket=?").bind(bucket).run();
  return json(200, { ok: true, expires_at: now() + ttl }, { "set-cookie": cookieHeader(token, ttl) });
}

async function logout(request, env) {
  const t = readCookie(request, COOKIE);
  if (t) await env.DB.prepare("DELETE FROM admin_sessions WHERE token_hash=?").bind(await sha256hex(t)).run();
  return json(200, { ok: true }, { "set-cookie": cookieHeader("", 0) });
}

/* ---------- 路由 ---------- */
export async function routeAdmin(request, env, url) {
  const p = url.pathname;
  const m = request.method;

  if (p === "/auth/admin/login" && m === "POST") return login(request, env, url);
  if (p === "/auth/admin/logout" && m === "POST") return logout(request, env);
  if (p === "/auth/admin/session" && m === "GET") {
    return (await adminValid(request, env)) ? json(200, { ok: true }) : json(401, { error: "未登录" });
  }

  if (p === "/api/tiers" && m === "GET") return listTiers(env);
  if (p.startsWith("/api/tiers/") && m === "PUT") return putTier(request, env, url);

  return null;
}
