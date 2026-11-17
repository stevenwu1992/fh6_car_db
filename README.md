# Forza Horizon 6 车辆索引

一个由粉丝制作的 **《Forza Horizon 6》车辆数据库网站**：把游戏本体里的原始参数整理成可搜索、可筛选、可并排比对的静态页面。

> 非官方项目，与 Microsoft / Playground Games 无任何关联。

---

## 在线访问

- **EdgeOne Makers**：<https://fh6-car-index.edgeone.cool>
- 也可直接打开仓库内的 `output/车辆索引.html`（纯静态，无需服务器）

---

## 功能

**车辆索引**

- 691 台可驾驶车辆，每台 151 项底层字段，NPC / 街车 24 台可单独开关显示
- 车鉴视图：按品牌 / 类型 / 上线日期 / 获取方式分组
- 数据表视图：固定表头、可排序、可勾选最多 4 台并排比对（默认全量 151 项）
- 筛选：品牌、车辆类型、驱动形式、引擎位置、产地、获取途径、仅宽体套件

**搜索**

- 车名、品牌、ID、引擎型号
- **功能关键字**：`宽体套件`、`离心机增`、`后轮转向`、`主动驾驶模式` 可直接筛出具备该功能的车辆

**详情页**

- **可选改装引擎**：等级、引擎、出处、马力、扭矩、价格、质量差；逐条标注支持的增压升级（单/双/四涡轮、正排量机增、离心机增）与档位；点引擎可反查同款引擎的所有车型
- **宽体套件**：每套的价格、质量变化，以及改装后的车宽 / 车长 / 车高 / 轴距 / 前轮距 / 后轮距 / 前后离地高度 / 可用最大前后胎宽与原厂对比
- **车辆悬挂**：前后悬挂结构（中英对照）、转向手感配置、最大前轮转角；支持后轮转向的车型单独列出转角比例与介入车速
- **主动驾驶模式**：可切换的车型，以及切换时改变的离地高度、弹簧刚度、牵引力控制、驱动形式
- **轮胎配方**：41 种配方档位，可展开 92 项曲线参数
- 151 项原始字段按 12 组展示，关键标定值加粗；字段说明可搜索

**其它**

- 简体 / 繁体两套页面 × 明暗两套配色，车名与品牌可中英切换
- 纯静态、零外部依赖，可离线运行

---

## 目录结构

```
fh6_car_db/
├─ build.py             # 从游戏本体导出 SQLite（Data_Car 等原始表 + 字段字典）
├─ build_assets.py      # 从游戏素材导出车图、品牌标、头图（webp）
├─ build_web.py         # 组装前端数据 payload，渲染四份 HTML
├─ web_template.py      # 整页 HTML / CSS / JS 模板（占位符 __DATA__ / __LANG__ / __THEME__）
├─ dictionary.py        # 151 项字段的中文名、单位、取值范围、说明、分组
├─ physics_dict.py      # 物理相关字段补充说明
├─ strtable.py          # ForzaTech .str 字符串表解析
├─ tables.py            # 表结构说明
├─ field_names.py       # 字段名映射
├─ extract_assets.py    # 素材批处理工具
├─ LICENSE
└─ output/
   ├─ 车辆索引.html          # 简体 · 浅色
   ├─ 车辆索引_暗色.html      # 简体 · 暗色
   ├─ 車輛索引.html          # 繁体 · 浅色
   ├─ 車輛索引_暗色.html      # 繁体 · 暗色
   └─ assets/               # 车卡图 691 · 详情大图 691 · 品牌标 97 · 头图
```

> `output/` 下的 SQLite 数据库与 Excel 清单**不随仓库提供**：它们由游戏本体导出，
> 体积大且属于游戏原始数据，请按下面的步骤自行生成。

---

## 本地使用

直接双击 `output/车辆索引.html` 即可，页面不依赖任何 CDN 或后端服务。

如需局域网共享，仓库之外还有一套 Docker 部署方案（nginx + 静态目录），
本仓库为保持体积精简未收录。

---

## 重新构建

需要 **Windows + 已安装《Forza Horizon 6》**，因为数据直接从游戏安装目录读取。

```bash
# 1. 修改 build.py 顶部的 GAME_DIR 指向自己的游戏目录
#    默认: H:\WindowsApps\Microsoft.ForteBaseGame_*\media\stripped

python build.py            # 导出 output/FH6_车辆数据库_中文版.sqlite
python build_assets.py     # 导出 output/assets/*.webp
python build_web.py        # 渲染四份 HTML
```

依赖：`pip install openpyxl zhconv pillow numpy`

构建脚本会读取游戏内的 `CHS.zip` / `CHT.zip` / `EN.zip` 字符串表做本地化，
因此简繁、中英三套文案都来自游戏本体，不是人工翻译。

---

## 数据说明

- **原始数据**：全部字段取自《Forza Horizon 6》游戏本体（`Data_Car`、`Data_Engine`、
  `Data_CarBody`、`List_Upgrade*`、`List_Suspension*` 等表），未做数值修改。
- **派生数据**：宽体加宽量、胎宽上限、引擎置换出处、赛季 / Car Pass 获取方式等，
  由多张原始表关联计算得出，计算方式写在对应脚本的注释里。
- **缺失数据的处理**：例如 `Data_Engine.EngineName` 有 16 条空串，页面会用
  `EngineConfigID` / `AspirationTypeId` / `Displacement` 推断并在页面上以 `*` 标注，
  不把燃油车误标成纯电。

---

## 关于 AI

**本项目的代码、文案与视觉均由 AI 辅助构建**：数据结构梳理、页面模板、交互逻辑、
字段说明撰写与问题排查大量借助 AI 完成，作者负责需求定义、数据核对与验收。
浏览器端的每一处数字都来自游戏文件，可回溯到具体表与字段。

---

## 版权与免责

- 车辆名称、车辆数据、车辆渲染图、品牌标识等素材版权归
  **Microsoft Corporation / Playground Games Limited** 所有，来源为《Forza Horizon 6》游戏本体。
- 本项目为**非商业粉丝项目**，仅用于数据查询与调校参考，不含任何破解或绕过机制。
- `LICENSE` 中的 MIT 许可证仅覆盖本仓库的代码与文档，**不覆盖**上述游戏素材与数据。
- 若权利方认为内容侵权，请通过 Issue 或作者 B 站主页联系，会立即移除。

---

## 作者与反馈

- B 站：[STWU](https://space.bilibili.com/883100)
- 数据错误、功能建议、车型补充，欢迎在 B 站私信或提 Issue

## License

代码与文档以 [MIT](LICENSE) 授权；游戏素材与数据不在授权范围内，详见 LICENSE 末尾说明。
