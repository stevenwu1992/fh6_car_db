import { handleContact } from "./contact.js";

const json = (code, body) =>
  new Response(JSON.stringify(body), {
    status: code,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);

    // 只有 /api/* 会进入 Worker（wrangler.toml 里 run_worker_first 控制），
    // 其余请求由静态资源层直接返回，不消耗 Worker 调用。
    if (pathname === "/api/contact") {
      if (request.method === "POST") return handleContact(request, env);
      return json(405, { error: "只支持 POST" });
    }

    return env.ASSETS.fetch(request);
  },
};
