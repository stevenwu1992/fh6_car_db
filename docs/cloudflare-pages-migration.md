# 迁移至 Cloudflare Pages：落地记录

> 对象：`fh6_car_db`（Forza Horizon 6 车辆索引）
> 目标：GitHub Pages → Cloudflare Pages，叠加分层缓存与国内链路优化
> 日期：2026-11-26

---

## 0. 先定一个前提：URL 结构不能变

这不是随便选的，是被现有代码结构逼出来的：

```
output/zh-hans.html        1.7 MB
  └─ 资源引用 "assets/car/1006.webp"        ← 相对路径，无 <base> 标签
  └─ 站内跳转 "href=zh-hant.html"           ← 同样相对
```

页面里所有资源路径都是**相对路径**，没有 `<base href>`，也没有根相对（`/assets/...`）引用。这意味着 HTML 必须从 `/output/` 目录下被访问，`assets/` 才能解析到 `/output/assets/`。

所以：

- ❌ 不能把 `output/` 直接当成站点根，否则线上地址会从 `/output/zh-hans.html` 变成 `/zh-hans.html`，历史外链、canonical、搜索引擎收录全部失效；
- ❌ 不能用 `_redirects` 把 `/` 用 200 重写到 `/output/zh-hans.html`，因为那样相对路径会从根目录解析，整站图片全裂；
- ✅ **保持 `/output/` 这一层路径不动**，站点根目录只是仓库里站点文件的镜像。

### 0.1 为什么输出目录用 `dist` 而不是仓库根

理论上把构建输出目录设成 `/` 也能跑，但那样 `build.py`、`web_template.py`、`server/` 这些源码会一起被上传成公开可访问的静态文件。控制台里没有任何「排除文件」的开关，而 `.assetsignore` 在 **Git 自动构建**场景下是否生效，官方文档没有明确承诺（它确定支持的是 `wrangler pages deploy` 直传）。

所以用一个一行构建命令把站点「挑」进 `dist/`，是唯一确定的行为：

```bash
mkdir -p dist && cp -r index.html output _headers dist/ && rm -rf dist/output/tables dist/output/*.sqlite dist/output/*.xlsx
```

这样：

- 部署包里只有 `index.html`、`output/`、`_headers`，源码一行都不进去；
- URL 仍是 `/output/zh-hans.html`，相对路径照旧成立；
- `_headers` 被显式拷进输出根，不依赖任何隐式规则。

最后那串 `rm -rf` 是给**本地直传**兜底的：`output/` 里有 `*.sqlite`（13 MB）、`*.xlsx`、`tables/` 三个被 gitignore 的产物，Git 构建拉不到它们，但你本地跑 `wrangler pages deploy dist` 时会被一起传上去——那是一份 13 MB 的数据库文件公开可下载。Git 构建时这些路径不存在，`rm -rf` 静默跳过，不会报错。

> 如果哪天忘了拷 `_headers`，站点能正常访问，只是缓存头全部不生效——这种「静默失效」一定要在验证清单里查（见第 5 节第 1 条）。

---

## 1. 本次新增的文件

| 文件 | 位置 | 作用 |
|---|---|---|
| `_headers` | 仓库根（构建时拷进 `dist/`） | 分级 Cache-Control + 安全头 + 预览域 noindex |
| `docs/cloudflare-pages-migration.md` | 仓库根 | 本文档 |

`_headers` 必须最终出现在**构建输出目录**里，由构建命令搬运；本文档只是记录，不参与部署。

---

## 2. 控制台配置

### 2.1 创建项目

```
Workers & Pages → Create → Pages → Connect to Git
  选 stevenwu1992/fh6_car_db
```

构建参数：

| 字段 | 值 | 说明 |
|---|---|---|
| Project name | `fh6-car-db` | 决定 `fh6-car-db.pages.dev` |
| Production branch | `main` | 与现有 GitHub Actions 一致 |
| Framework preset | `None` | 无框架 |
| Build command | `mkdir -p dist && cp -r index.html output _headers dist/ && rm -rf dist/output/tables dist/output/*.sqlite dist/output/*.xlsx` | 见 0.1，只挑站点文件进部署包 |
| Build output directory | `dist` | 不是 `/`，也不是 `output` |
| Root directory | 留空 | 仓库根 |

首次部署会复制约 50 MB（`output/` 下 14 MB 的 HTML + 35 MB 图片），上传耗时 1–3 分钟。部署完成后访问 `fh6-car-db.pages.dev/output/zh-hans.html`，确认内容完整、图片正常。

### 2.2 绑定域名

1. Pages 项目 → `Custom domains` → `Set up a custom domain`
2. 输入 `www.forzacardb.top`
3. **先删掉 Cloudflare DNS 里 `www` 指向 `xxx.github.io` 的那条 CNAME**，否则会报「记录已存在」或出现循环
4. 再输入根域 `forzacardb.top`，同样处理

> 域名 zone 已经在 Cloudflare，证书自动签发，通常 1–5 分钟变 Active。

### 2.3 收尾

确认新域名正常后，回 GitHub 仓库 `Settings → Pages` 关闭原服务。**建议先别删 `.github/workflows/static.yml`**，回滚时直接重开就行。

---

## 3. 缓存分层：为什么不能照抄那份指南

那份指南的核心问题是把 `/assets/*` 设成了 `max-age=31536000, immutable`。这套规则对 Vite/Next 那类产物（`index.a1b2c3.js`，文件名带内容哈希）是对的，对**你的仓库是错的**：

```
output/assets/car/1006.webp      ← 文件名 = 车辆 ID
output/assets/make/ABA.webp      ← 文件名 = 品牌缩写
output/assets/img/hero.webp      ← 固定名
```

文件名里没有哈希。`immutable` 的含义是「这个 URL 的内容永远不会变，连用户按 Ctrl+F5 都不要重新请求」。一旦你重导出了某张车辆图、或者换掉 hero 图，**老访客一年内都看不到新图，而且刷新也刷不出来**。这类问题极难自查，因为你自己测试时是无痕模式。

所以实际采用的分层是：

| 路径 | Cache-Control | 理由 |
|---|---|---|
| `/*`（主要命中 HTML） | `max-age=600, must-revalidate` | 与现状一致，10 分钟内改版能生效 |
| `/output/assets/fonts/*` | `max-age=31536000, immutable` | 字体文件名固定且不再变，安全 |
| `/output/assets/*`（图片） | `max-age=2592000, stale-while-revalidate=604800` | 30 天，过期后先给旧图再后台更新 |
| `/output/admin.html` | 跟随 `/*` + `noindex` | 后台页不进搜索 |

> ⚠️ 路径前缀必须是 `/output/assets/`，不是 `/assets/`。站点所有资源引用都是相对路径（`assets/car/1006.webp`），从 `/output/zh-hans.html` 解析出来的实际 URL 是 `/output/assets/car/1006.webp`。写成 `/assets/*` 不会报错，只是规则永不命中——这是最典型的「配置写了但没生效」。

整体收益：8 个 HTML 合计约 14 MB、`assets/` 共 35 MB，访客第二次进来 HTML 走浏览器缓存、图片走 30 天缓存，只有换设备或清缓存才重新下载。

### 3.1 边缘缓存（Cache Rules）

进入 `Caching → Cache Rules`，**顺序很重要，第一条必须是否决规则**：

**规则 1（必须放第一位）：API 不缓存**

```
名称：Bypass API
匹配：URI Path starts_with "/api/"  OR  URI Path starts_with "/auth/"  OR  URI Path equals "/health"
动作：Bypass cache
```

> 这条现在看着没用（你还没在 Pages 上跑 API），但一旦后面接 Pages Functions 或反代 Node 服务，缺了它就是灾难：`/api/me`、`/api/garage` 都是按 cookie 返回不同内容的，被边缘缓存一个月等于**把 A 用户的收藏返回给 B 用户**。Guide 里那条「Hostname equals 你的域名 → Edge TTL 1 个月」如果不加例外，正好会踩这个坑。

**规则 2：HTML 边缘长驻**

```
名称：Cache HTML on Edge
匹配：Hostname equals "www.forzacardb.top"  AND  URI Path not starts_with "/api/"
动作：Eligible for cache
      Edge TTL：Ignore cache-control header and use this TTL → 1 day
      Browser TTL：Respect existing headers
```

边缘 TTL 我建议先设 **1 天**，不要直接上 1 个月。Pages 每次部署确实会自动清理旧版本缓存，但 1 个月的窗口意味着「万一某次清理没覆盖到」，错误页面会挂很久。1 天已经足够让边缘常驻、不再回源，风险小得多。跑一周确认 `cf-cache-status` 稳定是 `HIT` 之后，再考虑拉长。

Browser TTL 选 `Respect existing headers` 是关键——这样浏览器端仍然严格执行 `_headers` 里的 600 秒，不会被边缘 TTL 带偏。

### 3.2 缓存时效总表（改了东西多久生效）

| 你改了什么 | 卡在哪一层 | 老访客多久看到新版 |
|---|---|---|
| 车表数据 / 任意 HTML | 浏览器 600 秒 | **10 分钟内**（第二次访问） |
| 车辆图片（文件名不变） | 浏览器 30 天 | **最长 30 天** |
| 字体 | 浏览器 1 年 immutable | 永远不会（字体确实不变） |
| `admin.html` | `no-store` | 立即 |

关键认知：**部署到 Cloudflare Pages 时，平台会清掉自己那层边缘缓存**，所以「边缘 1 天」在每次部署后都归零，真正的瓶颈是**浏览器那一层**。

这也意味着：控制台里点 Purge Cache 只能救新访客，救不了已经在浏览器里存了 30 天的老访客。改图要立刻生效，只有三条路：

1. **改文件名**（`1006.webp` → `1006-v2.webp`）并同步改引用 —— 最彻底，等于手动做内容哈希；
2. **加版本串**（`1006.webp?v=20261126`）—— 在 `build_web.py` 生成 HTML 时注入构建时间戳；
3. 降低 `/output/assets/*` 的 `max-age`（比如改 7 天或 1 天）—— 牺牲回访流量，换更新速度。

如果你一个月内会多次替换车辆图，建议直接降到 `max-age=604800`（7 天）；如果图片基本定型，30 天没问题。

### 3.3 协议与压缩

`Speed → Optimization`：

- `Protocol Optimization`：开 **HTTP/3 (with QUIC)**、开 **0-RTT Connection Resumption**
- `Content Optimization`：开 **Brotli**、开 **Early Hints**
- `SSL/TLS → Overview`：加密模式选 **Full (strict)**
- `SSL/TLS → Edge Certificates`：开 **Always Use HTTPS**

Brotli 对你这个页面收益很明显：1.7 MB 的 HTML 压完大约 200–300 KB，配合边缘缓存，国内首屏能从现在的 6 秒级压到 1–2 秒级。

---

## 4. 关于「第五阶段：优选 IP」——不建议做

那份指南最后的 Cloudflare for SaaS + CloudflareST 方案，在你的场景里会**直接打碎现在的架构**：

1. 它要求把 `forzacardb.top` 的 DNS 解析从 Cloudflare 迁到 DNSPod/华为云，做分运营商 A 记录；
2. 但 Pages 自定义域和 Worker 自定义域都**依赖域名托管在 Cloudflare**（CF 需要在自己的 DNS 里写 CNAME 并做归属验证）；
3. 一旦 NS 迁出，Pages 自定义域会掉线，绑定的 Worker `api.` 路由也会失效；
4. 而且优选 IP 本质是拿公共 anycast 地址做本地路由优选，属于灰色地带，Cloudflare 侧不提供任何保障。

**替代方案仍然是 EdgeOne**：等备案下来，用 CNAME 接入的方式把 `www` 挂到腾讯云 EdgeOne 中国大陆节点，回源填 `fh6-car-db.pages.dev`。这样 DNS 仍留在 Cloudflare，Pages 和后续 API 都不受影响，同时国内走境内节点。这也是设计文档 ADR-004 里那条硬约束的由来。

> 换句话说：Cloudflare Pages 负责「托管 + 缓存 + 全球可用」，EdgeOne 负责「中国大陆最后一公里」。两者是叠加关系，不是替代关系。

---

## 5. 验证清单

部署完成后，用无痕窗口 + DevTools Network 逐条核对：

```bash
# 1. HTML 头是否正确（应该看到 max-age=600 和 cf-cache-status）
curl -sI https://www.forzacardb.top/output/zh-hans.html | grep -iE 'cache-control|cf-cache|x-robots|strict-transport'

# 2. 图片是否走了 30 天缓存
curl -sI https://www.forzacardb.top/output/assets/car/1006.webp | grep -iE 'cache-control|cf-cache'

# 3. 字体是否 immutable
curl -sI https://www.forzacardb.top/output/assets/fonts/selawik-400.woff2 | grep -iE 'cache-control|cf-cache'

# 4. 确认服务端已经换成 Cloudflare Pages（不应再出现 x-github-request-id）
curl -sI https://www.forzacardb.top/output/zh-hans.html | grep -iE 'server|x-served-by|x-github'

# 5. 预览域是否被 noindex
curl -sI https://fh6-car-db.pages.dev/output/zh-hans.html | grep -i x-robots-tag
```

期望：

| 项 | 期望值 |
|---|---|
| HTML `cache-control` | `public, max-age=600, must-revalidate` |
| HTML `cf-cache-status` | 第二次请求为 `HIT` |
| 图片 `cache-control` | `public, max-age=2592000, stale-while-revalidate=604800` |
| 字体 `cache-control` | `public, max-age=31536000, immutable` |
| `x-github-request-id` | **不再出现** |
| `x-robots-tag`（预览域） | `noindex` |

浏览器侧：刷新两次，HTML 的 Size 列应显示 `(memory cache)` 或 `(disk cache)`，图片第二次应全部来自缓存。

---

## 6. 回滚

任何一步出问题，按这个顺序回：**DNS → Pages → GitHub Pages**。

1. Cloudflare DNS 把 `www` 的 CNAME 改回 `<用户名>.github.io`（保持橙云代理）
2. 等 1 分钟（CNAME 无长 TTL）
3. GitHub 仓库 `Settings → Pages` 重新启用，选 `GitHub Actions` 源
4. 推送一次空提交触发 `static.yml`

因为 Pages 项目不删数据、域名解析随时可改回，整个回滚是分钟级的，可以放心试。

---

## 7. 遗留问题

| # | 问题 | 影响 | 建议 |
|---|---|---|---|
| 1 | `admin.html` 被首页导航直接链接 | 后台入口暴露在公开页面 | 已加服务端密码登录（见 `server/README.md`）；入口仍建议从公开导航摘掉 |
| 2 | 8 个 HTML 内容几乎完全相同，仅语言/主题不同 | 约 14 MB 重复内容，每次改版 8 份全量更新 | 中期改成「外壳 + JSON 数据 + 前端渲染」，首屏可压到 100 KB 内 |
| 3 | `output/` 下无 `?v=` 版本串 | 改图后要靠 30 天缓存自然过期 | 构建时给资源加 `?v=<构建时间戳>`，就能安全启用 immutable |
| 4 | 站点仍无备案号 | 备案审核与 QQ 互联都会卡 | 备案下来后页脚补上并链 `beian.miit.gov.cn` |
