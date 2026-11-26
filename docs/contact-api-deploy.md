# 边缘接口部署：反馈表单（Pages Functions + D1 + Turnstile）

> 目标：在不改动现有静态站架构、不依赖 `server/` Node 服务的前提下，
> 增加一个同源的 `/api/contact` 接口，把访客反馈写进 Cloudflare D1。
> 域名下同源直连，无跨域、无额外跳转。

## 0. 这次的产物

| 文件 | 作用 |
|---|---|
| `functions/api/contact.js` | Pages Function，处理 `POST /api/contact` |
| `d1/contact-schema.sql` | `contacts` 表结构 |
| `wrangler.toml` | Pages 项目配置 + D1 绑定声明 |
| `output/feedback.html` | 表单页面，已挂到全站页脚「浏览 → 问题反馈」 |

请求链路：

```
浏览器  ──POST /api/contact──►  Cloudflare 边缘（Pages Function）
                                    ├─ Turnstile 校验
                                    ├─ 蜜罐 + 长度校验
                                    ├─ 同 IP 60s/3 次限流
                                    └─ D1 INSERT
```

---

## 1. 建 D1 数据库

控制台：`Workers & Pages → D1 SQL Database → Create`

| 字段 | 填什么 |
|---|---|
| Name | `fh6_contacts` |
| Location | 就近选（如 APAC） |

创建后在 `Console` 标签页粘贴 `d1/contact-schema.sql` 全文执行；或命令行：

```bash
npx wrangler d1 execute fh6_contacts --remote --file=d1/contact-schema.sql
```

执行完用这条确认表在：

```sql
SELECT name FROM sqlite_master WHERE type='table';
```

---

## 2. 绑定到 Pages 项目

控制台：`Workers & Pages → fh6-car-db → Settings → Bindings → Add → D1 database`

| 项 | 值 |
|---|---|
| Variable name | `DB` ← 必须与代码里的 `env.DB` 一致 |
| D1 database | `fh6_contacts` |

命令行等价写法已经写在 `wrangler.toml`，把 `database_id` 换成真实的即可。

> 绑定走的是「生产」环境，改完要**重新部署一次**才生效（Deployments → Retry deployment）。

---

## 3. 开 Turnstile（可选但强烈建议）

控制台：`Turnstile → Add site`

| 项 | 值 |
|---|---|
| Site name | `forzacardb.top` |
| Hostname | `www.forzacardb.top`、`forzacardb.top`、`fh6-car-db.pages.dev` |
| Widget mode | Managed（无感验证） |

拿到两把 key：

- **Site Key** → 填进 `output/feedback.html` 顶部的 `const SITE_KEY = "..."`（改完需重新部署）
- **Secret Key** → 存成 Pages 的 Secret，**不要写进代码或仓库**

```bash
npx wrangler pages secret put TURNSTILE_SECRET --project-name fh6-car-db
```

控制台等价：`Settings → Variables and Secrets → Add → 类型选 Secret，名称 TURNSTILE_SECRET`。

> 不配 Secret 时，服务端会跳过校验（方便先跑通链路），但页面上也没有验证组件——
> 这两处都留空等于裸奔，只适合本地调试。

---

## 4. WAF 速率限制

控制台：`Security → WAF → Rate limiting rules → Create rule`

| 项 | 值 |
|---|---|
| Rule name | `contact-form` |
| 匹配 | `http.request.uri.path eq "/api/contact"` |
| 速率 | 同一 IP，60 秒内 3 次 |
| 动作 | Block（或 Managed Challenge） |
| 持续时间 | 60 秒 |

代码里还有一层 D1 计数限流作为兜底，两条同时存在不冲突：WAF 在边缘直接拦掉，省一次函数调用。

---

## 5. 验证

```bash
# 正常提交
curl -s -X POST https://www.forzacardb.top/api/contact \
  -H 'content-type: application/json' \
  -d '{"name":"测试","contact":"test@example.com","message":"这是一条测试反馈"}' -w " [%{http_code}]\n"

# 非法：缺字段 → 400
curl -s -X POST https://www.forzacardb.top/api/contact \
  -H 'content-type: application/json' -d '{"name":""}' -w " [%{http_code}]\n"

# 方法错误 → 405
curl -s https://www.forzacardb.top/api/contact -w " [%{http_code}]\n"

# 连发 4 次，第 4 次应 429（WAF 或代码限流任一先触发）
for i in 1 2 3 4; do curl -s -o /dev/null -w "$i:%{http_code} " -X POST \
  https://www.forzacardb.top/api/contact -H 'content-type: application/json' \
  -d '{"name":"t","contact":"t@t.co","message":"hi"}'; done; echo
```

读数据：

```bash
npx wrangler d1 execute fh6_contacts --remote \
  --command="SELECT id,name,contact,message,datetime(created_at,'unixepoch','+8 hours') AS t FROM contacts ORDER BY id DESC LIMIT 20"
```

---

## 6. 与 `server/` Node 后端的关系

这两套东西现在并存，职责不同：

| | Pages Function（本次） | `server/` Node 服务 |
|---|---|---|
| 承载 | 反馈表单 | 登录、收藏、调校、评分、分级后台 |
| 依赖 | 无，边缘直跑 | Docker + SQLite |
| 路由 | `/api/contact` | `/api/*`、`/auth/*` |

**注意冲突点**：如果将来把 `/api/*` 整体反代到 Node 服务，`/api/contact` 会被一起吞掉。届时二选一：

1. 把反馈也搬进 Node（加一张表 + 一个接口），删掉 `functions/`；
2. 或者把 Node 的挂载点改成 `/svc/*`，让 `/api/contact` 留在边缘。

目前 Node 服务未部署，两者不冲突。

---

## 7. 防护层汇总

| 层 | 拦什么 | 配置位置 |
|---|---|---|
| Turnstile | 自动化脚本、无头浏览器 | `TURNSTILE_SECRET` + 页面 `SITE_KEY` |
| 蜜罐字段 `website` | 简单表单填充器 | 代码内置，无需配置 |
| WAF 速率限制 | 单 IP 高频灌水 | 控制台规则 |
| D1 计数限流 | WAF 规则失效时的兜底 | 代码内置 |
| 长度/类型校验 | 超大 payload、非法 JSON | 代码内置（上限 4 KB） |
| IP 只存哈希 | 隐私与合规 | 代码内置（SHA-256） |

D1 免费额度：5 GB 存储、每天 500 万行读 / 10 万行写。反馈表这个量级用不到零头。
