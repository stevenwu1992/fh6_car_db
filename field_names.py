"""字段名 → 中文的统一解析器。

数据库和 CSV 表头都需要中文名，但两者的解析链必须一致，否则会出现
「数据库里有中文、CSV 里没有」的割裂。这里把优先级固定下来：

    1. 该表的手写字典（physics_dict.py 优先，其次 dictionary.TABLE_FIELDS）
    2. 同名字段复用（Data_Car 的字段名在全库通用，NewProfile_Career_Garage
       就是照抄 Data_Car 的字段，没必要重写一遍）
    3. 调校字段 ``Tuning_xxx`` 单独拆解
    4. 词根表 AUTO_CN（整名匹配）
    5. 分词翻译（camelCase / 下划线拆词，逐词查 WORD_CN）
    6. 兜底：保留英文，状态标「待补」

只要 5 能覆盖，就不留英文——这样 200 多张表的表头不会出现中英混杂。
"""

from __future__ import annotations

import re
from typing import Final

import dictionary as D
from physics_dict import PHYSICS_FIELDS, physics_field

# 词根表：整名匹配（优先级高于分词）
AUTO_CN: Final[dict[str, tuple[str, str]]] = {
    "id": ("编号", "该表主键或外键编号"),
    "ordinal": ("序号", "在同类记录中的排列次序"),
    "releaseorder": ("发布顺序", "资源加入游戏的批次序号"),
    "displayorder": ("展示顺序", "在 UI 列表中的排列位置"),
    "sortorder": ("排序", "排序权重"),
    "sequence": ("顺序号", "同组内的先后次序"),
    "price": ("价格", "购买该部件/车辆所需的游戏币（CR）"),
    "level": ("等级", "改装档位或强度级别"),
    "isstock": ("是否原厂件", "1=原厂自带，0=改装件"),
    "mass": ("质量", "单位 kg"),
    "massdiff": ("质量变化", "装上该件后整车质量的变化量，单位 kg，负数为减重"),
    "weightdistdiff": ("配重变化", "对前后轴重量分配的影响比例"),
    "manufacturerid": ("厂商ID", "指向 List_PartManufacturer"),
    "displayname": ("显示名称", "本地化键（`_&…`），需查语言包还原"),
    "name": ("名称", "内部名称"),
    "description": ("描述", "说明文案"),
    "iconpath": ("图标路径", "UI 图标资源相对路径"),
    "imagepath": ("图片路径", "UI 大图资源相对路径"),
    "medianame": ("资源名", "模型/贴图/音频资源的定位名"),
    "partname": ("部件名", "改装件名称"),
    "partsstringid": ("部件文案ID", "指向 List_PartsStrings"),
    "carid": ("车辆ID", "指向 Data_Car.Id"),
    "carbodyid": ("车身ID", "指向 Data_CarBody.Id（= 车辆Id×1000）"),
    "engineid": ("引擎ID", "指向 Data_Engine.EngineID"),
    "drivetrainid": ("传动ID", "指向 Data_Drivetrain.DrivetrainID"),
    "motorid": ("电机ID", "指向 Data_Motor.MotorID"),
    "partid": ("部件ID", "改装件编号"),
    "contentid": ("内容包ID", "指向 ContentOffers"),
    "momentinertia": ("转动惯量", "单位 kg·m²"),
    "requiresgraphics": ("需要额外资源", "1=需要加载专属模型/贴图"),
    "title": ("标题", "UI 标题文案"),
    "shortdisplayname": ("短名称", "列表用的紧凑名称（本地化键）"),
    "thumbnail": ("缩略图路径", "列表/卡片缩略图资源"),
    "primarycolor": ("主色", "涂装主色，0xRRGGBB"),
    "secondarycolor": ("副色", "涂装副色，0xRRGGBB"),
    "valves": ("气门数", "每缸气门数量"),
    "tirecompound": ("轮胎配方", "指向 List_TireCompound"),
    "spacing": ("间距", "轮距调整量"),
    "weightreduction": ("减重比例", "轻量化套件的质量削减比例"),
    "wheelstyle": ("轮毂款式", "指向 List_Wheels"),
    "sideskirts": ("侧裙", "侧裙套件编号"),
    "carbody": ("车身套件", "车身包围编号"),
    "springdamper": ("避震套装", "指向弹簧阻尼参数组"),
    "singleturbo": ("单涡轮套件", "单涡轮增压配置编号"),
    "twinturbo": ("双涡轮套件", "双涡轮增压配置编号"),
    "shiftsystem": ("换档系统", "指向 List_ShiftSystem"),
    "suspensiontype": ("悬挂结构", "指向 List_SuspensionType"),
    "aspirationid": ("进气形式", "指向 List_Aspiration"),
    "powerminscale": ("功率最小缩放", "低功率端的效果缩放"),
    "powermaxscale": ("功率最大缩放", "高功率端的效果缩放"),
    "zerorpmscale": ("零转速缩放", "转速为 0 时的缩放值"),
    "widescale": ("宽体缩放", "宽体套件对轮距的缩放"),
    # 改装位（UpgradePresetPackages / NewProfile_Career_Garage 里成组出现）
    "engine": ("引擎", "该车已装的引擎升级件编号"),
    "drivetrain": ("传动", "传动升级件编号"),
    "motor": ("电机", "电机升级件编号"),
    "brakes": ("刹车", "刹车升级件编号"),
    "antiswayfront": ("前防倾杆", "前防倾杆升级件编号"),
    "antiswayrear": ("后防倾杆", "后防倾杆升级件编号"),
    "rearwing": ("尾翼", "尾翼升级件编号"),
    "rimsizefront": ("前轮辋尺寸", "前轮辋直径升级编号"),
    "rimsizerear": ("后轮辋尺寸", "后轮辋直径升级编号"),
    "camshaft": ("凸轮轴", "凸轮轴升级件编号"),
    "displacement": ("排气量", "扩缸升级件编号"),
    "pistonscompression": ("活塞压缩比", "活塞/压缩比升级件编号"),
    "fuelsystem": ("燃油系统", "燃油系统升级件编号"),
    "ignition": ("点火系统", "点火系统升级件编号"),
    "exhaust": ("排气系统", "排气系统升级件编号"),
    "intake": ("进气系统", "进气系统升级件编号"),
    "flywheel": ("飞轮", "飞轮升级件编号"),
    "manifold": ("进气歧管", "进气歧管升级件编号"),
    "restrictorplate": ("限流片", "限流片升级件编号"),
    "oilcooling": ("机油冷却", "机油冷却升级件编号"),
    "quadturbo": ("四涡轮", "四涡轮升级件编号"),
    "intercooler": ("中冷器", "中冷器升级件编号"),
    "clutch": ("离合器", "离合器升级件编号"),
    "driveline": ("传动轴", "传动轴升级件编号"),
    "differential": ("差速器", "差速器升级件编号"),
    "frontbumper": ("前保险杠", "前保险杠升级件编号"),
    "rearbumper": ("后保险杠", "后保险杠升级件编号"),
    "hood": ("引擎盖", "引擎盖升级件编号"),
    "tirewidthfront": ("前胎宽度", "前轮胎宽升级编号"),
    "tirewidthrear": ("后胎宽度", "后轮胎宽升级编号"),
    "chassistiffness": ("车身刚性", "车身刚性升级件编号"),
    "trackspacingfront": ("前轮距", "前轮距加宽升级编号"),
    "trackspacingrear": ("后轮距", "后轮距加宽升级编号"),
    "frontaspectratio": ("前胎扁平比", "前胎扁平比升级编号"),
    "rearaspectratio": ("后胎扁平比", "后胎扁平比升级编号"),
    "motorparts": ("电机部件", "电机部件升级编号"),
    "wheelstylerear": ("后轮毂款式", "后轮毂样式编号"),
    "tuning": ("调校", "该车的调校设定"),
    "purchasable": ("可购买", "1=可购买，0=不可购买"),
    "breadcrumbwhennew": ("新内容标记", "作为新内容时显示面包屑提示"),
    "curve": ("曲线", "曲线数据"),
    "primarygroup": ("主分组", "UI 归属分组"),
}

# 分词表：逐词翻译，覆盖 camelCase / 下划线命名
WORD_CN: Final[dict[str, str]] = {
    # 方向/位置
    "front": "前", "rear": "后", "left": "左", "right": "右",
    "up": "上", "down": "下", "center": "中央", "centre": "中央",
    "side": "侧", "inner": "内侧", "outer": "外侧", "top": "顶", "bottom": "底",
    "first": "第一", "second": "第二", "third": "第三", "fourth": "第四",
    "fifth": "第五", "sixth": "第六", "seventh": "第七", "eighth": "第八",
    "ninth": "第九", "tenth": "第十",
    # 通用
    "speed": "速度", "velocity": "速度", "accel": "加速", "decel": "减速",
    "angle": "角度", "time": "时间", "ratio": "比", "rate": "速率", "scale": "系数",
    "offset": "偏移", "width": "宽", "height": "高", "length": "长", "size": "尺寸",
    "weight": "重量", "force": "力", "torque": "扭矩", "power": "功率",
    "count": "数量", "num": "数量", "index": "索引", "type": "类型", "level": "等级",
    "name": "名称", "path": "路径", "value": "值", "min": "最小", "max": "最大",
    "mean": "均值", "stddev": "标准差", "var": "方差", "age": "权重",
    "start": "起始", "end": "结束", "line": "线", "mode": "模式", "flag": "标记",
    "is": "是否", "has": "有无", "use": "启用", "apply": "应用", "custom": "自定义",
    "default": "默认", "current": "当前", "cur": "当前", "original": "原始",
    "total": "累计", "color": "颜色", "colors": "颜色", "icon": "图标",
    "image": "图片", "logo": "标志", "music": "音乐", "radio": "电台", "track": "赛道",
    "car": "车辆", "cars": "车辆", "wheel": "车轮", "tire": "轮胎", "tyre": "轮胎",
    "spring": "弹簧", "damping": "阻尼", "bump": "压缩", "rebound": "回弹",
    "pressure": "压力", "friction": "摩擦", "slip": "滑移", "brake": "刹车",
    "braking": "制动", "throttle": "油门", "clutch": "离合器", "gear": "档位",
    "engine": "引擎", "motor": "电机", "damage": "损伤", "impact": "撞击",
    "probability": "概率", "weather": "天气", "season": "季节", "springs": "春季",
    "summer": "夏季", "autumn": "秋季", "winter": "冬季", "rpm": "转速",
    "peak": "峰值", "low": "低", "high": "高", "off": "关闭", "on": "开启",
    "pass": "通过", "passing": "超车", "follow": "跟车", "blocking": "阻挡",
    "sideswipe": "擦碰", "corner": "弯道", "cutting": "切入", "going": "驶出",
    "wide": "外侧", "temperament": "性情", "racing": "竞速", "behavior": "行为",
    "difficulty": "难度", "laps": "圈数", "lap": "圈", "route": "路线",
    "duration": "时长", "seconds": "秒", "reverse": "反向", "length": "长度",
    "button": "按键", "thumb": "摇杆", "trigger": "扳机", "shoulder": "肩键",
    "dpad": "十字键", "stick": "摇杆", "axis": "轴", "layout": "布局",
    "preset": "预设", "slot": "槽位", "group": "分组", "category": "分类",
    "tag": "标签", "sort": "排序", "order": "顺序", "version": "版本",
    "state": "状态", "status": "状态", "unlock": "解锁", "locked": "锁定",
    "purchas": "购买", "owned": "拥有", "favorite": "收藏", "visible": "可见",
    "hidden": "隐藏", "active": "启用", "enabled": "启用", "disable": "禁用",
    "count": "数量", "score": "分数", "points": "点数", "winnings": "奖金",
    "repair": "维修", "sold": "出售", "owner": "车主", "owners": "车主",
    "victories": "胜场", "podiums": "领奖台", "races": "比赛", "skill": "技巧",
    "distance": "里程", "driven": "行驶", "odometer": "里程表",
    "rebuild": "重建", "mod": "修正", "grip": "抓地", "flex": "形变",
    "air": "空气", "psi": "胎压", "gear": "档位", "drive": "驱动",
    "ratio": "比", "final": "最终", "cam": "倾角", "toe": "前束", "caster": "后倾",
    "swaybar": "防倾杆", "ride": "车身", "downforce": "下压力", "balance": "分配",
    "center": "中央", "centre": "中央", "diff": "差速器", "diff": "差速器",
    # —— 镜头与视角 ——
    "cam": "镜头", "camera": "镜头", "cockpit": "车内视角", "bumper": "保险杠",
    "hood": "引擎盖", "follow": "跟车", "radius": "半径", "target": "目标",
    "pitch": "俯仰", "yaw": "偏航", "roll": "横滚", "splitscreen": "分屏",
    "position": "位置", "rotation": "旋转", "preset": "预设", "allcaps": "全大写",
    "high": "高", "low": "低", "no": "无", "near": "近", "far": "远",
    # —— 差速器 ——
    "limitedslip": "限滑", "relvel": "相对速度", "clamp": "钳位",
    "inputtorque": "输入扭矩", "accelef": "加速",
    # —— 刹车系统 ——
    "drum": "鼓", "depth": "深度", "nonspinning": "非旋转", "rotor": "刹车盘",
    "thickness": "厚度", "caliper": "卡钳", "pistons": "活塞", "mm": "毫米",
    # —— 天气与季节 ——
    "pause": "暂停", "regional": "地区", "custom": "自定义", "presetid": "预设ID",
    # —— 变速箱 ——
    "shift": "换档", "shifttime": "换档时间", "clutchin": "离合接入",
    "clutchout": "离合断开", "transmission": "变速箱", "cvt": "无级变速",
    # —— 赛事与赛道 ——
    "laps": "圈数", "quickrace": "快速比赛", "lapcount": "圈数",
    "ribbon": "赛道带", "configuration": "配置", "reverseindex": "反向赛道索引",
    "homespace": "主场", "realworld": "真实赛道", "stray": "偏离",
    "teleport": "传送", "warning": "警告", "crosscountry": "越野",
    "startline": "起点线", "finishline": "终点线", "satimage": "卫星图",
    "carousel": "轮播", "placement": "位置", "winnings": "奖金", "scalar": "系数",
    # —— AI / Drivatar ——
    "difficulty": "难度", "level": "等级", "player": "玩家", "ai": "AI",
    "learning": "学习", "rate": "速率", "random": "随机", "seed": "种子",
    "relativefrequency": "相对频率", "variation": "变体", "behavior": "行为",
    "aggression": "激进程度", "clearance": "间距", "interaction": "交互",
    "scripted": "脚本", "trackedge": "赛道边缘", "trailing": "尾随",
    # —— 存档 / 通用字段 ——
    "vin": "车架号", "ordinal": "序号", "guid": "全局ID", "rowid": "行ID",
    "flags": "标记位", "feature": "特性", "profile": "配置文件",
    "quantity": "数量", "density": "密度", "material": "材质", "base": "基础",
    "parent": "父级", "child": "子级", "value": "值", "mapped": "映射",
    "maps": "映射", "compatibility": "兼容性", "preview": "预览",
    "template": "模板", "suffix": "后缀", "style": "样式", "theme": "主题",
    "release": "发布", "date": "日期", "utc": "UTC",
    "paid": "实付", "upsell": "追加销售", "promo": "促销", "free": "免费",
    "exception": "例外", "whitelist": "白名单", "redeem": "兑换",
    "launch": "弹射", "chunk": "分块", "null": "空", "special": "特殊",
    "latin": "拉丁", "substitution": "替换", "character": "字符",
    "alpha": "透明度", "text": "文本", "reader": "阅读器", "help": "帮助",
    "markup": "富文本", "subtitle": "副标题", "displaytype": "展示类型",
    "sortfield": "排序字段", "sortpriority": "排序优先级", "balanced": "均衡",
    "renderable": "可渲染", "installed": "已安装", "purchased": "已购买",
    "active": "启用", "visible": "可见", "show": "显示", "map": "地图",
    # —— 车辆部件 ——
    "wing": "尾翼", "mirrors": "后视镜", "windows": "车窗", "rim": "轮辋",
    "decals": "贴花", "paintable": "可涂装", "livery": "涂装", "vinyl": "乙烯基",
    "decal": "贴花", "paint": "涂装", "color": "颜色", "colour": "颜色",
    "rgb": "RGB值", "two": "双", "tone": "色调", "pri": "主", "sec": "副",
    "tertiary": "第三", "bias": "倾向", "specialchar": "特殊字符",
    "center": "中央", "cap": "盖", "lip": "唇", "spacer": "法兰盘",
    "track": "赛道", "spacing": "间距",
    # —— 坐标与通用缩写 ——
    "x": "X", "y": "Y", "z": "Z", "id": "ID", "ids": "ID", "idx": "索引",
    "num": "数量", "qty": "数量", "pct": "百分比", "disp": "显示", "min": "最小",
    "max": "最大", "avg": "平均", "std": "标准差", "acceleration": "加速",
    "handling": "操控", "launch": "弹射", "class": "等级", "rating": "评级",
    "key": "键", "keys": "键", "values": "值", "actual": "实际",
    "affected": "受影响", "by": "由", "anthem": "主题曲", "arena": "竞技场",
    "arrival": "到达", "aspiration": "进气", "atlas": "图集", "audio": "音频",
    "autosteer": "自动转向", "backfire": "回火", "background": "背景",
    "badge": "徽章", "block": "块", "bucket": "分桶", "career": "生涯",
    "clan": "俱乐部", "collision": "碰撞", "collisions": "碰撞", "config": "配置",
    "content": "内容", "country": "国家", "creator": "创建者", "cut": "切断",
    "data": "数据", "departure": "出发", "destination": "目的地",
    "dev": "开发", "differential": "差速器", "drag": "风阻", "drift": "漂移",
    "drivatar": "Drivatar", "driver": "车手", "drop": "下降", "dummy": "虚拟",
    "environment": "环境", "error": "错误", "event": "事件", "fan": "风扇",
    "featured": "精选", "field": "字段", "filename": "文件名", "flex": "形变",
    "flyer": "传单", "flying": "动态", "forced": "强制", "frac": "小数",
    "game": "游戏", "garage": "车库", "hardcore": "硬核", "headshot": "头像",
    "hide": "隐藏", "horizon": "地平线", "inair": "腾空", "include": "包含",
    "keyword": "关键词", "load": "加载", "location": "位置", "map": "地图",
    "media": "媒体", "midnight": "午夜", "mini": "迷你", "misc": "杂项",
    "mount": "挂载", "music": "音乐", "norm": "法线", "number": "编号",
    "offer": "提供", "ok": "适用", "oneover": "倒数", "package": "包",
    "parent": "父级", "physics": "物理", "powertrain": "动力总成",
    "primary": "主", "race": "比赛", "rarity": "稀有度", "redline": "红线",
    "relative": "相对", "remove": "移除", "requires": "需要", "restriction": "限制",
    "rich": "富", "rob": "抢夺", "rotors": "转子", "row": "行", "rule": "规则",
    "sat": "卫星", "secondary": "副", "sequence": "顺序", "shared": "共享",
    "short": "短", "should": "是否", "small": "小", "stagger": "错位",
    "stall": "失速", "steam": "Steam", "steer": "转向", "suspension": "悬挂",
    "table": "表", "team": "队伍", "teams": "队伍", "tune": "调校", "turn": "弯",
    "ui": "UI", "ungrouped": "未分组", "upgrade": "升级", "upper": "上",
    "lower": "下", "versioned": "版本化", "wear": "磨损", "wet": "湿",
    "wind": "风", "xmirror": "X镜像", "zero": "零", "database": "数据库",
    "version": "版本", "liv": "涂装", "vinyl": "乙烯基", "camber": "外倾角",
    "toe": "前束", "caster": "后倾角", "rideheight": "车身高度",
    "dampingstiffness": "阻尼硬度", "bumpratio": "压缩比", "downforce": "下压力",
    "brakebalance": "刹车分配", "brakepressure": "刹车力度", "centertorque": "中央扭矩分配",
    "reartoquesplit": "后轴扭矩分配", "throttlecut": "油门切断", "throttledelay": "油门延迟",
    "clutchwhenshifting": "换档需离合", "abs": "ABS", "tcs": "TCS",
    "stm": "STM", "sasr": "SASR", "sai": "主销内倾",
    "body": "车身", "roof": "车顶", "rimstyles": "轮毂样式", "styles": "样式",
    "mountpath": "挂载路径", "playlist": "播放列表", "grid": "发车格",
    "locator": "定位点", "mapx": "地图X", "mapy": "地图Y",
    "universe": "世界", "per": "每",
}


# 精确名表：分词拼不出来的零散字段，逐个手写（按列名精确匹配，区分大小写）
EXACT_CN: Final[dict[str, str]] = {
    "AllowStockManufacturerColorsForWheels": "允许轮毂使用原厂配色",
    "ApplyRecommendedTire": "应用推荐轮胎",
    "ApplyThrottleCutWhileDriving": "行驶中切断油门",
    "Arcade": "街机模式",
    "AutoSteerSTMSlipMax": "自动转向 STM 滑移上限",
    "AutoSteerSTMSlipMin": "自动转向 STM 滑移下限",
    "BadgeTexturePathPrefix": "等级徽章贴图前缀",
    "BiasHandbrake": "手刹偏置",
    "BlockDimX": "包围盒尺寸 X", "BlockDimY": "包围盒尺寸 Y", "BlockDimZ": "包围盒尺寸 Z",
    "BrakeBiasSlider": "刹车分配滑块",
    "BrakeDrawOffset": "刹车盘绘制偏移",
    "BrakeTorqueSlider": "刹车扭矩滑块",
    "BucketHero": "分桶主视觉图",
    "ButtonA": "A 键", "ButtonB": "B 键", "ButtonX": "X 键", "ButtonY": "Y 键",
    "CMBackFront": "重心前后位置", "CMHeight": "重心高度",
    "CMHeightDiff": "重心高度差", "CMLeftRight": "重心左右位置",
    "CarRestrictions": "车型限制条件",
    "CareerMinEligiblePI": "生涯赛事最低准入 PI",
    "CareerRaceCollectionId": "生涯赛事合集ID",
    "CareerRaceCollectionTypeId": "生涯赛事合集类型ID",
    "CareerRaceId": "生涯赛事ID",
    "CareerRacesInCollectionId": "合集内赛事关系ID",
    "CenterLimitedSlipAccelDefInputTorque": "中央限滑-加速默认输入扭矩",
    "CenterLimitedSlipRelVelClamp": "中央限滑-相对速度钳位",
    "CenterLimitedSlipTorqueAccel": "中央限滑-加速扭矩",
    "CenterLimitedSlipTorqueDecel": "中央限滑-减速扭矩",
    "ChassisStiffness": "车身刚性",
    "ClutchInTime": "离合接入时间", "ClutchOutTime": "离合断开时间",
    "ColorFinish": "漆面类型", "ColorFinishID": "漆面类型ID",
    "CreatorXUID": "创建者 XUID",
    "CustomRouteP2P": "自定义点对点路线",
    "DPadUp": "十字键-上", "DPadDown": "十字键-下",
    "DPadLeft": "十字键-左", "DPadRight": "十字键-右",
    "DamageModDefID": "损伤模型ID",
    "DefaultManufacturerColorIndex": "默认厂商色索引",
    "DefaultStartGridPositionsId": "默认发车格位置ID",
    "DisplayNameMarkup": "富文本显示名",
    "DisplayScenario": "展示场景",
    "DisplaySubtitle": "显示副标题",
    "DisplayType": "展示类型",
    "DriverModelId": "车手模型ID",
    "DummyAxleInRear": "虚拟轴位于后轴",
    "DummyAxleWheelbase": "虚拟轴轴距",
    "DurationInSeconds": "时长（秒）",
    "EndPart": "结束部件", "StartPart": "起始部件",
    "EnvImagePath": "环境图片路径",
    "ErrorString": "错误信息",
    "EventLabEvent": "EventLab 活动",
    "EverymanUpgradeDisplayOrder": "通用改装展示顺序",
    "ExhaustLevel": "排气等级",
    "FeaturedVideo": "精选视频",
    "FinishLine": "终点线",
    "FlexDamperMax": "柔性阻尼上限", "FlexDamperMin": "柔性阻尼下限",
    "FlexDamperMaxOffroad": "柔性阻尼上限（越野）",
    "FlexDamperMinOffroad": "柔性阻尼下限（越野）",
    "FlyerContainerName": "传单容器名",
    "FlyingStartPosId": "动态起跑位置ID",
    "FracDigits": "小数位数",
    "FrictionDisplay": "摩擦系数显示值",
    "FrontBrakeNonSpinningMass": "前刹车非旋转质量",
    "FrontLatFrictionMult": "前轴侧向摩擦倍率",
    "FrontLatFrictionScale": "前轴侧向摩擦系数",
    "FrontLimitedSlipAccelDefInputTorque": "前限滑-加速默认输入扭矩",
    "FrontLimitedSlipRelVelClamp": "前限滑-相对速度钳位",
    "FrontLimitedSlipTorqueAccel": "前限滑-加速扭矩",
    "FrontLimitedSlipTorqueDecel": "前限滑-减速扭矩",
    "FrontLongFrictionMult": "前轴纵向摩擦倍率",
    "FrontLongFrictionScale": "前轴纵向摩擦系数",
    "FrontTireAspectRatioOffset": "前胎扁平比偏移",
    "FrontWheelDiameter": "前轮直径",
    "HasCurrentOwnerViewedCar": "当前车主已查看该车",
    "HasHelicopter": "有直升机",
    "HasProps": "有道具",
    "HasRallyTimer": "有拉力计时",
    "HasTraffic": "有交通车",
    "HeadshotLargePath": "大头像资源路径",
    "HelpString": "帮助文本",
    "HideManufacturerColors": "隐藏厂商色",
    "HideNormalColors": "隐藏普通色",
    "HideSpecialColors": "隐藏特殊色",
    "HighestSkillScore": "最高技巧分",
    "IconPathLarge": "大图标路径",
    "InAirPitchDamping": "腾空俯仰阻尼", "InAirPitchStrength": "腾空俯仰强度",
    "InAirRollDamping": "腾空横滚阻尼", "InAirRollStrength": "腾空横滚强度",
    "InAirYawDamping": "腾空偏航阻尼", "InAirYawStrength": "腾空偏航强度",
    "InitialMass": "初始质量", "InitialWeight": "初始重量",
    "IsAutoRedeem": "自动兑换",
    "IsNew": "新内容标记",
    "IsRealWorld": "真实赛道",
    "IsRewindAvailable": "可用倒带",
    "IsSpecialChar": "特殊字符",
    "IsTimedEvent": "计时赛",
    "IsWhiteList": "白名单",
    "KeyPartName": "关键部件名",
    "KeywordOneID": "关键词1 ID", "KeywordTwoID": "关键词2 ID",
    "LatinSubstitutionChar": "拉丁字符替换",
    "LiveryFileName": "涂装文件名",
    "LoadBackToStart": "回到起点重新加载",
    "LocationAllCaps": "位置（全大写）",
    "LowerAlphaText2": "下层透明文字2",
    "MPPitProfile": "多人模式维修区配置",
    "MPSortOrder": "多人模式排序",
    "MakeId": "品牌ID",
    "ManufacturerCode": "厂商代码",
    "MapsTo": "映射到",
    "MassLevel": "质量等级",
    "MaxDisplayPerformanceIndex": "显示 PI 上限",
    "MaxPerformanceIndex": "内部 PI 上限",
    "MaxRevRangePerSecond": "每秒最大转速变化",
    "MidnightCarModelId": "午夜车模型ID",
    "ModFullDamage": "全损时系数", "ModZeroDamage": "无损时系数",
    "MultipleOfEngineTorqueForSpring": "弹簧用引擎扭矩倍数",
    "MusicEndWaypoint": "音乐结束路点", "MusicStartWaypoint": "音乐起始路点",
    "NoDecalsWingAftermarket": "副厂尾翼不可贴花",
    "NoDecalsWingStock": "原厂尾翼不可贴花",
    "NoHoodAftermarket": "无副厂引擎盖",
    "NoHoodStock": "无原厂引擎盖",
    "NoPaintableWingAftermarket": "副厂尾翼不可涂装",
    "NoPaintableWingStock": "原厂尾翼不可涂装",
    "NumInputColors": "输入颜色数量",
    "NumRPMEntriesArray": "扭矩曲线采样点数",
    "NumSkillPointsEarned": "累计技巧点",
    "NumTimesSold": "出售次数",
    "NumberOfAIDrivers": "AI 车手数量",
    "OKForBody": "可用于车身", "OKForRoof": "可用于车顶",
    "OffThrottleMomentInertia": "收油时转动惯量",
    "OneOverSpringConstant": "弹簧常数倒数",
    "Part": "部件",
    "PartAttributeID": "部件属性ID",
    "PartEnumValue": "部件枚举值",
    "PartLevel": "部件等级",
    "PartManufacturer": "部件厂商",
    "PartManufacturerID": "部件厂商ID",
    "PartPosX": "部件位置 X", "PartPosY": "部件位置 Y", "PartPosZ": "部件位置 Z",
    "PartsString": "部件文案",
    "PartsValue": "零件价值",
    "Passing_LowRelVelPassProbability": "超车-低速差时超车概率",
    "Passing_StartPassAtImpactTime": "超车-撞击时开始超车",
    "Passing_TrackEdgeClearance": "超车-赛道边缘间距",
    "PeakIntakePSI": "峰值进气压力",
    "PeakSASRDisplay": "峰值滑移角显示值",
    "PeakSASRScale": "峰值滑移角系数",
    "PreviewTexture": "预览贴图",
    "PriceDisplay": "价格显示", "PricePaid": "实付价格", "PriceScale": "价格缩放",
    "PrimaryColorDisplayName": "主色显示名",
    "PrimaryColorValid": "主色是否有效",
    "QuickRaceLapCount": "快速比赛圈数",
    "QuickRaceLapCountKinect": "快速比赛圈数（Kinect）",
    "RacingLineOffsetVariance": "走线偏移方差",
    "ReaderDesc": "阅读器描述",
    "RearBrakeNonSpinningMass": "后刹车非旋转质量",
    "RearLatFrictionMult": "后轴侧向摩擦倍率",
    "RearLatFrictionScale": "后轴侧向摩擦系数",
    "RearLimitedSlipAccelDefInputTorque": "后限滑-加速默认输入扭矩",
    "RearLimitedSlipRelVelClamp": "后限滑-相对速度钳位",
    "RearLimitedSlipTorqueAccel": "后限滑-加速扭矩",
    "RearLimitedSlipTorqueDecel": "后限滑-减速扭矩",
    "RearLongFrictionMult": "后轴纵向摩擦倍率",
    "RearLongFrictionScale": "后轴纵向摩擦系数",
    "RearTireAspectRatioOffset": "后胎扁平比偏移",
    "RearToqueSplit": "后轴扭矩分配（原文拼写 Toque）",
    "RearWheelDiameter": "后轮直径",
    "RelativeFrequency": "相对频率",
    "ReleasePointABS": "ABS 释放点",
    "RequiresClutchWhenShifting": "换档需踩离合",
    "RibbonImageFullScreen": "赛道带全屏图",
    "RichPresence": "在线状态（Xbox 富状态）",
    "RouteContainerName": "路线容器名",
    "RuleContainerName": "规则容器名",
    "SecondaryColorDisplayName": "副色显示名",
    "ShiftSystemID": "换档系统ID",
    "ShortDisplayNameAllCaps": "短名称（全大写）",
    "SortPriority": "排序优先级",
    "StaggeredStart": "错位起跑",
    "SteamAppId": "Steam 应用ID",
    "SteamAppIdTesting": "Steam 测试应用ID",
    "SteerMaxAngleFiltered": "滤波后的最大转向角",
    "SteeringSettingsProfileID": "转向参数组ID",
    "SuperchargerCSC": "离心式机械增压",
    "SuperchargerDSC": "正排量机械增压",
    "SuspensionDamageModDefID": "悬挂损伤模型ID",
    "TCProfileID": "TCS 配置ID",
    "ThrottleDelayAccel": "油门延迟（加速）",
    "ThrottleDelayDeccel": "油门延迟（减速）",
    "TimeDrivenInRoadTrips": "公路旅行驾驶时长",
    "TireBrand": "轮胎品牌", "TireBrandId": "轮胎品牌ID",
    "TireCompoundId": "轮胎配方ID",
    "TireModelName": "轮胎型号名",
    "TiresDamageModDefID": "轮胎损伤模型ID",
    "TorqueCurveFullThrottleID": "全油门扭矩曲线ID",
    "TorqueCurveID": "扭矩曲线ID",
    "TorqueCurveMaxRPM": "扭矩曲线最高转速",
    "TorqueDropOffRPM0": "扭矩回落起始转速",
    "TorqueDropOffRPM1": "扭矩回落结束转速",
    "TorqueDropOffScale0": "扭矩回落比例（起点）",
    "TorqueDropOffScale1": "扭矩回落比例（终点）",
    "TotalRepairs": "累计维修次数",
    "TrackBuildNumber": "赛道构建号",
    "TuneFileName": "调校文件名",
    "Tuning_frontDampingStiffness": "调校：前阻尼硬度",
    "Tuning_rearDampingStiffness": "调校：后阻尼硬度",
    "UngroupedPartEnum": "未分组部件枚举",
    "UpgradeAreaId": "改装大区ID",
    "UseCrossCountryAI": "启用越野 AI",
    "UseInAirABS": "腾空时启用 ABS",
    "VariableTimingID": "可变气门正时ID",
    "VariableTimingType": "可变气门正时类型",
    "VersionedTuneXUID": "版本化调校 XUID",
    "WearDisplay": "磨损显示值",
    "WetTireModelName": "雨胎型号名",
    "WindInstabilityScale": "风不稳定系数",
    "XMirror321": "X 轴镜像（321 布局）",
    "YawOverride": "偏航覆盖",
    "livtype": "涂装类型",
    "vinyllocfield": "乙烯基定位字段",
    "database_version": "数据库版本号",
    "DevCenterId": "开发中心ID",
    "ParentOfferId": "父内容包ID",
    "OfferId": "内容包ID",
    "PackageName": "内容包名称",
    "MountPath": "挂载路径",
    "DisplayNameMarkup": "富文本显示名",
    "IconPathBase": "基础图标路径",
    "LogoSmall": "小型标志",
    "SmallIconPath": "小图标路径",
}


# 逐表覆盖：同名字段换到别的表语义会跑偏
TABLE_OVERRIDES: Final[dict[str, dict[str, tuple[str, str]]]] = {
    "Tracks": {
        "DisplayName": ("赛道名称", "赛道的中文名（本地化键）。"),
        "ShortDisplayName": ("赛道短名称", "列表用的紧凑名称。"),
        "MediaName": ("资源名", "赛道的资源定位名。"),
        "Length": ("赛道长度", "单位米。"),
        "Active": ("是否启用", "1=在赛事列表中可选。"),
        "IsPurchased": ("已解锁", "1=玩家已解锁该赛道。"),
    },
    "ContentOffers": {
        "DisplayName": ("内容包名称", "内容包的中文名（本地化键）。"),
        "DisplaySubtitle": ("内容包副标题", "售卖页的副标题文案（本地化键）。"),
        "Description": ("内容包描述", "售卖页的详细介绍（本地化键）。"),
        "DisplayNameMarkup": ("富文本名称", "带格式标记的显示名。"),
        "ImagePath": ("封面图路径", "售卖页主图资源。"),
        "ThumbPath": ("缩略图路径", "列表缩略图资源。"),
        "IsFree": ("是否免费", "1=免费内容。"),
        "IsNew": ("是否新品", "1=标记为最新内容。"),
        "Visible": ("是否可见", "1=在商店中可见。"),
        "SortOrder": ("排序", "商店中的排列顺序。"),
        "ReleaseOrder": ("发布顺序", "内容包的发布批次。"),
        "ShouldUpsell": ("是否推荐加购", "1=在购买流程中推荐。"),
        "SteamAppId": ("Steam 应用ID", "对应 Steam 商店的 AppID。"),
        "SteamAppIdTesting": ("Steam 测试应用ID", "测试分支使用的 AppID。"),
        "TrackBuildNumber": ("构建号", "该内容对应的构建编号。"),
    },
    "Environments": {
        "DisplayName": ("场景名称", "场景的中文名（本地化键）。"),
        "Name": ("场景内部名", "场景的英文代号。"),
    },
}


def _split(name: str) -> list[str]:
    """把 ``Tuning_frontTirePressure`` / ``IsPurchased`` 拆成词。"""
    parts: list[str] = []
    for chunk in name.split("_"):
        if not chunk:
            continue
        for w in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", chunk):
            parts.append(w)
    return parts


def _translate_words(name: str) -> str:
    """逐词翻译；有一个词不认识就整体放弃，避免拼出半中半英的怪名字。"""
    parts = _split(name)
    if not parts:
        return ""
    out = []
    for w in parts:
        zh = WORD_CN.get(w.lower())
        if not zh:
            return ""
        out.append(zh)
    text = "".join(out)
    return text


def resolve(table: str, col: str) -> tuple[dict[str, str], str]:
    """解析字段中文名。

    Args:
        table: 表名。
        col: 列名。

    Returns:
        ``(元数据, 状态)``。状态取值为 ``手写`` / ``同名字段`` / ``自动推断`` / ``待补``。
    """
    # 0. 本身已是中文（字典表自己的列名），直接透传
    if any("\u4e00" <= ch <= "\u9fff" for ch in col):
        return {"cn": col, "unit": "—", "desc": "字典表自身的列名。"}, "本身中文"

    # 1. 物理表手写
    meta = physics_field(table, col)
    if meta:
        return meta, "手写"

    # 2. 本表手写
    meta = D.FIELDS.get(col) if table == "Data_Car" else D.TABLE_FIELDS.get(table, {}).get(col)
    if meta:
        return meta, "手写"

    # 2.5 逐表覆盖（同名字段在别的表语义可能跑偏）
    override = TABLE_OVERRIDES.get(table, {}).get(col)
    if override:
        return {"cn": override[0], "unit": "—", "desc": override[1]}, "手写"

    # 3. 跨表同名字段：Data_Car 的字段名在全库通用
    #    （NewProfile_Career_Garage 就是照抄 Data_Car 的字段）
    meta = D.FIELDS.get(col)
    if meta:
        return {**meta, "desc": f"与 Data_Car 同名字段一致。{meta.get('desc', '')}"}, "同名字段"
    for table_dict in PHYSICS_FIELDS.values():
        if col in table_dict:
            base = table_dict[col]
            return {**base, "desc": f"与其他物理表同名字段一致。{base.get('desc', '')}"}, "同名字段"

    # 4. 精确名表 → 整名词根
    if col in EXACT_CN:
        return ({"cn": EXACT_CN[col], "unit": "—",
                 "desc": "按字段名与所在表语义人工命名。"}, "自动推断")
    key = col.lower()
    if key in AUTO_CN:
        cn, desc = AUTO_CN[key]
        return {"cn": cn, "unit": "—", "desc": desc}, "自动推断"

    # 5. 带序号的成组字段
    m = re.fullmatch(r"Radio(\d+)TrackInt", col)
    if m:
        return ({"cn": f"电台{m.group(1)} 曲目ID", "unit": "—",
                 "desc": "该车自定义电台里第几个曲目的内部 ID。"}, "自动推断")
    m = re.fullmatch(r"GearRatio(\d+)", col)
    if m:
        idx = int(m.group(1)) + 1
        return ({"cn": f"{idx} 档齿比", "unit": "比", "desc": "该档位的齿轮比。"}, "自动推断")
    m = re.fullmatch(r"ApplyRecommendedTire(.+)", col)
    if m:
        zh = _translate_words(m.group(1))
        if zh:
            return ({"cn": f"应用推荐轮胎-{zh}", "unit": "—",
                     "desc": "该赛事是否用推荐轮胎覆盖此维度。"}, "自动推断")

    # 6. 调校字段：Tuning_xxx
    if col.startswith("Tuning_"):
        body = col[len("Tuning_"):]
        zh = _translate_words(body)
        if zh:
            return {"cn": f"调校：{zh}", "unit": "—", "desc": "车库存档里的调校滑块取值。"}, "自动推断"

    # 6. 曲线采样点
    if key.startswith("v") and key[1:].isdigit():
        return ({"cn": f"曲线采样点 v{key[1:]}", "unit": "—",
                 "desc": "曲线离散点序列中的一个取值。"}, "自动推断")

    # 7. 前后缀派生
    for prefix, zh_p in (("front", "前"), ("rear", "后")):
        if key.startswith(prefix) and len(col) > len(prefix):
            sub, state = resolve(table, col[len(prefix):])
            if sub.get("cn"):
                return ({"cn": zh_p + sub["cn"], "unit": sub.get("unit", "—"),
                         "desc": f"{zh_p}轴：{sub.get('desc', '')}"}, "自动推断")

    # 8. 分词翻译
    zh = _translate_words(col)
    if zh:
        return {"cn": zh, "unit": "—", "desc": "按字段名词根推断。"}, "自动推断"

    # 9. 放弃
    return {}, "待补"
