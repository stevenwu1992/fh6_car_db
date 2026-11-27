/**
 * FH6 车辆索引 —— 玩家账号 / 收藏 / 评分 / 调校 / 分级标签后台
 *
 * 零依赖 Node 服务（node:sqlite + node:crypto），可直接 `node server/server.mjs` 跑，
 * 也可放进 Docker 与静态站同机部署。数据模型与 docs/architecture-player-identity.md 对齐：
 * 匿名优先、sessions 只存 token 哈希、identities 独立表、garage 一车一状态。
 *
 * 安全策略（对应文档 §8）：
 *  - Cookie: HttpOnly + SameSite=Lax + Secure(生产) + Path=/，token 只存 sha256
 *  - 写操作：Origin 白名单 + X-CSRF: 1 + JSON content-type，缺一 403
 *  - 限流：IP 维度滑动窗口（写 60/10min、登录 5/10min、建匿名用户 20/天）
 *  - 请求体上限 32KB（调校 64KB），字段白名单校验，car_id 只接受纯数字
 *  - 管理端：两条路并行 —— ① ADMIN_PASSWORD 密码登录，签发独立短效 admin 会话
 *              ② ADMIN_EMAILS 邮箱白名单，命中才把 users.is_admin 置 1
 *              两者都只影响「改分级标签」这一个写接口，且写操作一律进 audit_log
 */
import { createServer } from "node:http";
import { createHash, randomBytes, timingSafeEqual } from "node:crypto";
import { readFileSync, existsSync, mkdirSync } from "node:fs";
import { join, dirname, extname, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { DatabaseSync } from "node:sqlite";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const CFG = {
  port: Number(process.env.PORT || 8787),
  dbPath: process.env.DB_PATH || join(__dirname, "data", "fh6.db"),
  siteOrigin: (process.env.SITE_ORIGIN || "http://localhost:8787").replace(/\/$/, ""),
  apiOrigin: (process.env.API_ORIGIN || "").replace(/\/$/, ""),
  cookieName: "fh6_sid",
  sessionDays: 365,
  secure: process.env.NODE_ENV === "production",
  adminEmails: (process.env.ADMIN_EMAILS || "").split(",").map(s => s.trim().toLowerCase()).filter(Boolean),
  adminPassword: process.env.ADMIN_PASSWORD || "",
  adminTtlHours: Math.max(1, Math.min(72, Number(process.env.ADMIN_TTL_HOURS || 12))),
  dev: process.env.DEV === "1",
  steamKey: process.env.STEAM_API_KEY || "",
  resendKey: process.env.RESEND_API_KEY || "",
  mailFrom: process.env.MAIL_FROM || "",
  staticDir: process.env.STATIC_DIR || join(ROOT, "output"),
};

mkdirSync(dirname(CFG.dbPath), { recursive: true });
const db = new DatabaseSync(CFG.dbPath);
db.exec(readFileSync(join(__dirname, "schema.sql"), "utf8"));

const now = () => Math.floor(Date.now() / 1000);
const sha = s => createHash("sha256").update(s).digest("hex");
const uid = p => p + randomBytes(8).toString("hex");
const token = () => randomBytes(32).toString("base64url");
const json = (res, code, body, headers = {}) => {
  const s = JSON.stringify(body);
  res.writeHead(code, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    ...headers,
  });
  res.end(s);
};
const err = (res, code, c, m) => json(res, code, { error: { code: c, message: m } });

/* ---------- 限流 ---------- */
function rateLimit(bucket, limit, windowSec) {
  const t = now();
  const row = db.prepare("SELECT window_start, count FROM rate_limits WHERE bucket=?").get(bucket);
  if (!row || t - row.window_start >= windowSec) {
    db.prepare("INSERT INTO rate_limits(bucket,window_start,count) VALUES(?,?,1) ON CONFLICT(bucket) DO UPDATE SET window_start=?,count=1")
      .run(bucket, t, t);
    return true;
  }
  if (row.count >= limit) return false;
  db.prepare("UPDATE rate_limits SET count=count+1 WHERE bucket=?").run(bucket);
  return true;
}

/* ---------- 会话 ---------- */
function parseCookies(req) {
  const out = {};
  for (const part of (req.headers.cookie || "").split(";")) {
    const i = part.indexOf("=");
    if (i > 0) out[part.slice(0, i).trim()] = decodeURIComponent(part.slice(i + 1).trim());
  }
  return out;
}
const cookie = (val, maxAge) =>
  `${CFG.cookieName}=${val}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAge}${CFG.secure ? "; Secure" : ""}`;

function userOf(req) {
  const t = parseCookies(req)[CFG.cookieName];
  if (!t) return null;
  const row = db.prepare(
    "SELECT s.user_id, s.expires_at, u.is_admin, u.display_name, u.is_anonymous FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?"
  ).get(sha(t));
  if (!row) return null;
  if (row.expires_at < now()) {
    db.prepare("DELETE FROM sessions WHERE token_hash=?").run(sha(t));
    return null;
  }
  db.prepare("UPDATE users SET last_seen_at=? WHERE id=?").run(now(), row.user_id);
  return { id: row.user_id, isAdmin: !!row.is_admin, isAnonymous: !!row.is_anonymous, name: row.display_name };
}

function issueSession(res, userId, req) {
  const t = token();
  const exp = now() + CFG.sessionDays * 86400;
  db.prepare("INSERT INTO sessions(token_hash,user_id,created_at,expires_at,ip_hash,ua_hash) VALUES(?,?,?,?,?,?)")
    .run(sha(t), userId, now(), exp, sha(clientIp(req)), sha(String(req.headers["user-agent"] || "")));
  res.setHeader("set-cookie", cookie(t, CFG.sessionDays * 86400));
  return t;
}

const clientIp = req =>
  String(req.headers["cf-connecting-ip"] || req.headers["x-forwarded-for"] || "").split(",")[0].trim()
  || req.socket.remoteAddress || "0.0.0.0";

/* ---------- 管理员密码会话 ---------- */
const ADMIN_COOKIE = "fh6_admin";
const adminCookie = (val, maxAge) =>
  `${ADMIN_COOKIE}=${val}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${maxAge}${CFG.secure ? "; Secure" : ""}`;

function hasAdmin(req) {
  const t = parseCookies(req)[ADMIN_COOKIE];
  if (!t) return false;
  const h = sha(t);
  const row = db.prepare("SELECT expires_at FROM admin_sessions WHERE token_hash=?").get(h);
  if (!row) return false;
  if (row.expires_at <= now()) {
    db.prepare("DELETE FROM admin_sessions WHERE token_hash=?").run(h);
    return false;
  }
  return true;
}

function issueAdminSession(req, res) {
  const t = token();
  const ttl = CFG.adminTtlHours * 3600;
  const exp = now() + ttl;
  db.prepare("INSERT INTO admin_sessions(token_hash,created_at,expires_at,ip_hash,ua_hash) VALUES(?,?,?,?,?)")
    .run(sha(t), now(), exp, sha(clientIp(req)), sha(String(req.headers["user-agent"] || "")));
  db.prepare("DELETE FROM admin_sessions WHERE expires_at <= ?").run(now());
  res.setHeader("set-cookie", adminCookie(t, ttl));
  return exp;
}

// 两侧都先做 sha256 再比较：长度恒为 32 字节，timingSafeEqual 才是真正的定长比较。
const passwordMatches = input => {
  const a = createHash("sha256").update(String(input ?? "")).digest();
  const b = createHash("sha256").update(CFG.adminPassword).digest();
  return timingSafeEqual(a, b);
};

/* ---------- 邮件（Resend，零依赖直连 REST） ---------- */
const mailReady = () => Boolean(CFG.resendKey && CFG.mailFrom);

async function sendLoginMail(email, link) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${CFG.resendKey}`, "content-type": "application/json" },
    body: JSON.stringify({
      from: CFG.mailFrom,
      to: [email],
      subject: "登录 FH6 车辆索引",
      html: `<div style="font:400 15px/1.7 -apple-system,'Segoe UI',system-ui,'Microsoft YaHei',sans-serif;color:#111114">
        <p>点下面的链接完成登录，15 分钟内有效：</p>
        <p><a href="${link}" style="color:#e8185f">${link}</a></p>
        <p style="color:#65656d;font-size:13px">如果不是你本人操作，忽略这封邮件即可，链接会自行失效。</p>
      </div>`,
    }),
  });
  if (!r.ok) console.error("[mail]", r.status, (await r.text()).slice(0, 200));
  return r.ok;
}

function ensureAnon(req, res) {
  const u = userOf(req);
  if (u) return u;
  const ip = clientIp(req);
  if (!rateLimit(`ip:${sha(ip)}:newuser`, 20, 86400)) return null;
  const id = uid("u_");
  db.prepare("INSERT INTO users(id,display_name,is_anonymous,created_at,last_seen_at) VALUES(?,?,1,?,?)")
    .run(id, "游客", now(), now());
  issueSession(res, id, req);
  return { id, isAdmin: false, isAnonymous: true, name: "游客" };
}

/* ---------- 请求防护 ---------- */
function readBody(req, limit) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", c => {
      size += c.length;
      if (size > limit) { reject(Object.assign(new Error("payload"), { code: "PAYLOAD_TOO_LARGE" })); req.destroy(); return; }
      chunks.push(c);
    });
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8");
      if (!raw) return resolve({});
      try { resolve(JSON.parse(raw)); } catch { reject(Object.assign(new Error("json"), { code: "BAD_JSON" })); }
    });
    req.on("error", reject);
  });
}

const ALLOWED_ORIGINS = new Set([CFG.siteOrigin, CFG.apiOrigin].filter(Boolean));
function guardWrite(req, res) {
  const origin = req.headers.origin;
  if (!origin || !ALLOWED_ORIGINS.has(origin)) { err(res, 403, "BAD_ORIGIN", "来源不被允许"); return false; }
  if (req.headers["x-csrf"] !== "1") { err(res, 403, "CSRF", "缺少 X-CSRF 头"); return false; }
  if (!String(req.headers["content-type"] || "").includes("application/json")) {
    err(res, 415, "BAD_TYPE", "需要 application/json"); return false;
  }
  return true;
}

const CAR_RE = /^\d{1,6}$/;
/* 调校可选的适用分级：13 张分级表的组别名 + 漂移/通用 */
const TIER_GROUPS = [
  "R 998公路", "S2 900公路", "S1 800公路", "S1 800泥地", "S1 800越野",
  "A 700公路", "A 700泥地", "A 700越野", "B 600公路", "B 600泥地", "B 600越野",
  "C 500公路", "C 500泥地", "漂移神车", "通用",
];
const SHARE_RE = /^\d{9}$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const validDate = v => {
  if (!DATE_RE.test(v)) return false;
  const d = new Date(v + "T00:00:00Z");
  if (Number.isNaN(d.getTime())) return false;
  return v <= new Date().toISOString().slice(0, 10);
};
const norm = v => String(v ?? "").normalize("NFKC").trim();          // 分享码：全角转半角
const text = v => String(v ?? "").replace(/\u3000/g, " ").replace(/\s+/g, " ").trim();  // 文本：保留中文标点
const cjkLen = v => Array.from(String(v ?? "")).length;
const STATES = new Set(["owned", "favorite", "wishlist"]);

/* ---------- 路由 ---------- */
const MIME = {
  ".html": "text/html; charset=utf-8", ".webp": "image/webp", ".png": "image/png",
  ".jpg": "image/jpeg", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8",
  ".ico": "image/x-icon",
};

function serveStatic(req, res, pathname) {
  let p = decodeURIComponent(pathname);
  if (p === "/" || p === "") p = "/zh-hans.html";
  const file = normalize(join(CFG.staticDir, p));
  if (!file.startsWith(CFG.staticDir) || !existsSync(file)) return false;
  const body = readFileSync(file);
  res.writeHead(200, {
    "content-type": MIME[extname(file)] || "application/octet-stream",
    "cache-control": p.endsWith(".html") ? "no-cache" : "public, max-age=86400",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
  });
  res.end(body);
  return true;
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const path = url.pathname;
  const method = req.method || "GET";

  // 基础安全头
  res.setHeader("x-frame-options", "DENY");
  res.setHeader("x-content-type-options", "nosniff");
  res.setHeader("referrer-policy", "strict-origin-when-cross-origin");
  res.setHeader("permissions-policy", "geolocation=(), microphone=(), camera=()");

  try {
    if (path === "/health") return json(res, 200, { ok: true, db: "ok", ts: now() });

    /* --- 管理端密码登录 --- */
    if (path === "/auth/admin/session" && method === "GET") {
      return hasAdmin(req) ? json(res, 200, { ok: true }) : err(res, 401, "NO_ADMIN", "未登录");
    }

    if (path === "/auth/admin/login" && method === "POST") {
      if (!guardWrite(req, res)) return;
      if (!CFG.adminPassword) return err(res, 503, "NOT_CONFIGURED", "服务端尚未配置 ADMIN_PASSWORD");
      const ipKey = "admin:login:" + sha(clientIp(req));
      if (!rateLimit(ipKey, 5, 900)) return err(res, 429, "RATE_LIMITED", "尝试过于频繁，请 15 分钟后再试");
      if (!rateLimit("admin:login:global", 100, 3600)) return err(res, 429, "RATE_LIMITED", "登录尝试过多，请稍后再试");
      const body = await readBody(req, 1024);
      const exp = passwordMatches(body.password) ? issueAdminSession(req, res) : 0;
      db.prepare("INSERT INTO audit_log(id,user_id,action,detail,created_at) VALUES(?,?,?,?,?)")
        .run(uid("a_"), null, exp ? "admin_login_ok" : "admin_login_fail",
             JSON.stringify({ ip: sha(clientIp(req)) }), now());
      if (!exp) return err(res, 401, "BAD_PASSWORD", "密码不正确");
      db.prepare("DELETE FROM rate_limits WHERE bucket=?").run(ipKey);
      return json(res, 200, { ok: true, expires_at: exp });
    }

    if (path === "/auth/admin/logout" && method === "POST") {
      if (!guardWrite(req, res)) return;
      const t = parseCookies(req)[ADMIN_COOKIE];
      if (t) db.prepare("DELETE FROM admin_sessions WHERE token_hash=?").run(sha(t));
      res.setHeader("set-cookie", adminCookie("", 0));
      return json(res, 200, { ok: true });
    }

    /* --- 身份 --- */
    if (path === "/api/me" && method === "GET") {
      const u = ensureAnon(req, res);
      if (!u) return err(res, 429, "RATE_LIMITED", "创建会话过于频繁");
      const stats = db.prepare(
        "SELECT state, COUNT(*) n FROM garage WHERE user_id=? GROUP BY state").all(u.id);
      const identities = db.prepare("SELECT provider, email FROM identities WHERE user_id=?").all(u.id);
      return json(res, 200, {
        user: { id: u.id, display_name: u.name || "游客", is_anonymous: u.isAnonymous, is_admin: u.isAdmin || hasAdmin(req) },
        identities: identities.map(i => ({ provider: i.provider, email: i.email })),
        stats: Object.fromEntries(stats.map(r => [r.state, r.n])),
        csrf: 1,
      });
    }

    if (path === "/auth/logout" && method === "POST") {
      if (!guardWrite(req, res)) return;
      const t = parseCookies(req)[CFG.cookieName];
      if (t) db.prepare("DELETE FROM sessions WHERE token_hash=?").run(sha(t));
      res.setHeader("set-cookie", cookie("", 0));
      return json(res, 200, { ok: true });
    }

    /* --- Steam OpenID 2.0 --- */
    if (path === "/auth/steam/start" && method === "GET") {
      const u = ensureAnon(req, res);
      if (!u) return err(res, 429, "RATE_LIMITED", "创建会话过于频繁");
      const state = token();
      const next = (url.searchParams.get("next") || "/").slice(0, 200);
      db.prepare("INSERT INTO login_tokens(token_hash,email,user_id,next_path,created_at,expires_at) VALUES(?,?,?,?,?,?)")
        .run(sha(state), "steam", u.id, next, now(), now() + 600);
      const ret = `${CFG.apiOrigin || CFG.siteOrigin}/auth/steam/callback?state=${encodeURIComponent(state)}`;
      const q = new URLSearchParams({
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": ret,
        "openid.realm": CFG.siteOrigin,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
      });
      res.writeHead(302, { location: "https://steamcommunity.com/openid/login?" + q.toString() });
      return res.end();
    }

    if (path === "/auth/steam/callback" && method === "GET") {
      const state = url.searchParams.get("state") || "";
      const row = db.prepare("SELECT * FROM login_tokens WHERE token_hash=?").get(sha(state));
      if (!row || row.used_at || row.expires_at < now()) return err(res, 400, "BAD_STATE", "登录状态已失效，请重新发起");
      /* 必须把参数原样回传给 Steam 校验，只读 claimed_id 等于任何人都能冒充 */
      const body = new URLSearchParams();
      for (const [k, v] of url.searchParams) if (k.startsWith("openid.")) body.append(k, v);
      body.set("openid.mode", "check_authentication");
      let ok = false;
      try {
        const vr = await fetch("https://steamcommunity.com/openid/login", {
          method: "POST", body,
          headers: { "content-type": "application/x-www-form-urlencoded" },
        });
        ok = /is_valid\s*:\s*true/i.test(await vr.text());
      } catch { ok = false; }
      if (!ok) return err(res, 400, "STEAM_INVALID", "Steam 校验失败，请重试");
      const m = /^https?:\/\/steamcommunity\.com\/openid\/id\/(\d{17})$/.exec(url.searchParams.get("openid.claimed_id") || "");
      if (!m) return err(res, 400, "STEAM_ID", "Steam ID 格式不正确");
      const steamId = m[1];                    // 17 位，必须按字符串处理
      db.prepare("UPDATE login_tokens SET used_at=? WHERE token_hash=?").run(now(), row.token_hash);

      const ident = db.prepare("SELECT * FROM identities WHERE provider='steam' AND provider_uid=?").get(steamId);
      let userId = ident ? ident.user_id : (row.user_id || uid("u_"));
      if (!ident) {
        if (row.user_id && db.prepare("SELECT 1 FROM users WHERE id=?").get(row.user_id)) {
          userId = row.user_id;
        } else {
          userId = uid("u_");
          db.prepare("INSERT INTO users(id,display_name,is_anonymous,created_at) VALUES(?,?,0,?)").run(userId, "Steam 玩家", now());
        }
        db.prepare("INSERT INTO identities(id,user_id,provider,provider_uid,created_at) VALUES(?,?,?,?,?)")
          .run(uid("i_"), userId, "steam", steamId, now());
      }
      db.prepare("UPDATE users SET is_anonymous=0 WHERE id=?").run(userId);

      if (CFG.steamKey) {
        try {
          const r = await fetch(`https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=${CFG.steamKey}&steamids=${steamId}`);
          const j = await r.json();
          const p = j?.response?.players?.[0];
          if (p) db.prepare("UPDATE users SET display_name=?, avatar_url=? WHERE id=?")
            .run(String(p.personaname || "Steam 玩家").slice(0, 40), String(p.avatarfull || ""), userId);
        } catch { /* 拉昵称失败不影响登录 */ }
      }
      const old = parseCookies(req)[CFG.cookieName];
      if (old) db.prepare("DELETE FROM sessions WHERE token_hash=?").run(sha(old));
      issueSession(res, userId, req);
      const next = row.next_path && row.next_path.startsWith("/") ? row.next_path : "/";
      res.writeHead(302, { location: next });
      return res.end();
    }

    if (path === "/auth/email/start" && method === "POST") {
      if (!guardWrite(req, res)) return;
      const ip = clientIp(req);
      if (!rateLimit(`ip:${sha(ip)}:login`, 5, 600)) return err(res, 429, "RATE_LIMITED", "尝试过于频繁");
      const body = await readBody(req, 4096);
      const email = String(body.email || "").trim().toLowerCase();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return err(res, 400, "BAD_EMAIL", "邮箱格式不正确");
      if (!rateLimit(`em:${sha(email)}:login`, 3, 3600)) return err(res, 429, "RATE_LIMITED", "该邮箱请求过于频繁");
      const u = ensureAnon(req, res);
      if (!u) return err(res, 429, "RATE_LIMITED", "创建会话过于频繁");
      const t = token();
      db.prepare("INSERT INTO login_tokens(token_hash,email,user_id,next_path,created_at,expires_at) VALUES(?,?,?,?,?,?)")
        .run(sha(t), email, u.id, String(body.next || "/"), now(), now() + 900);
      const link = `${CFG.apiOrigin || CFG.siteOrigin}/auth/verify?token=${encodeURIComponent(t)}`;
      if (CFG.dev) {
        console.log(`[magic-link] ${email} → ${link}`);
        return json(res, 200, { ok: true, dev_link: link });
      }
      if (!mailReady()) {
        console.warn("[mail] 未配置 RESEND_API_KEY / MAIL_FROM，邮箱登录返回 503");
        return err(res, 503, "MAIL_NOT_CONFIGURED", "邮件登录尚未开通，请改用 Steam 登录");
      }
      if (!await sendLoginMail(email, link)) return err(res, 502, "MAIL_FAILED", "验证邮件发送失败，请稍后再试");
      return json(res, 200, { ok: true });
    }

    if (path === "/auth/verify" && method === "GET") {
      const t = url.searchParams.get("token") || "";
      const row = db.prepare("SELECT * FROM login_tokens WHERE token_hash=?").get(sha(t));
      if (!row || row.used_at || row.expires_at < now()) return err(res, 400, "BAD_TOKEN", "链接无效或已过期");
      db.prepare("UPDATE login_tokens SET used_at=? WHERE token_hash=?").run(now(), row.token_hash);

      const email = row.email;
      let identity = db.prepare("SELECT * FROM identities WHERE provider='email' AND provider_uid=?").get(email);
      let userId;
      if (identity) {
        userId = identity.user_id;
        db.prepare("UPDATE users SET is_anonymous=0 WHERE id=?").run(userId);
      } else {
        userId = row.user_id;
        if (!userId || !db.prepare("SELECT 1 FROM users WHERE id=?").get(userId)) {
          userId = uid("u_");
          db.prepare("INSERT INTO users(id,display_name,is_anonymous,created_at) VALUES(?,?,0,?)").run(userId, email.split("@")[0], now());
        }
        db.prepare("INSERT INTO identities(id,user_id,provider,provider_uid,email,created_at) VALUES(?,?,?,?,?,?)")
          .run(uid("i_"), userId, "email", email, email, now());
        db.prepare("UPDATE users SET is_anonymous=0, display_name=? WHERE id=?").run(email.split("@")[0], userId);
      }
      if (CFG.adminEmails.includes(email)) db.prepare("UPDATE users SET is_admin=1 WHERE id=?").run(userId);
      // 轮换会话，防 session fixation
      const old = parseCookies(req)[CFG.cookieName];
      if (old) db.prepare("DELETE FROM sessions WHERE token_hash=?").run(sha(old));
      issueSession(res, userId, req);
      const next = row.next_path && row.next_path.startsWith("/") ? row.next_path : "/";
      res.writeHead(302, { location: next });
      return res.end();
    }

    /* --- 我的车库 --- */
    if (path === "/api/garage" && method === "GET") {
      const u = ensureAnon(req, res);
      if (!u) return err(res, 429, "RATE_LIMITED", "稍后再试");
      const rows = db.prepare("SELECT car_id, state, updated_at FROM garage WHERE user_id=?").all(u.id);
      const ratings = db.prepare("SELECT car_id, score FROM ratings WHERE user_id=?").all(u.id);
      return json(res, 200, { garage: rows, ratings });
    }

    if (path.startsWith("/api/garage/") && ["PUT", "DELETE"].includes(method)) {
      if (!guardWrite(req, res)) return;
      const u = userOf(req);
      if (!u) return err(res, 401, "NO_SESSION", "请刷新页面后重试");
      const carId = path.split("/")[3];
      if (!CAR_RE.test(carId)) return err(res, 400, "BAD_CAR", "车辆 ID 不合法");
      if (method === "DELETE") {
        db.prepare("DELETE FROM garage WHERE user_id=? AND car_id=?").run(u.id, carId);
        return json(res, 200, { car_id: carId, state: null });
      }
      const body = await readBody(req, 2048);
      const state = String(body.state || "");
      if (!STATES.has(state)) return err(res, 400, "BAD_STATE", "状态不合法");
      const cnt = db.prepare("SELECT COUNT(*) n FROM garage WHERE user_id=?").get(u.id).n;
      if (cnt >= 5000) return err(res, 409, "QUOTA", "标记数量已达上限");
      db.prepare("INSERT INTO garage(user_id,car_id,state,updated_at) VALUES(?,?,?,?) ON CONFLICT(user_id,car_id) DO UPDATE SET state=excluded.state,updated_at=excluded.updated_at")
        .run(u.id, carId, state, now());
      return json(res, 200, { car_id: carId, state, updated_at: now() });
    }

    if (path === "/api/garage/bulk" && method === "POST") {
      if (!guardWrite(req, res)) return;
      const u = userOf(req);
      if (!u) return err(res, 401, "NO_SESSION", "请刷新页面后重试");
      const body = await readBody(req, 65536);
      const items = Array.isArray(body.items) ? body.items.slice(0, 500) : [];
      let n = 0;
      const stmt = db.prepare("INSERT INTO garage(user_id,car_id,state,updated_at) VALUES(?,?,?,?) ON CONFLICT(user_id,car_id) DO UPDATE SET state=excluded.state,updated_at=excluded.updated_at");
      for (const it of items) {
        const carId = String(it.car_id || ""), state = String(it.state || "");
        if (!CAR_RE.test(carId) || !STATES.has(state)) continue;
        stmt.run(u.id, carId, state, now()); n++;
      }
      return json(res, 200, { ok: true, applied: n });
    }

    /* --- 评分 --- */
    if (path.startsWith("/api/ratings/") && method === "PUT") {
      if (!guardWrite(req, res)) return;
      const u = userOf(req);
      if (!u) return err(res, 401, "NO_SESSION", "请刷新页面后重试");
      if (u.isAnonymous) return err(res, 403, "LOGIN_REQUIRED", "评分需要登录");
      const carId = path.split("/")[3];
      if (!CAR_RE.test(carId)) return err(res, 400, "BAD_CAR", "车辆 ID 不合法");
      const body = await readBody(req, 1024);
      const score = Number(body.score);
      if (!Number.isInteger(score) || score < 1 || score > 5) return err(res, 400, "BAD_SCORE", "评分需为 1–5");
      if (!rateLimit(`u:${u.id}:rate`, 30, 600)) return err(res, 429, "RATE_LIMITED", "操作过于频繁");
      db.prepare("INSERT INTO ratings(user_id,car_id,score,updated_at) VALUES(?,?,?,?) ON CONFLICT(user_id,car_id) DO UPDATE SET score=excluded.score,updated_at=excluded.updated_at")
        .run(u.id, carId, score, now());
      const agg = db.prepare("SELECT COUNT(*) v, AVG(score) a FROM ratings WHERE car_id=?").get(carId);
      return json(res, 200, { car_id: carId, score, avg: Math.round(agg.a * 10) / 10, votes: agg.v });
    }

    /* --- 聚合统计（公开） --- */
    if (path === "/api/stats" && method === "GET") {
      const ids = (url.searchParams.get("ids") || "").split(",").filter(s => CAR_RE.test(s)).slice(0, 400);
      if (!ids.length) return json(res, 200, { stats: {} });
      const ph = ids.map(() => "?").join(",");
      const g = db.prepare(
        `SELECT car_id, SUM(state='favorite') fav, SUM(state='owned') owned, SUM(state='wishlist') wish
         FROM garage WHERE car_id IN (${ph}) GROUP BY car_id`).all(...ids);
      const r = db.prepare(
        `SELECT car_id, COUNT(*) votes, AVG(score) avg FROM ratings WHERE car_id IN (${ph}) GROUP BY car_id`).all(...ids);
      const map = {};
      for (const id of ids) map[id] = { fav: 0, owned: 0, wish: 0, votes: 0, avg: 0 };
      for (const x of g) Object.assign(map[x.car_id], { fav: x.fav, owned: x.owned, wish: x.wish });
      for (const x of r) Object.assign(map[x.car_id], { votes: x.votes, avg: Math.round(x.avg * 10) / 10 });
      return json(res, 200, { stats: map });
    }

    /* --- 调校 --- */
    if (path === "/api/tunes" && method === "GET") {
      const carId = url.searchParams.get("carId");
      const sort = url.searchParams.get("sort") === "likes" ? "likes" : "time";
      if (carId && !CAR_RE.test(carId)) return err(res, 400, "BAD_CAR", "车辆 ID 不合法");
      const me = userOf(req);
      const cols = `t.id,t.car_id,t.share_code,t.author_id,t.tier_group,t.game_date,t.note,t.created_at,u.display_name,
                    (SELECT COUNT(*) FROM tune_likes l WHERE l.tune_id=t.id) likes,
                    EXISTS(SELECT 1 FROM tune_likes l2 WHERE l2.tune_id=t.id AND l2.user_id=?) mine`;
      const order = sort === "likes"
        ? "likes DESC, COALESCE(NULLIF(t.game_date,''), t.created_at) DESC"
        : "COALESCE(NULLIF(t.game_date,''), date(t.created_at,'unixepoch')) DESC, t.created_at DESC";
      const rows = carId
        ? db.prepare(`SELECT ${cols} FROM tunes t JOIN users u ON u.id=t.user_id
                      WHERE t.car_id=? ORDER BY ${order} LIMIT 100`).all(me ? me.id : "", carId)
        : db.prepare(`SELECT ${cols} FROM tunes t JOIN users u ON u.id=t.user_id
                      ORDER BY ${order} LIMIT 100`).all(me ? me.id : "");
      return json(res, 200, { tunes: rows.map(r => ({ ...r, mine: !!r.mine })), sort });
    }

    if (path === "/api/tunes" && method === "POST") {
      if (!guardWrite(req, res)) return;
      const u = userOf(req);
      if (!u) return err(res, 401, "NO_SESSION", "请刷新页面后重试");
      if (u.isAnonymous) return err(res, 403, "LOGIN_REQUIRED", "上传调校需要登录");
      if (!rateLimit(`u:${u.id}:tune`, 10, 3600)) return err(res, 429, "RATE_LIMITED", "上传过于频繁");
      const body = await readBody(req, 16384);

      const carId = norm(body.car_id);
      const shareCode = norm(body.share_code);
      const authorId = text(body.author_id);
      const tierGroup = norm(body.tier_group);
      const gameDate = norm(body.game_date);
      const note = text(body.note).replace(/[\u0000-\u001f]/g, " ");

      if (!CAR_RE.test(carId)) return err(res, 400, "BAD_CAR", "车辆 ID 不合法");
      if (!SHARE_RE.test(shareCode)) return err(res, 400, "BAD_SHARE_CODE", "调校分享码必须是 9 位数字");
      if (cjkLen(authorId) < 2 || cjkLen(authorId) > 32) return err(res, 400, "BAD_AUTHOR", "请填写 2–32 字的调校作者游戏 ID");
      if (!/^[\w\u4e00-\u9fa5 ._#-]+$/u.test(authorId)) return err(res, 400, "BAD_AUTHOR", "作者 ID 含有不支持的字符");
      if (!TIER_GROUPS.includes(tierGroup)) return err(res, 400, "BAD_TIER", "请选择调校适用的强度分级");
      if (cjkLen(note) > 100) return err(res, 400, "NOTE_TOO_LONG", "说明最多 100 个字符");
      if (gameDate && !validDate(gameDate)) return err(res, 400, "BAD_DATE", "发布时间格式应为 YYYY-MM-DD，且不能晚于今天");

      const dup = db.prepare("SELECT id FROM tunes WHERE car_id=? AND share_code=?").get(carId, shareCode);
      if (dup) return err(res, 409, "DUPLICATE", "这台车已经收录过这个分享码");

      const payload = JSON.stringify(body.payload ?? {});
      if (payload.length > 12000) return err(res, 413, "TOO_BIG", "调校数据过大");
      const id = uid("t_");
      db.prepare(`INSERT INTO tunes(id,user_id,car_id,share_code,author_id,tier_group,game_date,note,payload,created_at,updated_at)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)`)
        .run(id, u.id, carId, shareCode, authorId, tierGroup, gameDate, note, payload, now(), now());
      return json(res, 200, { id, car_id: carId, share_code: shareCode });
    }

    if (/^\/api\/tunes\/[^/]+\/like$/.test(path) && method === "POST") {
      if (!guardWrite(req, res)) return;
      const u = userOf(req);
      if (!u) return err(res, 401, "NO_SESSION", "请刷新页面后重试");
      if (u.isAnonymous) return err(res, 403, "LOGIN_REQUIRED", "点赞需要登录");
      const id = path.split("/")[3];
      const tune = db.prepare("SELECT id FROM tunes WHERE id=?").get(id);
      if (!tune) return err(res, 404, "NOT_FOUND", "调校不存在");
      if (!rateLimit(`u:${u.id}:like`, 60, 600)) return err(res, 429, "RATE_LIMITED", "操作过于频繁");
      const had = db.prepare("SELECT 1 FROM tune_likes WHERE tune_id=? AND user_id=?").get(id, u.id);
      if (had) db.prepare("DELETE FROM tune_likes WHERE tune_id=? AND user_id=?").run(id, u.id);
      else db.prepare("INSERT INTO tune_likes(tune_id,user_id,created_at) VALUES(?,?,?)").run(id, u.id, now());
      const n = db.prepare("SELECT COUNT(*) n FROM tune_likes WHERE tune_id=?").get(id).n;
      return json(res, 200, { id, liked: !had, likes: n });
    }

    if (path.startsWith("/api/tunes/") && method === "DELETE") {
      if (!guardWrite(req, res)) return;
      const u = userOf(req);
      if (!u) return err(res, 401, "NO_SESSION", "请刷新页面后重试");
      const id = path.split("/")[3];
      const row = db.prepare("SELECT user_id FROM tunes WHERE id=?").get(id);
      if (!row) return err(res, 404, "NOT_FOUND", "调校不存在");
      if (row.user_id !== u.id && !u.isAdmin) return err(res, 403, "FORBIDDEN", "只能删除自己的调校");
      db.prepare("DELETE FROM tunes WHERE id=?").run(id);
      return json(res, 200, { ok: true });
    }

    /* --- 管理员：批量导入调校 --- */
    if (path === "/api/admin/tunes/bulk" && method === "POST") {
      if (!guardWrite(req, res)) return;
      const u = userOf(req);
      if (!u) return err(res, 401, "NO_SESSION", "请刷新页面后重试");
      if (!u.isAdmin) return err(res, 403, "FORBIDDEN", "需要管理员权限");
      const body = await readBody(req, 262144);
      const rows = Array.isArray(body.rows) ? body.rows.slice(0, 500) : [];
      if (!rows.length) return err(res, 400, "EMPTY", "没有可导入的行");
      const insert = db.prepare(`INSERT INTO tunes(id,user_id,car_id,share_code,author_id,tier_group,game_date,note,payload,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)`);
      const exists = db.prepare("SELECT 1 FROM tunes WHERE car_id=? AND share_code=?");
      const ok = [], bad = [];
      rows.forEach((r, i) => {
        const carId = norm(r.car_id), code = norm(r.share_code), author = text(r.author_id),
              tier = norm(r.tier_group), date = norm(r.game_date), note = text(r.note).slice(0, 100);
        const why =
          !CAR_RE.test(carId) ? "车辆ID不合法" :
          !SHARE_RE.test(code) ? "分享码非 9 位数字" :
          cjkLen(author) < 2 ? "作者ID过短" :
          !TIER_GROUPS.includes(tier) ? "分级不在允许列表" :
          (date && !validDate(date)) ? "日期格式不正确" :
          exists.get(carId, code) ? "已存在同名分享码" : "";
        if (why) { bad.push({ line: i + 1, why, row: r }); return; }
        insert.run(uid("t_"), u.id, carId, code, author, tier, date, note, "{}", now(), now());
        ok.push(code);
      });
      db.prepare("INSERT INTO audit_log(id,user_id,action,detail,created_at) VALUES(?,?,?,?,?)")
        .run(uid("a_"), u.id, "tunes_bulk", JSON.stringify({ ok: ok.length, bad: bad.length }), now());
      return json(res, 200, { imported: ok.length, failed: bad.length, errors: bad.slice(0, 50) });
    }

    /* --- 分级标签（读公开 / 写仅管理员） --- */
    if (path === "/api/tiers" && method === "GET") {
      const rows = db.prepare("SELECT car_id,race_tier,race_group,drift_tier,updated_at FROM tier_overrides").all();
      return json(res, 200, { overrides: rows, server_time: now() });
    }

    if (path.startsWith("/api/tiers/") && method === "PUT") {
      if (!guardWrite(req, res)) return;
      const u = userOf(req);
      const admin = (u && u.isAdmin) || hasAdmin(req);
      if (!admin) return u ? err(res, 403, "FORBIDDEN", "需要管理员权限")
                           : err(res, 401, "NO_SESSION", "请刷新页面后重试");
      const carId = path.split("/")[3];
      if (!CAR_RE.test(carId)) return err(res, 400, "BAD_CAR", "车辆 ID 不合法");
      const body = await readBody(req, 2048);
      const raceTier = body.race_tier ? String(body.race_tier).slice(0, 12) : null;
      const raceGroup = body.race_group ? String(body.race_group).slice(0, 24) : null;
      const driftTier = body.drift_tier ? String(body.drift_tier).slice(0, 12) : null;
      db.prepare(`INSERT INTO tier_overrides(car_id,race_tier,race_group,drift_tier,updated_by,updated_at)
                  VALUES(?,?,?,?,?,?)
                  ON CONFLICT(car_id) DO UPDATE SET race_tier=excluded.race_tier, race_group=excluded.race_group,
                    drift_tier=excluded.drift_tier, updated_by=excluded.updated_by, updated_at=excluded.updated_at`)
        .run(carId, raceTier, raceGroup, driftTier, u ? u.id : null, now());
      db.prepare("INSERT INTO audit_log(id,user_id,action,detail,created_at) VALUES(?,?,?,?,?)")
        .run(uid("a_"), u ? u.id : null, "tier_update", JSON.stringify({ carId, raceTier, raceGroup, driftTier }), now());
      return json(res, 200, { ok: true, car_id: carId });
    }

    /* --- 静态资源 --- */
    if (method === "GET" || method === "HEAD") {
      if (serveStatic(req, res, path)) return;
    }

    return err(res, 404, "NOT_FOUND", "没有这个接口");
  } catch (e) {
    if (e?.code === "PAYLOAD_TOO_LARGE") return err(res, 413, "TOO_BIG", "请求体过大");
    if (e?.code === "BAD_JSON") return err(res, 400, "BAD_JSON", "JSON 解析失败");
    console.error("[500]", path, e);
    return err(res, 500, "INTERNAL", "服务异常");
  }
});

server.listen(CFG.port, () => {
  console.log(`FH6 API + 静态站: http://localhost:${CFG.port}  (static=${CFG.staticDir})`);
  if (CFG.dev) console.log("DEV=1：magic link 会打印到控制台，并随响应返回 dev_link");
  if (!CFG.adminPassword) console.warn("[WARN] 未设置 ADMIN_PASSWORD —— 后台密码登录会返回 503");
  else if (CFG.adminPassword.length < 12) console.warn("[WARN] ADMIN_PASSWORD 少于 12 位，建议换成更长的随机串");
  else console.log(`后台密码登录已启用，会话有效期 ${CFG.adminTtlHours} 小时`);
});
