/**
 * POST /api/contact —— 站点反馈表单
 *
 * 运行在 Cloudflare Pages Functions（边缘），数据落 D1。
 * 不依赖 server/ 那套 Node 服务，独立可用。
 *
 * 防护三层：
 *   1. Turnstile 人机验证（配了 TURNSTILE_SECRET 才启用）
 *   2. 蜜罐字段 website：正常用户看不见，被填即视为脚本
 *   3. D1 计数限流：同 IP 60 秒内最多 3 条（WAF 规则未生效时的兜底）
 */

const MAX_BODY = 4096;
const RATE_LIMIT = 3;
const RATE_WINDOW = 60;

const json = (code, body) =>
  new Response(JSON.stringify(body), {
    status: code,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });

const clean = (v, max) => String(v ?? "").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, "").trim().slice(0, max);

async function sha(s) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}

async function turnstileOk(secret, token, ip) {
  if (!secret) return true;                     // 未配置就跳过，方便先跑通链路
  if (!token) return false;
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ secret, response: token, remoteip: ip }),
  }).catch(() => null);
  if (!r) return false;
  const d = await r.json().catch(() => ({}));
  return d.success === true;
}

export async function onRequestPost({ request, env }) {
  if (!(request.headers.get("content-type") || "").includes("application/json")) {
    return json(415, { error: "需要 application/json" });
  }

  const raw = await request.text();
  if (raw.length > MAX_BODY) return json(413, { error: "内容过长" });

  let b;
  try { b = JSON.parse(raw); } catch { return json(400, { error: "JSON 解析失败" }); }

  // 蜜罐命中：假装成功，不给脚本任何反馈信号
  if (clean(b.website, 40)) return json(200, { ok: true });

  const name = clean(b.name, 40);
  const contact = clean(b.contact, 120);
  const message = String(b.message ?? "")
    .replace(/\r/g, "").replace(/[^\S\n]+/g, " ").trim().slice(0, 1000);

  if (name.length < 1) return json(400, { error: "请填写称呼" });
  if (contact.length < 3) return json(400, { error: "请填写有效的联系方式" });
  if (message.length < 2) return json(400, { error: "请填写反馈内容" });

  const ip = request.headers.get("cf-connecting-ip") || "0.0.0.0";
  if (!await turnstileOk(env.TURNSTILE_SECRET, b.turnstileToken, ip)) {
    return json(403, { error: "人机验证未通过，请刷新后重试" });
  }

  const ipHash = await sha(ip);
  const now = Math.floor(Date.now() / 1000);

  const hit = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM contacts WHERE ip_hash=? AND created_at>?"
  ).bind(ipHash, now - RATE_WINDOW).first();
  if ((hit?.n ?? 0) >= RATE_LIMIT) return json(429, { error: "提交过于频繁，请稍后再试" });

  const r = await env.DB.prepare(
    "INSERT INTO contacts(name,contact,message,created_at,ip_hash,ua) VALUES(?,?,?,?,?,?)"
  ).bind(name, contact, message, now, ipHash, clean(request.headers.get("user-agent"), 120)).run();

  return json(200, { ok: true, id: r.meta?.last_row_id ?? null });
}

export async function onRequestGet() {
  return json(405, { error: "只支持 POST" });
}
