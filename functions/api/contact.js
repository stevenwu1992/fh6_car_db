/**
 * Pages Functions 适配层（可选）。
 * 当前部署目标是 Workers，入口在 src/index.js；保留本文件是为了将来能退回 Pages 而不改实现。
 */

import { handleContact } from "../../src/contact.js";

const json = (code, body) =>
  new Response(JSON.stringify(body), {
    status: code,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

export const onRequestPost = ({ request, env }) => handleContact(request, env);

export const onRequestGet = () => json(405, { error: "只支持 POST" });
