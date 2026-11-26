"""FH6 车辆数据库字段字典（中文）。

本模块是纯数据：把 `Data_Car` 等表的每个字段翻译成中文名，并说明其
类型、单位、取值范围与设计意图。内容依据三方面交叉确认：

1. 游戏自带 `CarDetails` 表的官方中文标签与帮助文本（`IDS_HelpString_*`）；
2. 对 691 台车做数值分布统计后反推的物理单位（如 `SimPeakPower` ×100 = W）；
3. ForzaTech 系列（FH4/FH5/FH6）一脉相承的物理字段命名约定。

约定：``enums`` 键指向「枚举字典」工作表中的枚举表名，
表示该字段的取值需要到对应枚举表里查中文含义。
"""

from __future__ import annotations

from typing import Final, TypedDict


class Field(TypedDict, total=False):
    """单个字段的元数据。"""

    cn: str        # 中文名
    typ: str       # SQLite 类型 + 语义
    unit: str      # 单位
    rng: str       # 取值范围（实测）
    desc: str      # 详细说明
    enums: str     # 关联枚举表


# ---------------------------------------------------------------------------
# 分组：决定 Excel 「字段字典」工作表的排序与分组标题
# ---------------------------------------------------------------------------
FIELD_GROUPS: Final[dict[str, list[str]]] = {
    "① 标识与本地化": [
        "Id", "Year", "MakeID", "MakeName", "DisplayName", "ModelShort",
        "MediaName", "ModelId", "Thumbnail",
    ],
    "② 分类与归属": [
        "ClassID", "CarTypeID", "CarClassModifier", "FamilyModelID", "FamilyBodyID",
        "FamilySpecialID", "RegionID", "CountryID", "MaterialTypeID",
    ],
    "③ 动力总成与结构": [
        "PowertrainID", "DriveTypeID", "EnginePlacementID", "EngineConfigID",
        "CylinderID", "AspirationTypeId", "Displacement", "NumGears", "BrakeProfile",
    ],
    "④ 质量、轮胎与尺寸": [
        "CurbWeight", "WeightDistribution", "TireBrandID",
        "FrontTireWidthMM", "FrontTireAspect", "FrontWheelDiameterIN",
        "RearTireWidthMM", "RearTireAspect", "RearWheelDiameterIN",
        "StockWheelID", "FrontStockRideHeight", "RearStockRideHeight",
    ],
    "⑤ 空气动力学": [
        "BodyAeroLongitudinalDrag", "BodyAeroVerticalDrag", "BodyAeroLateralDragFront",
        "BodyAeroLateralDragRear", "BodyAeroForwardDownforceFront", "BodyAeroForwardDownforceRear",
        "BodyAeroAngleZeroDownforce", "BodyAeroWIForceScale",
        "FrontDownforceClampKG", "RearDownforceClampKG",
        "TireAeroHackShouldApply", "TireAeroHackMinSpringLoad", "TireAeroHackMaxSpringLoad",
    ],
    "⑥ 轮胎摩擦与轴荷标定": [
        "FixListingRearFricScale", "FixListingNormSlip0", "FixListingNormSlip1",
        "FixListingSteerAngle0", "FixListingSteerAngle1",
        "Traction_Road", "Traction_OffRoad", "Traction_Snow", "MinOffRoadPerfRating",
        "LatFrontScalarMax", "LatFrontScalarClamp", "LatRearScalarMax", "LatRearScalarClamp",
        "LongAccelFrontScalarMax", "LongAccelFrontScalarClamp",
        "LongAccelRearScalarMax", "LongAccelRearScalarClamp",
        "LongBrakeFrontScalarMax", "LongBrakeFrontScalarClamp",
        "LongBrakeRearScalarMax", "LongBrakeRearScalarClamp",
    ],
    "⑦ 手感与电子辅助标定": [
        "GameTorqueScale", "GameDragScale", "GameDownforceScale", "GameDownforceScaleOffroad",
        "AssistsTCSSlipDefTakeoff", "AssistsTCSSlipDefMoving", "AssistsTCSControlSpeed",
        "AssistsTCSFullEffectFricDiff", "AssistsTCSFullSteerSlipScaleRWD",
        "AssistsTCSFullSteerSlipScaleFWD", "AssistsTCSFullSteerSlipScaleAWD",
        "AutoSteerOverrideID", "AIPlayerID", "SpeedLimiterID",
        "UseTireRigidBodies", "UseMultiRaycastTireCollision",
        "SprungForcesApplyToFullCarMass", "UseForcePropLongTorque",
    ],
    "⑧ 手工性能数据": [
        "Time:0-60-sec", "Time:0-100-sec", "QuarterMileTime-sec",
        "QuarterMileSpeed-mph", "TopSpeed-mph",
    ],
    "⑨ 仿真性能（自动生成）": [
        "SimPeakPower", "SimPeakAngVel", "SimPeakTorque", "SimPeakTorqueAngVel",
        "SimRedlineAngVel", "SimTimeTo60MPH", "SimTimeTo100MPH", "SimTimeQuarterMile",
        "SimTopSpeed", "SimSpeedQuarterMile", "SimBrakeDistance60MPH",
        "SimBrakeDistance100MPH", "SimLatGees60MPH", "SimLatGees120MPH",
    ],
    "⑩ 五维评级": [
        "HandlingRating", "SpeedRating", "AccelerationRating", "BrakingRating",
        "LaunchRating", "OffroadRating",
    ],
    "⑪ 价格、等级与解锁": [
        "PI", "PerformanceIndex", "BaseCost", "BaseRarity", "MaxUpgradeWizardPerfRating",
        "ContentId", "IsPurchased", "IsUnicorn", "IsArcade", "IsDrivable",
        "NotAvailableInAutoshow", "NotAvailableInAuctionHouse",
        "DoNotAllowRemovalFromGarage", "VisibleOnlyIfOwned",
        "IsCarExperienceUnlocked", "HasCarExperience",
    ],
    "⑫ 外观、涂装与展示": [
        "CaliperRGBFront", "CaliperRGBRear", "CaliperAngleFront", "CaliperAngleRear",
        "HasLivery", "HasRaceLivery", "WingMask", "IsOpenCockpit", "IsOpenWheel",
        "ConvertibleType", "RaceMode", "PuddleScale", "GaugeID", "MakeIcon",
        "IsCameraCollidable", "UseBoxCameraCollision",
        "TurnOffHeadlightsInAutoShow", "ShowDriverInExteriorCamera",
        "IsInstalled",
    ],
}


FIELDS: Final[dict[str, Field]] = {
    # ---------------- ① 标识与本地化 ----------------
    "Id": {
        "cn": "车辆ID", "typ": "INTEGER 主键", "unit": "—", "rng": "247 ~ 4354",
        "desc": "车辆在数据库中的唯一编号，全库主键。它同时是本地化键的后缀——"
                "游戏用 `IDS_DisplayName_<Id>` 和 `IDS_ModelShort_<Id>` 去语言包里取车名，"
                "因此改一辆车的名字只需改字符串表，不必动数据库。"
                "所有子表（车身、升级、涂装）都靠它或它的十倍值关联。",
    },
    "Year": {
        "cn": "车型年份", "typ": "INT", "unit": "年", "rng": "1932 ~ 2554",
        "desc": "车辆的款型年份（Model Year），即厂商发布该代车型的年份，不是上牌年份。"
                "游戏中用于车库排序、分代筛选与赛事年代限制。"
                "注意库内存在 2554 这类明显笔误值，属原始数据瑕疵。",
    },
    "MakeID": {
        "cn": "品牌ID", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 262（96 个品牌在用）",
        "desc": "制造商编号，指向 `List_CarMake.ID`。用它可以取到品牌的中文名、"
                "厂商代码（如 TOY/FER/POR）与品牌 Logo 资源路径。",
        "enums": "List_CarMake",
    },
    "MakeName": {
        "cn": "品牌名称（本地化键）", "typ": "TEXT", "unit": "—", "rng": "`_&…` 哈希键",
        "desc": "品牌显示名的本地化哈希键，是 `List_CarMake.DisplayName` 的冗余副本，"
                "放在主表里避免每次都要 JOIN。需经语言包解析后才能看到「丰田」这类文字，"
                "直接看是 `_&8687362392245583904` 这样的数字串。",
    },
    "DisplayName": {
        "cn": "车型名称（本地化键）", "typ": "TEXT", "unit": "—", "rng": "`_&…` 哈希键",
        "desc": "车型本身的名字，**不含品牌**，如「2000GT」「F355 Berlinetta」「Integra Type R」。"
                "游戏里的完整车名 = 品牌 + 该字段。哈希无法逆向，但键名规律是 "
                "`IDS_DisplayName_<Id>`，按 Id 到 `Data_Car.str` 里查即可精确还原。",
    },
    "ModelShort": {
        "cn": "车型简称（本地化键）", "typ": "TEXT", "unit": "—", "rng": "`_&…` 哈希键",
        "desc": "带款型年份的紧凑车名，如「丰田 2000GT」「911 Carrera '73」，"
                "用于车库列表、HUD 等空间紧张的场合；键名为 `IDS_ModelShort_<Id>`。"
                "注意它与 `DisplayName` 的写法并不完全对称（有的含品牌、有的不含），"
                "是两套独立的文案。",
    },
    "MediaName": {
        "cn": "资源名", "typ": "TEXT", "unit": "—", "rng": "如 `TOY_2000GT_69`",
        "desc": "车辆资源的内部代号，命名规则是「品牌代码_车型_年份后两位」。"
                "它是整库最重要的关联键之一：`Data_Engine`、`Data_Motor` 都靠它挂到车上，"
                "模型、贴图、引擎音效也按这个名去找。替换/移植车辆时改的就是它。",
    },
    "ModelId": {
        "cn": "模型ID", "typ": "INT", "unit": "—", "rng": "247 ~ 4354",
        "desc": "指向车辆外观模型资源的编号。绝大多数情况下与 `Id` 相同，"
                "个别换壳车（同底盘不同年份）会出现差异，做模型替换时要按此字段判断。",
    },
    "Thumbnail": {
        "cn": "缩略图路径", "typ": "TEXT 资源路径", "unit": "—", "rng": "`game:\\Media\\…\\Thumbnail_<Id>.png`",
        "desc": "车库缩略图的相对资源路径，文件名中的数字就是 `Id`。"
                "想批量导出/替换车辆图标，按这个路径定位即可。",
    },

    # ---------------- ② 分类与归属 ----------------
    "ClassID": {
        "cn": "车辆等级", "typ": "INT 外键", "unit": "—", "rng": "0 ~ 6（D/C/B/A/S1/S2/R）",
        "desc": "车辆的赛事等级，指向 `CarClasses.Id`。0=D、1=C、2=B、3=A、4=S1、5=S2、6=R。"
                "等级由性能指标 PI 决定（400/500/600/700/800/900/998 为分界），"
                "但存储的是等级而不是阈值，所以改 PI 不会自动跟着改等级。"
                "本版本没有 X 级（ClassID=7）的原生车辆，自行改车的才会用上。",
        "enums": "CarClasses",
    },
    "CarTypeID": {
        "cn": "车辆类型", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 3",
        "desc": "1=量产车、2=预先调校车（Pre-Tuned，已装好升级件）、3=赛车。"
                "影响车库分组与部分赛事的准入判定。",
        "enums": "List_CarType",
    },
    "CarClassModifier": {
        "cn": "等级修正系数", "typ": "REAL", "unit": "—", "rng": "全库恒为 0",
        "desc": "为特殊车辆预留的等级偏移量，用于让某台车在计算等级时被人工抬高或压低。"
                "当前版本 691 台车全部为 0，说明该机制未启用，可直接忽略。",
    },
    "FamilyModelID": {
        "cn": "车系", "typ": "INT 外键", "unit": "—", "rng": "0 ~ 52（41 个在用）",
        "desc": "车辆所属的「车型家族」，指向 `List_FamilyModel`，取值是具体家族名"
                "（Integra / Civic / Corvette / Mustang / Skyline / 911 / 法拉利 V8 …），"
                "而不是车身形式。用于车系相关的赛事与成就。"
                "注意该字典只定义了 36 个家族（Id 1~39，中间有空洞），"
                "另有 13 个 ID 在字典里没有对应记录，那 116 台车属于「未定义车系」。",
        "enums": "List_FamilyModel",
    },
    "FamilyBodyID": {
        "cn": "车身样式", "typ": "INT 外键", "unit": "—", "rng": "0 ~ 45（34 种在用）",
        "desc": "车身结构形式（双门轿跑、四门轿车、敞篷、旅行车等），指向 `List_FamilyBody`。"
                "与车系配合使用：车系答「这是什么类型的车」，车身样式答「长什么形状」。",
        "enums": "List_FamilyBody",
    },
    "FamilySpecialID": {
        "cn": "特殊车系标记", "typ": "INT 外键", "unit": "—", "rng": "0 ~ 5（0=无）",
        "desc": "标记该车属于某个特殊玩法阵营（如电影车、极限竞速特别版等），"
                "指向 `List_FamilySpecial`。0 表示无特殊归属。",
        "enums": "List_FamilySpecial",
    },
    "RegionID": {
        "cn": "产地大区", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 3",
        "desc": "品牌所属大洲级分区，1=亚洲、2=欧洲、3=美洲。"
                "用于赛事按地区筛选（如「欧系车限定」），粒度比国家粗。",
        "enums": "List_Region",
    },
    "CountryID": {
        "cn": "出产地", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 31（14 个在用）",
        "desc": "制造商所在国家/地区，指向 `List_Country`，其国旗图标用于车库筛选。"
                "注意存的是「品牌国籍」而非产地工厂所在地，例如在美国生产的日系车仍算日本。",
        "enums": "List_Country",
    },
    "MaterialTypeID": {
        "cn": "车身材质", "typ": "INT 外键", "unit": "—", "rng": "1=铝合金，2=碳纤维",
        "desc": "车身覆盖件材质，指向 `List_MaterialType`，决定碰撞碎片的物理材质、"
                "音效与重量换算。全库只用到铝（1）与碳纤维（2）两种。",
        "enums": "List_MaterialType",
    },

    # ---------------- ③ 动力总成与结构 ----------------
    "PowertrainID": {
        "cn": "动力总成布局", "typ": "INT 外键", "unit": "—", "rng": "0 ~ 6",
        "desc": "把「驱动形式 + 引擎位置」打包成一个编号，指向 `Powertrains.Id`。"
                "0=前驱前置、1=后驱前置、2=后驱中置、3=后驱后置、4=四驱前置、5=四驱中置、6=四驱后置。"
                "它决定车库里的驱动示意图，也影响改装时的引擎置换可选范围。",
        "enums": "Powertrains",
    },
    "DriveTypeID": {
        "cn": "驱动类型", "typ": "INT 外键", "unit": "—", "rng": "1=FWD，2=RWD，3=AWD",
        "desc": "驱动形式。物理上决定扭矩分配到哪些车轮，"
                "也是调校界面里差速器、中央差速器滑块的可见性开关。",
        "enums": "List_DriveType",
    },
    "EnginePlacementID": {
        "cn": "引擎位置", "typ": "INT 外键", "unit": "—", "rng": "1=前置，2=中置，3=后置",
        "desc": "引擎相对乘员舱的位置。官方帮助文本：「通常会影响车重分配」。"
                "它同时约束可用的引擎置换套件与传动布局。",
        "enums": "List_EnginePlacement",
    },
    "EngineConfigID": {
        "cn": "引擎形式", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 6",
        "desc": "气缸排布形式：1=V型、2=W型、3=直列、4=转子、5=水平对置(F)、6=电动(E)。"
                "库里另定义了 SH/PH/SPH（星型等特殊形式）但无车辆使用。",
        "enums": "List_EngineConfig",
    },
    "CylinderID": {
        "cn": "气缸数", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 14",
        "desc": "气缸数量分类，指向 `List_Cylinders`，中文描述如「四汽缸」「双转子」。"
                "注意它同时覆盖转子引擎（按转子数计）和电动机（ID 10 为电子式）。",
        "enums": "List_Cylinders",
    },
    "AspirationTypeId": {
        "cn": "进气形式", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 8",
        "desc": "自然进气 / 涡轮 / 双涡轮 / 四涡轮 / 离心式机械增压(DSC) / 正排量机械增压(CSC) / 涡轮+机增 / 无。"
                "决定增压值曲线、泄压阀音效与可安装的增压升级件。",
        "enums": "List_Aspiration",
    },
    "Displacement": {
        "cn": "排气量", "typ": "INT", "unit": "cm³ (cc)", "rng": "0 ~ 8383",
        "desc": "引擎总排气量，单位毫升。0 表示纯电动车（无内燃机）。"
                "这是排量税、赛事分级（如 2.0L 以下组）等规则的直接依据。",
    },
    "NumGears": {
        "cn": "档位数", "typ": "INT", "unit": "档", "rng": "1 ~ 10",
        "desc": "变速箱前进档数量。1 档为电动车的单速减速器。"
                "影响极速与加速的平衡，也是改装变速箱时齿比表的行数。",
    },
    "BrakeProfile": {
        "cn": "刹车配置ID", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 102（34 种在用）",
        "desc": "指向 `List_BrakeProfile` 的刹车系统参数组，包含前后刹车盘尺寸、"
                "卡钳活塞数、热容量与衰退曲线。改刹车升级件时实际切换的就是这个 Profile。",
        "enums": "List_BrakeProfile",
    },

    # ---------------- ④ 质量、轮胎与尺寸 ----------------
    "CurbWeight": {
        "cn": "整备质量", "typ": "REAL", "unit": "×100 kg（数值 ×100 = kg）", "rng": "1.406 ~ 95.0",
        "desc": "车辆总质量，官方帮助文本说明「包括车手重量」。"
                "单位是 100 kg：库里 14.4543 表示 1445 kg。"
                "这是全库影响最大的单一物理量——加速、刹车、过弯、悬挂全部由它缩放。",
    },
    "WeightDistribution": {
        "cn": "前轴重量比", "typ": "REAL", "unit": "比例 (0~1)", "rng": "0.33 ~ 0.66",
        "desc": "静止时前轮承担的重量百分比，0.52 即前后 52:48。"
                "直接决定转向不足/转向过度的基础倾向，也是调校界面显示的配重条。",
    },
    "TireBrandID": {
        "cn": "轮胎品牌ID", "typ": "INT 外键", "unit": "—", "rng": "0 ~ 35（15 种在用）",
        "desc": "原厂轮胎品牌编号，0 表示无品牌（多为基础车或赛车）。"
                "品牌只是外观/文案差异，真正的抓地力由 `List_UpgradeTireCompound` 决定。",
        "enums": "List_PartManufacturer",
    },
    "FrontTireWidthMM": {
        "cn": "前胎宽度", "typ": "INT", "unit": "mm", "rng": "90 ~ 420",
        "desc": "前轮胎面宽度。官方帮助文本：「轮胎宽度/扁平比/轮辋直径」三件套的第一项。"
                "宽度越大接地面积越大，抓地力与滚阻同步上升。",
    },
    "FrontTireAspect": {
        "cn": "前胎扁平比", "typ": "INT", "unit": "%", "rng": "23 ~ 115",
        "desc": "胎壁高度占胎宽的百分比。官方说明：「扁平比代表轮胎高度与宽度的百分比」。"
                "数值小=薄胎（操控精准但颠簸），数值大=厚胎（舒适、越野）。",
    },
    "FrontWheelDiameterIN": {
        "cn": "前轮辋直径", "typ": "INT", "unit": "英寸", "rng": "5 ~ 24",
        "desc": "前轮辋（不含轮胎）的直径。与胎宽、扁平比一起决定轮胎外径，"
                "进而影响终传比与实际车速表读数。",
    },
    "RearTireWidthMM": {
        "cn": "后胎宽度", "typ": "INT", "unit": "mm", "rng": "90 ~ 535",
        "desc": "后轮胎面宽度。后驱大马力车通常明显宽于前胎以抑制打滑，"
                "库里最大 535mm 属直线加速赛车规格。",
    },
    "RearTireAspect": {
        "cn": "后胎扁平比", "typ": "INT", "unit": "%", "rng": "23 ~ 100",
        "desc": "后胎胎壁高度与胎宽之比。",
    },
    "RearWheelDiameterIN": {
        "cn": "后轮辋直径", "typ": "INT", "unit": "英寸", "rng": "5 ~ 24",
        "desc": "后轮辋直径。前后不同直径在直线加速车与复古车上很常见。",
    },
    "StockWheelID": {
        "cn": "原厂轮毂ID", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 15081（687 种）",
        "desc": "原厂轮辋款式编号，指向 `List_Wheels`。换轮毂时替换的就是它，"
                "决定轮辐造型、材质与重量。",
        "enums": "List_Wheels",
    },
    "FrontStockRideHeight": {
        "cn": "前原厂车高", "typ": "REAL", "unit": "m", "rng": "0.040 ~ 0.897",
        "desc": "前轴原厂离地间隙（静态车高）。调校界面「车高」滑块的默认值，"
                "降低车高可降低重心与风阻，但会减少悬挂行程导致托底。",
    },
    "RearStockRideHeight": {
        "cn": "后原厂车高", "typ": "REAL", "unit": "m", "rng": "0.045 ~ 0.897",
        "desc": "后轴原厂离地间隙。前后车高差决定车辆的「rake」姿态，"
                "影响高速下压力分布。",
    },

    # ---------------- ⑤ 空气动力学 ----------------
    "BodyAeroLongitudinalDrag": {
        "cn": "纵向风阻", "typ": "REAL", "unit": "内部力单位（≈N @ 参考速度）", "rng": "52.9 ~ 1697.6",
        "desc": "车身沿行驶方向的阻力系数，数值越大越「顶风」，极速越低。"
                "这是决定极速的第一因素，与 `GameDragScale` 相乘后生效。",
    },
    "BodyAeroVerticalDrag": {
        "cn": "垂直风阻", "typ": "REAL", "unit": "内部力单位", "rng": "全库恒为 500.0",
        "desc": "车身竖直方向的阻尼系数（抑制车辆被「吸起」或「压扁」）。"
                "全库统一 500，说明是全局常量而非按车调校，实际分析时可忽略。",
    },
    "BodyAeroLateralDragFront": {
        "cn": "前部侧向风阻", "typ": "REAL", "unit": "内部力单位", "rng": "165 ~ 450",
        "desc": "车头受到横向气流时的阻力，主要影响漂移时的车身横摆阻尼——"
                "数值越大，车尾甩出去后被「风」拉回来的力越强，手感越稳。",
    },
    "BodyAeroLateralDragRear": {
        "cn": "后部侧向风阻", "typ": "REAL", "unit": "内部力单位", "rng": "170 ~ 640",
        "desc": "车尾的横向气动阻尼。后部远大于前部时，高速横摆更安定；"
                "漂移车通常在这里调低以获得更活的尾部。",
    },
    "BodyAeroForwardDownforceFront": {
        "cn": "前部下压力", "typ": "REAL", "unit": "内部力单位（可负）", "rng": "-112.1 ~ 453.3",
        "desc": "前轴在参考速度下产生的下压力。负值表示实际是「升力」——"
                "老式车与掀背车常见的车头飘。这是前轮高速抓地力的关键来源。",
    },
    "BodyAeroForwardDownforceRear": {
        "cn": "后部下压力", "typ": "REAL", "unit": "内部力单位（可负）", "rng": "-77.9 ~ 626.1",
        "desc": "后轴下压力。尾翼升级会显著抬高此值。"
                "前后配比失衡会导致高速时前后抓地力不均，典型症状是高速推头或甩尾。",
    },
    "BodyAeroAngleZeroDownforce": {
        "cn": "零升力攻角", "typ": "REAL", "unit": "度", "rng": "全库恒为 45.0",
        "desc": "车身攻角达到该角度时下压力归零的参考角。全库统一 45°，"
                "属全局标定值，不用于区分车型。",
    },
    "BodyAeroWIForceScale": {
        "cn": "风阻-下压力耦合系数", "typ": "REAL", "unit": "倍率", "rng": "0.14 ~ 1.75",
        "desc": "把「风阻」与「下压力」绑定的比例系数（WI = Wing/Induced）。"
                "数值高意味着该车的下压力主要靠增加风阻换来——"
                "正是赛车尾翼的物理本质，也解释了为何大尾翼车极速会掉。",
    },
    "FrontDownforceClampKG": {
        "cn": "前部下压力上限", "typ": "REAL", "unit": "kg", "rng": "140 ~ 1673.8",
        "desc": "前轴下压力的硬上限，防止极端调校或高速度下产生不合理的物理数值。"
                "超跑与赛车才需要大值。",
    },
    "RearDownforceClampKG": {
        "cn": "后部下压力上限", "typ": "REAL", "unit": "kg", "rng": "260 ~ 1970.5",
        "desc": "后轴下压力硬上限。与前一字段共同决定「最大能压多死」，"
                "是判断一台车能否跑出高下压力调校的依据。",
    },
    "TireAeroHackShouldApply": {
        "cn": "启用轮胎气动修正", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 0",
        "desc": "是否对轮胎施加额外的气动阻力/下压力修正。当前版本全局关闭，"
                "属于遗留开关。",
    },
    "TireAeroHackMinSpringLoad": {
        "cn": "气动修正-最小弹簧载荷", "typ": "REAL", "unit": "内部力单位", "rng": "全库恒为 5.0",
        "desc": "上述修正生效所需的弹簧载荷下限，配合 `TireAeroHackShouldApply` 使用，"
                "开关关闭时无意义。",
    },
    "TireAeroHackMaxSpringLoad": {
        "cn": "气动修正-最大弹簧载荷", "typ": "REAL", "unit": "内部力单位", "rng": "全库恒为 5.0",
        "desc": "上述修正的弹簧载荷上限。同上，开关关闭时无意义。",
    },

    # ---------------- ⑥ 轮胎摩擦与轴荷标定 ----------------
    "FixListingRearFricScale": {
        "cn": "后轴摩擦修正系数", "typ": "REAL", "unit": "倍率", "rng": "全库恒为 1.35",
        "desc": "用于修正「清单式」轮胎模型下后轴摩擦力的缩放值（Fix Listing 是"
                "一套旧的轮胎数据兼容逻辑）。全库统一，属全局参数。",
    },
    "FixListingNormSlip0": {
        "cn": "修正滑移起点", "typ": "REAL", "unit": "归一化滑移率", "rng": "全库恒为 0.5",
        "desc": "上述修正的滑移率区间下界，与下一字段构成线性插值区间。全库统一。",
    },
    "FixListingNormSlip1": {
        "cn": "修正滑移终点", "typ": "REAL", "unit": "归一化滑移率", "rng": "全库恒为 1.0",
        "desc": "上述修正的滑移率区间上界。全库统一。",
    },
    "FixListingSteerAngle0": {
        "cn": "修正转向角起点", "typ": "REAL", "unit": "归一化转角", "rng": "全库恒为 0.5",
        "desc": "修正生效的转向角区间下界。全库统一。",
    },
    "FixListingSteerAngle1": {
        "cn": "修正转向角终点", "typ": "REAL", "unit": "归一化转角", "rng": "全库恒为 1.0",
        "desc": "修正生效的转向角区间上界。全库统一。",
    },
    "Traction_Road": {
        "cn": "路面抓地力", "typ": "REAL", "unit": "系数 (0~1)", "rng": "0.000 ~ 1.000",
        "desc": "沥青路面下的整体抓地力缩放。它是「这台车在柏油路上能有多抓」的总开关，"
                "与轮胎配方、下压力相乘后决定实际过弯 G 值。越野胎在这里通常偏低。",
    },
    "Traction_OffRoad": {
        "cn": "越野抓地力", "typ": "REAL", "unit": "系数 (0~1)", "rng": "0.000 ~ 1.000",
        "desc": "草地、泥地等非铺装路面的抓地力缩放。"
                "拉力车与皮卡普遍高于同级别跑车，是判断车辆「能不能下土路」的直接指标。",
    },
    "Traction_Snow": {
        "cn": "雪地抓地力", "typ": "REAL", "unit": "系数 (0~1)", "rng": "0.000 ~ 0.998",
        "desc": "冰雪路面的抓地力缩放。四季赛季节切换时这项差异会被放大，"
                "也是雪地调校的核心变量。",
    },
    "MinOffRoadPerfRating": {
        "cn": "越野性能下限", "typ": "REAL", "unit": "PI 归一化值 (0~1)", "rng": "0.000 ~ 0.821",
        "desc": "越野场景下的性能指标保底值。普通跑车进越野赛事时会被这项「兜底」拉低评分，"
                "避免出现跑车在泥地刷分的失衡情况。",
    },
    "LatFrontScalarMax": {
        "cn": "前轴侧向抓地上限", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "前轮侧向（过弯）摩擦力的最大缩放系数。数值 >1 相当于给前轮额外抓地，"
                "是调节转向不足的重要手段；0 表示禁用该修正。",
    },
    "LatFrontScalarClamp": {
        "cn": "前轴侧向抓地箝位", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "上述系数的硬性上限（clamp）。与 Max 的区别在于 Clamp 是保证不会被"
                "物理求解器越过的绝对边界，Max 是曲线峰值目标。",
    },
    "LatRearScalarMax": {
        "cn": "后轴侧向抓地上限", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "后轮侧向摩擦力的最大缩放系数。调高更容易转向不足（稳），"
                "调低则尾部更活（易甩尾）。",
    },
    "LatRearScalarClamp": {
        "cn": "后轴侧向抓地箝位", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "后轴侧向系数的硬上限。",
    },
    "LongAccelFrontScalarMax": {
        "cn": "前轴加速抓地上限", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "前轮在纵向加速时的摩擦缩放。四驱与前驱车此值影响起步打滑程度。",
    },
    "LongAccelFrontScalarClamp": {
        "cn": "前轴加速抓地箝位", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "前轴加速系数的硬上限。",
    },
    "LongAccelRearScalarMax": {
        "cn": "后轴加速抓地上限", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "后轮纵向加速摩擦缩放。后驱大马力车此项决定「能不能起步不打滑」，"
                "也是弹射起步表现的关键参数。",
    },
    "LongAccelRearScalarClamp": {
        "cn": "后轴加速抓地箝位", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "后轴加速系数的硬上限。",
    },
    "LongBrakeFrontScalarMax": {
        "cn": "前轴制动抓地上限", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "前轮在刹车时的摩擦缩放。前刹承担大部分制动力，此值直接决定"
                "100-0 的刹车距离与刹车时的点头幅度。",
    },
    "LongBrakeFrontScalarClamp": {
        "cn": "前轴制动抓地箝位", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "前轴制动的硬上限。",
    },
    "LongBrakeRearScalarMax": {
        "cn": "后轴制动抓地上限", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "后轮刹车摩擦缩放。过高会让车尾在重刹时先失去附着而甩尾。",
    },
    "LongBrakeRearScalarClamp": {
        "cn": "后轴制动抓地箝位", "typ": "REAL", "unit": "倍率", "rng": "0.00 ~ 2.00",
        "desc": "后轴制动的硬上限。",
    },

    # ---------------- ⑦ 手感与电子辅助标定 ----------------
    "GameTorqueScale": {
        "cn": "扭矩输出缩放", "typ": "REAL", "unit": "倍率", "rng": "0.66 ~ 1.13",
        "desc": "把引擎台架扭矩乘以该系数后送进物理引擎——本质是「手感作弊系数」。"
                "大于 1 的车（如经典肌肉车）实际推背感比台架数据更强，"
                "小于 1 的车（如某些实测过猛的电动车）会被削弱。分析真实性能时应乘上它。",
    },
    "GameDragScale": {
        "cn": "风阻缩放", "typ": "REAL", "unit": "倍率", "rng": "0.70 ~ 1.30",
        "desc": "整车风阻的乘数，直接乘在车身纵向风阻上：1.0 为原始值，"
                "数值越大风阻越高、极速越低；越小风阻越省、极速越高。"
                "因阻力功率与速度的立方成正比，极速大致按该系数的 −1/3 次方变化，"
                "1.30 约损失 8% 极速，0.70 约多出 12%。"
                "它只在实时驾驶层生效，库里的 SimTopSpeed 用纯车身风阻算出，不含此系数。",
    },
    "GameDownforceScale": {
        "cn": "下压力缩放（铺装）", "typ": "REAL", "unit": "倍率", "rng": "0.60 ~ 1.70",
        "desc": "铺装路面上整体下压力的乘数，与车身气动数据相乘后生效。"
                "是调整「高速贴地感」最直接的旋钮。",
    },
    "GameDownforceScaleOffroad": {
        "cn": "下压力缩放（越野）", "typ": "REAL", "unit": "倍率", "rng": "0.10 ~ 2.00",
        "desc": "非铺装路面下的下压力乘数。越野时下压力意义有限，"
                "该值通常远低于铺装值，避免飞坡时被「吸」在地上。",
    },
    "AssistsTCSSlipDefTakeoff": {
        "cn": "TCS 起步滑移阈值", "typ": "REAL", "unit": "归一化滑移率", "rng": "全库恒为 33.0",
        "desc": "牵引力控制系统在起步阶段介入的滑移率门限。全库统一 33，"
                "说明起步阶段 TCS 判定为全局逻辑，不按车型区分。",
    },
    "AssistsTCSSlipDefMoving": {
        "cn": "TCS 行驶滑移阈值", "typ": "REAL", "unit": "归一化滑移率", "rng": "0.25 ~ 0.70",
        "desc": "行驶中介入的滑移率门限。数值越小 TCS 越早介入、车越「老实」；"
                "大马力后驱车通常给较大值，允许更多打滑。",
    },
    "AssistsTCSControlSpeed": {
        "cn": "TCS 响应速度", "typ": "INT", "unit": "内部速率", "rng": "25 或 30",
        "desc": "TCS 削减扭矩的快慢，全库只有 25/30 两档。可近似理解为"
                "「电子系统反应有多急」，与车辆性格对应。",
    },
    "AssistsTCSFullEffectFricDiff": {
        "cn": "TCS 全效摩擦差", "typ": "REAL", "unit": "摩擦差", "rng": "0.55 ~ 1.00",
        "desc": "TCS 达到完全介入强度所需的轮速差阈值。越小越容易触发大力干预，"
                "雨雪天手感差异主要来自这里。",
    },
    "AssistsTCSFullSteerSlipScaleRWD": {
        "cn": "TCS 打方向滑移缩放（后驱）", "typ": "REAL", "unit": "倍率", "rng": "0.90 ~ 2.50",
        "desc": "后驱车在打方向时允许的额外滑移量。调大可让 TCS 在转向时更宽容，"
                "过弯不被电子系统「掐死」。",
    },
    "AssistsTCSFullSteerSlipScaleFWD": {
        "cn": "TCS 打方向滑移缩放（前驱）", "typ": "REAL", "unit": "倍率", "rng": "1.00 / 2.50",
        "desc": "前驱车的对应参数。前驱车打方向同时给油容易推头，此项决定电子系统"
                "在多大程度上容忍前轮空转。",
    },
    "AssistsTCSFullSteerSlipScaleAWD": {
        "cn": "TCS 打方向滑移缩放（四驱）", "typ": "REAL", "unit": "倍率", "rng": "1.00 ~ 2.50",
        "desc": "四驱车的对应参数。四驱车四个轮子都可打滑，TCS 的宽容度标定更关键。",
    },
    "AutoSteerOverrideID": {
        "cn": "自动转向配置ID", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 3",
        "desc": "指向 `AutoSteerOverrides`，覆盖辅助转向（自动补方向）的参数组。"
                "影响开启辅助时车辆的自动修正幅度。",
        "enums": "AutoSteerOverrides",
    },
    "AIPlayerID": {
        "cn": "AI 车手模型ID", "typ": "INT", "unit": "—", "rng": "全库恒为 0",
        "desc": "指定该车在 AI 驾驶时使用的车手行为模型（`DrivatarTestingAIPlayers`）。"
                "0 表示使用默认模型。",
    },
    "SpeedLimiterID": {
        "cn": "限速器配置ID", "typ": "INT", "unit": "—", "rng": "全库恒为 0",
        "desc": "限速器参数组编号，0=无限速。理论上可用于模拟电子限速车型，"
                "当前版本未启用。",
    },
    "UseTireRigidBodies": {
        "cn": "启用轮胎刚体", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
        "desc": "是否把轮胎当作独立刚体参与碰撞求解。开启后轮胎可以单独脱落/变形，"
                "物理更真实但更吃性能，通常只在高精度车辆上开启。",
    },
    "UseMultiRaycastTireCollision": {
        "cn": "启用多射线轮胎碰撞", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 1",
        "desc": "轮胎接地判定是否使用多射线采样（而非单点）。全库统一开启，"
                "这是现代 ForzaTech 的标准做法，用于精确计算接地压力分布。",
    },
    "SprungForcesApplyToFullCarMass": {
        "cn": "簧上力作用于整车质量", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
        "desc": "悬挂受力计算时是否按整车质量而非簧上质量分配。影响过坎时车身的"
                "起伏幅度，属于手感微调开关。",
    },
    "UseForcePropLongTorque": {
        "cn": "纵向力按扭矩传播", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
        "desc": "驱动力的纵向分量是否走扭矩传播链路（而非直接施加力）。"
                "影响四驱系统前后轴扭矩分配的响应速度。",
    },

    # ---------------- ⑧ 手工性能数据 ----------------
    "Time:0-60-sec": {
        "cn": "0-60 mph 加速", "typ": "REAL", "unit": "秒", "rng": "0.0 ~ 32.8",
        "desc": "官方手工填写的 0-60 英里/小时（约 96.6 km/h）加速成绩，用于车库数值展示。"
                "注意它和后面的 `SimTimeTo60MPH`（物理仿真算出来的）并不相等——"
                "前者是宣传口径，后者是引擎实际跑出来的。",
    },
    "Time:0-100-sec": {
        "cn": "0-100 mph 加速", "typ": "REAL", "unit": "秒", "rng": "0.0 ~ 126.7",
        "desc": "0-100 mph（约 161 km/h）加速成绩，手工填写值。",
    },
    "QuarterMileTime-sec": {
        "cn": "四分之一英里耗时", "typ": "REAL", "unit": "秒", "rng": "0.0 ~ 27.7",
        "desc": "静止起步跑完 402 米（1/4 英里）所需时间，直线加速能力的经典指标。",
    },
    "QuarterMileSpeed-mph": {
        "cn": "四分之一英里尾速", "typ": "REAL", "unit": "mph", "rng": "0.0 ~ 175.0",
        "desc": "冲过 402 米终点瞬间的速度，反映中后段加速能力。",
    },
    "TopSpeed-mph": {
        "cn": "极速（标称）", "typ": "REAL", "unit": "mph", "rng": "0.0 ~ 351.0",
        "desc": "官方标称极速，用于车库展示与评级。"
                "实际能跑多快取决于风阻与齿比，见 `SimTopSpeed`。",
    },

    # ---------------- ⑨ 仿真性能 ----------------
    "SimPeakPower": {
        "cn": "峰值功率", "typ": "REAL", "unit": "×100 W（数值 ×100 = W）", "rng": "31.0 ~ 20803.5",
        "desc": "物理引擎算出的最大功率。单位是 100 瓦：库里 2236.9 即 223.7 kW ≈ 300 hp。"
                "取值来自引擎扭矩曲线与转速的乘积，是「这台车真实有多快」的核心依据。"
                "乘 `GameTorqueScale` 后才是最终输出。",
    },
    "SimPeakAngVel": {
        "cn": "峰值功率转速", "typ": "REAL", "unit": "rpm", "rng": "2000 ~ 15900",
        "desc": "达到峰值功率时的曲轴转速。库里原始值是 rad/s，展示时按 rpm = rad/s × 9.5493 换算。"
                "库内中位数约 6500 rpm。",
    },
    "SimPeakTorque": {
        "cn": "峰值扭矩", "typ": "REAL", "unit": "×100 N·m（数值 ×100 = N·m）", "rng": "0.075 ~ 40.0",
        "desc": "物理引擎算出的最大扭矩。单位是 100 牛·米：库里 2.93 即 293 N·m。"
                "与功率的关系为 P = T × ω，可据此交叉验证数据是否自洽。",
    },
    "SimPeakTorqueAngVel": {
        "cn": "峰值扭矩转速", "typ": "REAL", "unit": "rpm", "rng": "0 ~ 10200",
        "desc": "达到最大扭矩时的曲轴转速（rpm），由 rad/s × 9.5493 换算而来。"
                "它与 `SimPeakAngVel` 的差距反映引擎的「高转特性」——差距越大越偏高转。",
    },
    "SimRedlineAngVel": {
        "cn": "断油转速", "typ": "REAL", "unit": "rpm", "rng": "2500 ~ 21000",
        "desc": "引擎断油（红线）转速，展示为 rpm（由 rad/s × 9.5493 换算）。"
                "中位数约 7000 rpm，最高约 21000 rpm 属 F1 级。",
    },
    "SimTimeTo60MPH": {
        "cn": "仿真 0-60 mph", "typ": "REAL", "unit": "秒", "rng": "0.0 ~ 27.18",
        "desc": "物理引擎实算的 0-60 mph 加速成绩，包含轮胎打滑与换档损失。"
                "与手工值对比可以看出一台车的「纸面实力」和「实际手感」差多少。",
    },
    "SimTimeTo100MPH": {
        "cn": "仿真 0-100 mph", "typ": "REAL", "unit": "秒", "rng": "0.0 ~ 80.80",
        "desc": "实算的 0-100 mph 加速成绩。",
    },
    "SimTimeQuarterMile": {
        "cn": "仿真 1/4 英里耗时", "typ": "REAL", "unit": "秒", "rng": "6.68 ~ 36.00",
        "desc": "实算的四分之一英里直线加速成绩。",
    },
    "SimTopSpeed": {
        "cn": "仿真极速", "typ": "REAL", "unit": "m/s", "rng": "12.75 ~ 136.16",
        "desc": "实算极速，单位米/秒（×3.6 = km/h）。136 m/s ≈ 490 km/h。"
                "与 `TopSpeed-mph` 对比能看出风阻/齿比是否限制了标称极速。",
    },
    "SimSpeedQuarterMile": {
        "cn": "仿真 1/4 英里尾速", "typ": "REAL", "unit": "m/s", "rng": "12.74 ~ 100.31",
        "desc": "实算的四分之一英里冲线速度（m/s）。",
    },
    "SimBrakeDistance60MPH": {
        "cn": "60-0 mph 刹车距离", "typ": "REAL", "unit": "m", "rng": "0.0 ~ 60.37",
        "desc": "从 60 mph（约 97 km/h）全力刹停的距离，米。"
                "这是判断刹车升级是否值得的直接指标。",
    },
    "SimBrakeDistance100MPH": {
        "cn": "100-0 mph 刹车距离", "typ": "REAL", "unit": "m", "rng": "0.0 ~ 140.42",
        "desc": "从 100 mph（约 161 km/h）全力刹停的距离，米。",
    },
    "SimLatGees60MPH": {
        "cn": "60 mph 侧向加速度", "typ": "REAL", "unit": "g", "rng": "0.547 ~ 2.287",
        "desc": "在 60 mph 定速绕圈时能承受的最大侧向加速度（g 值）。"
                "这是「过弯能力」最硬的量化指标，比 0-100 更能区分操控好坏。",
    },
    "SimLatGees120MPH": {
        "cn": "120 mph 侧向加速度", "typ": "REAL", "unit": "g", "rng": "0.558 ~ 3.150",
        "desc": "在 120 mph 下的最大侧向加速度。高速下气动下压力开始起作用，"
                "因此该值可能高于 60 mph 的值——这正是尾翼车的特征。",
    },

    # ---------------- ⑩ 五维评级 ----------------
    "HandlingRating": {
        "cn": "操控评级", "typ": "REAL", "unit": "分 (0~10)", "rng": "2.39 ~ 9.78",
        "desc": "车库中那根「操控」进度条。官方说明：「车辆的过弯能力，用 0-10 表示」。"
                "由侧向 G 值、车重、轮胎综合算出，用于直观比较而非物理计算。",
    },
    "SpeedRating": {
        "cn": "极速评级", "typ": "REAL", "unit": "分 (0~10)", "rng": "1.00 ~ 10.00",
        "desc": "车库「极速」进度条，由 `TopSpeed-mph` 映射而来。",
    },
    "AccelerationRating": {
        "cn": "加速评级", "typ": "REAL", "unit": "分 (0~10)", "rng": "1.00 ~ 10.00",
        "desc": "车库「加速」进度条，由 0-60 成绩映射而来。",
    },
    "BrakingRating": {
        "cn": "刹车评级", "typ": "REAL", "unit": "分 (0~10)", "rng": "1.82 ~ 10.00",
        "desc": "车库「刹车」进度条，由刹车距离映射而来。",
    },
    "LaunchRating": {
        "cn": "起跑评级", "typ": "REAL", "unit": "分 (0~10)", "rng": "1.00 ~ 10.00",
        "desc": "起步能力的独立评分，综合了驱动形式、轮胎与扭矩输出特性，"
                "四驱车通常显著高于同动力后驱车。",
    },
    "OffroadRating": {
        "cn": "越野评级", "typ": "REAL", "unit": "分 (0~10)", "rng": "3.70 ~ 10.00",
        "desc": "越野能力评分，综合 `Traction_OffRoad`、悬挂行程与车高。"
                "注意全库下限是 3.70 而非 0，说明即使是超跑也保留了一点越野底分。",
    },

    # ---------------- ⑪ 价格、等级与解锁 ----------------
    "PI": {
        "cn": "性能指标（PI）", "typ": "INT", "unit": "分 (100~998)", "rng": "100 ~ 998",
        "desc": "玩家看到的性能分（Performance Index）。分档：D≤400、C≤500、B≤600、"
                "A≤700、S1≤800、S2≤900、R≤998，超过 998 即 X 级。"
                "赛事大多按 PI 限制准入，是全库最常用的筛选维度。",
    },
    "PerformanceIndex": {
        "cn": "性能指标（内部值）", "typ": "REAL", "unit": "归一化 (0~1)", "rng": "0.000 ~ 0.886",
        "desc": "PI 的内部归一化形式，`CarClasses.MaxPerformanceIndex` 用的就是这个刻度"
                "（如 D 级上限 0.2874）。它与显示 PI 之间是非线性映射，"
                "做精确分档计算时要用它而非 PI。",
    },
    "BaseCost": {
        "cn": "基础售价", "typ": "INT", "unit": "CR（游戏币）", "rng": "0 ~ 70,000,000",
        "desc": "车库购买价。0 表示不可直接购买（奖励车、赛事奖励或 DLC 独占）。"
                "注意价格会随市场波动，这里的值是定价基准而非实时行情。",
    },
    "BaseRarity": {
        "cn": "基础稀有度", "typ": "REAL", "unit": "级 (0~10)", "rng": "0.0 ~ 10.0",
        "desc": "车辆稀有度权重，影响抽奖、车展刷新与拍卖行定价倾向。"
                "8 以上通常为传奇车，10 多为极限竞速特别版或电影道具车。",
    },
    "MaxUpgradeWizardPerfRating": {
        "cn": "满改后 PI 上限", "typ": "REAL", "unit": "归一化 PI (0~1)", "rng": "0.000 ~ 0.963",
        "desc": "用「自动升级向导」把这台车改到最强时能达到的 PI 归一化值。"
                "它划定了该车的改装天花板——判断一台车值不值得练，看这个比看当前 PI 更有意义。",
    },
    "ContentId": {
        "cn": "内容包ID", "typ": "INT 外键", "unit": "—", "rng": "0 或 99",
        "desc": "车辆所属的内容包/版本，指向 `ContentOffers`。"
                "0=本体随盘车辆、99=后续更新／车包内容。"
                "用于判断某车是否需要购买 DLC 才能获得。",
        "enums": "ContentOffers",
    },
    "IsPurchased": {
        "cn": "已购买标记", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 1",
        "desc": "模板库中的默认状态位。全库为 1 只表示「在数据库层面已解锁」，"
                "玩家实际是否拥有记录在存档里，与此无关。",
    },
    "IsUnicorn": {
        "cn": "独角兽车标记", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 0",
        "desc": "历史遗留的「独角兽车」标记（指极难获得、不可交易的车）。"
                "本版本全部为 0，稀缺性改由 `BaseRarity` 与拍卖行规则控制。",
    },
    "IsArcade": {
        "cn": "街机模式车辆", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（23 台）",
        "desc": "标记该车是否出现在街机/临时驾驶玩法中。"
                "开启的车通常是交通车、特技车或剧情专用车，不进入正常车库。",
    },
    "IsDrivable": {
        "cn": "可驾驶", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 1",
        "desc": "是否允许玩家驾驶。全库为 1；若为 0 则该条目只是资源占位"
                "（如纯交通模型），不能进车库。",
    },
    "NotAvailableInAutoshow": {
        "cn": "不出现在车展", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（189 台）",
        "desc": "为 1 时该车不会出现在「车展」里，只能通过抽奖、赛事奖励、"
                "拍卖行或 DLC 获得。189 台属于这一类。",
    },
    "NotAvailableInAuctionHouse": {
        "cn": "不可拍卖", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（53 台）",
        "desc": "为 1 时禁止在拍卖行交易，通常用于免费赠送车、剧情车与 DLC 绑定车，"
                "防止被倒卖。",
    },
    "DoNotAllowRemovalFromGarage": {
        "cn": "禁止移出车库", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（29 台）",
        "desc": "为 1 时玩家无法删除/出售该车，避免把剧情必需车辆弄丢导致卡关。",
    },
    "VisibleOnlyIfOwned": {
        "cn": "仅拥有后可见", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 0",
        "desc": "是否在未拥有时对玩家完全隐藏（连车展列表都不显示）。"
                "本版本全部为 0，隐藏类车辆改用 `NotAvailableInAutoshow` 控制。",
    },
    "IsCarExperienceUnlocked": {
        "cn": "车辆体验已解锁", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 0",
        "desc": "车辆专属「体验任务」（Car Experience）的初始解锁状态。"
                "全库为 0 表示默认都需要玩家自己触发解锁。",
    },
    "HasCarExperience": {
        "cn": "拥有车辆体验", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（13 台）",
        "desc": "该车是否配有关卡式的专属体验任务。为 1 的 13 台车"
                "可在「车辆体验」入口里挑战。",
    },

    # ---------------- ⑫ 外观、涂装与展示 ----------------
    "CaliperRGBFront": {
        "cn": "前卡钳颜色", "typ": "INT RGB", "unit": "0xRRGGBB 十进制", "rng": "8 种",
        "desc": "前刹车卡钳的默认涂装颜色，按 24 位 RGB 存成十进制整数"
                "（如 1330090 = 0x144CAA 蓝）。",
    },
    "CaliperRGBRear": {
        "cn": "后卡钳颜色", "typ": "INT RGB", "unit": "0xRRGGBB 十进制", "rng": "8 种",
        "desc": "后刹车卡钳默认颜色，编码同上。前后通常一致，个别车会做成撞色。",
    },
    "CaliperAngleFront": {
        "cn": "前卡钳安装角度", "typ": "REAL", "unit": "弧度", "rng": "-1.99 ~ 2.19",
        "desc": "前卡钳在刹车盘上的旋转安装角（弧度），纯视觉参数，"
                "决定卡钳在轮圈里的位置（前置/后置）。",
    },
    "CaliperAngleRear": {
        "cn": "后卡钳安装角度", "typ": "REAL", "unit": "弧度", "rng": "-1.98 ~ 2.38",
        "desc": "后卡钳的安装角，纯视觉参数。",
    },
    "HasLivery": {
        "cn": "可涂装", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（392 台）",
        "desc": "是否允许玩家自定义涂装。为 0 的车只能使用原厂配色，"
                "常见于版权受限的电影车或特殊涂装车。",
    },
    "HasRaceLivery": {
        "cn": "带赛车涂装", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（392 台）",
        "desc": "是否自带不可修改的赛车涂装。与 `HasLivery` 呈互补关系"
                "（有固定涂装的不能自定义）。",
    },
    "WingMask": {
        "cn": "尾翼遮罩", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
        "desc": "涂装编辑时是否屏蔽尾翼区域，避免玩家的贴图被强行拉伸到尾翼上。",
    },
    "IsOpenCockpit": {
        "cn": "开放式座舱", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
        "desc": "标记该车没有封闭车顶（如方程式、开轮赛车）。"
                "影响车内视角、车手模型渲染与雨天效果。",
    },
    "IsOpenWheel": {
        "cn": "开轮式", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（39 台）",
        "desc": "车轮完全外露的车（F1、方程式、卡丁车）。"
                "这会影响轮对轮碰撞的判定方式，也是赛事分组的依据之一。",
    },
    "ConvertibleType": {
        "cn": "敞篷类型", "typ": "INT", "unit": "—", "rng": "0=硬顶，1/2=两种敞篷",
        "desc": "0=非敞篷、1=软顶敞篷、2=硬顶敞篷（可开合）。"
                "决定是否播放开篷动画以及车内视角的风噪处理。",
    },
    "RaceMode": {
        "cn": "赛车模式", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1（9 台）",
        "desc": "为 1 的车拥有独立的「赛车模式」配置（`List_DrivingMode`），"
                "切换后气动、悬挂、换档逻辑整体替换——通常是可变形或双性格的顶级车。",
    },
    "PuddleScale": {
        "cn": "水花强度缩放", "typ": "REAL", "unit": "倍率", "rng": "0.291 ~ 1.500",
        "desc": "车辆碾过积水时溅起水花的强度与体积缩放。"
                "本质是视觉效果参数，但也会轻微影响湿地的水滑阻力。",
    },
    "GaugeID": {
        "cn": "仪表盘样式ID", "typ": "INT", "unit": "—", "rng": "全库恒为 -1",
        "desc": "指定车内仪表盘的布局样式。-1 表示「按车型自动匹配」"
                "（用模型自带的仪表），因此全库统一为 -1。",
    },
    "MakeIcon": {
        "cn": "品牌图标代号", "typ": "TEXT", "unit": "—", "rng": "全库恒为 `BOING`",
        "desc": "品牌 Logo 的占位代号。全库统一为 `BOING`（占位符），"
                "真实 Logo 走 `List_CarMake.IconPath`，此字段无实际作用。",
    },
    "IsCameraCollidable": {
        "cn": "相机可碰撞", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
        "desc": "第三人称相机是否会与该车车身发生碰撞（被顶开）。"
                "关闭后相机可穿模进入车内，用于体积异常巨大的车辆。",
    },
    "UseBoxCameraCollision": {
        "cn": "相机用包围盒碰撞", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
        "desc": "相机碰撞检测是否简化为包围盒（性能优先，精度较低）。",
    },
    "TurnOffHeadlightsInAutoShow": {
        "cn": "车展关闭大灯", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 0",
        "desc": "在车展/拍照模式下是否强制关闭大灯。全库为 0，"
                "说明该开关未被任何车辆使用。",
    },
    "ShowDriverInExteriorCamera": {
        "cn": "外视角显示车手", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 1",
        "desc": "使用车外视角时是否渲染车手模型。全库为 1；"
                "某些敞篷/开轮车若设为 0 会看到空座椅。",
    },
    "IsInstalled": {
        "cn": "已安装标记", "typ": "INT 布尔", "unit": "—", "rng": "全库恒为 1",
        "desc": "内容管理层面的「该资源已随包安装」标记，"
                "用于判断车辆资源是否存在于本地，不影响玩法。",
    },
}


# ---------------------------------------------------------------------------
# 其余核心表的字段字典
# ---------------------------------------------------------------------------
TABLE_FIELDS: Final[dict[str, dict[str, Field]]] = {
    "Data_Engine": {
        "EngineID": {"cn": "引擎ID", "typ": "INTEGER 主键", "unit": "—", "rng": "1 ~ 699",
                     "desc": "引擎参数的唯一编号。"},
        "EngineMass-kg": {"cn": "引擎质量", "typ": "REAL", "unit": "kg", "rng": "—",
                          "desc": "引擎本体（含附件）的质量。换引擎时整车质量变动的主要来源，"
                                  "所以轻量引擎是性价比最高的升级之一。"},
        "MediaName": {"cn": "资源名", "typ": "TEXT", "unit": "—", "rng": "与 Data_Car.MediaName 同名",
                      "desc": "与车辆主表的 `MediaName` 同名，是引擎挂到车上的关联键。"
                              "注意这不是唯一键——同款车不同年份可能共用引擎记录。"},
        "ConfigID": {"cn": "引擎形式", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 6",
                     "desc": "V/W/直列/转子/水平对置/电动，含义同 `List_EngineConfig`。",
                     "enums": "List_EngineConfig"},
        "CylinderID": {"cn": "气缸数", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 14",
                       "desc": "气缸数量分类，见 `List_Cylinders`。", "enums": "List_Cylinders"},
        "Compression": {"cn": "压缩比", "typ": "REAL", "unit": ":1", "rng": "—",
                        "desc": "气缸总容积与燃烧室容积之比。压缩比越高热效率越好、"
                                "越容易爆震；这是「换活塞提升压缩比」升级的物理依据。"},
        "VariableTimingID": {"cn": "可变气门正时", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 3",
                             "desc": "1=无、2=VTEC、3=非 VTEC 的可变正时。"
                                     "影响高转速区间的扭矩曲线形状。",
                             "enums": "List_VariableTiming"},
        "AspirationID_Stock": {"cn": "原厂进气形式", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 8",
                               "desc": "自然进气/涡轮/机械增压等，见 `List_Aspiration`。",
                               "enums": "List_Aspiration"},
        "StockBoost-bar": {"cn": "原厂增压值", "typ": "REAL", "unit": "bar", "rng": "—",
                           "desc": "涡轮/机械增压车型的原厂增压压力。0 表示自然进气。"
                                   "这是「提升增压值」调校项的基线。"},
        "MomentInertia": {"cn": "转动惯量", "typ": "REAL", "unit": "kg·m²", "rng": "—",
                          "desc": "引擎旋转部件的等效转动惯量。数值越大转速攀升越慢，"
                                  "这就是「换轻量飞轮提升响应」在物理上的意义。"},
        "GasTankSize": {"cn": "油箱容量", "typ": "REAL", "unit": "L", "rng": "—",
                        "desc": "油箱容积（电动车为电池等效容量）。影响加油频率与整车配重。"},
        "FuelBurnPerHorsepowerHour": {"cn": "比油耗", "typ": "REAL", "unit": "—", "rng": "—",
                                      "desc": "每马力每小时消耗的燃油量系数，用于计算油耗速率。"
                                              "大排量高转速引擎此值更高。"},
        "TorqueSteerLeftSpeedScale": {"cn": "左偏扭矩转向缩放", "typ": "REAL", "unit": "倍率", "rng": "—",
                                      "desc": "大扭矩前驱车全油门时车头向左跑偏的强度缩放。"},
        "TorqueSteerRightSpeedScale": {"cn": "右偏扭矩转向缩放", "typ": "REAL", "unit": "倍率", "rng": "—",
                                       "desc": "同上，向右跑偏的强度。左右不对称是刻意模拟"
                                               "半轴长度差带来的真实特性。"},
        "EngineGraphingMaxTorque": {"cn": "曲线图最大扭矩", "typ": "REAL", "unit": "内部缩放值", "rng": "—",
                                    "desc": "性能曲线 UI 绘图时用的扭矩轴上限，经过额外缩放，"
                                            "与 `SimPeakTorque` 不是同一量纲。不要用它做物理计算。"},
        "EngineGraphingMaxPower": {"cn": "曲线图最大功率", "typ": "REAL", "unit": "内部缩放值", "rng": "—",
                                   "desc": "绘图用的功率轴上限，同样是 UI 缩放值而非物理量。"},
        "EngineGraphingAspirationID": {"cn": "曲线图进气类型", "typ": "INT 外键", "unit": "—", "rng": "—",
                                       "desc": "绘图时用于选择曲线形状模板的进气类型编号。"
                                               "可能与原厂进气形式不同（升级后绘制的曲线不同）。"},
        "EngineName": {"cn": "引擎名称", "typ": "TEXT", "unit": "—", "rng": "如「3.0L V12」",
                       "desc": "引擎的展示名称，排量+形式的组合，直接用于改装界面与车辆详情。"},
        "EngineRotation": {"cn": "引擎旋转方向", "typ": "INT", "unit": "—", "rng": "—",
                           "desc": "曲轴旋转方向（正/反）。影响车内视角看到的引擎抖动与"
                                   "扭矩反作用的方向，属细节拟真参数。"},
        "Carbureted": {"cn": "化油器", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
                       "desc": "是否为化油器供油（老车为 1）。影响油门响应延迟、"
                               "冷启动表现与排气音色。"},
        "Diesel": {"cn": "柴油机", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
                   "desc": "是否为柴油引擎。影响扭矩曲线（低转高扭）、断油转速与排气黑烟。"},
        "Rotary": {"cn": "转子引擎", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
                   "desc": "是否为转子（汪克尔）引擎。转子引擎的排量按双倍折算，"
                           "这也解释了为何 1.3L 转子能对标 2.6L 活塞机。"},
        "BackfireIntensityScalar": {"cn": "回火强度", "typ": "REAL", "unit": "倍率", "rng": "—",
                                    "desc": "收油时排气管回火（放炮）的强度缩放，纯视听参数。"},
        "BackfireSootToFireRatioScalar": {"cn": "回火黑烟/火焰比", "typ": "REAL", "unit": "比例", "rng": "—",
                                          "desc": "回火时黑烟与明火的比例。柴油与老车偏黑烟，"
                                                  "赛车偏明火。"},
    },
    "Data_Drivetrain": {
        "DrivetrainID": {"cn": "传动系统ID", "typ": "INTEGER 主键", "unit": "—", "rng": "1 ~ 693",
                         "desc": "每台车一份的传动配置记录编号（行数与车辆数基本一一对应，"
                                 "但库内没有显式外键，跨表时建议以 `Data_Car.DriveTypeID` 为准）。"},
        "DrivetypeID": {"cn": "驱动类型", "typ": "INT 外键", "unit": "—", "rng": "1=FWD，2=RWD，3=AWD",
                        "desc": "该传动配置对应的驱动形式，与 `Data_Car.DriveTypeID` 一致。",
                        "enums": "List_DriveType"},
        "EngineMountingDirection": {"cn": "引擎安装方向", "typ": "INT", "unit": "—", "rng": "—",
                                    "desc": "引擎在机舱内的朝向（纵置/横置）。纵置利于后驱传动，"
                                            "横置常见于前驱平台。"},
        "ShiftSystemID": {"cn": "换档系统", "typ": "INT 外键", "unit": "—", "rng": "1 ~ 6",
                          "desc": "变速箱类型（手动/自动/双离合/序列式等），指向 `List_ShiftSystem`。"
                                  "它决定换档耗时、转速匹配方式与是否支持自动补油。",
                          "enums": "List_ShiftSystem"},
    },
    "Data_Motor": {
        "MotorID": {"cn": "电机ID", "typ": "INTEGER 主键", "unit": "—", "rng": "1 ~ 21",
                    "desc": "驱动电机的参数编号。电动车没有 `Data_Engine` 记录，改由本表描述动力源。"},
        "MotorMass-kg": {"cn": "电机质量", "typ": "REAL", "unit": "kg", "rng": "—",
                         "desc": "电机本体质量。"},
        "MediaName": {"cn": "资源名", "typ": "TEXT", "unit": "—", "rng": "与 Data_Car.MediaName 同名",
                      "desc": "与车辆主表同名的关联键。"},
        "MomentInertia": {"cn": "转动惯量", "typ": "REAL", "unit": "kg·m²", "rng": "—",
                          "desc": "电机转子的等效转动惯量，影响电门响应的凌厉程度。"},
        "MotorGraphingMaxTorque": {"cn": "曲线图最大扭矩", "typ": "REAL", "unit": "内部缩放值", "rng": "—",
                                   "desc": "UI 曲线绘制的扭矩轴上限，非物理量。"},
        "MotorGraphingMaxPower": {"cn": "曲线图最大功率", "typ": "REAL", "unit": "内部缩放值", "rng": "—",
                                  "desc": "UI 曲线绘制的功率轴上限，非物理量。"},
        "MotorName": {"cn": "电机名称", "typ": "TEXT", "unit": "—", "rng": "—",
                      "desc": "电机的展示名称。"},
        "RedlineRPM": {"cn": "电机最高转速", "typ": "REAL", "unit": "rpm", "rng": "—",
                       "desc": "电机允许的最高转速（电动车通常 12000~20000 rpm）。"},
        "NumRPMEntriesArray": {"cn": "扭矩曲线采样点数", "typ": "INT", "unit": "点", "rng": "—",
                               "desc": "扭矩曲线数组的长度，配合 `TorqueCurveFullThrottleID` 定位曲线数据。"},
        "TorqueCurveFullThrottleID": {"cn": "全油门扭矩曲线ID", "typ": "INT 外键", "unit": "—", "rng": "—",
                                      "desc": "指向 `List_TorqueCurve`，给出转速-扭矩的离散点序列。"
                                              "这是引擎/电机性能的「原始真相」，其余峰值字段都是它的派生结果。",
                                      "enums": "List_TorqueCurve"},
        "BatteryCapacity": {"cn": "电池容量", "typ": "REAL", "unit": "kWh", "rng": "—",
                            "desc": "动力电池容量。影响整车质量与电量消耗速率（本作不含续航机制，"
                                    "主要用于配重与 UI 展示）。"},
        "ConfigID": {"cn": "电机形式", "typ": "INT 外键", "unit": "—", "rng": "—",
                     "desc": "电机布置/形式分类。", "enums": "List_EngineConfig"},
    },
    "Data_CarBody": {
        "Id": {"cn": "车身ID", "typ": "INTEGER 主键", "unit": "—", "rng": "= 车辆Id × 1000",
               "desc": "车身尺寸记录的主键，取值规律是「车辆 `Id` × 1000」"
                       "（如车辆 247 对应车身 247000），据此可直接关联。"},
        "Height": {"cn": "车高", "typ": "REAL", "unit": "m", "rng": "—", "desc": "车身高度（几何尺寸）。"},
        "Length": {"cn": "车长", "typ": "REAL", "unit": "m", "rng": "—", "desc": "车身长度。"},
        "Width": {"cn": "车宽", "typ": "REAL", "unit": "m", "rng": "—", "desc": "车身宽度（不含后视镜）。"},
        "Wheelbase": {"cn": "轴距", "typ": "REAL", "unit": "m", "rng": "—",
                      "desc": "前后轴中心距。轴距越长高速越稳、转向越迟钝。"},
        "ModelWheelbase": {"cn": "模型轴距", "typ": "REAL", "unit": "m", "rng": "—",
                           "desc": "实际渲染模型的轴距，可能与物理轴距有毫米级差异，用于对齐轮拱。"},
        "ModelFrontTrackOuter": {"cn": "模型前轮距", "typ": "REAL", "unit": "m", "rng": "—",
                                 "desc": "模型层面左右前轮外缘之间的距离。"},
        "ModelRearTrackOuter": {"cn": "模型后轮距", "typ": "REAL", "unit": "m", "rng": "—",
                                "desc": "模型层面左右后轮外缘距离。前后轮距差影响视觉姿态与过弯宽度感。"},
        "ModelFrontStockRideHeight": {"cn": "模型前车高", "typ": "REAL", "unit": "m", "rng": "—",
                                      "desc": "模型的前轴静态离地高度，应与 `Data_Car.FrontStockRideHeight` 一致。"},
        "ModelRearStockRideHeight": {"cn": "模型后车高", "typ": "REAL", "unit": "m", "rng": "—",
                                     "desc": "模型的后轴静态离地高度。"},
        "BottomCenterWheelbasePosx": {"cn": "轴距中心 X", "typ": "REAL", "unit": "m", "rng": "—",
                                      "desc": "整车质心参考点在模型坐标系中的 X 偏移（横向）。"},
        "BottomCenterWheelbasePosy": {"cn": "轴距中心 Y", "typ": "REAL", "unit": "m", "rng": "—",
                                      "desc": "质心参考点的 Y 偏移（垂直方向）。"},
        "BottomCenterWheelbasePosZ": {"cn": "轴距中心 Z", "typ": "REAL", "unit": "m", "rng": "—",
                                      "desc": "质心参考点的 Z 偏移（纵向，沿车长方向）。"},
        "PristineBoundingBoxMinX": {"cn": "包围盒最小 X", "typ": "REAL", "unit": "m", "rng": "—",
                                    "desc": "完好状态下车身包围盒的最小 X 坐标，用于碰撞粗筛与相机避让。"},
        "PristineBoundingBoxMinY": {"cn": "包围盒最小 Y", "typ": "REAL", "unit": "m", "rng": "—",
                                    "desc": "包围盒最小 Y 坐标（车身最低点）。"},
        "PristineBoundingBoxMinZ": {"cn": "包围盒最小 Z", "typ": "REAL", "unit": "m", "rng": "—",
                                    "desc": "包围盒最小 Z 坐标（车尾方向）。"},
        "PristineBoundingBoxMaxX": {"cn": "包围盒最大 X", "typ": "REAL", "unit": "m", "rng": "—",
                                    "desc": "包围盒最大 X 坐标（车身最宽处）。"},
        "PristineBoundingBoxMaxY": {"cn": "包围盒最大 Y", "typ": "REAL", "unit": "m", "rng": "—",
                                    "desc": "包围盒最大 Y 坐标（车顶最高点）。"},
        "PristineBoundingBoxMaxZ": {"cn": "包围盒最大 Z", "typ": "REAL", "unit": "m", "rng": "—",
                                    "desc": "包围盒最大 Z 坐标（车头方向）。"},
        "releaseOrder": {"cn": "发布顺序", "typ": "INT", "unit": "—", "rng": "—",
                         "desc": "该车身资源加入游戏的批次序号，用于按版本排序。"},
    },
    "Data_UpgradePart": {
        "Id": {"cn": "部件类别ID", "typ": "INTEGER 主键", "unit": "—", "rng": "—",
               "desc": "升级部件类别的编号。"},
        "TableName": {"cn": "数据表名", "typ": "TEXT", "unit": "—", "rng": "如 List_UpgradeEngine",
                      "desc": "该类别对应的实际数据表。改装系统的「品类型 → 数据表」路由就靠它。"},
        "CategoryName": {"cn": "大类名", "typ": "TEXT", "unit": "—", "rng": "Car/Engine/Drivetrain/CarBody/Motor",
                         "desc": "升级件所属的大类，与 `Data_UpgradePartCategory` 呼应。"},
        "PartName": {"cn": "部件名", "typ": "TEXT", "unit": "—", "rng": "—",
                     "desc": "部件的中文/英文名（用于 UI 分组标题）。"},
        "CameraName": {"cn": "镜头名", "typ": "TEXT", "unit": "—", "rng": "—",
                       "desc": "在改装界面选择该部件时切换到的特写镜头名称。"},
        "OkIfNoStockPart": {"cn": "允许无原厂件", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
                            "desc": "该类别是否允许「没有原厂件」的情况（如原厂无尾翼的车也能加装尾翼）。"},
        "HasRequiresGraphics": {"cn": "有外观依赖", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
                                "desc": "该部件是否有额外的模型/贴图依赖需要加载。"},
        "HasManufacturerId": {"cn": "有厂商字段", "typ": "INT 布尔", "unit": "—", "rng": "0 / 1",
                              "desc": "该部件数据表是否含厂商字段（用于显示品牌副厂件）。"},
    },
}
