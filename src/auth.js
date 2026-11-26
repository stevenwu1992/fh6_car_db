/**
 * 邮箱注册/登录 + Steam 登录（Cloudflare Worker + D1）
 *
 * 参考 https://github.com/G4brym/authentication-using-d1-example 的做法：
 *   users 存凭据、user_sessions 存会话、密码用 PBKDF2 派生、会话只存 token 的 SHA-256。
 * 本实现不引入 hono / workers-qb，保持零依赖，直接走 D1 prepared statement。
 *
 * 端点：
 *   POST /api/auth/register  { email, password, name? }
 *   POST /api/auth/login     { email, password }
 *   POST /api/auth/logout
 *   GET  /api/me
 *   GET  /auth/steam/start?next=...
 *   GET  /auth/steam/callback
 */

const COOKIE = "fh6_sid";
const STATE_COOKIE = "fh6_oauth";
const SESSION_DAYS = 30;

import { adminValid } from "./admin.js";

// Workers 免费版单次调用 CPU 上限 10ms：PBKDF2 210k 次会超时，这里取 10k。
// 迭代次数写进哈希串，将来升级到付费版可以直接调高而不影响老密码。
const PBKDF2_ITER = 10000;

const enc = new TextEncoder();

/* ---------- 基础工具 ---------- */
const json = (code, body, extraHeaders = {}) =>
  new Response(JSON.stringify(body), {
    status: code,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extraHeaders },
  });

const b64url = bytes =>
  btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

const unb64 = s => {
  let t = s.replace(/-/g, "+").replace(/_/g, "/");
  while (t.length % 4) t += "=";
  return Uint8Array.from(atob(t), c => c.charCodeAt(0));
};

const now = () => Math.floor(Date.now() / 1000);

async function sha256hex(s) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(s));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}

function safeEqual(a, b) {
  if (a.length !== b.length) return false;
  let x = 0;
  for (let i = 0; i < a.length; i++) x |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return x === 0;
}

/* ---------- 密码 ---------- */
async function hashPassword(pw) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const key = await crypto.subtle.importKey("raw", enc.encode(pw), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt, iterations: PBKDF2_ITER }, key, 256);
  return `pbkdf2$${PBKDF2_ITER}$${b64url(salt)}$${b64url(new Uint8Array(bits))}`;
}

async function verifyPassword(pw, stored) {
  if (!stored) return false;
  const [algo, iterStr, saltB64, hashB64] = String(stored).split("$");
  if (algo !== "pbkdf2") return false;
  const salt = unb64(saltB64);
  const key = await crypto.subtle.importKey("raw", enc.encode(pw), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt, iterations: Number(iterStr) }, key, 256);
  return safeEqual(b64url(new Uint8Array(bits)), hashB64);
}

// 登录时对不存在的邮箱也做一次等价耗时的校验
let DUMMY = null;
async function dummyHash() {
  if (!DUMMY) DUMMY = await hashPassword("timing-equalizer-not-a-real-password");
  return DUMMY;
}

/* ---------- Cookie ---------- */
function readCookie(request, name) {
  for (const part of (request.headers.get("cookie") || "").split(";")) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i).trim() === name) return decodeURIComponent(part.slice(i + 1).trim());
  }
  return null;
}

function cookie(name, value, maxAge, secure) {
  return `${name}=${encodeURIComponent(value)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAge}${secure ? "; Secure" : ""}`;
}

/* ---------- 限流 ---------- */
async function rateLimit(env, bucket, limit, windowSec) {
  const t = now();
  const row = await env.DB.prepare("SELECT window_start, count FROM auth_rate_limits WHERE bucket=?").bind(bucket).first();
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

/* ---------- 会话 ---------- */
async function issueSession(env, userId, request) {
  const token = b64url(crypto.getRandomValues(new Uint8Array(32)));
  const ip = request.headers.get("cf-connecting-ip") || "0.0.0.0";
  const t = now();
  await env.DB.prepare(
    "INSERT INTO user_sessions(token_hash,user_id,created_at,expires_at,ip_hash,ua_hash) VALUES(?,?,?,?,?,?)"
  ).bind(await sha256hex(token), userId, t, t + SESSION_DAYS * 86400,
         await sha256hex(ip), await sha256hex(request.headers.get("user-agent") || "")).run();
  return token;
}

export async function currentUser(request, env) {
  const token = readCookie(request, COOKIE);
  if (!token) return null;
  const row = await env.DB.prepare(
    "SELECT s.expires_at, u.id, u.email, u.name, u.is_admin FROM user_sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?"
  ).bind(await sha256hex(token)).first();
  if (!row) return null;
  if (row.expires_at <= now()) {
    await env.DB.prepare("DELETE FROM user_sessions WHERE token_hash=?").bind(await sha256hex(token)).run();
    return null;
  }
  return row;
}

const guest = () => ({ user: { id: null, display_name: "游客", email: null, is_anonymous: true, is_admin: false, logged_in: false }, identities: [], stats: {} });
const shape = u => ({
  user: { id: u.id, display_name: u.name || "玩家", email: u.email || null, is_anonymous: false, is_admin: !!u.is_admin, logged_in: true },
  identities: u.email ? [{ provider: "email", email: u.email }] : [],
  stats: {},
});

/* ---------- 输入校验 ---------- */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const EMAIL_MAX = 120;

function safeNext(v) {
  const s = String(v || "/");
  if (!s.startsWith("/") || s.startsWith("//")) return "/";
  return s;
}

/* ---------- 邮箱注册 / 登录 ---------- */
async function register(request, env) {
  const ip = request.headers.get("cf-connecting-ip") || "0.0.0.0";
  if (!await rateLimit(env, "reg:ip:" + await sha256hex(ip), 5, 600)) {
    return json(429, { error: "注册过于频繁，请稍后再试" });
  }
  const body = await request.json().catch(() => ({}));
  const email = String(body.email || "").trim().toLowerCase();
  const password = String(body.password || "");
  const name = String(body.name || "").trim().slice(0, 40);

  if (!EMAIL_RE.test(email) || email.length > EMAIL_MAX) return json(400, { error: "邮箱格式不正确" });
  if (password.length < 8) return json(400, { error: "密码至少 8 位" });
  if (password.length > 128) return json(400, { error: "密码过长" });

  const exists = await env.DB.prepare("SELECT id FROM users WHERE email=?").bind(email).first();
  if (exists) return json(409, { error: "该邮箱已注册，请直接登录" });

  const id = "u_" + b64url(crypto.getRandomValues(new Uint8Array(9)));
  await env.DB.prepare(
    "INSERT INTO users(id,email,name,password_hash,email_verified,is_admin,created_at) VALUES(?,?,?,?,0,0,?)"
  ).bind(id, email, name || email.split("@")[0].slice(0, 20), await hashPassword(password), now()).run();

  const token = await issueSession(env, id, request);
  return json(200, { ok: true, ...shape({ id, email, name: name || email.split("@")[0], is_admin: 0 }) },
    { "set-cookie": cookie(COOKIE, token, SESSION_DAYS * 86400, true) });
}

async function login(request, env) {
  const ip = request.headers.get("cf-connecting-ip") || "0.0.0.0";
  if (!await rateLimit(env, "login:ip:" + await sha256hex(ip), 10, 600)) {
    return json(429, { error: "尝试过于频繁，请稍后再试" });
  }
  const body = await request.json().catch(() => ({}));
  const email = String(body.email || "").trim().toLowerCase();
  const password = String(body.password || "");
  if (!EMAIL_RE.test(email) || !password) return json(400, { error: "请输入邮箱与密码" });

  if (!await rateLimit(env, "login:em:" + await sha256hex(email), 5, 600)) {
    return json(429, { error: "该邮箱尝试过于频繁，请 10 分钟后再试" });
  }

  const u = await env.DB.prepare(
    "SELECT id, email, name, password_hash, is_admin FROM users WHERE email=?"
  ).bind(email).first();
  // 用户不存在时也跑一次 PBKDF2，避免通过响应时间枚举邮箱是否注册
  const stored = u?.password_hash || await dummyHash();
  const ok = await verifyPassword(password, stored);
  if (!u || !ok) return json(401, { error: "邮箱或密码不正确" });

  const token = await issueSession(env, u.id, request);
  return json(200, { ok: true, ...shape(u) }, { "set-cookie": cookie(COOKIE, token, SESSION_DAYS * 86400, true) });
}

async function logout(request, env) {
  const token = readCookie(request, COOKIE);
  if (token) await env.DB.prepare("DELETE FROM user_sessions WHERE token_hash=?").bind(await sha256hex(token)).run();
  return json(200, { ok: true }, { "set-cookie": cookie(COOKIE, "", 0, true) });
}

async function me(request, env) {
  const u = await currentUser(request, env);
  const isAdmin = await adminValid(request, env);
  if (!u) {
    const g = guest();
    if (isAdmin) { g.user.is_admin = true; g.user.display_name = "管理员"; }
    return json(200, g);
  }
  const body = shape(u);
  if (isAdmin) body.user.is_admin = true;
  return json(200, body);
}

/* ---------- Steam OpenID 2.0 ---------- */
const STEAM_OPENID = "https://steamcommunity.com/openid/login";

function steamStart(request, env, url) {
  const origin = url.origin;
  const next = safeNext(url.searchParams.get("next"));
  const state = b64url(crypto.getRandomValues(new Uint8Array(16)));
  const returnTo = `${origin}/auth/steam/callback?state=${state}&next=${encodeURIComponent(next)}`;
  const u = new URL(STEAM_OPENID);
  u.searchParams.set("openid.ns", "http://specs.openid.net/auth/2.0");
  u.searchParams.set("openid.mode", "checkid_setup");
  u.searchParams.set("openid.return_to", returnTo);
  u.searchParams.set("openid.realm", origin);
  u.searchParams.set("openid.identity", "http://specs.openid.net/auth/2.0/identifier_select");
  u.searchParams.set("openid.claimed_id", "http://specs.openid.net/auth/2.0/identifier_select");
  return new Response(null, {
    status: 302,
    headers: {
      location: u.toString(),
      "set-cookie": cookie(STATE_COOKIE, state, 600, true),
      "cache-control": "no-store",
    },
  });
}

async function steamCallback(request, env, url) {
  const origin = url.origin;
  const next = safeNext(url.searchParams.get("next"));
  const cookieState = readCookie(request, STATE_COOKIE);
  const queryState = url.searchParams.get("state");

  // state 必须与浏览器 cookie 一致，否则是登录 CSRF
  if (!cookieState || !queryState || !safeEqual(cookieState, queryState)) {
    return new Response("登录状态校验失败，请重新发起登录", { status: 400 });
  }

  // 把 Steam 回传的全部 openid.* 原样回抛，要求 Steam 亲自确认 is_valid:true
  const form = new URLSearchParams();
  for (const [k, v] of url.searchParams) if (k.startsWith("openid.")) form.append(k, v);
  form.set("openid.mode", "check_authentication");

  const vr = await fetch(STEAM_OPENID, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  }).catch(() => null);
  if (!vr || !vr.ok) return new Response("Steam 校验请求失败", { status: 502 });
  const text = await vr.text();
  if (!/is_valid\s*:\s*true/.test(text)) return new Response("Steam 校验未通过", { status: 403 });

  const claimed = url.searchParams.get("openid.claimed_id") || "";
  const m = claimed.match(/steamcommunity\.com\/openid\/id\/(\d{17})$/);
  if (!m) return new Response("Steam 返回的账号标识不合法", { status: 400 });
  const steamId = m[1];

  // 可选：拉昵称与头像
  let persona = null, avatar = null;
  if (env.STEAM_API_KEY) {
    try {
      const pr = await fetch(`https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=${env.STEAM_API_KEY}&steamids=${steamId}`);
      const pj = await pr.json();
      const p = pj?.response?.players?.[0];
      if (p) { persona = p.personaname || null; avatar = p.avatarfull || null; }
    } catch { /* 拿不到资料不影响登录 */ }
  }

  const link = await env.DB.prepare("SELECT user_id FROM steam_links WHERE steam_id=?").bind(steamId).first();
  let userId;
  if (link) {
    userId = link.user_id;
    if (persona) await env.DB.prepare("UPDATE steam_links SET persona=?, avatar=? WHERE steam_id=?").bind(persona, avatar, steamId).run();
  } else {
    const cur = await currentUser(request, env);
    if (cur) {
      // 已登录状态下绑定 Steam
      userId = cur.id;
      await env.DB.prepare("INSERT INTO steam_links(steam_id,user_id,persona,avatar,linked_at) VALUES(?,?,?,?,?)")
        .bind(steamId, userId, persona, avatar, now()).run();
    } else {
      userId = "u_" + b64url(crypto.getRandomValues(new Uint8Array(9)));
      await env.DB.prepare("INSERT INTO users(id,email,name,password_hash,email_verified,is_admin,created_at) VALUES(?,NULL,?,NULL,0,0,?)")
        .bind(userId, persona || "Steam 玩家", now()).run();
      await env.DB.prepare("INSERT INTO steam_links(steam_id,user_id,persona,avatar,linked_at) VALUES(?,?,?,?,?)")
        .bind(steamId, userId, persona, avatar, now()).run();
    }
  }

  const token = await issueSession(env, userId, request);
  return new Response(null, {
    status: 302,
    headers: {
      location: origin + next,
      "set-cookie": cookie(COOKIE, token, SESSION_DAYS * 86400, true),
      "cache-control": "no-store",
    },
  });
}

/* ---------- 路由 ---------- */
export async function routeAuth(request, env, url) {
  const p = url.pathname;
  const m = request.method;

  if (p === "/api/me" && m === "GET") return me(request, env);
  if (p === "/api/auth/register" && m === "POST") return register(request, env);
  if (p === "/api/auth/login" && m === "POST") return login(request, env);
  if (p === "/api/auth/logout" && m === "POST") return logout(request, env);
  if (p === "/auth/steam/start" && m === "GET") return steamStart(request, env, url);
  if (p === "/auth/steam/callback" && m === "GET") return steamCallback(request, env, url);

  return null;
}
