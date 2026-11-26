import { handleContact } from "./contact.js";
import { routeAuth } from "./auth.js";
import { routeAdmin } from "./admin.js";

const json = (code, body) =>
  new Response(JSON.stringify(body), {
    status: code,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const { pathname } = url;

    // 进入 Worker 的只有 run_worker_first 声明的 /api/* 与 /auth/*
    if (pathname === "/api/contact") {
      if (request.method === "POST") return handleContact(request, env);
      return json(405, { error: "只支持 POST" });
    }

    const adminRes = await routeAdmin(request, env, url);
    if (adminRes) return adminRes;

    const authRes = await routeAuth(request, env, url);
    if (authRes) return authRes;

    if (pathname.startsWith("/api/") || pathname.startsWith("/auth/")) {
      return json(404, { error: "接口不存在" });
    }

    return env.ASSETS.fetch(request);
  },
};
