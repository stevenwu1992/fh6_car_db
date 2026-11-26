# 玩家账号服务（本地 / Docker 均可）

对应设计文档 `docs/architecture-player-identity.md`：匿名优先、会话只存哈希、
identities 独立表、garage 一车一状态。运行时为零依赖 Node（`node:sqlite`）。

## 上线（Docker）

```bash
# 1. 改 server/docker-compose.yml 里的 SITE_ORIGIN / ADMIN_EMAILS
docker compose -f server/docker-compose.yml up -d --build
# 2. 反代：nginx / Caddy 把 www.forzacardb.top 指到 127.0.0.1:8787（含 /api 与 /auth）
# 3. 验证
curl https://www.forzacardb.top/health     # {"ok":true,...}
```

> 反向代理务必保留 `Origin` 与 `Cookie` 头，并透传 `X-Forwarded-For`（限流按 IP）。
> 若把站点留在 GitHub Pages，则需把 API 放到 `api.forzacardb.top` 并把 `API_ORIGIN` 指过去，
> 前端 `window.__FH6_API__` 也要改成该地址。

## 跑起来

```bash
# 1. 生成配置
cp server/.env.example server/.env      # 或直接看下面的环境变量表

# 2. 启动（同时托管 output/ 静态站）
DEV=1 SITE_ORIGIN=http://localhost:8787 ADMIN_EMAILS=you@example.com \
  PORT=8787 node server/server.mjs

# 打开 http://localhost:8787/   ← 站点
#      http://localhost:8787/admin.html ← 分级后台（需管理员邮箱登录）
```

`DEV=1` 时登录链接会打印到控制台，并随 `/auth/email/start` 响应返回 `dev_link`，
不需要真的发邮件。上线时去掉 `DEV`，接 Resend 或自建 SMTP 发信。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `PORT` | 8787 | 监听端口 |
| `DB_PATH` | `server/data/fh6.db` | SQLite 文件位置（自动建目录/建表） |
| `SITE_ORIGIN` | `http://localhost:8787` | 允许的写操作来源，**必须与访问域名一致** |
| `API_ORIGIN` | 空 | 仅当 API 独立子域时填写，用于拼登录链接 |
| `ADMIN_EMAILS` | 空 | 逗号分隔；命中即 `is_admin=1` |
| `ADMIN_PASSWORD` | 空 | 后台管理密码；**留空则后台无法登录**（返回 503） |
| `ADMIN_TTL_HOURS` | 12 | 后台会话有效期，1–72 |
| `NODE_ENV=production` | — | 开启 `Secure` Cookie |
| `DEV=1` | — | 登录链接直出，便于本地联调 |
| `STATIC_DIR` | `output` | 静态文件根目录 |

## 后台登录（密码 + 防护）

`output/admin.html` 是纯静态页面，**页面里不存任何密码**——密码只在服务端比对。
页面打开后先问 `/api/me`，非管理员就显示密码框；密码通过后拿到一枚独立的
`fh6_admin` 会话 cookie，才渲染表格。

```bash
# 生成一个够强的密码
node -e "console.log(require('crypto').randomBytes(24).toString('base64url'))"
# 写进环境（docker-compose 的 environment 或 .env）
ADMIN_PASSWORD=<上面生成的值>
```

防护链路：

| 层 | 做法 |
|---|---|
| 密码比对 | 两侧 sha256 后 `timingSafeEqual`，定长常量时间，不泄露长度与内容 |
| 会话 | 独立 cookie `fh6_admin`，`HttpOnly` + `SameSite=Strict`，默认 12 小时 |
| 爆破 | 单 IP 5 次失败锁 15 分钟，全局 100 次/小时；成功即清零 |
| 提权范围 | 只签 `admin_sessions`，**不写 `users.is_admin`**，不污染玩家账号 |
| 审计 | 成功/失败都写 `audit_log`（`admin_login_ok` / `admin_login_fail`），只记 IP 哈希 |
| 写接口 | `/api/tiers/:carId` 需管理员；所有写操作仍要 Origin 白名单 + `X-CSRF` + JSON |

> `SameSite=Strict` 只在**同站**请求里发送。若把 API 放到另一个注册域（不是 `*.forzacardb.top`），
> 后台会话会失效——那种情况要改回 `Lax` 并补 CSRF token 校验。


## 调校上传约定

| 字段 | 规则 |
|---|---|
| `share_code` | 9 位数字（游戏内分享码），同车不可重复 |
| `author_id` | 调校作者的游戏 ID，2–32 字符 |
| `tier_group` | 必填，取 13 个分级组别 + `漂移神车` / `通用` |
| `note` | ≤ 100 字符，公开展示 |

## 接口

`GET /api/me` · `GET /api/garage` · `PUT|DELETE /api/garage/:carId` · `POST /api/garage/bulk`
`PUT /api/ratings/:carId` · `GET /api/stats?ids=1,2,3`
`GET|POST /api/tunes` · `DELETE /api/tunes/:id`
`GET /auth/steam/start` · `GET /auth/steam/callback`（Steam OpenID 2.0）
`GET /auth/admin/session` · `POST /auth/admin/login` · `POST /auth/admin/logout`（后台密码）
`GET /api/tiers` · `PUT /api/tiers/:carId`（管理员）
`POST /auth/email/start` · `GET /auth/verify` · `POST /auth/logout`

## 安全

- Cookie `HttpOnly` + `SameSite=Lax` + `Secure`(生产)，token 只存 SHA-256
- 写操作三重校验：Origin 白名单 + `X-CSRF: 1` + `application/json`
- 限流：登录 5 次/10 分钟/IP、同邮箱 3 次/小时、匿名建号 20 个/天、评分 30 次/10 分钟/人
- 请求体上限 32 KB（调校 64 KB），`car_id` 只接受纯数字，状态/评分白名单校验
- 管理员以邮箱白名单判定，前端按钮只是入口，权限判断全在服务端

## 部署

```bash
node server/server.mjs        # 前台
# 或 pm2/systemd；Dockerfile 就是 node:22-alpine + 复制本目录
```
