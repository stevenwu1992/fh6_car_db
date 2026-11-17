"""FH6 手感/物理相关表的中文字段字典。

覆盖「开起来是什么感觉」这条链路上的核心表：

    轮胎配方   List_TireCompound（122 字段）
    轮胎曲线   List_TyreCurveDB / List_TireFrictionCurve / List_TireFrictionMultiCurve / List_TireAffectCurve
    悬挂       List_SpringDamperPhysics / List_AntiSwayPhysics / List_ThirdSpringElement
               List_PreloadAndDroopDamper / List_SuspensionPhysicsType
    空气动力   List_AeroPhysics / List_AeroStaticSystem / List_DragWallSettingsOverride
    转向手感   List_SteeringSettings / List_RearSteeringSettings
    刹车       List_BrakeProfile

写作依据：字段名语义 + 同族字段的取值分布 + 表间引用关系（例如
`FrictionMultiCurveID` 指向 `List_TireFrictionMultiCurve`，而该表又用
`MinLoadCurve/MaxLoadCurve + TireFrictionCurveID0/1` 表示「轻载/重载两条曲线」，
据此把 `*Peak0/1` 一类字段解释为轻载/重载工况）。

凡是从数据分布反推、没有官方文案支撑的，说明里会写明「推断」字样。
"""

from __future__ import annotations

from typing import Final


def _f(cn: str, unit: str = "—", desc: str = "", rng: str = "",
       enums: str = "", typ: str = "") -> dict[str, str]:
    """构造一条字段元数据（省略空项，保持字典简洁）。"""
    d = {"cn": cn, "unit": unit, "desc": desc}
    if rng:
        d["rng"] = rng
    if enums:
        d["enums"] = enums
    if typ:
        d["typ"] = typ
    return d


# ---------------------------------------------------------------------------
# 轮胎配方 List_TireCompound
# ---------------------------------------------------------------------------
# 字段名里带 _Offroad / _Snow 后缀的，由物理查找函数按「基名 + 路面」派生，
# 不必逐条重复书写。
_TIRE: Final[dict[str, dict[str, str]]] = {
    "TireCompoundID": _f("轮胎配方ID", "—", "配方编号，被 List_UpgradeTireCompound 与 List_TyreCurveDB 引用。", "1~53"),
    "DisplayName": _f("配方名称", "—", "内部名称，前缀数字与 ID 对应（如 8_Modern_Ultra High Performance）。"),
    "TorqueFreeLatFrictionScale": _f("侧向摩擦系数", "倍率", "不打滑（无力矩）状态下的侧向抓地基准值，越大过弯越吃得住。铺装路面 1.26~1.6，热熔/漂移配方更高。"),
    "TorqueFreeLongFrictionScaleBrake": _f("纵向制动摩擦系数", "倍率", "纯刹车方向的最大摩擦，决定刹车距离。铺装路面 1.2~1.7，普遍高于同配方侧向值。"),
    "TorqueFreeLongFrictionScaleAccel0": _f("纵向加速摩擦系数（低速端）", "倍率", "起步阶段的纵向抓地；与下一字段构成随车速衰减的两段。"),
    "TorqueFreeLongFrictionScaleAccel1": _f("纵向加速摩擦系数（高速端）", "倍率", "高速时的纵向抓地，通常与低速端相同。"),
    "TorqueFreeLongFrictionScaleAccelSpeed0": _f("加速摩擦-低速分界", "m/s", "低于此车速用 Accel0 的系数，全表统一 5.0 m/s（18 km/h）。"),
    "TorqueFreeLongFrictionScaleAccelSpeed1": _f("加速摩擦-高速分界", "m/s", "高于此车速用 Accel1 的系数，全表统一 15.0 m/s（54 km/h）。"),
    "WetFrictionModFrictionScale": _f("湿滑摩擦缩放", "倍率", "雨天路面整体摩擦的乘数，全表统一 0.95（雨战比干地滑 5%）。"),
    "WetFrictionModSlipScale": _f("湿滑滑移缩放", "倍率", "雨天允许的额外滑移量，数值越大雨天越容易甩尾；热熔胎普遍更高。"),
    "MomentInertia": _f("轮胎转动惯量", "kg·m²", "决定轮胎加速旋转/锁死时的响应快慢，全表多为 1.6。"),
    "WidthAffectFrictionWidth0": _f("胎宽-摩擦曲线点0", "mm", "胎宽影响摩擦的三点折线的第一点（100mm）。"),
    "WidthAffectFrictionWidth1": _f("胎宽-摩擦曲线点1", "mm", "第二点（250mm，基准宽度）。"),
    "WidthAffectFrictionWidth2": _f("胎宽-摩擦曲线点2", "mm", "第三点（400mm）。"),
    "WidthAffectFrictionScale0": _f("胎宽-摩擦系数0", "倍率", "100mm 宽时的摩擦缩放（0.85），窄胎抓地打折。"),
    "WidthAffectFrictionScale1": _f("胎宽-摩擦系数1", "倍率", "250mm 宽时为 0.95。"),
    "WidthAffectFrictionScale2": _f("胎宽-摩擦系数2", "倍率", "400mm 宽时为 1.05，宽胎有额外收益。"),
    "WidthAffectLoadWidth0": _f("胎宽-承载曲线点0", "mm", "胎宽影响承载能力的三点折线第一点。"),
    "WidthAffectLoadWidth1": _f("胎宽-承载曲线点1", "mm", "第二点。"),
    "WidthAffectLoadWidth2": _f("胎宽-承载曲线点2", "mm", "第三点。"),
    "WidthAffectLoadScale0": _f("胎宽-承载系数0", "倍率", "窄胎承载能力只有基准的 0.75。"),
    "WidthAffectLoadScale1": _f("胎宽-承载系数1", "倍率", "基准宽度为 1.0。"),
    "WidthAffectLoadScale2": _f("胎宽-承载系数2", "倍率", "宽胎承载 1.25 倍。"),
    "DiameterAffectFrictionDiameter0": _f("轮径-摩擦曲线点0", "m", "轮径影响摩擦的三点折线第一点（0.3m）。"),
    "DiameterAffectFrictionDiameter1": _f("轮径-摩擦曲线点1", "m", "第二点（0.7m）。"),
    "DiameterAffectFrictionDiameter2": _f("轮径-摩擦曲线点2", "m", "第三点（2.0m，怪兽卡车级）。"),
    "DiameterAffectFrictionScale0": _f("轮径-摩擦系数0", "倍率", "小轮径的摩擦缩放，全表统一 1.0（不做惩罚）。"),
    "DiameterAffectFrictionScale1": _f("轮径-摩擦系数1", "倍率", "中间轮径的摩擦缩放，统一 1.0。"),
    "DiameterAffectFrictionScale2": _f("轮径-摩擦系数2", "倍率", "大轮径的摩擦缩放，统一 1.0。"),
    "SurfaceDragNormalisedLoadCap": _f("接地拖曳载荷上限", "归一化载荷", "限制轮胎在极端载荷下的额外拖曳，防止高速时数值发散。"),
    "AirTempDiffHeatTransfer": _f("气温换热系数", "系数", "胎温向气温靠拢的速率；越大越容易升/降温。"),
    "AirTempDiffHeatTransferOverheated": _f("过热后气温换热系数", "系数", "胎温超过阈值后散热加快的系数，模拟过热后性能骤降。"),
    "OverheatedTemp": _f("过热温度", "°C", "超过此温度进入「过热」状态，抓地力开始明显衰减。", "167~239"),
    "AirSpeedToDoubleHeatTransfer": _f("风速使换热翻倍的速度", "km/h", "车速达到该值时空气对流散热效率翻倍，全表 60。"),
    "RollResistanceHeatTransfer": _f("滚阻生热系数", "系数", "滚动阻力转化为热量的比例。"),
    "FrictionHeatTransfer": _f("摩擦生热系数", "系数", "滑移摩擦转化为胎温的比例，决定激烈驾驶时胎温上升快慢。"),
    "FrictionWear": _f("摩擦磨损系数", "每单位", "单位摩擦功造成的磨损量，轮胎损耗速度的总开关。"),
    "RelTireSpeedToDoubleHeatTransfer": _f("相对胎速使换热翻倍", "km/h", "胎面与地面的相对滑移速度达到该值时，摩擦换热翻倍。"),
    "LoadToDoubleHeatTransfer": _f("载荷使换热翻倍", "N", "垂直载荷达到该值时换热翻倍。"),
    "HeatSlipMagToSlipPercentIn0": _f("热-滑移映射输入0", "滑移量", "把「生热滑移量」映射成「有效滑移百分比」的分段折线，第 0 个输入点。"),
    "HeatSlipMagToSlipPercentOut0": _f("热-滑移映射输出0", "%", "第 0 个输入点对应的滑移百分比。"),
    "HeatSlipMagToSlipPercentIn1": _f("热-滑移映射输入1", "滑移量", "折线第 1 个输入点。"),
    "HeatSlipMagToSlipPercentOut1": _f("热-滑移映射输出1", "%", "折线第 1 个输出点。"),
    "HeatSlipMagToSlipPercentIn2": _f("热-滑移映射输入2", "滑移量", "折线第 2 个输入点。"),
    "HeatSlipMagToSlipPercentOut2": _f("热-滑移映射输出2", "%", "折线第 2 个输出点。"),
    "PressureChangeSpeed": _f("胎压变化速率", "系数", "胎温变化引起胎压变化的响应速度。"),
    "SlidingFrictionHeatTransfer": _f("滑动摩擦生热", "系数", "轮胎抱死/打滑时额外生热的比例。"),
    "SlidingOffsetCooling": _f("滑动冷却偏移", "系数", "滑动状态下散热效率的修正。"),
    "SlidingOffsetOverheatedTemp": _f("滑动过热温度", "°C", "滑动状态下的过热阈值，通常远高于静态过热温度。"),
    "SlidingOffsetCoolingOverheated": _f("滑动过热冷却", "系数", "过热后滑动状态的散热修正。"),
    "SlidingSlipIn0": _f("滑动判定输入0", "滑移量", "判定「已进入滑动」的滑移量区间起点。"),
    "SlidingSlipOut0": _f("滑动判定输出0", "系数", "区间起点处的滑动修正系数。"),
    "SlidingSlipIn1": _f("滑动判定输入1", "滑移量", "区间终点。"),
    "SlidingSlipOut1": _f("滑动判定输出1", "系数", "区间终点处的修正系数。"),
    "SlidingOffsetAddToTemp": _f("滑动附加温升", "系数", "滑动时额外叠加到胎温上的量。"),
    "SlidingOffsetAddToTempClamp": _f("滑动附加温升上限", "系数", "上述附加温升的钳位值。"),
    "CamberAffectOutsideHeatIn": _f("外倾-外侧生热输入", "度", "外倾角达到该值时轮胎外侧显著升温。"),
    "CamberAffectOutsideHeatOut": _f("外倾-外侧生热输出", "倍率", "对应的生热倍率。"),
    "HUDTemps0": _f("HUD 温度刻度0", "°C", "仪表盘胎温条的刻度下界。"),
    "HUDTemps1": _f("HUD 温度刻度1", "°C", "胎温条的低温/正常分界（约 113~131°C）。"),
    "HUDTemps2": _f("HUD 温度刻度2", "°C", "正常/高温分界。"),
    "HUDTemps3": _f("HUD 温度刻度3", "°C", "高温/过热分界，与 OverheatedTemp 对应。"),
    "FrictionMultiCurveLateralID": _f("侧向摩擦多段曲线ID", "外键", "指向 List_TireFrictionMultiCurve，是侧向抓地的真正来源。", enums="List_TireFrictionMultiCurve"),
    "FrictionMultiCurveLongitudinalAccelID": _f("纵向加速摩擦多段曲线ID", "外键", "指向 List_TireFrictionMultiCurve，驱动时的纵向抓地。", enums="List_TireFrictionMultiCurve"),
    "FrictionMultiCurveLongitudinalBrakeID": _f("纵向制动摩擦多段曲线ID", "外键", "指向 List_TireFrictionMultiCurve，刹车时的纵向抓地。", enums="List_TireFrictionMultiCurve"),
    "AffectCurveTempAffectFrictionID": _f("温度影响摩擦曲线ID", "外键", "指向 List_TireAffectCurve：胎温 → 摩擦系数。", enums="List_TireAffectCurve"),
    "AffectCurveTempAffectWearID": _f("温度影响磨损曲线ID", "外键", "胎温 → 磨损速率。", enums="List_TireAffectCurve"),
    "AffectCurvePressureAffectFrictionID": _f("胎压影响摩擦曲线ID", "外键", "胎压 → 摩擦系数。", enums="List_TireAffectCurve"),
    "AffectCurvePressureAffectWearID": _f("胎压影响磨损曲线ID", "外键", "胎压 → 磨损速率。", enums="List_TireAffectCurve"),
    "AffectCurveStartPressureAffectPeakSASRID": _f("初始胎压影响峰值滑移角曲线ID", "外键", "初始胎压 → 峰值滑移角（SASR）。", enums="List_TireAffectCurve"),
    "AffectCurveCamberAffectLatFrictionID": _f("外倾影响侧向摩擦曲线ID", "外键", "外倾角 → 侧向摩擦。", enums="List_TireAffectCurve"),
    "AffectCurveCamberAffectLongFrictionID": _f("外倾影响纵向摩擦曲线ID", "外键", "外倾角 → 纵向摩擦。", enums="List_TireAffectCurve"),
    "AffectCurveWearAffectFrictionID": _f("磨损影响摩擦曲线ID", "外键", "磨损程度 → 剩余抓地。", enums="List_TireAffectCurve"),
    "AffectCurveSpeedAffectFrictionID": _f("车速影响摩擦曲线ID", "外键", "车速 → 摩擦系数（高速时轮胎会略微失抓）。", enums="List_TireAffectCurve"),
    "CompoundStiffness": _f("配方刚性", "系数", "胎体整体刚性，影响转向响应与路感；热熔胎明显更高。"),
    "Asphalt_PneumaticTrail_Peak": _f("沥青路气胎拖距峰值", "倍率", "气胎拖距（回正力矩的来源）在沥青路的峰值缩放。"),
    "Offroad_PneumaticTrail_Peak": _f("越野路气胎拖距峰值", "倍率", "非铺装路面的对应值。"),
    "Snow_PneumaticTrail_Peak": _f("雪地气胎拖距峰值", "倍率", "雪地的对应值。"),
    "LatStiffnessForPneumaticScrub": _f("气胎拖距横向刚度", "N/rad", "计算气胎拖距横向分量的刚度基准。"),
    "LightestNormLoadForPneumaticTrailCurve": _f("气胎拖距-最轻载荷", "归一化载荷", "气胎拖距曲线的最轻载荷参考点（0.25）。"),
    "HeaviestNormLoadForPneumaticTrailCurve": _f("气胎拖距-最重载荷", "归一化载荷", "最重载荷参考点（0.75）。"),
    "AffectCurveNormSlipAngleAffectPneumaticTrailAtLightestLoadID": _f("轻载下滑移角影响拖距曲线ID", "外键", "轻载时滑移角 → 气胎拖距。", enums="List_TireAffectCurve"),
    "AffectCurveNormSlipAngleAffectPneumaticTrailAtHeaviestLoadID": _f("重载下滑移角影响拖距曲线ID", "外键", "重载时滑移角 → 气胎拖距。", enums="List_TireAffectCurve"),
    "IsOffroad": _f("是否越野胎", "布尔", "1=越野配方，会参与 Offroad 抓地力计算。"),
    "CarcassSpring": _f("胎体弹簧刚度", "N/mm", "胎体本身的垂向刚度，影响细小颠簸的过滤；赛胎更硬。"),
    "TireCompression": _f("轮胎压缩量", "比例", "允许的最大垂向压缩比例。"),
    "CarcassBumpD": _f("胎体压缩阻尼", "系数", "胎体受压时的阻尼。"),
    "CarcassReboundD": _f("胎体回弹阻尼", "系数", "胎体回弹时的阻尼。"),
    "AirSpring": _f("空气弹簧刚度", "N/mm", "胎内空气提供的刚度分量。"),
    "MinSpringKMultiplier": _f("最小弹簧刚度倍率", "倍率", "胎压/温度变化时弹簧刚度的下界。"),
    "MaxSpringKMultiplier": _f("最大弹簧刚度倍率", "倍率", "弹簧刚度的上界。"),
    "PowerSpringK": _f("弹簧刚度指数", "指数", "渐进式弹簧的非线性指数。"),
    "UseTyreSpringProgressive": _f("启用渐进弹簧", "布尔", "1=弹簧刚度随压缩量非线性增长。"),
    "TireRollResistance": _f("轮胎滚动阻力", "系数", "滚动阻力系数，影响极速与油耗表现。"),
    "DefaultPressure": _f("默认胎压", "psi", "调校界面的默认胎压。"),
    "PressureIncreaseWithMassScaler": _f("胎压随载荷增长系数", "倍率", "车重增加时胎压上升的比例。"),
    "DownforceMult0": _f("下压力对抓地增益0", "倍率", "低速段下压力转化为抓地的系数。"),
    "DownforceMult1": _f("下压力对抓地增益1", "倍率", "高速段的对应系数，通常低于低速段。"),
    "DownforceSpeed0": _f("下压力增益-低速分界", "km/h", "低于该车速用 Mult0。"),
    "DownforceSpeed1": _f("下压力增益-高速分界", "km/h", "高于该车速用 Mult1。"),
    "WetOffroadFrictionScale": _f("湿滑越野摩擦缩放", "倍率", "雨天越野路面的抓地缩放。"),
    "WetOffroadSlipScale": _f("湿滑越野滑移缩放", "倍率", "雨天越野路面的滑移缩放。"),
}

# ---------------------------------------------------------------------------
# 轮胎曲线 List_TyreCurveDB
# ---------------------------------------------------------------------------
_SURFACES: Final[dict[str, str]] = {
    "Asph": "沥青（铺装路面）",
    "Off": "越野（非铺装路面）",
    "Snow": "雪地",
}
# 0/1 的含义由 List_TireFrictionMultiCurve 的 MinLoadCurve/MaxLoadCurve 双曲线结构反推
_LOAD_IDX: Final[str] = "轻载（0）/ 重载（1）两种载荷工况"
_METRICS: Final[dict[str, tuple[str, str]]] = {
    "LatSlipPeak": ("侧向峰值滑移角", "侧向力达到峰值时的滑移角（度）。越大越「软」，转向更渐进；越小越锐利。"),
    "LongSlipPeak": ("纵向峰值滑移率", "加速方向达到峰值时的滑移率（%）。"),
    "BrkSlipPeak": ("制动峰值滑移率", "刹车方向达到峰值时的滑移率（%）。"),
    "LatCurveShape": ("侧向曲线形状", "侧向摩擦曲线的形状系数，数值越大峰值越尖、越过峰值后掉得越快。"),
    "AccelCurveShape": ("加速曲线形状", "纵向加速曲线的形状系数。"),
    "BrkCurveShape": ("制动曲线形状", "纵向制动曲线的形状系数。"),
    "LatEnd": ("侧向末端保有率", "滑移远超峰值后仍保留的侧向摩擦比例（0.8 = 只剩 80%）。"),
    "AccEnd": ("加速末端保有率", "大滑移下保留的加速摩擦比例。"),
    "BrkEnd": ("制动末端保有率", "大滑移下保留的制动摩擦比例。"),
    "PreLat": ("侧向峰前斜率", "峰值之前摩擦上升段的斜率系数。"),
    "PreAcc": ("加速峰前斜率", "加速方向的峰前斜率。"),
    "PreBrk": ("制动峰前斜率", "制动方向的峰前斜率。"),
    "LatFlat": ("侧向峰值平台", "峰值附近维持高抓地的角度跨度（度），越大越宽容。"),
    "AccFlat": ("加速峰值平台", "加速方向峰值平台的跨度。"),
    "BrkFlat": ("制动峰值平台", "制动方向峰值平台的跨度。"),
}


def _tyre_curve_fields() -> dict[str, dict[str, str]]:
    """按「路面 × 指标 × 载荷」生成 List_TyreCurveDB 的 90 个数值字段。"""
    out: dict[str, dict[str, str]] = {
        "TireCompoundID": _f("轮胎配方ID", "外键", "与 List_TireCompound 一一对应。"),
        "DisplayName": _f("配方名称", "—", "内部名称，与 List_TireCompound 同名。"),
    }
    for surf, surf_cn in _SURFACES.items():
        for metric, (metric_cn, metric_desc) in _METRICS.items():
            for idx, idx_cn in (("0", "轻载"), ("1", "重载")):
                out[f"{surf}_{metric}{idx}"] = _f(
                    f"{surf_cn}-{metric_cn}（{idx_cn}）", "度/%" if "Slip" in metric else "系数",
                    f"{metric_desc} 适用于{idx_cn}工况（{_LOAD_IDX}）。")
    return out


# ---------------------------------------------------------------------------
# 悬挂：弹簧阻尼 List_SpringDamperPhysics
# ---------------------------------------------------------------------------
_SPRING: Final[dict[str, dict[str, str]]] = {
    "SpringDamperPhysicsID": _f("悬挂参数ID", "—", "悬挂参数组编号。"),
    "Ordinal": _f("车辆序号", "外键", "等于 Data_Car.Id，一台车一组悬挂参数。"),
    "SuspensionPhysicsTypeID": _f("悬挂物理类型ID", "外键", "指向 List_SuspensionPhysicsType，决定几何运动学。", enums="List_SuspensionPhysicsType"),
    "UseProgressiveSpring": _f("渐进式弹簧", "布尔", "1=弹簧刚度随压缩非线性上升。"),
    "DefRideHeight": _f("默认车高", "m", "调校界面「车高」滑块的默认位置。"),
    "MinRideHeight": _f("最低车高", "m", "车高滑块下界。"),
    "MaxRideHeight": _f("最高车高", "m", "车高滑块上界。"),
    "MaxCompressHeight": _f("最大压缩行程", "m", "悬挂从静态到触底可压缩的距离，决定过坎会不会打底。"),
    "DefSpringRate": _f("默认弹簧刚度", "内部刚度单位", "弹簧硬度默认值，越大侧倾越小、路感越硬。"),
    "MinSpringRate": _f("最小弹簧刚度", "内部刚度单位", "滑块下界。"),
    "MaxSpringRate": _f("最大弹簧刚度", "内部刚度单位", "滑块上界。"),
    "DefDampenBumpRate": _f("默认压缩阻尼", "阻尼单位", "悬挂被压缩时的阻力，管「吃进颠簸」的那一半。"),
    "MinDampenBumpRate": _f("最小压缩阻尼（低速）", "阻尼单位", "低速压缩阻尼滑块下界。"),
    "MaxDampenBumpRate": _f("最大压缩阻尼（低速）", "阻尼单位", "低速压缩阻尼滑块上界。"),
    "MinDampenBumpRateHighVelocity": _f("最小压缩阻尼（高速）", "阻尼单位", "高速压缩段（快过坎）的阻尼下界。"),
    "MaxDampenBumpRateHighVelocity": _f("最大压缩阻尼（高速）", "阻尼单位", "高速压缩段的上界。"),
    "DampenBumpHighVelocityThreshold": _f("高速压缩阈值", "m/s", "超过此压缩速度从「低速阻尼」切到「高速阻尼」。"),
    "MinDampenBumpRateSuperHighVelocity": _f("最小压缩阻尼（超高速）", "阻尼单位", "剧烈冲击（大坎、落地）时的阻尼下界。"),
    "MaxDampenBumpRateSuperHighVelocity": _f("最大压缩阻尼（超高速）", "阻尼单位", "超高速段的上界。"),
    "DampenBumpSuperHighVelocityThreshold": _f("超高速压缩阈值", "m/s", "切到超高速阻尼的速度阈值。"),
    "DefDampenReboundRate": _f("默认回弹阻尼", "阻尼单位", "悬挂伸张时的阻力，管「压下去后怎么弹回来」。回弹过小会连续弹跳。"),
    "MinDampenReboundRate": _f("最小回弹阻尼（低速）", "阻尼单位", "低速回弹滑块下界。"),
    "MaxDampenReboundRate": _f("最大回弹阻尼（低速）", "阻尼单位", "低速回弹滑块上界。"),
    "MinDampenReboundRateHighVelocity": _f("最小回弹阻尼（高速）", "阻尼单位", "高速回弹段下界。"),
    "MaxDampenReboundRateHighVelocity": _f("最大回弹阻尼（高速）", "阻尼单位", "高速回弹段上界。"),
    "DampenReboundHighVelocityThreshold": _f("高速回弹阈值", "m/s", "切到高速回弹阻尼的速度阈值。"),
    "MinDampenReboundRateSuperHighVelocity": _f("最小回弹阻尼（超高速）", "阻尼单位", "超高速回弹段下界。"),
    "MaxDampenReboundRateSuperHighVelocity": _f("最大回弹阻尼（超高速）", "阻尼单位", "超高速回弹段上界。"),
    "DampenReboundSuperHighVelocityThreshold": _f("超高速回弹阈值", "m/s", "切到超高速回弹阻尼的速度阈值。"),
    "StaticToe": _f("静态前束", "度", "原厂前束角。正值内八（稳），负值外八（转向更活）。"),
    "StaticCamber": _f("静态外倾", "度", "原厂外倾角。负值（车轮上端内倾）提升过弯侧向抓地。"),
    "Caster": _f("主销后倾角", "度", "影响回正力矩与转向手感重量，越大高速越稳、转向越沉。"),
    "MaxStretchDeltaFromRideHeight": _f("最大拉伸行程", "m", "悬挂从静态到完全伸张的距离，决定过坑时车轮能否贴地。"),
    "BumpStopLength": _f("缓冲块长度", "m", "触底前缓冲块的厚度。"),
    "BumpStopSpringK": _f("缓冲块刚度", "内部刚度单位", "缓冲块被压到时的等效弹簧刚度。"),
    "BumpStopSpringKMax": _f("缓冲块最大刚度", "内部刚度单位", "完全压死时的刚度上限。"),
    "BumpStopBumpD": _f("缓冲块压缩阻尼", "阻尼单位", "缓冲块受压时的阻尼。"),
    "BumpStopBumpDMax": _f("缓冲块压缩阻尼上限", "阻尼单位", "压缩阻尼的最大值。"),
    "BumpStopReboundD": _f("缓冲块回弹阻尼", "阻尼单位", "缓冲块回弹时的阻尼。"),
    "BumpStopReboundDMax": _f("缓冲块回弹阻尼上限", "阻尼单位", "回弹阻尼的最大值。"),
    "BumpStopPowerK": _f("缓冲块刚度指数", "指数", "缓冲块刚度随压缩量的非线性指数。"),
    "BumpStopPowerBump": _f("缓冲块压缩指数", "指数", "压缩段的非线性指数。"),
    "BumpStopPowerReb": _f("缓冲块回弹指数", "指数", "回弹段的非线性指数。"),
    "BumpStopGForceClamp": _f("缓冲块 G 值钳位", "g", "缓冲块能传递的最大加速度，防止极端冲击炸开物理。"),
    "RollCentreHeight": _f("侧倾中心高度", "m", "前后轴侧倾中心的离地高度，决定过弯时车身如何侧倾。"),
    "AntiGeometryPercent": _f("抗几何百分比", "比例", "抗俯仰/抗抬头的几何补偿比例（0~1）。"),
    "UseBlowOffDamper": _f("泄压式阻尼", "布尔", "1=启用泄压阀式阻尼，遇大冲击时瞬间卸压，改善越野贴地性。"),
}

# ---------------------------------------------------------------------------
# 悬挂：防倾杆 / 第三弹簧 / 预载下垂 / 类型
# ---------------------------------------------------------------------------
_ANTISWAY: Final[dict[str, dict[str, str]]] = {
    "AntiSwayPhysicsID": _f("防倾杆参数ID", "—", "防倾杆参数组编号。"),
    "Ordinal": _f("车辆序号", "外键", "等于 Data_Car.Id。"),
    "DefSwaybarStiffness": _f("默认防倾杆刚度", "内部刚度单位", "左右轮之间抗侧倾的默认硬度。前硬→推头，后硬→甩尾。"),
    "MinSwaybarStiffness": _f("最小防倾杆刚度", "内部刚度单位", "调校滑块下界。"),
    "MaxSwaybarStiffness": _f("最大防倾杆刚度", "内部刚度单位", "调校滑块上界。"),
    "SwaybarDamping": _f("防倾杆阻尼", "阻尼单位", "抑制侧倾建立速度的阻尼项。"),
    "BeamStiffness": _f("梁式刚度", "内部刚度单位", "整体桥/扭力梁结构的附加刚度，独立悬挂多为 0。"),
}

_THIRD: Final[dict[str, dict[str, str]]] = {
    "ThirdSpringID": _f("第三弹簧ID", "—", "第三弹簧（防俯仰/防侧倾辅助弹簧）配置编号。"),
    "Name": _f("配置名称", "—", "如 Active_100、RALLY_Active_100，数字大致对应强度倍数。"),
    "ThirdElementSpring": _f("第三弹簧刚度", "倍率", "辅助弹簧的刚度倍率，0 表示不启用。"),
    "ThirdElementDBump": _f("第三弹簧压缩阻尼", "倍率", "压缩方向阻尼。"),
    "ThirdElementDRebound": _f("第三弹簧回弹阻尼", "倍率", "回弹方向阻尼。"),
    "ThirdElementDBumpFast": _f("第三弹簧高速压缩阻尼", "倍率", "快速压缩段的阻尼。"),
    "ThirdElementDReboundFast": _f("第三弹簧高速回弹阻尼", "倍率", "快速回弹段的阻尼。"),
    "ThirdElementDBumpFastTreshold": _f("高速压缩阈值", "m/s", "切到高速压缩阻尼的速度阈值。"),
    "ThirdElementDReboundFastTrehsold": _f("高速回弹阈值", "m/s", "切到高速回弹阻尼的速度阈值（原文拼写为 Trehsold）。"),
    "ThirdSpringOffroadScaler": _f("越野缩放", "倍率", "非铺装路面上第三弹簧效果的缩放。"),
    "ThirdElementGForceClamp": _f("G 值钳位", "g", "第三弹簧可施加的最大加速度。"),
}

_PRELOAD: Final[dict[str, dict[str, str]]] = {
    "PreloadAndDroopDamperID": _f("预载配置ID", "—", "弹簧预载与下垂阻尼配置编号。"),
    "UseNoClampDroop": _f("不钳位下垂", "布尔", "1=允许悬挂在伸张时不受钳位限制。"),
    "SpringPreloadNormForce": _f("弹簧预载力", "归一化力", "弹簧在自由长度时就已压缩的力，影响车身高度与初始支撑。"),
    "UseLoadDamper": _f("启用载荷阻尼", "布尔", "1=阻尼随垂向载荷变化（重载时更硬）。"),
    "MinDamperLoad": _f("最小载荷", "归一化", "载荷阻尼生效的载荷下界。"),
    "MaxDamperLoad": _f("最大载荷", "归一化", "载荷阻尼生效的载荷上界。"),
    "DroopBumpDamperMultMin": _f("下垂段压缩阻尼倍率(下限)", "倍率", "车轮下坠（droop）时压缩阻尼的缩放。"),
    "DroopReboundDamperMultMin": _f("下垂段回弹阻尼倍率(下限)", "倍率", "下坠时回弹阻尼的缩放。"),
    "DroopBumpDamperMultMax": _f("下垂段压缩阻尼倍率(上限)", "倍率", "同上，上界。"),
    "DroopReboundDamperMultMax": _f("下垂段回弹阻尼倍率(上限)", "倍率", "同上，上界。"),
}

_SUSP_TYPE: Final[dict[str, dict[str, str]]] = {
    "SuspensionPhysicsTypeID": _f("悬挂类型ID", "—", "悬挂几何模型编号，被 List_SpringDamperPhysics 引用。"),
    "Name": _f("类型名称", "—", "INDEPENDANT（独立）/ ARTICULATED（整体桥、铰接）等。"),
    "Path": _f("参数文件路径", "资源路径", "具体悬挂几何参数的 XML 路径，空串表示使用默认模型。"),
}

# ---------------------------------------------------------------------------
# 空气动力学
# ---------------------------------------------------------------------------
_AERO: Final[dict[str, dict[str, str]]] = {
    "AeroPhysicsID": _f("气动参数ID", "—", "气动参数组编号。"),
    "Ordinal": _f("车辆序号", "外键", "等于 Data_Car.Id。"),
    "DefaultTuneSlider": _f("默认调校滑块位置", "0~1", "空力调校滑块的默认值（0.5 = 中间档）。"),
    "Drag0": _f("风阻（滑块 0）", "内部力单位", "下压力/风阻滑块在最小值时的风阻。"),
    "Downforce0": _f("下压力（滑块 0）", "内部力单位", "滑块最小时的整车下压力。"),
    "Drag1": _f("风阻（滑块 1）", "内部力单位", "滑块最大值时的风阻——加大尾翼攻角会同时抬高这一项。"),
    "Downforce1": _f("下压力（滑块 1）", "内部力单位", "滑块最大时的下压力。"),
    "AngleZeroDownforce": _f("零下压力攻角", "度", "车身攻角达到该值时下压力归零，用于计算攻角修正。"),
    "LateralDrag": _f("侧向风阻", "内部力单位", "侧滑时的气动阻力，影响漂移时的横摆阻尼。"),
    "DFTorqueScaleOneSliderInput0": _f("下压力矩映射一-输入0", "0~1", "第一段「滑块位置 → 前后下压力分配」映射的起始输入。"),
    "DFTorqueScaleOneSliderInput1": _f("下压力矩映射一-输入1", "0~1", "第一段映射的中间输入点。"),
    "DFTorqueScaleOneSliderInput2": _f("下压力矩映射一-输入2", "0~1", "第一段映射的结束输入。"),
    "DFTorqueScaleOneTorqueScaleOutput0": _f("下压力矩映射一-输出0", "倍率", "对应输入0的前后扭矩分配倍率。"),
    "DFTorqueScaleOneTorqueScaleOutput1": _f("下压力矩映射一-输出1", "倍率", "对应输入1的倍率。"),
    "DFTorqueScaleOneTorqueScaleOutput2": _f("下压力矩映射一-输出2", "倍率", "对应输入2的倍率。"),
    "DFTorqueScaleTwoSliderInput0": _f("下压力矩映射二-输入0", "0~1", "第二段映射（通常用于高速段）的起始输入。"),
    "DFTorqueScaleTwoSliderInput1": _f("下压力矩映射二-输入1", "0~1", "第二段映射的中间输入。"),
    "DFTorqueScaleTwoSliderInput2": _f("下压力矩映射二-输入2", "0~1", "第二段映射的结束输入。"),
    "DFTorqueScaleTwoTorqueScaleOutput0": _f("下压力矩映射二-输出0", "倍率", "对应输入0的倍率。"),
    "DFTorqueScaleTwoTorqueScaleOutput1": _f("下压力矩映射二-输出1", "倍率", "对应输入1的倍率。"),
    "DFTorqueScaleTwoTorqueScaleOutput2": _f("下压力矩映射二-输出2", "倍率", "对应输入2的倍率。"),
    "DownforceOffThrottleOffset": _f("收油下压力偏移", "内部力单位", "松开油门时下压力的瞬时增减（模拟尾翼卸载）。"),
    "DragOffThrottleOffset": _f("收油风阻偏移", "内部力单位", "收油时风阻的瞬时增减。"),
    "DownforceBrakingOffset": _f("刹车下压力偏移", "内部力单位", "踩刹车时下压力的瞬时增减（模拟车头下压）。"),
    "DragBrakingOffset": _f("刹车风阻偏移", "内部力单位", "刹车时风阻的瞬时增减。"),
}

_AERO_STATIC: Final[dict[str, dict[str, str]]] = {
    "CarId": _f("车辆ID", "外键", "等于 Data_Car.Id，仅少数带主动气动/风扇的车有此记录。"),
    "StaticDragReduction": _f("静态风阻削减", "内部力单位", "固定式空力套件带来的风阻变化。"),
    "FrontStaticDownforce": _f("前静态下压力", "内部力单位", "不随攻角变化的固定下压力。"),
    "RearStaticDownforce": _f("后静态下压力", "内部力单位", "后轴的固定下压力。"),
    "AngleZeroStaticDownforce": _f("零下压力攻角", "度", "静态下压力归零的攻角。"),
    "StaticDownforceAtMinNormRPM": _f("最低转速下的下压力系数", "倍率", "风扇/主动气动在最低转速时的下压力比例。"),
    "StaticDownforceAtMaxNormRPM": _f("最高转速下的下压力系数", "倍率", "最高转速时的比例。"),
    "StaticEfficiencyAtMinRide": _f("最低车高下的效率", "倍率", "车高最低时地效/风扇的效率。"),
    "StaticEfficiencyAtMaxRide": _f("最高车高下的效率", "倍率", "车高最高时的效率。"),
    "StaticDownforceOffroadMult": _f("越野下压力倍率", "倍率", "非铺装路面上的下压力缩放。"),
    "NormFanSpeed": _f("风扇归一化转速", "0~1", "主动风扇的默认转速比例。"),
}

_DRAG_WALL: Final[dict[str, dict[str, str]]] = {
    "CarId": _f("车辆ID", "外键", "等于 Data_Car.Id，仅极速异常的车需要单独设定。"),
    "MinSpeedForDragWall": _f("风阻墙起始速度", "mph", "低于此速度不施加额外风阻。"),
    "MedSpeedForDragWall": _f("风阻墙中间速度", "mph", "风阻开始显著增加的速度。"),
    "MaxSpeedForDragWall": _f("风阻墙满速", "mph", "达到此速度时额外风阻拉满，用于压制极速。"),
    "MedDragAccForDragWall": _f("中间段额外减速度", "g", "中间速度区间施加的减速度。"),
    "MaxDragAccForDragWall": _f("满速额外减速度", "g", "满速时施加的减速度，防止物理发散。"),
}

# ---------------------------------------------------------------------------
# 转向手感
# ---------------------------------------------------------------------------
_STEER: Final[dict[str, dict[str, str]]] = {
    "SteeringSettingsID": _f("转向参数ID", "—", "转向手感参数组编号。"),
    "Name": _f("配置名称", "—", "Default / Drift / MonsterTruck / HighDownforce 等。"),
    "SteerMaxAngVelTurning": _f("最大转向角速度（转向）", "度/秒", "打方向时方向盘的最大角速度，越大转向越「快」。"),
    "SteerMaxAngVelStraighten": _f("最大转向角速度（回正）", "度/秒", "回正时的最大角速度。"),
    "SteerAngVelCountersteer": _f("反打角速度", "度/秒", "反打方向时的最大角速度——漂移车此项明显更高。"),
    "SteerAngVelDynFindPeak": _f("动态找峰角速度", "度/秒", "动态峰值检测用的辅助角速度，数值小则转向更「黏」。"),
    "SteerAccelTimeToMaxRate": _f("达到最大角速度的时间", "秒", "转向从静止到最大角速度的加速时间。"),
    "SteerSpeedSensitiveMaxGees": _f("速度敏感-最大 G 值", "g", "转向速度敏感性生效的侧向 G 上限。"),
    "SteerSpeedSensitiveMinMaxAngle": _f("速度敏感-最小最大转角", "度", "高速时允许的最大转向角下限，防止高速打死。"),
    "SteerSpeedSensitiveSlowSpeed": _f("速度敏感-低速阈值", "m/s", "低于此速度视为低速，不削减转角。"),
    "SteerSpeedSensitiveFastSpeed": _f("速度敏感-高速阈值", "m/s", "高于此速度转角削减到最小值。"),
    "SteerSpeedSensitiveFastRateScale": _f("高速转角缩放", "倍率", "高速时转角相对于低速的缩放比例。"),
    "SteerLoadFilterMultiplier": _f("转向负载滤波倍率", "倍率", "方向盘手感随载荷变化的滤波强度。"),
    "SteerLoadTreshold": _f("转向负载阈值", "内部单位", "触发负载滤波的力反馈阈值（原文拼写 Treshold）。"),
}


def _rear_steer_fields() -> dict[str, dict[str, str]]:
    """生成后轮转向表：低速/高速 × 前/后轴 × 5 个采样点。"""
    out: dict[str, dict[str, str]] = {
        "Id": _f("后轮转向配置ID", "—", "配置编号。"),
        "Name": _f("配置名称", "—", "Modern / Retro / Race / Truck / MonsterTruck 等。"),
        "MaxRearSteerAngleAsFractionOfFront": _f("后轮最大转角占前轮比例", "比例", "1.0 表示后轮最多可转到与前轮同角度。"),
        "LowSpeedCurveSpeedMS": _f("低速曲线-参考车速", "m/s", "低速转向曲线的参考车速。"),
        "HighSpeedCurveSpeedMS": _f("高速曲线-参考车速", "m/s", "高速转向曲线的参考车速。"),
        "MaxRearSteerAngleForCounterSteer": _f("反打时后轮最大转角", "比例", "反打方向时后轮参与转向的程度，0=不参与。"),
    }
    for speed, speed_cn in (("LowSpeed", "低速"), ("HighSpeed", "高速")):
        for axle, axle_cn in (("Front", "前轮转角"), ("Rear", "后轮转角")):
            for i in range(5):
                out[f"{speed}Curve{axle}NormAngle{i}"] = _f(
                    f"{speed_cn}曲线-{axle_cn}采样点{i}", "归一化角",
                    f"{speed_cn}工况下，前轮转角处于第 {i} 个归一化采样点（0=左满舵，4=右满舵）时，"
                    f"{axle_cn}的对应比例。前轮曲线定义输入，后轮曲线定义输出。")
    return out


# ---------------------------------------------------------------------------
# 刹车
# ---------------------------------------------------------------------------
_BRAKE: Final[dict[str, dict[str, str]]] = {
    "BrakesProfileID": _f("刹车参数ID", "—", "刹车标定组编号，被 Data_Car.BrakeProfile 引用。"),
    "Name": _f("配置名称", "—", "如 Modern Supercars、Retro Muscle、FormulaCar。"),
    "DurationABS": _f("ABS 循环周期", "秒", "ABS 每次泄压-建压的周期，越短介入越细腻。"),
    "ReleasePointABSFrontNoSteer": _f("ABS 前轴释放点（直行）", "滑移比", "直行刹车时前轮 ABS 开始泄压的滑移阈值。"),
    "ReleasePointABSFrontFullSteer": _f("ABS 前轴释放点（满舵）", "滑移比", "打满方向时前轴阈值会降低，避免转向时抱死。"),
    "ReleasePointABSRearNoSteer": _f("ABS 后轴释放点（直行）", "滑移比", "直行时后轴的泄压阈值。"),
    "ReleasePointABSRearFullSteer": _f("ABS 后轴释放点（满舵）", "滑移比", "满舵时后轴阈值，通常比前轴更敏感。"),
    "BrakeToFullSteerBrakeRate": _f("满舵时制动力保留率", "比例", "打满方向时允许保留的制动力比例。"),
    "BrakeBiasRearScaler": _f("后轴制动力缩放", "倍率", "前后刹车力分配的缩放，越大越偏后（更容易甩尾）。"),
    "FrontMinBrakePosNoSteer": _f("前轮最小制动位置（直行）", "归一化", "直行时前轮能施加的最小制动力。"),
    "FrontMinBrakePosFullSteer": _f("前轮最小制动位置（满舵）", "归一化", "满舵时的对应值，越大越容易在弯中锁前轮。"),
    "RearMinBrakePosNoSteer": _f("后轮最小制动位置（直行）", "归一化", "直行时后轮的最小制动力。"),
    "RearMinBrakePosFullSteer": _f("后轮最小制动位置（满舵）", "归一化", "满舵时的对应值。"),
}

# ---------------------------------------------------------------------------
# 轮胎摩擦曲线附属表
# ---------------------------------------------------------------------------
_FRICTION_CURVE: Final[dict[str, dict[str, str]]] = {
    "FrictionCurveID": _f("摩擦曲线ID", "—", "曲线编号，被 List_TireFrictionMultiCurve 引用。"),
    "NumCurveValues": _f("采样点数", "点", "v0~vN 中有效采样点的个数。"),
    "FrictionScale": _f("摩擦整体缩放", "倍率", "对该条曲线所有取值的统一缩放。"),
}

_MULTI_CURVE: Final[dict[str, dict[str, str]]] = {
    "FrictionMultiCurveID": _f("多段摩擦曲线ID", "—", "被 List_TireCompound.FrictionMultiCurve*ID 引用。"),
    "MaxSlip": _f("最大滑移量", "滑移单位", "曲线横轴的上限，超过即按末端值处理。"),
    "MinLoadCurve": _f("最轻载荷下的曲线值", "归一化载荷", "轻载工况对应的摩擦曲线编号或参考值。"),
    "MaxLoadCurve": _f("最重载荷下的曲线值", "归一化载荷", "重载工况对应的参考值。"),
    "LoadClamp": _f("载荷钳位", "N", "超过此载荷一律按最大值计算，防止数值爆炸。"),
    "TireFrictionCurveID0": _f("轻载摩擦曲线ID", "外键", "指向 List_TireFrictionCurve。", enums="List_TireFrictionCurve"),
    "TireFrictionCurveID1": _f("重载摩擦曲线ID", "外键", "指向 List_TireFrictionCurve。", enums="List_TireFrictionCurve"),
}

_AFFECT_CURVE: Final[dict[str, dict[str, str]]] = {
    "AffectCurveID": _f("影响曲线ID", "—", "曲线编号，被 List_TireCompound 的各项 ApplyCurve* 引用。"),
    "DisplayName": _f("曲线名称", "—", "说明该曲线把什么量映射成什么量。"),
    "NumValues": _f("采样点数", "点", "v0~vN 中有效采样点个数。"),
    "MinInput": _f("输入下界", "随曲线而定", "横轴（输入量）的最小值。"),
    "MaxInput": _f("输入上界", "随曲线而定", "横轴的最大值。"),
    "OutputScale": _f("输出缩放", "倍率", "纵轴（输出量）的整体缩放系数。"),
}


# ---------------------------------------------------------------------------
# 牵引力控制与驾驶模式（同属手感链路）
# ---------------------------------------------------------------------------
_TCS: Final[dict[str, dict[str, str]]] = {
    "TC_ProfileID": _f("TCS 配置ID", "—", "牵引力控制标定组编号，被 TCProfileID_Override 引用。"),
    "TC_Profilename": _f("配置名称", "—", "Street / Sport / Race / Rally / Drift / OffRoad / Vintage / Electric。"),
    # 下面 6 个是「基名」，_Road / _OffRoad / _Snow 三个变体由后缀规则自动派生
    "TC_SlipStart0": _f("介入起始滑移-低速端", "滑移率", "滑移达到此值 TCS 开始介入；低速端。"),
    "TC_SlipStart1": _f("介入起始滑移-高速端", "滑移率", "高速时的介入起点，通常高于低速端。"),
    "TC_SlipEnd0": _f("完全介入滑移-低速端", "滑移率", "滑移达到此值时 TCS 介入力度拉满；低速端。"),
    "TC_SlipEnd1": _f("完全介入滑移-高速端", "滑移率", "高速时的拉满阈值。"),
    "MinFullSteer": _f("满舵最小修正", "倍率", "打满方向时 TCS 的最小修正强度。"),
    "MaxFullSteer": _f("满舵最大修正", "倍率", "打满方向时的最大修正强度。"),
    "TC_Speed0": _f("速度分段点0", "m/s", "低速端与高速端的分界车速。"),
    "TC_Speed1": _f("速度分段点1", "m/s", "第二个速度分段点。"),
    "TC_Yaw0": _f("偏航角映射点0", "归一化", "车身偏航角 → TCS 削减力度的映射折线第 0 点。"),
    "TC_Yaw1": _f("偏航角映射点1", "归一化", "折线第 1 点。"),
    "TC_Yaw2": _f("偏航角映射点2", "归一化", "折线第 2 点。"),
    "TC_Yaw3": _f("偏航角映射点3", "归一化", "折线第 3 点。"),
    "TC_Yaw4": _f("偏航角映射点4", "归一化", "折线第 4 点。"),
    "TC_YawTC0": _f("偏航角对应削减量0", "倍率", "与 TC_Yaw0 对应：该偏航角下的扭矩削减比例。"),
    "TC_YawTC1": _f("偏航角对应削减量1", "倍率", "与 TC_Yaw1 对应。"),
    "TC_YawTC2": _f("偏航角对应削减量2", "倍率", "与 TC_Yaw2 对应。"),
    "TC_YawTC3": _f("偏航角对应削减量3", "倍率", "与 TC_Yaw3 对应。"),
    "TC_YawTC4": _f("偏航角对应削减量4", "倍率", "与 TC_Yaw4 对应。"),
    "TC_WetYScale": _f("湿滑偏航缩放", "倍率", "雨天时偏航修正的缩放。"),
    "TC_OffroadYScale": _f("越野偏航缩放", "倍率", "非铺装路面时偏航修正的缩放。"),
    "TC_SnowYScale": _f("雪地偏航缩放", "倍率", "雪地时偏航修正的缩放。"),
    "TC_YawVel0": _f("偏航角速度映射点0", "rad/s", "车身偏航角速度 → 削减力度的映射第 0 点。"),
    "TC_YawVel1": _f("偏航角速度映射点1", "rad/s", "第 1 点。"),
    "TC_YawVelTC0": _f("偏航角速度对应削减量0", "倍率", "与 TC_YawVel0 对应。"),
    "TC_YawVelTC1": _f("偏航角速度对应削减量1", "倍率", "与 TC_YawVel1 对应。"),
    "TCSFullEffectSlipRWD": _f("后驱满效滑移", "滑移率", "后驱车 TCS 达到最大介入强度所需的滑移量。"),
    "TCSFullEffectSlipFWD": _f("前驱满效滑移", "滑移率", "前驱车的对应值。"),
    "TCSFullEffectSlipAWD": _f("四驱满效滑移", "滑移率", "四驱车的对应值。"),
    "TC_TakeOffSlip": _f("起步滑移阈值", "滑移率", "弹射起步时允许的初始滑移，越小起步越「乖」。"),
}

_MODE: Final[dict[str, dict[str, str]]] = {
    "DrivingModeID": _f("驾驶模式ID", "—", "驾驶模式配置编号。"),
    "Ordinal": _f("适用车辆序号", "外键", "该模式覆盖绑定到哪台车（Data_Car.Id）。"),
    "AeroMod": _f("气动修改", "布尔", "1=切换该模式时用下面的偏移量覆盖整车气动。"),
    "SuspensionMod": _f("悬挂修改", "布尔", "1=覆盖悬挂参数。"),
    "EngineMod": _f("引擎修改", "布尔", "1=覆盖引擎扭矩输出。"),
    "DriveTrainMod": _f("传动修改", "布尔", "1=覆盖驱动形式与差速器。"),
    "ChassisMod": _f("车身修改", "布尔", "1=覆盖车身刚性等底盘参数。"),
    "VisualAnimation": _f("视觉动画", "布尔", "1=切换模式时播放变形/开合动画。"),
    "FrontDownforceOffset": _f("前下压力偏移", "内部力单位", "相对基础值的下压力增减。"),
    "RearDownforceOffset": _f("后下压力偏移", "内部力单位", "后轴的对应增减。"),
    "FrontDragOffset": _f("前风阻偏移", "内部力单位", "车头风阻增减。"),
    "RearDragOffset": _f("后风阻偏移", "内部力单位", "车尾风阻增减。"),
    "FrontActiveAeroMultiplier": _f("前主动气动倍率", "倍率", "主动尾翼/襟翼对前部下压力的放大。"),
    "RearActiveAeroMultiplier": _f("后主动气动倍率", "倍率", "后部的对应倍率。"),
    "FrontRideHeight_Override": _f("前车高覆盖", "m", "该模式下的前轴车高。"),
    "FrontSpringK_Override": _f("前弹簧刚度覆盖", "内部刚度单位", "该模式下的前弹簧硬度。"),
    "RearRideHeight_Override": _f("后车高覆盖", "m", "该模式下的后轴车高。"),
    "RearSpringK_Override": _f("后弹簧刚度覆盖", "内部刚度单位", "该模式下的后弹簧硬度。"),
    "ThirdSpringElementMultiplier": _f("第三弹簧倍率", "倍率", "该模式下第三弹簧效果的缩放。"),
    "DampenBumpRate_Override": _f("压缩阻尼覆盖", "阻尼单位", "该模式下的压缩阻尼。"),
    "DampenReboundRate_Override": _f("回弹阻尼覆盖", "阻尼单位", "该模式下的回弹阻尼。"),
    "ModeShiftUpDelay": _f("升档延迟", "秒", "该模式下升档前的等待时间。"),
    "ModeShiftDownDelay": _f("降档延迟", "秒", "降档前的等待时间。"),
    "ModeShiftUpTime": _f("升档耗时", "秒", "升档动作本身的时长。"),
    "ModeShiftDownTime": _f("降档耗时", "秒", "降档动作本身的时长。"),
    "EngineTorqueMode_Override": _f("引擎扭矩模式覆盖", "枚举", "该模式强制使用的扭矩输出曲线模式。"),
    "GameTorqueScale_Override": _f("扭矩缩放覆盖", "倍率", "该模式下的 GameTorqueScale（台架扭矩→手感）。"),
    "ZeroThrottleTorqueScale_Override": _f("零油门扭矩缩放", "倍率", "完全松油时保留的发动机拖曳扭矩。"),
    "TCProfileID_Override": _f("TCS 配置覆盖", "外键", "该模式使用哪套牵引力控制标定。", enums="List_TractionControl"),
    "DriveType_Override": _f("驱动形式覆盖", "枚举", "该模式强制切换的驱动形式（如漂移模式改后驱）。"),
    "RearTorqueSplit_Override": _f("后轴扭矩分配覆盖", "比例", "四驱车该模式下分给后轴的扭矩比例。"),
    "FrontDiff_Accel": _f("前差速器加速锁止", "比例", "前差速器在加速时的锁止率。"),
    "FrontDiff_Decel": _f("前差速器减速锁止", "比例", "前差速器在收油/减速时的锁止率。"),
    "RearDiff_Accel": _f("后差速器加速锁止", "比例", "后差速器加速锁止率，越大越容易甩尾。"),
    "RearDiff_Decel": _f("后差速器减速锁止", "比例", "后差速器减速锁止率。"),
    "CentreDiff_Accel": _f("中央差速器加速锁止", "比例", "四驱车中央差速器的加速锁止率。"),
    "CentreDiff_Decel": _f("中央差速器减速锁止", "比例", "中央差速器减速锁止率。"),
    "GameDragScale": _f("风阻缩放", "倍率", "该模式下整车风阻的乘数。"),
    "GameDownforceScale": _f("下压力缩放", "倍率", "该模式下整车下压力的乘数。"),
    "GameDownforceOffroadScale": _f("越野下压力缩放", "倍率", "非铺装路面的下压力乘数。"),
    "StaticDownforceModeScale": _f("静态下压力缩放", "倍率", "固定式空力部件在该模式下的缩放。"),
    "NormFanSpeed": _f("风扇转速", "0~1", "主动风扇的转速比例。"),
}


# ---------------------------------------------------------------------------
# 汇总 + 派生查找
# ---------------------------------------------------------------------------
PHYSICS_FIELDS: Final[dict[str, dict[str, dict[str, str]]]] = {
    "List_TireCompound": _TIRE,
    "List_TyreCurveDB": _tyre_curve_fields(),
    "List_TireFrictionCurve": _FRICTION_CURVE,
    "List_TireFrictionMultiCurve": _MULTI_CURVE,
    "List_TireAffectCurve": _AFFECT_CURVE,
    "List_SpringDamperPhysics": _SPRING,
    "List_AntiSwayPhysics": _ANTISWAY,
    "List_ThirdSpringElement": _THIRD,
    "List_PreloadAndDroopDamper": _PRELOAD,
    "List_SuspensionPhysicsType": _SUSP_TYPE,
    "List_AeroPhysics": _AERO,
    "List_AeroStaticSystem": _AERO_STATIC,
    "List_DragWallSettingsOverride": _DRAG_WALL,
    "List_SteeringSettings": _STEER,
    "List_RearSteeringSettings": _rear_steer_fields(),
    "List_BrakeProfile": _BRAKE,
    "List_TractionControl": _TCS,
    "List_DrivingMode": _MODE,
}

# 路面后缀 → （中文后缀，说明前缀）
_SURFACE_SUFFIX: Final[dict[str, tuple[str, str]]] = {
    "_Offroad": ("（越野路面）", "越野路面"),
    "_OffRoad": ("（越野路面）", "越野路面"),
    "_Snow": ("（雪地）", "雪地"),
    "_Road": ("（铺装路面）", "铺装路面"),
}


def physics_field(table: str, column: str) -> dict[str, str] | None:
    """查物理表字段的中文元数据，自动处理路面后缀派生。

    Args:
        table: 表名，如 ``List_TireCompound``。
        column: 列名。

    Returns:
        字段元数据字典；未收录返回 ``None``。

    Note:
        ``List_TireCompound`` 里有大量 ``X / X_Offroad / X_Snow`` 三胞胎，
        只写基名即可，后缀变体由本函数实时派生，避免重复 40 多行。
    """
    table_dict = PHYSICS_FIELDS.get(table)
    if not table_dict:
        return None
    if column in table_dict:
        return table_dict[column]
    for suffix, (cn_suffix, desc_prefix) in _SURFACE_SUFFIX.items():
        if column.endswith(suffix):
            base = table_dict.get(column[: -len(suffix)])
            if base:
                # 基名说明里常带「铺装路面 1.2~1.7」这类只对沥青成立的数值，
                # 派生到越野/雪地时要把这些句子剔掉，避免误导。
                segments = [s for s in base["desc"].split("。") if s.strip()]
                if not suffix.endswith("_Road"):
                    segments = [s for s in segments if "铺装路面" not in s]
                desc = "。".join(segments) + ("。" if segments else "")
                return {
                    **base,
                    "cn": base["cn"] + cn_suffix,
                    "desc": f"{desc_prefix}：{desc}",
                }
    return None
