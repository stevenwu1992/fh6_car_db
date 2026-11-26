# Cloudflare Pages 迁移 Runbook

> 面向执行：每一步都有「做什么 → 填什么 → 怎么验」。
> 配套背景与取舍见 `docs/cloudflare-pages-migration.md`，接口细节见 `docs/contact-api-deploy.md`。
> 编写日期：2026-11-26

---

## 0. 起点核对（先确认，别跳过）

以下是 2026-11-26 20:45 的外部实测结果：

| 项 | 现状 | 说明 |
|---|---|---|
| `www.forzacardb.top` | 200，响应头含 `x-github-request-id`、`x-served-by: cache-rtm-…` | 源站是 **GitHub Pages**，Cloudflare 只做代理 |
| `forzacardb.top` | **无 A/AAAA 记录** | 根域现在打不开，不是故障，是没配解析 |
| `api.forzacardb.top` | NXDOMAIN | 未创建 |
| `/api/*`、`/auth/*` | 404 `text/html` | 没有任何后端，落在 GitHub Pages 的 404 页 |
| 代码版本 | 已上线 `5f6ccb7` | 转速 rpm、反馈页、后台密码门都已随 GitHub Pages 生效 |

> 换句话说：**代码是新的，托管是旧的，后端是空的**。本 Runbook 解决后两者。

**总耗时**：阶段 A 约 30 分钟，阶段 B 约 20 分钟，阶段 C 约 15 分钟。阶段 D 是独立工程，不含在内。

---

## 阶段 A：静态站切到 Pages

### A1. 创建 Pages 项目

```
Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git
→ 选仓库 stevenwu1992/fh6_car_db → Begin setup
```

### A2. 填构建参数

| 字段 | 填什么 |
|---|---|
| Project name | `fh6-car-db`（若你用别的名字，后面要同步改 `wrangler.toml`） |
| Production branch | `main` |
| Framework preset | `None` |
| Build command | `mkdir -p dist && cp -r index.html output _headers dist/ && rm -rf dist/output/tables dist/output/*.sqlite dist/output/*.xlsx` |
| Build output directory | `dist` |
| Root directory | 留空 |

> `dist` 必须和控制台里的 `wrangler.toml` → `pages_build_output_dir = "./dist"` 一致。
> 若两处不一致，构建会报 output directory 相关错误。

**验收 A2**：构建日志应显示成功，末尾出现类似 `Success: ... files uploaded`。

### A3. 先验 pages.dev，别急着换域名

```bash
curl -sI https://fh6-car-db.pages.dev/output/zh-hans.html | head -8
```

| 期望 | 说明 |
|---|---|
| `200` | 构建成功 |
| 响应头**没有** `x-github-request-id` | 已由 Pages 提供 |
| `cache-control: public, max-age=600, must-revalidate` | `_headers` 生效（GitHub Pages 上看到的是 GitHub 自己的 600，两者同值但来源不同） |

再打开 `https://fh6-car-db.pages.dev/output/assets/car/1006.webp` 确认图片正常——如果 404，说明 `assets` 目录没被拷进 `dist`，回头检查构建命令。

### A4. 绑定 www

⚠️ **顺序不能反**：先删旧记录，再加自定义域。

1. `DNS → Records`，找到 `www` 指向 `*.github.io` 的 CNAME，**删除**
2. 回到 Pages 项目 → `Custom domains` → `Set up a custom domain`
3. 输入 `www.forzacardb.top` → `Continue` → `Activate domain`
4. 等状态变为 `Active`（通常 1–5 分钟）

**常见失败**：第 2 步报「记录已存在」→ 说明第 1 步没删干净（可能还有 A 记录或重复 CNAME）。

### A5. 绑定根域（顺手修掉现在的空白）

同样在 `Custom domains` 添加 `forzacardb.top`。Cloudflare 支持在根域做 CNAME 展平，会自动建好记录。

**验收 A5**：

```bash
curl -sI https://forzacardb.top/ | head -3     # 期望 200 或 301，不再是超时
curl -sI https://www.forzacardb.top/output/zh-hans.html | grep -i 'x-github\|x-served-by'   # 期望无输出
```

### A6. 关闭 GitHub Pages

确认 A4/A5 都正常后再做：

```
GitHub 仓库 → Settings → Pages → Source 设为 None
```

**不要删** `.github/workflows/static.yml`，回滚时要靠它一键恢复。

### A7. 阶段 A 验收

```bash
# 1) 源站已换
curl -sI https://www.forzacardb.top/output/zh-hans.html | grep -i 'x-github\|x-served-by'   # 空

# 2) 缓存头按我们写的来
curl -sI https://www.forzacardb.top/output/assets/fonts/selawik-400.woff2 | grep -i cache-control
# 期望：public, max-age=31536000, immutable

# 3) 图片 30 天
curl -sI https://www.forzacardb.top/output/assets/car/1006.webp | grep -i cache-control
# 期望：public, max-age=2592000, stale-while-revalidate=604800

# 4) 后台页 no-store
curl -sI https://www.forzacardb.top/output/admin.html | grep -iE 'cache-control|x-robots'
# 期望：no-store + noindex, nofollow
```

---

## 阶段 B：反馈接口（D1 + Pages Functions）

### B1. 建 D1

```
Workers & Pages → D1 SQL Database → Create
Name: fh6_contacts
Location: 就近（如 APAC）
```

### B2. 建表

进入该库 → `Console` → 粘贴 `d1/contact-schema.sql` 全文 → 执行。

**验收 B2**：

```sql
SELECT name FROM sqlite_master WHERE type='table';
-- 应看到 contacts
```

### B3. 绑定到 Pages 项目

```
Pages 项目 → Settings → Bindings → Add → D1 database
Variable name: DB            ← 必须与代码 env.DB 一致，大小写敏感
D1 database:   fh6_contacts
Environment:   Production（Preview 可另配）
```

### B4. 重新部署（关键）

**绑定不会自动生效**，必须触发一次新部署：

```
Deployments → 右上角 Retry deployment
```

**验收 B4**：

```bash
curl -s https://www.forzacardb.top/api/contact -w ' [%{http_code}]\n'
# 期望：{"error":"只支持 POST"} [405]     ← JSON，不是 HTML 404
```

返回 HTML 404 说明别急着往下走：`functions/` 没被编译，或构建输出目录不对。

### B5. 提交链路验收

```bash
curl -s -X POST https://www.forzacardb.top/api/contact \
  -H 'content-type: application/json' \
  -d '{"name":"测试","contact":"test@example.com","message":"迁移验收"}' -w ' [%{http_code}]\n'
# 期望：{"ok":true,"id":1} [200]
```

查库确认：

```bash
npx wrangler d1 execute fh6_contacts --remote \
  --command="SELECT id,name,message,datetime(created_at,'unixepoch','+8 hours') t FROM contacts ORDER BY id DESC LIMIT 5"
```

浏览器验收：打开 `https://www.forzacardb.top/output/feedback.html`，填完提交应显示「已收到，感谢反馈」。

---

## 阶段 C：防刷

### C1. 创建 Turnstile

```
Turnstile → Add site
Site name: forzacardb.top
Hostnames: www.forzacardb.top、forzacardb.top、fh6-car-db.pages.dev
Widget mode: Managed
```

记下 **Site Key**（公开）和 **Secret Key**（保密）。

### C2. Site Key 写进页面

编辑 `output/feedback.html` 顶部：

```js
const SITE_KEY = "0x4AAA...";   // ← 换成你的 Site Key
```

提交推送，等 Pages 自动构建完成。

**注意**：`output/feedback.html` 不是构建生成的，改完直接提交即可；但若你重跑 `python build_web.py`，它不会被覆盖（构建只写 8 个索引页和 admin.html）。

### C3. Secret 存成环境变量

```bash
npx wrangler pages secret put TURNSTILE_SECRET --project-name fh6-car-db
```

或控制台：`Settings → Variables and Secrets → Add → Secret`。

改完**再部署一次**。

**验收 C2+C3**：打开反馈页，应看到人机验证组件；不带 token 直接 POST 应返回 `403 人机验证未通过`。

### C4. WAF 速率限制

```
Security → WAF → Rate limiting rules → Create rule
Name: contact-form
匹配表达式: http.request.uri.path eq "/api/contact"
速率: 同一 IP / 60 秒 / 3 次
动作: Block
持续时间: 60 秒
```

**验收 C4**：

```bash
for i in 1 2 3 4; do curl -s -o /dev/null -w "$i:%{http_code} " -X POST \
  https://www.forzacardb.top/api/contact -H 'content-type: application/json' \
  -d '{"name":"t","contact":"t@t.co","message":"hi"}'; done; echo
# 期望：第 4 次为 429 或 403
```

> 免费版可配的规则条数有限，具体以控制台提示为准；代码里还有一层 D1 计数限流兜底，即使 WAF 没配上也不会被灌爆。

---

## 阶段 D：登录与后台（独立工程，不在本次迁移内）

**先说清楚**：阶段 A–C 完成后，`/output/admin.html` 依然会显示「无法连接 API」。因为 Pages 只提供静态资源和边缘函数，而登录、收藏、调校、评分、分级后台都在 `server/` 那套 Node 服务里，它现在没有被部署到任何地方。

两条路，二选一：

### D-1：Node 服务 + 独立子域（改动小）

| 步骤 | 内容 | 前置改动 |
|---|---|---|
| 1 | 云主机部署 `server/`（Docker），监听 8787 | 无 |
| 2 | Cloudflare 建 `api.forzacardb.top` 指向该主机 | 无 |
| 3 | 前端注入 `window.__FH6_API__` | 需改 `web_template.py` 一处 |
| 4 | 后台页支持跨域 | 需改 `build_web.py` 的 ADMIN_HTML（目前只认相对路径） |
| 5 | 服务端放开 CORS | 需在 `server.mjs` 加 `Access-Control-Allow-Origin` + `Allow-Credentials` |

### D-2：全量搬到 Workers + D1（工程量大）

把 `server/server.mjs` 的会话、garage、tunes、ratings 逻辑逐条翻译成 Worker + D1 查询。收益是零服务器运维，代价是要重写全部数据访问层，并处理 SQLite → D1 的差异（无 `AUTOINCREMENT` 语义差异、事务限制等）。

**建议**：先用 D-1 让功能跑起来，等玩家量真的上来了再评估 D-2。

---

## 验收总表

| # | 检查项 | 命令 | 期望 |
|---|---|---|---|
| 1 | 源站已切换 | `curl -sI …/output/zh-hans.html \| grep x-github` | 无输出 |
| 2 | HTML 缓存 | `curl -sI …/output/zh-hans.html \| grep -i cache-control` | `max-age=600, must-revalidate` |
| 3 | 图片缓存 | `curl -sI …/assets/car/1006.webp \| grep -i cache-control` | `max-age=2592000` |
| 4 | 字体缓存 | `curl -sI …/assets/fonts/selawik-400.woff2 \| grep -i cache-control` | `immutable` |
| 5 | 后台页不缓存 | `curl -sI …/output/admin.html \| grep -i cache-control` | `no-store` |
| 6 | 反馈接口存活 | `curl -s …/api/contact` | `405` JSON |
| 7 | 反馈可写库 | POST 一条 | `{"ok":true}` |
| 8 | 限流生效 | 连发 4 次 | 第 4 次 429/403 |
| 9 | 根域可访问 | `curl -sI https://forzacardb.top/` | 200/301 |

---

## 回滚

**阶段 A 回滚**（5 分钟内可完成）：

1. Cloudflare `DNS → Records`：把 `www` 改回指向 `<用户名>.github.io` 的 CNAME（保持橙云）
2. GitHub 仓库 `Settings → Pages`：Source 改回 `GitHub Actions`
3. Actions 里手动跑一次 `Deploy static content to Pages`
4. Pages 项目保留不删，随时可再切回

**阶段 B/C 回滚**：删除绑定或清空 `TURNSTILE_SECRET` 即可，D1 数据不会丢；`functions/` 目录留着不影响静态访问。

---

## 常见失败对照

| 现象 | 原因 | 处理 |
|---|---|---|
| 构建失败，提示 project name | `wrangler.toml` 的 `name` 与项目名不一致 | 改名或改 `wrangler.toml` |
| 构建成功但页面 404 | Build output directory 填错（填了 `output` 或 `/`） | 改回 `dist` |
| 图片全裂 | `dist` 里缺 `output/assets` | 检查构建命令是否拷了 `output` |
| `/api/contact` 返回 HTML 404 | `functions/` 未编译，或构建输出目录不对 | 确认目录结构与 A2 |
| `/api/contact` 500 | `DB` 绑定缺失或名字不是 `DB` | 回阶段 B3，绑完重新部署 |
| 绑自定义域报「记录已存在」 | 旧 CNAME/A 记录没删 | 回 A4 第 1 步 |
| 改了 `_headers` 不生效 | 文件没被拷进 `dist` | 检查构建命令里的 `_headers` |
| 后台页仍显示无法连接 API | 阶段 D 未做，属预期 | 见阶段 D |

---

## 配额核对（已按当前项目实际体量核算）

| 限制项 | 免费额度 | 本项目 | 结论 |
|---|---|---|---|
| 单站点文件数 | 20,000 | 1,552 | 充裕 |
| 单文件大小 | 25 MiB | 最大 1.7 MB（HTML） | 充裕 |
| 每月构建次数 | 500 | 每次推送 1 次 | 充裕 |
| 自定义域名 | 100 / 项目 | 2 | 充裕 |
| `_headers` 规则数 | 100 | 4 | 充裕 |
| Functions 请求 | 计入 Workers 计划配额 | 仅反馈接口 | 充裕 |

Sources（核实日期 2026-11-26）：
- Cloudflare Pages Limits — https://developers.cloudflare.com/pages/platform/limits/
- Pages Functions — https://developers.cloudflare.com/pages/functions/
- D1 Limits — https://developers.cloudflare.com/d1/platform/limits/
