"""车辆索引页面模板：GT 风格车鉴 + 数据表。

单独成文件，方便只改版式不动数据管线。`build_web.py` 把 `__DATA__` 换成 JSON 后写出。

版式要点：
    · 头图     全屏游戏截图 + FH6 标识，左侧压深，右下角顶到折线的四组数字
    · 车鉴     按品牌分段，段落头 = 品牌标 + 大号品牌名 + 细线 + 台数；车卡无边框，车图压基线
    · 数据表   同一批车的密集视图，字号 15px、行高 56px，关键列加粗
    · 抽屉     单台车：大图 + 六宫格核心数据 + 151 项全字段 + 可选轮胎
"""

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN" data-type="software">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>车辆索引 · Forza Horizon 6 车辆数据库</title>
<meta name="description" content="Forza Horizon 6 全车辆数据库：691 台车、96 个品牌、每车 151 项出厂字段与 41 种轮胎配方，可按品牌浏览、排序、并排比对。">
<meta name="page-type" content="software">
<meta name="site-kind" content="gaming">
<meta name="theme-color" content="#0B0B0E">
<meta property="og:title" content="车辆索引 · Forza Horizon 6 车辆数据库">
<meta property="og:description" content="691 台车、151 项字段、41 种轮胎配方，一次看全。">
<meta property="og:image" content="assets/img/hero.webp">
<meta property="og:type" content="website">
<link rel="icon" href="assets/img/mark.png">
<style>
  /* ── 基础 ───────────────────────────────────────────── */
  *,*::before,*::after{box-sizing:border-box}
  /* Selawik：微软以 SIL OFL 1.1 发布的开源字体，与 Segoe UI 度量兼容，
     可以自由嵌入网页与商用。只用来兜底非 Windows 平台（Bahnschrift / Segoe UI 缺席时），
     Windows 上仍然优先用系统字体，不额外下载。 */
  @font-face{font-family:"Selawik";src:url("assets/fonts/selawik-300.woff2") format("woff2");font-weight:300;font-style:normal;font-display:swap}
  @font-face{font-family:"Selawik";src:url("assets/fonts/selawik-400.woff2") format("woff2");font-weight:400;font-style:normal;font-display:swap}
  @font-face{font-family:"Selawik";src:url("assets/fonts/selawik-600.woff2") format("woff2");font-weight:600;font-style:normal;font-display:swap}
  @font-face{font-family:"Selawik";src:url("assets/fonts/selawik-700.woff2") format("woff2");font-weight:700;font-style:normal;font-display:swap}

  :root{
    --paper:#ffffff; --paper-2:#f4f4f5; --white:#ffffff;
    --ink:#111114; --ink-2:#2d2d33; --steel:#65656d; --steel-2:#6e6e76;
    --rule:#e3e3e6; --rule-soft:#f0f0f2;
    --accent:#e8185f; --accent-2:#ff6a3d;
    --dark:#0b0b0e;
    --bar-bg:rgba(255,255,255,.92);
    --shadow:rgba(17,17,20,.10);
    --sel:#fdf0f4;
    --gut:clamp(20px,3.4vw,56px);
    --maxw:1320px;
    --navh:56px; --barh:66px;
    --r:2px;
    --disp:"Bahnschrift","Segoe UI Variable Display","Segoe UI","Selawik","Microsoft YaHei UI","PingFang SC","Hiragino Sans GB",sans-serif;
    --text:"Segoe UI Variable Text","Segoe UI","Selawik","Microsoft YaHei UI","PingFang SC","Hiragino Sans GB",sans-serif;
    --mono:"Cascadia Mono",Consolas,"Courier New",monospace;
  }
  html[data-theme="dark"]{
    --paper:#0b0b0e; --paper-2:#17171c; --white:#15151a;
    --ink:#f4f4f7; --ink-2:#cfcfd7; --steel:#9c9ca6; --steel-2:#8d8d97;
    --rule:#2b2b33; --rule-soft:#1e1e24;
    --accent:#ff2d6f; --accent-2:#ff7a4d;
    --dark:#08080a;
    --bar-bg:rgba(11,11,14,.92);
    --shadow:rgba(0,0,0,.5);
    --sel:rgba(255,255,255,.09);
    color-scheme:dark;
  }
  html{color-scheme:light;-webkit-text-size-adjust:100%;scroll-padding-top:calc(var(--barh) + 24px)}
  body{
    margin:0;background:var(--paper);color:var(--ink);
    font:400 16px/1.65 var(--text);
    -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  }
  img{display:block;max-width:100%}
  a{color:inherit}
  button{font:inherit;color:inherit}
  h1,h2,h3,h4,p,dl,dd,figure{margin:0}
  ::selection{background:var(--accent);color:#fff}
  :focus-visible{outline:2px solid var(--accent);outline-offset:3px}
  .wrap{width:min(100% - 2*var(--gut),var(--maxw));margin-inline:auto}
  .num{font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}
  .skip{
    position:fixed;left:16px;top:-60px;z-index:200;background:var(--ink);color:#fff;
    padding:10px 16px;font-size:14px;text-decoration:none;transition:top .16s;
  }
  .skip:focus{top:12px}

  /* ── 顶部导航（只在头图上，随页面滚走） ────────────── */
  .nav{
    position:absolute;top:0;left:0;right:0;z-index:40;height:68px;
    display:flex;align-items:center;gap:34px;color:#fff;
    padding:0 var(--gut);
    background:linear-gradient(180deg,rgba(8,8,10,.62),rgba(8,8,10,0));
  }
  .nav-mark{display:flex;align-items:center;gap:11px;min-height:40px;text-decoration:none;font:600 15px/1 var(--disp);letter-spacing:.06em}
  .nav-mark img{width:22px;height:22px}
  .nav-links{display:flex;gap:26px;margin-left:auto}
  .nav-links a{
    position:relative;text-decoration:none;font-size:14px;letter-spacing:.02em;
    color:rgba(255,255,255,.78);padding:6px 0;transition:color .16s;
  }
  .nav-links a::after{
    content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:#fff;
    transform:scaleX(0);transform-origin:left;transition:transform .24s cubic-bezier(.2,.7,.2,1);
  }
  .nav-links a:hover{color:#fff}
  .nav-links a:hover::after{transform:none}
  .nav-links button{
    position:relative;background:none;border:0;cursor:pointer;padding:6px 0;
    font:400 14px/1.4 var(--text);letter-spacing:.02em;color:rgba(255,255,255,.78);
    transition:color .16s;
  }
  .nav-links button::after{
    content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:#fff;
    transform:scaleX(0);transform-origin:left;transition:transform .24s cubic-bezier(.2,.7,.2,1);
  }
  .nav-links button:hover{color:#fff}
  .nav-links button:hover::after{transform:none}

  /* ── 头图 ───────────────────────────────────────────── */
  .hero{position:relative;min-height:100svh;display:flex;flex-direction:column;justify-content:flex-end;overflow:hidden;background:var(--dark)}
  .hero-bg{
    position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:9% 50%;
    filter:brightness(1.05) saturate(1.03);
    animation:heroIn 1.8s cubic-bezier(.2,.7,.2,1) both;
  }
  .hero-veil{
    position:absolute;inset:0;
    background:
      linear-gradient(90deg,rgba(9,9,11,.92) 0%,rgba(9,9,11,.84) 20%,rgba(9,9,11,.62) 34%,rgba(9,9,11,.2) 52%,rgba(9,9,11,0) 68%),
      linear-gradient(180deg,rgba(9,9,11,.5) 0%,rgba(9,9,11,0) 24%,rgba(9,9,11,.06) 66%,rgba(9,9,11,.62) 100%);
  }
  .hero-in{position:relative;z-index:2;color:#fff;padding:150px 0 clamp(40px,6vh,72px)}
  .kicker{
    display:flex;align-items:center;gap:10px;
    font:500 12px/1 var(--text);letter-spacing:.18em;color:rgba(255,255,255,.72);
    text-transform:uppercase;
  }
  .kicker::before{content:"";width:26px;height:2px;background:var(--accent)}
  .hero-logo{width:clamp(220px,29vw,340px);height:auto;margin-top:26px;filter:drop-shadow(0 10px 26px rgba(0,0,0,.45))}
  .hero h1{
    margin-top:26px;font:600 clamp(44px,5.6vw,72px)/1.02 var(--disp);
    letter-spacing:-.03em;font-stretch:94%;
  }
  .hero-lead{margin-top:14px;font-size:clamp(15px,1.15vw,17px);line-height:1.6;color:rgba(255,255,255,.82);max-width:24em;text-shadow:0 1px 16px rgba(0,0,0,.45)}
  .hero-acts{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}
  .facts{
    display:flex;flex-wrap:wrap;gap:0;margin-top:40px;
    border-top:1px solid rgba(255,255,255,.18);padding-top:18px;max-width:760px;
  }
  .facts>div{display:flex;flex-direction:column;gap:5px;padding:0 24px;border-left:1px solid rgba(255,255,255,.16)}
  .facts>div:first-child{padding-left:0;border-left:0}
  .facts dd{font:600 26px/1 var(--disp);letter-spacing:-.01em}
  .facts dt{font-size:12px;letter-spacing:.1em;color:rgba(255,255,255,.58)}
  .facts dt em{display:block;margin-top:3px;font-style:normal;font-size:10.5px;letter-spacing:.02em;color:rgba(255,255,255,.42)}
  /* 数据版本信息：比 facts 低一级，只做交代、不抢视觉 */
  .hero-build{
    display:flex;flex-wrap:wrap;gap:4px 22px;margin-top:16px;
    font:500 11.5px/1.5 var(--text);letter-spacing:.06em;color:rgba(255,255,255,.42);
  }
  .hero-build b{
    color:rgba(255,255,255,.72);font-weight:600;letter-spacing:.02em;
    font-variant-numeric:tabular-nums;
  }

  /* ── 按钮 ───────────────────────────────────────────── */
  .btn{
    display:inline-flex;align-items:center;gap:9px;height:46px;padding:0 22px;border-radius:var(--r);
    border:1px solid transparent;background:none;cursor:pointer;text-decoration:none;
    font:500 14.5px/1 var(--text);letter-spacing:.02em;
    transition:background .16s,color .16s,border-color .16s,transform .12s;
  }
  .btn:active{transform:translateY(1px)}
  .btn--solid{background:var(--accent);color:#fff}
  .btn--solid:hover{background:#c8124f}
  .btn--ghost{border-color:rgba(255,255,255,.34);color:#fff}
  .btn--ghost:hover{background:rgba(255,255,255,.1);border-color:#fff}
  .btn--ink{background:var(--ink);color:var(--paper)}
  .btn--ink:hover{opacity:.88}
  .btn--line{border-color:var(--rule);color:var(--ink-2)}
  .btn--line:hover{border-color:var(--ink);color:var(--ink)}
  .btn svg{width:15px;height:15px;flex:none}

  /* ── 工具条 ─────────────────────────────────────────── */
  .bar{
    position:sticky;top:0;z-index:50;background:var(--bar-bg);
    backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
    border-bottom:1px solid var(--rule);
  }
  .bar-in{
    display:flex;align-items:center;gap:10px;min-height:var(--barh);
    padding:10px 0;flex-wrap:wrap;
  }
  .bar-mark{display:flex;align-items:center;justify-content:center;text-decoration:none;flex:none;width:40px;height:40px}
  .bar-mark img{width:24px;height:24px}

  .find{position:relative;display:flex;align-items:center;flex:1 1 200px;max-width:300px}
  .find svg{position:absolute;left:12px;width:16px;height:16px;color:var(--steel);pointer-events:none}
  .find input{
    width:100%;height:42px;padding:0 40px 0 38px;border:1px solid var(--rule);border-radius:var(--r);
    background:var(--white);color:var(--ink);font:400 15px/1 var(--text);outline:none;
    transition:border-color .16s,box-shadow .16s;
  }
  .find input::placeholder{color:var(--steel-2)}
  .find input:focus{border-color:var(--ink);box-shadow:0 0 0 3px rgba(17,17,20,.06)}
  .find kbd{
    position:absolute;right:10px;font:500 11px/20px var(--mono);color:var(--steel-2);
    border:1px solid var(--rule);border-radius:2px;padding:0 5px;pointer-events:none;
  }

  .chips{display:flex;gap:4px;flex:none}
  .chip{
    height:34px;min-width:32px;padding:0 8px;border:1px solid transparent;border-radius:var(--r);
    background:none;cursor:pointer;color:var(--ink-2);
    font:600 12.5px/1 var(--disp);letter-spacing:.03em;
    transition:background .14s,color .14s,border-color .14s;
  }
  .chip:hover{background:var(--paper-2)}
  .chip.on{background:var(--ink);color:var(--paper)}
  .chip[data-cls]:not([data-cls=""]).on{background:var(--cc);color:var(--ct,#fff)}
  .chip:not(.on)::before{
    content:"";display:inline-block;width:6px;height:6px;border-radius:50%;
    background:var(--cc,transparent);margin-right:5px;vertical-align:1px;
  }
  .chip[data-cls=""]::before{display:none}

  /* 等级下拉：一个按钮 + 分组菜单（组别按等级配色） */
  .clsdd{position:relative}
  #clsBtn{display:inline-flex;align-items:center;gap:8px;min-width:120px;justify-content:space-between;
    height:34px;padding:0 12px;border:1px solid var(--rule);border-radius:var(--r);background:none;
    cursor:pointer;font:600 12.5px/1 var(--disp);letter-spacing:.03em;color:var(--ink)}
  #clsBtn::after{content:"";width:0;height:0;border:4px solid transparent;border-top-color:currentColor;
    margin-top:3px;opacity:.55}
  #clsBtn .dot{width:7px;height:7px;border-radius:50%;background:var(--cc,var(--steel));flex:none}
  #clsBtn.on{background:var(--cc,var(--ink));color:var(--ct,#fff);border-color:transparent}
  #clsBtn.on .dot{background:currentColor}
  .clsmenu{position:absolute;z-index:40;top:calc(100% + 6px);left:0;width:236px;max-height:340px;overflow:auto;
    background:var(--paper);border:1px solid var(--rule);border-radius:var(--r);
    box-shadow:0 14px 34px var(--shadow);padding:6px;display:none}
  .clsdd.open .clsmenu{display:block}
  .clsmenu .all{display:block;width:100%;text-align:left;padding:8px 10px;border:0;background:none;
    cursor:pointer;font:500 13px/1.2 var(--text);color:var(--ink-2);border-radius:3px}
  .clsmenu .all:hover{background:var(--paper-2)}
  .clsmenu .gh{display:flex;align-items:center;gap:8px;padding:9px 10px 5px;font:600 11px/1 var(--mono);
    letter-spacing:.1em;color:var(--steel-2)}
  .clsmenu .gh::after{content:"";flex:1;height:1px;background:var(--rule-soft)}
  .clsmenu .gi{display:flex;align-items:center;gap:8px;width:100%;padding:7px 10px;border:0;background:none;
    cursor:pointer;text-align:left;font:500 12.5px/1.2 var(--text);color:var(--ink-2);border-radius:3px}
  .clsmenu .gi:hover{background:var(--paper-2)}
  .clsmenu .gi .dot{width:7px;height:7px;border-radius:50%;background:var(--cc);flex:none}
  .clsmenu .gi.on{background:var(--cc);color:var(--ct,#fff)}
  .clsmenu .gi.on .dot{background:currentColor}
  .sel{position:relative;flex:none}
  select{
    appearance:none;-webkit-appearance:none;
    height:42px;padding:0 32px 0 12px;border:1px solid var(--rule);border-radius:var(--r);
    background:var(--white) url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' fill='none' stroke='%236b6b73' stroke-width='1.4'/></svg>") no-repeat right 11px center;
    color:var(--ink-2);font:400 14px/1 var(--text);cursor:pointer;outline:none;
    transition:border-color .16s;
  }
  select:hover{border-color:#bcbab2}
  /* 全局 :focus-visible 的 accent 描边会盖掉 select 的 outline:none，
     这里显式关掉，聚焦只靠边框加深标识，键盘用户照样看得出来 */
  select:focus-visible{outline:none;border-color:var(--ink)}
  .sel select{min-width:84px;font-size:13.5px}
  #fBrand,#fCtry,#fBk{max-width:118px}

  .views{display:flex;padding:3px;background:var(--paper-2);border-radius:var(--r);flex:none}
  .views button{
    display:flex;align-items:center;gap:6px;height:36px;padding:0 9px;border:0;border-radius:2px;
    background:none;cursor:pointer;color:var(--steel);font:500 13.5px/1 var(--text);
    transition:background .16s,color .16s;
  }
  .views button svg{width:14px;height:14px}
  .views button span{font-size:13px}
  .views button.on{background:var(--white);color:var(--ink);box-shadow:0 1px 2px rgba(17,17,20,.08)}
  .views button:disabled{opacity:.32;cursor:not-allowed}

  .lang{display:flex;padding:3px;background:var(--paper-2);border-radius:var(--r);flex:none}
  .lang button{
    height:30px;min-width:34px;padding:0 7px;border:0;border-radius:2px;background:none;cursor:pointer;
    font:600 12.5px/1 var(--disp);letter-spacing:.06em;color:var(--steel);
    transition:background .16s,color .16s;
  }
  .lang button.on{background:var(--ink);color:var(--paper)}
  /* 车名语言开关前的说明文字：只在宽屏出现，窄屏优先让位给控件 */
  .lang-lab{font-size:12.5px;color:var(--steel);letter-spacing:.02em;flex:none;white-space:nowrap}
  /* 简 / 繁 是两个独立网页之间的跳转，不是页内状态，所以用链接而不是 button，
     避免被 applyLang() 的 .lang button 逻辑误伤 */
  /* 与左侧「中 / EN」拉开一点距离并加一条细分隔线：两者是不同性质的切换
     （页内车名语言 vs 跨页简繁版本），不加线容易被读成四选一 */
  .doc-switch{display:flex;flex:none;position:relative;margin-left:6px;padding:3px;background:var(--paper-2);border-radius:var(--r)}
  .doc-switch::before{content:"";position:absolute;left:-11px;top:50%;transform:translateY(-50%);width:1px;height:18px;background:var(--rule)}
  .doc-switch>span,.doc-switch>a{
    display:grid;place-items:center;height:30px;min-width:34px;padding:0 7px;border-radius:2px;
    font:600 12.5px/1 var(--disp);letter-spacing:.06em;color:var(--steel);
    text-decoration:none;transition:background .16s,color .16s;
  }
  .doc-switch>a:hover{color:var(--ink)}
  .doc-switch>.on{background:var(--ink);color:var(--paper)}
  .doc-switch[hidden]{display:none}
  .icon-btn{
    width:42px;height:42px;display:grid;place-items:center;border:1px solid var(--rule);border-radius:var(--r);
    background:var(--white);color:var(--ink-2);cursor:pointer;flex:none;transition:border-color .16s,color .16s;
  }
  .icon-btn:hover{border-color:var(--ink);color:var(--ink)}
  .icon-btn svg{width:16px;height:16px}
  .icon-btn .moon{display:none}
  html[data-theme="dark"] .icon-btn .sun{display:none}
  html[data-theme="dark"] .icon-btn .moon{display:block}
  .tally{margin-left:auto;color:var(--steel);font-size:12.5px;letter-spacing:.01em;flex:none;white-space:nowrap}
  .tally b{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}

  .more{position:relative;flex:none}
  .more-btn{width:42px;height:42px;display:grid;place-items:center;border:1px solid var(--rule);border-radius:var(--r);background:var(--white);cursor:pointer;transition:border-color .16s}
  .more-btn:hover{border-color:var(--ink)}
  .more-btn svg{width:16px;height:16px}
  .menu{
    position:absolute;right:0;top:calc(100% + 8px);min-width:190px;padding:6px;
    background:var(--white);border:1px solid var(--rule);border-radius:var(--r);
    box-shadow:0 18px 40px rgba(17,17,20,.14);display:none;z-index:60;
  }
  .menu.on{display:block}
  .menu button{
    display:flex;width:100%;align-items:center;gap:10px;padding:10px 12px;border:0;background:none;
    text-align:left;font:400 14px/1.2 var(--text);cursor:pointer;border-radius:2px;
  }
  .menu button:hover{background:var(--paper-2)}
  .menu kbd{margin-left:auto;font:500 11px/1 var(--mono);color:var(--steel-2)}

  /* ── 车鉴 ───────────────────────────────────────────── */
  .cat{padding:44px 0 96px}
  .sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  .result{display:none;align-items:center;gap:12px;margin:0 0 26px;font-size:16px;color:var(--steel)}
  .result.on{display:flex}
  .result b{color:var(--ink);font-weight:600}
  /* 处在筛选状态时最显眼的逃生口：做成实心按钮，字号加粗放大 */
  .result button{
    margin-left:auto;flex:none;border:0;cursor:pointer;
    padding:11px 22px;border-radius:var(--r);
    background:var(--ink);color:var(--paper);
    font:700 15px/1 var(--text);letter-spacing:.03em;
    box-shadow:0 1px 0 rgba(0,0,0,.06);
    transition:opacity .15s ease,transform .15s ease;
  }
  .result button:hover{opacity:.85}
  .result button:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
  .result button:active{transform:translateY(1px)}

  .catbar{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:0 0 22px;margin:0 0 26px;border-bottom:1px solid var(--rule)}
  .catbar .lab{font:500 12px/1 var(--text);letter-spacing:.1em;color:var(--steel-2)}
  .seg{display:flex;padding:3px;background:var(--paper-2);border-radius:var(--r)}
  .seg button{
    height:32px;padding:0 14px;border:0;border-radius:2px;background:none;cursor:pointer;
    font:500 13px/1 var(--text);color:var(--steel);transition:background .16s,color .16s;
  }
  .seg button.on{background:var(--white);color:var(--ink);box-shadow:0 1px 2px var(--shadow)}
  .npctog{display:flex;align-items:center;gap:8px;margin-left:auto;font-size:13px;color:var(--steel);cursor:pointer}
  .npctog b{color:var(--ink);font-weight:600}
  .catbar .hintline{margin-left:auto;font-size:12.5px;color:var(--steel-2)}
  .catbar-sep{width:1px;height:22px;background:var(--rule);flex:none}
  .catbar .sel select{height:36px;min-width:0;max-width:140px;font-size:13px}
  .catbar .sel{flex:none}
  /* 驱动是一级、引擎位置是二级：紧贴一级、字号略收，形成从属关系 */
  .catbar .sel--sub{margin-left:-10px}
  .catbar .sel--sub select{max-width:132px;font-size:12.5px;color:var(--ink-2)}
  /* 两个开关作为一组推到右端：分组条放不下时整组一起换行，
     否则单个开关被顶到下一行会显得孤零零 */
  .catbar .toggrp{display:flex;align-items:center;gap:14px;margin-left:auto}
  .catbar .toggrp .npctog{margin-left:0}

  .brand{padding:0 0 88px;content-visibility:auto;contain-intrinsic-size:auto 760px}
  .brand.hide{display:none}
  .brand-h{display:flex;align-items:center;gap:18px;padding:0 0 6px;margin-bottom:18px}
  .make{position:relative;width:84px;height:49px;flex:none;display:grid;place-items:center}
  .make:empty{display:none}
  .make img{position:relative;z-index:1;width:100%;height:100%;object-fit:contain}
  .make img{position:relative;max-width:100%;max-height:100%;object-fit:contain}
  .brand-name{
    font:600 clamp(24px,2.3vw,32px)/1.1 var(--disp);letter-spacing:-.02em;font-stretch:96%;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;
  }
  .brand-name small{
    display:block;margin-top:5px;font:500 11.5px/1 var(--text);letter-spacing:.1em;
    color:var(--steel-2);text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  }
  .brand-name .cn{display:block}
  .brand-line{flex:1;height:1px;background:var(--rule);min-width:20px}
  .brand-n{
    flex:none;display:inline-flex;align-items:center;background:none;border:0;cursor:pointer;
    min-height:38px;padding:4px 0 4px 10px;
    font:500 13.5px/1 var(--text);color:var(--steel);letter-spacing:.02em;
    transition:color .16s;
  }
  .brand-n:hover{color:var(--accent)}
  .brand-n b{font:600 15px/1 var(--disp);color:var(--ink);margin-right:3px}
  .brand-n:hover b{color:var(--accent)}

  .cars{display:grid;grid-template-columns:repeat(auto-fill,minmax(258px,1fr));gap:38px 26px}
  .car{position:relative;display:flex;flex-direction:column}
  .car.hide{display:none}
  .car-link{display:block;text-decoration:none;color:inherit}
  .car-stage{
    position:relative;height:158px;display:grid;align-items:end;justify-items:center;
    padding:0 2px 8px;border-radius:var(--r);
    transition:background .2s;
  }
  .car-stage img{
    max-width:100%;max-height:100%;width:auto;height:auto;
    transition:transform .5s cubic-bezier(.2,.7,.2,1);transform-origin:50% 85%;
  }
  .car:hover .car-stage img,.car:focus-within .car-stage img{transform:translateY(-7px) scale(1.02)}
  .nav-auth{margin-left:4px;padding:5px 12px;border:1px solid var(--rule);border-radius:99px;
    background:none;cursor:pointer;font:500 13px/1 var(--text);color:var(--ink)}
  .nav-auth:hover{border-color:var(--ink)}
  .dact{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin:16px 0 0;
    padding:12px 0;border-top:1px solid var(--rule-soft);border-bottom:1px solid var(--rule-soft)}
  .dact .afav{display:inline-flex;align-items:center;gap:7px;padding:7px 14px;border:1px solid var(--rule);
    border-radius:99px;background:none;cursor:pointer;font:500 13.5px/1 var(--text);color:var(--ink-2)}
  .dact .afav[aria-pressed="true"]{border-color:var(--accent);color:var(--accent);background:var(--sel)}
  .dact .arate{display:inline-flex;align-items:center;gap:3px}
  .dact .arate button{width:26px;height:26px;border:0;background:none;cursor:pointer;font-size:17px;
    line-height:1;color:var(--rule);padding:0}
  .dact .arate button.on{color:#f5b301}
  .dact .astat{font-size:12.5px;color:var(--steel)}
  .dact .astat b{color:var(--ink);font-weight:600}
  .dact .alogin{font-size:12.5px;color:var(--steel);cursor:pointer;text-decoration:underline}
  #loginBox{position:fixed;inset:0;z-index:120;background:rgba(8,8,10,.55);display:grid;place-items:center;padding:24px}
  #loginBox .lb-card{width:min(420px,100%);background:var(--paper);color:var(--ink);border-radius:6px;
    padding:26px 26px 20px;box-shadow:0 24px 60px rgba(0,0,0,.35)}
  #loginBox h3{font:600 20px/1.25 var(--disp);margin:0 0 8px}
  #loginBox p{font-size:13px;color:var(--steel);margin:0 0 6px;line-height:1.6}
  #loginBox .row{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
  #loginBox input{flex:1;min-width:180px;padding:10px 12px;border:1px solid var(--rule);border-radius:var(--r);
    background:var(--paper);color:var(--ink);font:400 14px/1.2 var(--text)}
  #loginBox button{padding:10px 16px;border:0;border-radius:var(--r);background:var(--ink);color:var(--paper);
    font:500 13.5px/1 var(--text);cursor:pointer}
  #loginBox button.ghost{background:none;color:var(--steel);border:1px solid var(--rule)}
  #loginBox .lb-msg{min-height:18px;font-size:12.5px;color:var(--steel);margin-top:10px}
  #loginBox .lb-tabs{display:flex;gap:6px;margin:16px 0 4px}
  #loginBox .lb-tabs button{flex:1;background:none;color:var(--steel);border:1px solid var(--rule)}
  #loginBox .lb-tabs button.on{background:var(--ink);color:var(--paper);border-color:var(--ink)}
  .tuneform{margin-top:12px;display:grid;gap:8px}
  .tuneform .row{display:flex;gap:8px;flex-wrap:wrap}
  .tuneform input,.tuneform select{flex:1;min-width:150px;padding:8px 10px;border:1px solid var(--rule);
    border-radius:var(--r);background:var(--paper);color:var(--ink);font:400 13px/1.3 var(--text)}
  .tuneform button{padding:8px 16px;border:0;border-radius:var(--r);background:var(--ink);color:var(--paper);
    font:500 13px/1 var(--text);cursor:pointer}
  .tuneform .tunemsg{margin:0;font-size:12px;color:var(--steel);min-height:16px}
  .tunelist .ti-h{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .tunelist .ti-h code{font:600 12.5px/1 var(--mono);color:var(--ink);background:var(--paper-2);
    padding:3px 7px;border-radius:3px;letter-spacing:.06em}
  .tunelist .ti-h span{color:var(--steel-2)}
  .tunelist .ti p{margin:6px 0 0;color:var(--ink-2);font-size:12.5px;line-height:1.55}
  .lb-steam{display:block;text-align:center;width:100%;padding:10px 16px;border:1px solid var(--rule);
    border-radius:var(--r);color:var(--ink);text-decoration:none;font:500 13.5px/1 var(--text)}
  .lb-steam:hover{border-color:var(--ink)}
  .tunebox{margin-top:22px;padding-top:18px;border-top:1px solid var(--rule)}
  .tunebox .tune-title{margin:0 0 12px;font:600 21px/1.25 var(--disp);letter-spacing:.02em;color:var(--ink)}
  .tunebox summary{cursor:pointer;font:500 13px/1.4 var(--text);color:var(--ink-2)}
  .tunebox .row{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
  .tunebox input,.tunebox textarea{flex:1;min-width:180px;padding:8px 10px;border:1px solid var(--rule);
    border-radius:var(--r);background:var(--paper);color:var(--ink);font:400 13px/1.4 var(--text)}
  .tunebox button{padding:8px 14px;border:0;border-radius:var(--r);background:var(--ink);
    color:var(--paper);font:500 13px/1 var(--text);cursor:pointer}
  /* 分级下拉：直接用首页 .clsdd/.clsmenu 的皮肤，只调宽度 */
  .tunebox .tsel{flex:none;min-width:196px}
  .tunebox .tsel .chip{width:100%;justify-content:flex-start;font:500 13px/1 var(--text)}
  .tunebox .tsel .clsmenu{width:224px}
  /* 分享码点击复制 */
  .tune-code{cursor:pointer;transition:background .15s,color .15s}
  .tune-code:hover{background:var(--ink);color:var(--paper)}
  .tune-code.copied{background:var(--accent);color:#fff}
  .copytip{position:fixed;z-index:400;transform:translate(-50%,-100%);background:var(--ink);color:var(--paper);
    font:500 12px/1 var(--text);padding:6px 10px;border-radius:5px;pointer-events:none;
    box-shadow:0 6px 18px rgba(0,0,0,.18);animation:tipIn .16s ease-out}
  @keyframes tipIn{from{opacity:0;transform:translate(-50%,-88%)}to{opacity:1;transform:translate(-50%,-100%)}}
  .tunelist{margin-top:10px;display:grid;gap:8px}
  .tunelist .ti{border:1px solid var(--rule);border-radius:var(--r);padding:9px 12px;font-size:12.5px;color:var(--steel)}
  .tunelist .ti b{color:var(--ink);font-size:13.5px;font-weight:600}
  .gh-badge{display:block;height:64px;width:auto}
  .car-meta .tierb{margin-left:auto}
  .tierb{display:inline-flex;align-items:center;flex:0 0 auto}
  .tierb img{display:block;height:22px;width:43px;object-fit:contain}
  #tbl td.tier{text-align:left}
  #tbl th.tier,#tbl td.tier{white-space:nowrap}
  #tbl th.tt,#tbl td.tt{display:none}
  body.tiermode #tbl th.tt,body.tiermode #tbl td.tt{display:table-cell;white-space:nowrap}
  body.tiermode #tbl td.tt{font-size:12px;color:var(--ink-2)}
  #tbl .tcell{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;min-width:0;width:100%}
  #tbl th.tier,#tbl td.tier{text-align:center;vertical-align:middle}
  #tbl .tcell .tierb{flex:0 0 auto}
  #tbl .tcell .tierb img{height:21px;width:41px}
  #tbl .tcell i{display:block;font-style:normal;font-size:12.5px;line-height:1.2;font-weight:600;color:var(--ink-2);white-space:nowrap}
  .dtier{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 0}
  .dtier .dti{display:inline-flex;align-items:center;gap:9px;padding:7px 12px;border:1px solid var(--rule);border-radius:var(--r)}
  .dtier .dti img{height:26px;width:51px;object-fit:contain;display:block}
  .dtier .dti span{font-size:12.5px;color:var(--steel);line-height:1.35}
  .dtier .dti b{display:block;font-size:13.5px;color:var(--ink);font-weight:600}
  .car-meta{display:flex;align-items:center;gap:9px;margin-top:16px;font-size:12.5px;color:var(--steel);letter-spacing:.02em}
  /* 只作用于色牌本身：数据表里 <td class="cls"> 同名，若不限定会把整格涂成等级色 */
  span.cls{
    display:inline-grid;place-items:center;min-width:44px;height:30px;padding:0 8px;border-radius:3px;
    background:var(--cc,#6e6e76);color:var(--ct,#fff);font:700 13.5px/1 var(--disp);letter-spacing:.05em;
  }
  .plate{
    display:inline-flex;align-items:stretch;height:21px;flex:none;
    border:1px solid var(--cc);border-radius:2px;overflow:hidden;
    font:700 11.5px/1 var(--disp);letter-spacing:.04em;
  }
  .plate b{display:grid;place-items:center;min-width:21px;padding:0 4px;background:var(--cc);color:var(--ct)}
  .plate i{display:grid;place-items:center;padding:0 6px;background:#0b0b0e;color:#fff;font-style:normal;
    font-variant-numeric:tabular-nums;letter-spacing:.02em}
  .car-name{
    margin-top:7px;font:600 clamp(17px,1.32vw,19px)/1.28 var(--disp);letter-spacing:-.005em;color:var(--ink);
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
    min-height:2.56em;font-stretch:97%;
  }
  .car:hover .car-name{text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:4px}
  .car-nums{
    display:grid;grid-template-columns:1fr 1fr 1fr;margin-top:13px;padding-top:10px;
    border-top:1px solid var(--rule);transition:border-color .2s;
  }
  .car:hover .car-nums{border-top-color:var(--ink)}
  .car-nums>div{display:flex;flex-direction:column-reverse;gap:3px}
  .car-nums dt{font:500 11.5px/1 var(--text);letter-spacing:.08em;color:var(--steel-2)}
  .car-nums dd{font:600 19px/1.05 var(--disp);letter-spacing:-.01em;color:var(--ink)}
  .car-nums dd i{font-style:normal;font-size:11.5px;color:var(--steel);margin-left:2px;font-weight:400}
  .car-stage img{max-height:var(--mh,110px)}
  /* 赛季 / 通行证角标叠在缩略图左上角，不占位、不改变卡片高度 */
  .car-flags{position:absolute;left:2px;top:6px;z-index:2;display:flex;flex-direction:column;
    align-items:flex-start;gap:4px;pointer-events:none}
  .flag{display:inline-block;padding:3px 7px;border:1px solid var(--rule);border-radius:2px;
    font:600 10.5px/1.25 var(--text);letter-spacing:.02em;white-space:nowrap}
  .flag--cp{background:var(--accent);border-color:var(--accent);color:#fff}
  .flag--sea{background:var(--paper);color:var(--ink)}
  /* 宽体套件：实心深色，和 Carpass 的粉色实心区分开；暗色主题下自动反转为浅底深字 */
  .flag--wide{background:var(--ink);border-color:var(--ink);color:var(--paper)}

  .car-add{
    position:absolute;right:0;top:2px;width:30px;height:30px;display:grid;place-items:center;
    border:1px solid var(--rule);border-radius:var(--r);background:var(--paper);color:var(--ink-2);
    cursor:pointer;opacity:0;transition:opacity .16s,background .16s,color .16s,border-color .16s;
  }
  .car-add svg{width:14px;height:14px}
  .car:hover .car-add,.car-add:focus-visible,.car.on .car-add{opacity:1}
  .car-add:hover{border-color:var(--ink);color:var(--ink)}
  .car.on .car-add{background:var(--accent);border-color:var(--accent);color:#fff}
  .car.on .car-nums{border-top-color:var(--accent)}
  .car.on .car-name{text-decoration:underline;text-decoration-color:var(--accent);text-decoration-thickness:2px;text-underline-offset:4px}

  .empty{min-height:54vh;padding:120px 0;text-align:center;display:none}
  .empty.on{display:block}
  .empty h3{font:600 26px/1.2 var(--disp);letter-spacing:-.01em}
  .empty p{margin-top:10px;color:var(--steel)}
  .empty .btn{margin-top:22px}

  /* ── 数据表 ─────────────────────────────────────────── */
  .sheet{display:none;padding-bottom:20px}
  .sheet.on{display:block}
  .tbl-hint{display:flex;align-items:baseline;gap:8px;color:var(--steel);font-size:13.5px;margin:0 0 14px}
  .tbl-hint b{color:var(--ink);font-weight:600}
  table{width:100%;border-collapse:separate;border-spacing:0}
  /* 用自动布局：fixed 模式的列宽只认第一行（分组表头是 colspan），
     强度列会被压到 50px 导致组别文字截断 */
  #tbl{table-layout:auto;min-width:1700px}
  /* 列宽跟随内容，两侧各留半个中文字符（约 7px） */
  #tbl thead th.tier{width:1%}
  #tbl th.tier,#tbl td.tier{padding-left:7px;padding-right:7px}
  /* 驱动/配置列也按内容收窄，并居中（原来带 .l 是左对齐且被拉宽） */
  #tbl th.drv,#tbl td.drv{width:1%;white-space:nowrap;text-align:center;padding-left:7px;padding-right:7px}
  #tbl thead th.tt{width:1%}
  /* 多出 4 列后不能让 fixed 布局把每列压扁：撑开到可横向滚动 */
  body.tiermode #tbl{table-layout:auto;min-width:1720px}
  body.tiermode #tbl th.tt,body.tiermode #tbl td.tt{min-width:0;text-align:center;padding-left:7px;padding-right:7px}
  thead th{
    position:sticky;top:var(--barh);z-index:6;background:var(--paper);
    text-align:right;white-space:nowrap;
  }
  tr.grp th{
    top:var(--barh);height:30px;padding:0 8px;text-align:left;
    font:500 11.5px/1 var(--text);letter-spacing:.1em;color:var(--steel-2);
    border-bottom:1px solid var(--rule);
  }
  tr.cols th{
    top:calc(var(--barh) + 30px);height:48px;padding:0 8px 6px;cursor:pointer;user-select:none;vertical-align:bottom;
    font:500 12.5px/1 var(--text);color:var(--steel);border-bottom:1px solid var(--ink);
    transition:color .14s;
  }
  tr.cols th:hover{color:var(--ink)}
  tr.cols th.l{text-align:left}
  tr.cols th i{display:block;font-style:normal;color:var(--steel-2);font-size:10.5px;letter-spacing:.04em;margin-top:3px;font-weight:400}
  tr.cols th.on{color:var(--ink);font-weight:600}
  tr.cols th.on::after{content:"↓";font-size:10px;margin-left:5px;color:var(--accent)}
  tr.cols th.on.asc::after{content:"↑"}

  tbody td{
    height:56px;padding:0 8px;text-align:right;white-space:nowrap;
    border-bottom:1px solid var(--rule-soft);font-size:15px;color:var(--ink-2);
    font-variant-numeric:tabular-nums;
  }
  tbody td.l{text-align:left}
  tbody tr{cursor:pointer}
  tbody tr.hide{display:none}
  tbody tr:hover td{background:var(--paper-2)}
  tbody tr:hover .thumbcell img{transform:scale(1.06)}
  tbody tr.on td{background:var(--sel)}
  tbody tr.on td:first-child{box-shadow:inset 3px 0 0 var(--accent)}

  col.c-pick{width:46px} col.c-yr{width:56px} col.c-cls{width:52px}
  col.c-pi{width:70px} col.c-hp{width:66px} col.c-tq{width:62px} col.c-kg{width:66px}
  col.c-pwr{width:64px} col.c-t60{width:62px} col.c-tsm{width:64px} col.c-latg{width:58px}
  col.c-brk{width:54px} col.c-drv{width:54px} col.c-eng{width:150px}
  th.pick,td.pick{width:46px;padding:0 0 0 4px}
  .pick input{width:16px;height:16px}
  th.yr,td.yr{width:56px}
  th.nm,td.nm{text-align:left}
  th.cls,td.cls{width:52px}
  /* 数据表等级牌：只保留紧凑小色块，选中 / 未选中完全一致，并在格子里水平垂直居中 */
  #tbl td.cls{text-align:center;vertical-align:middle}
  #tbl td.cls span.cls{
    min-width:30px;width:30px;height:22px;padding:0;border-radius:4px;
    font:700 12px/1 var(--disp);letter-spacing:.02em;
  }
  #tbl tr.cols th[data-k="cls"]{text-align:center}
  th.pi,td.pi{width:70px}
  th.hp,td.hp{width:66px}
  th.tq,td.tq{width:62px}
  th.kg,td.kg{width:66px}
  th.pwr,td.pwr{width:64px}
  th.t60,td.t60{width:64px}
  th.tsm,td.tsm{width:70px}
  th.latg,td.latg{width:58px}
  th.brk,td.brk{width:54px}
  th.drv,td.drv{width:54px}
  th.eng,td.eng{width:auto}
  /* 车辆获取方式：主行是 Acquired via，Car Pass 车在下方补一行加入日期 */
  col.c-acq{width:136px}
  th.acq,td.acq{width:136px;text-align:left;white-space:nowrap}
  th.acq{font-size:12px}
  td.acq{color:var(--ink-2);font-size:12.5px;overflow:hidden;text-overflow:ellipsis}
  td.acq em.sub{display:block;margin-top:3px;font:500 10.5px/1.25 var(--text);font-style:normal;
    color:var(--steel);white-space:nowrap;letter-spacing:.01em}
  td.eng sup.guess,.dh-meta sup.guess{font-size:11px;color:var(--accent);margin-left:2px;cursor:help}

  .pick,.yr,.nm{position:sticky;background:var(--paper);z-index:3}
  td.pick{left:0}
  td.yr{left:46px}
  td.nm{left:102px;box-shadow:1px 0 0 var(--rule)}
  th.pick{left:0;z-index:8}
  th.yr{left:46px;z-index:8}
  th.nm{left:102px;z-index:8;text-align:left;box-shadow:1px 0 0 var(--rule)}
  tbody tr:hover .pick,tbody tr:hover .yr,tbody tr:hover .nm{background:var(--paper-2)}
  tbody tr.on .pick,tbody tr.on .yr,tbody tr.on .nm{background:var(--sel)}

  .thumbcell{display:flex;align-items:center;gap:13px}
  .thumbcell img{width:58px;height:34px;object-fit:contain;flex:none;transition:transform .3s}
  /* 两行车名：表格行高 56px 容得下 2×20px，长车名不用再被挤成省略号；
     仍保留 td.nm 的 title 作为超长名的兜底 */
  .nmtext{font:600 15.5px/1.3 var(--disp);letter-spacing:-.005em;color:var(--ink);
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
    overflow:hidden;white-space:normal;overflow-wrap:anywhere}
  td.hp,td.kg,td.t60,td.pi{font-weight:600;color:var(--ink)}
  td.pi{position:relative}
  td.pi b{font-weight:600}
  td.pi i{display:block;height:2px;width:38px;margin:4px 0 0 auto;background:var(--rule-soft)}
  td.pi i::after{content:"";display:block;height:100%;width:var(--v);background:var(--cc)}
  td.drv{color:var(--steel);font-size:13.5px}
  td.eng{color:var(--steel);font-size:13.5px;overflow:hidden;text-overflow:ellipsis;text-align:left}

  .chk{appearance:none;width:16px;height:16px;border:1px solid #bcbab2;border-radius:2px;background:var(--white);cursor:pointer;position:relative}
  .chk:checked{background:var(--accent);border-color:var(--accent)}
  .chk:checked::after{content:"";position:absolute;left:5px;top:1.5px;width:4px;height:8px;border:2px solid #fff;border-top:0;border-left:0;transform:rotate(40deg)}

  /* ── 底部 ───────────────────────────────────────────── */
  .foot{background:var(--dark);color:rgba(255,255,255,.64);padding:76px 0 44px;margin-top:40px;border-top:1px solid transparent}
  html[data-theme="dark"] .foot{border-top-color:var(--rule)}
  .foot-top{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr) minmax(0,1fr);gap:40px;padding-bottom:44px;border-bottom:1px solid rgba(255,255,255,.13)}
  .foot-brand{display:flex;align-items:center;gap:14px;color:#fff}
  .foot-brand img{width:34px;height:34px}
  .foot-brand strong{font:600 26px/1.1 var(--disp);letter-spacing:-.01em}
  .foot p{font-size:14px;line-height:1.7;margin-top:14px;max-width:34em}
  .foot h3{font:500 12px/1 var(--text);letter-spacing:.16em;color:rgba(255,255,255,.45);margin-bottom:16px}
  .foot ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:11px}
  .foot a,.foot button{color:rgba(255,255,255,.8);text-decoration:none;font-size:14.5px;background:none;border:0;padding:0;cursor:pointer;text-align:left}
  .foot a:hover,.foot button:hover{color:#fff;text-decoration:underline;text-underline-offset:4px}
  .foot-bot{display:flex;flex-wrap:wrap;gap:16px 32px;padding-top:22px;font-size:12.5px;line-height:1.7;color:rgba(255,255,255,.56)}
  .foot-bot span:last-child{margin-left:auto}

  /* ── 抽屉 ───────────────────────────────────────────── */
  .scrim{position:fixed;inset:0;background:rgba(11,11,14,.55);opacity:0;pointer-events:none;transition:opacity .26s;z-index:80}
  .scrim.on{opacity:1;pointer-events:auto}
  .drawer{
    position:fixed;top:0;right:0;bottom:0;width:min(920px,100%);z-index:90;
    background:var(--paper);display:flex;flex-direction:column;
    transform:translateX(100%);transition:transform .34s cubic-bezier(.22,.8,.2,1);
    box-shadow:-30px 0 80px rgba(11,11,14,.18);
  }
  .drawer.on{transform:none}
  .dh{padding:26px 34px 18px;border-bottom:1px solid var(--ink);position:relative;flex:none}
  .dh .cls{margin-bottom:12px}
  .dh h2{font:600 clamp(24px,2.4vw,34px)/1.12 var(--disp);letter-spacing:-.02em;padding-right:56px;font-stretch:96%}
  .dh-meta{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:12px;font-size:13.5px;color:var(--steel)}
  .dh-meta b{color:var(--ink);font-weight:600}
  .dh-meta i{font-style:normal;font-size:11px;color:var(--steel-2);margin-left:6px}
  .dadd{
    display:inline-flex;align-items:center;gap:7px;margin-top:14px;height:36px;padding:0 14px;
    border:1px solid var(--rule);border-radius:var(--r);background:var(--paper);cursor:pointer;
    font:500 13.5px/1 var(--text);color:var(--ink-2);transition:border-color .16s,background .16s,color .16s;
  }
  .dadd svg{width:13px;height:13px}
  .dadd:hover{border-color:var(--ink);color:var(--ink)}
  .dadd.on{background:var(--accent);border-color:var(--accent);color:#fff}
  .x{
    position:absolute;right:24px;top:26px;width:40px;height:40px;display:grid;place-items:center;
    border:1px solid var(--rule);border-radius:var(--r);background:var(--paper);cursor:pointer;
    transition:border-color .16s,background .16s;
  }
  .x:hover{border-color:var(--ink);background:var(--white)}
  .x svg{width:15px;height:15px}
  .dbody{overflow:auto;flex:1;padding:0 34px 80px;overscroll-behavior:contain}

  .dhero{height:300px;display:grid;place-items:center;background:transparent;border-radius:var(--r);margin-top:16px;padding:8px 20px}
  .dhero img{max-width:100%;max-height:var(--mh,300px);width:auto;height:auto;object-fit:contain}
  .dstats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));border:1px solid var(--rule);margin-top:18px;background:var(--white);border-radius:var(--r)}
  .dstats>div{padding:14px 14px 13px;border-left:1px solid var(--rule-soft)}
  .dstats>div:first-child{border-left:0}
  .dstats dt{font:500 11.5px/1 var(--text);letter-spacing:.1em;color:var(--steel-2)}
  .dstats dd{margin-top:6px;font:600 21px/1.05 var(--disp);letter-spacing:-.01em}
  .dstats dd span{font-size:11.5px;font-weight:400;color:var(--steel);margin-left:2px;letter-spacing:0}

  .dfind{position:relative;display:flex;align-items:center;margin-top:26px}
  .dfind svg{position:absolute;left:12px;width:15px;height:15px;color:var(--steel);pointer-events:none}
  .dfind input{
    width:100%;height:42px;padding:0 14px 0 36px;border:1px solid var(--rule);border-radius:var(--r);
    background:var(--white);font:400 14.5px/1 var(--text);outline:none;color:var(--ink);
  }
  .dfind input:focus{border-color:var(--ink)}

  .sec{margin-top:34px}
  .sec h3{
    display:flex;align-items:baseline;justify-content:space-between;gap:12px;
    padding-bottom:9px;border-bottom:1px solid var(--ink);
    font:600 17px/1.2 var(--disp);letter-spacing:.01em;
  }
  .sec h3 em{font:400 12.5px/1 var(--text);color:var(--steel);font-style:normal;letter-spacing:.02em}
  .grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:36px}
  .kv>span{min-width:0}
  .kv{display:flex;align-items:baseline;justify-content:space-between;gap:14px;padding:10px 0;border-bottom:1px solid var(--rule-soft);font-size:14.5px}
  .kv.hide{display:none}
  .kv span{color:var(--steel);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .kv b{font-weight:600;color:var(--ink);text-align:right;max-width:60%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-variant-numeric:tabular-nums}
  .kv b em{display:inline-block;font-style:normal;font-weight:400;font-size:11.5px;color:var(--steel);margin-left:6px;max-width:120px;overflow:hidden;text-overflow:ellipsis;vertical-align:baseline}
  .kv b i{font-style:normal;font-weight:400;color:var(--steel);font-size:12px;margin-left:6px}
  /* 关键标定值：数值加粗放大，在一堆原始参数里一眼能抓到 */
  .kv--key b{font-weight:800;font-size:15.5px}
  .kv--wide{grid-column:1/-1}
  /* 后轮转向：独立一块，带醒目标签 */
  .rsteer{margin-top:14px;padding:14px 16px;border:1px solid var(--rule);border-radius:var(--r);
    background:var(--paper-2);display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 24px}
  .rsteer>.rh{grid-column:1/-1;display:flex;align-items:center;gap:10px;margin-bottom:2px}
  .rsteer .tag{display:inline-block;padding:3px 8px;border-radius:2px;background:var(--accent);
    color:#fff;font:700 11px/1.2 var(--disp);letter-spacing:.06em}
  .rsteer>.rh em{font-style:normal;font-size:12.5px;color:var(--steel)}
  .rsteer .kv{padding:6px 0;border-bottom:0;font-size:13.5px}
  .rsteer .kv span{color:var(--steel)}
  .rsteer .kv b{font-weight:600;font-size:13.5px}
  .kv>span em{font:400 11px var(--mono);color:var(--steel-2);margin-left:8px;font-style:normal}

  .tirewrap{overflow-x:auto;margin-top:4px}
  .tire{min-width:0;font-size:13.5px}
  .tire th{position:static;background:none;padding:10px 8px;text-align:right;font:500 12px/1 var(--text);color:var(--steel);border-bottom:1px solid var(--rule);cursor:default}
  .tire th:first-child,.tire td:first-child{text-align:left}
  .tire td{height:auto;padding:11px 8px;text-align:right;border-bottom:1px solid var(--rule-soft);font-size:13.5px;color:var(--ink-2)}
  .tire td.wrap,.tire th.wrap{white-space:normal;overflow-wrap:anywhere;text-align:left;min-width:96px}
  .tire th.wrap{text-align:left}
  .tire tr[data-curve]{cursor:pointer}
  .tire tr[data-curve]:hover td{background:var(--white)}
  .tire .lv{font:600 14px/1 var(--disp);color:var(--ink)}
  .tire .stk{display:inline-block;margin-left:6px;padding:2px 5px;background:var(--paper-2);color:var(--steel);font-size:10.5px;border-radius:1px}
  .hint{margin-top:12px;font-size:13px;color:var(--steel)}
  .swp{table-layout:fixed}
  .swp th{text-align:right;padding-left:6px;padding-right:6px}
  .swp th:nth-child(1),.swp th:nth-child(2),.swp th:nth-child(3){text-align:left}
  .swp td{padding-left:6px;padding-right:6px}
  .swp td:first-child{text-align:left}
  .swp .lv{display:inline-grid;place-items:center;min-width:20px;height:18px;padding:0 4px;border-radius:2px;
    background:var(--paper-2);color:var(--steel);font:600 11px/1 var(--disp)}
  .swp tr.isstock .lv{background:var(--accent);color:#fff}
  .swp tr.isstock td{background:color-mix(in srgb, var(--accent) 6%, transparent)}
  /* 引擎的增压升级：挂在引擎名下方的小标签，CSC 用强调色突出 */
  .asp{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px}
  .asp i{font-style:normal;font-size:10px;line-height:1;padding:2px 4px;border-radius:2px;
    background:var(--paper-2);color:var(--steel);white-space:nowrap}
  /* 离心机增是最特殊的一条升级路径，详情里仍用强调色，其余保持中性 */
  .asp i.csc{background:var(--accent);color:#fff}
  .swp td.src{white-space:normal;overflow-wrap:anywhere;text-align:left;max-width:220px}
  .swp td.englink{cursor:pointer;text-decoration:underline;text-decoration-color:transparent;
    text-underline-offset:3px;text-decoration-thickness:1px;transition:text-decoration-color .15s}
  .swp tr:hover td.englink{text-decoration-color:var(--accent)}
  .only-m{display:none}
  @media (max-width:760px){.only-m{display:inline}}

  /* ── 弹层（字段说明 / 轮胎曲线） ─────────────────────── */
  .modal{position:fixed;inset:0;z-index:100;display:none;padding:40px 24px}
  .modal.on{display:block}
  .box{
    display:flex;flex-direction:column;max-width:1120px;margin:0 auto;background:var(--paper);
    border:1px solid var(--ink);border-radius:var(--r);max-height:calc(100vh - 80px);
    box-shadow:0 40px 100px rgba(11,11,14,.3);
  }
  .mh{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 24px;border-bottom:1px solid var(--ink);flex:none}
  .mh h2{font:600 20px/1.2 var(--disp);letter-spacing:-.01em}
  .mh .note{font-size:13px;color:var(--steel)}
  .mh .grow{flex:1}
  .mh input{
    height:38px;padding:0 12px;border:1px solid var(--rule);border-radius:var(--r);background:var(--white);
    font:400 14px/1 var(--text);outline:none;width:210px;color:var(--ink);
  }
  .mh input:focus{border-color:var(--ink)}
  .mb{overflow:auto;padding:0 24px 24px;flex:1}
  .mb table{min-width:0}
  .mb thead th{position:sticky;top:0;background:var(--paper);z-index:2;text-align:left;padding:12px 8px;border-bottom:1px solid var(--rule);font:500 12px/1 var(--text);letter-spacing:.08em;color:var(--steel);cursor:default}
  .mb tbody td{height:auto;padding:11px 8px;text-align:left;font-size:14px;line-height:1.55;white-space:normal;border-bottom:1px solid var(--rule-soft);color:var(--ink-2);vertical-align:top}
  .mb tbody tr:hover td{background:var(--paper-2)}
  .mb td.k{font-family:var(--mono);font-size:12.5px;color:var(--ink)}
  .mb td.cn{font-weight:600;color:var(--ink);white-space:nowrap}
  .mb td.t{font-size:12.5px;color:var(--steel);white-space:normal;overflow-wrap:anywhere}
  .mb td.t em{display:block;margin-top:2px;font-style:normal;font-size:11px;line-height:1.4;color:var(--steel-2)}

  /* 宽体套件表：单元格里主值是改装后的实测参数，下面一行小字是相对原厂的变化量 */
  .wbody th{white-space:nowrap}
  .wbody td{font-variant-numeric:tabular-nums}
  .wbody td em{display:block;margin-top:3px;font-style:normal;font-size:11px;line-height:1;color:var(--accent)}
  .wbody td i{display:block;margin-top:3px;font-style:normal;font-size:11px;line-height:1;color:var(--steel-2)}
  .wbody tr.stock td{color:var(--steel);background:var(--paper-2)}
  .wbody tr.stock .lv{color:var(--steel)}

  /* 详情页选项：折叠全库统一字段 + 空力套件表 */
  .duni{display:inline-flex;align-items:center;gap:8px;margin-top:12px;
    font:500 12.5px/1 var(--text);color:var(--steel);cursor:pointer;user-select:none}
  .duni b{font-weight:600;color:var(--ink-2)}
  .kv.off{display:none}
  .sec--empty{display:none}
  .ttune .tbadge{height:22px;width:43px;object-fit:contain;display:block}
  .ttune td{vertical-align:top}
  .ttune td.nt{white-space:normal;min-width:220px;color:var(--steel);font-size:12px;line-height:1.5}
  .awing th em{display:block;margin-top:3px;font-style:normal;font-size:10.5px;font-weight:400;
    color:var(--steel-2);letter-spacing:0}
  .awing td{white-space:nowrap}
  .awing td i{font-style:normal;color:var(--steel-2);margin-left:2px}
  .awing td em{display:block;margin-top:2px;font-style:normal;font-size:11px;color:var(--accent)}

  /* ── 网站说明（窄卡片，纯文本） ─────────────────────── */
  .about-box{max-width:660px}
  .about-body{padding:30px 32px 34px}
  .about-mark{display:flex;align-items:center;gap:10px;margin-bottom:22px}
  .about-mark img{width:30px;height:30px}
  .about-mark span{font:600 11.5px/1 var(--disp);letter-spacing:.16em;color:var(--steel)}
  .about-body h3{margin:0 0 14px;font:600 24px/1.3 var(--disp);letter-spacing:-.01em;color:var(--ink)}
  .about-body p{margin:0 0 12px;font-size:14.5px;line-height:1.85;color:var(--ink-2)}
  .about-body p:last-child{margin-bottom:0}
  .about-body .about-lead{margin-bottom:0;font-size:15px}
  /* 能力清单：左标签右说明，比一串段落更好扫读 */
  .about-list{margin:20px 0 0;border-top:1px solid var(--rule)}
  .about-list>div{
    display:grid;grid-template-columns:96px minmax(0,1fr);gap:14px;
    padding:12px 0;border-bottom:1px solid var(--rule-soft);
  }
  .about-list dt{font:600 12px/1.6 var(--text);letter-spacing:.08em;color:var(--steel)}
  .about-list dd{margin:0;font-size:14px;line-height:1.7;color:var(--ink-2)}
  .about-list dd b{font-weight:600;color:var(--ink)}
  .about-body .about-note{margin:18px 0 0;font-size:12.5px;line-height:1.8;color:var(--steel)}
  /* 作者与反馈：整块底纹 + 实心链接按钮，作为说明页的收尾 */
  .about-author{
    margin:22px 0 0;padding:18px 20px;border-radius:var(--r);
    background:var(--paper-2);border:1px solid var(--rule-soft);
  }
  .about-author p{margin:0 0 14px;font-size:13.5px;line-height:1.8;color:var(--ink-2)}
  .about-author p b{font-weight:600;color:var(--ink)}
  .about-author .about-link{
    display:inline-flex;align-items:center;gap:8px;
    padding:11px 20px;border-radius:var(--r);
    background:var(--ink);color:var(--paper);text-decoration:none;
    font:700 14.5px/1 var(--text);letter-spacing:.02em;
    transition:opacity .15s ease,transform .15s ease;
  }
  .about-author .about-link:hover{opacity:.85}
  .about-author .about-link:active{transform:translateY(1px)}
  .about-author .about-link i{font-style:normal;font-size:13px;opacity:.75}
  .about-author .about-link:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
  .mb td.k{white-space:normal;overflow-wrap:anywhere}

  /* ── 比对 ───────────────────────────────────────────── */
  .cmp{position:fixed;inset:0;z-index:110;background:var(--paper);display:none;flex-direction:column}
  .cmp.on{display:flex}
  .cmp-h{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:18px 34px;border-bottom:1px solid var(--ink);flex:none}
  .cmp-h h2{font:600 22px/1.2 var(--disp);letter-spacing:-.01em}
  .cmp-h p{font-size:13.5px;color:var(--steel)}
  .cmp-h .grow{flex:1}
  .cmp-h label{display:flex;align-items:center;gap:8px;font-size:13.5px;color:var(--ink-2);cursor:pointer}
  .cmp-b{overflow:auto;flex:1;padding:0 34px 60px}
  .cmp table{min-width:640px}
  .cmp thead th{position:sticky;top:0;z-index:4;background:var(--paper);text-align:left;padding:16px 14px 12px;border-bottom:1px solid var(--ink);cursor:default;vertical-align:bottom}
  .cmp thead th b{display:block;font:600 16px/1.25 var(--disp);color:var(--ink)}
  .cmp thead th em{display:block;margin-top:5px;font-style:normal;font-size:12px;color:var(--steel)}
  .cmp tbody td{height:auto;padding:10px 14px;text-align:right;font-size:14.5px;border-bottom:1px solid var(--rule-soft);color:var(--ink-2);vertical-align:top}
  .cmp tbody td.f{position:sticky;left:0;background:var(--paper);text-align:left;color:var(--ink);white-space:nowrap;box-shadow:1px 0 0 var(--rule)}
  .cmp tbody td.f em{font-style:normal;font-family:var(--mono);font-size:11px;color:var(--steel-2);margin-left:7px}
  .cmp tbody tr:hover td{background:var(--paper-2)}
  .cmp tbody tr:hover td.f{background:var(--white)}
  .cmp td.win{color:var(--ink);font-weight:600}
  .cmp td.win span{text-decoration:underline;text-decoration-color:var(--accent);text-decoration-thickness:2px;text-underline-offset:4px}
  .cmp td u{text-decoration:none;font-size:11px;color:var(--steel);margin-left:4px}
  .cmp tr.gth td{height:auto;background:var(--paper-2);text-align:left;padding:8px 14px;font:500 11.5px/1 var(--text);letter-spacing:.1em;color:var(--steel);border-bottom:1px solid var(--rule)}
  /* 比对表里新加的改装/底盘行：增压标签、补充说明都要跟着单元格对齐 */
  .cmp tbody td .asp{justify-content:flex-end;margin-top:0}
  .cmp tbody td i{font-style:normal;font-size:12px;color:var(--steel);margin-left:5px}
  .cmp tbody td span em{font-style:normal;font-size:12px;color:var(--steel);margin-left:3px}

  /* ── 选择条 ─────────────────────────────────────────── */
  .selbar{
    position:fixed;left:50%;bottom:24px;z-index:60;transform:translate(-50%,180%);
    display:flex;align-items:center;gap:18px;padding:12px 14px 12px 20px;
    background:var(--ink);color:#fff;border-radius:var(--r);box-shadow:0 20px 50px rgba(11,11,14,.3);
    transition:transform .3s cubic-bezier(.22,.8,.2,1);
  }
  .selbar.on{transform:translate(-50%,0)}
  .selbar span{font-size:14px}
  .selbar b{font:600 16px/1 var(--disp)}
  .selbar .go{height:38px;padding:0 18px;border:0;border-radius:2px;background:var(--accent);color:#fff;font:500 14px/1 var(--text);cursor:pointer}
  .selbar .go:hover{background:#c8124f}
  .selbar .go:disabled{opacity:.4;cursor:not-allowed}
  /* 次级动作：描边而非第二个实心主按钮，选择条里只留一个视觉重心 */
  .selbar .line{height:38px;padding:0 14px;border:1px solid rgba(255,255,255,.34);border-radius:2px;
    background:none;color:#fff;font:500 13.5px/1 var(--text);cursor:pointer;white-space:nowrap;
    transition:border-color .16s,background .16s}
  .selbar .line:hover{border-color:#fff;background:rgba(255,255,255,.09)}
  .selbar .line.done{border-color:#fff;background:rgba(255,255,255,.14)}
  .selbar .clear{background:none;border:0;color:rgba(255,255,255,.7);font-size:13.5px;cursor:pointer;text-decoration:underline;text-underline-offset:3px}
  .selbar .clear:hover{color:#fff}

  /* ── 动效 ───────────────────────────────────────────── */
  @keyframes heroIn{from{transform:scale(1.06);opacity:.35}to{transform:none;opacity:1}}
  @keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
  .hero-in>*{animation:rise .85s cubic-bezier(.2,.7,.2,1) both}
  .hero-in>*:nth-child(1){animation-delay:.1s}
  .hero-in>*:nth-child(2){animation-delay:.18s}
  .hero-in>*:nth-child(3){animation-delay:.26s}
  .hero-in>*:nth-child(4){animation-delay:.34s}
  .hero-in>*:nth-child(5){animation-delay:.42s}
  .hero-in>*:nth-child(6){animation-delay:.5s}
  .hero-in>*:nth-child(7){animation-delay:.58s}

  /* ── 窄屏 ───────────────────────────────────────────── */
  #tbl[data-tier="1"] .latg,#tbl[data-tier="1"] .brk,
  #tbl[data-tier="2"] .latg,#tbl[data-tier="2"] .brk,
  #tbl[data-tier="3"] .latg,#tbl[data-tier="3"] .brk{display:none}
  #tbl[data-tier="2"] .tq,#tbl[data-tier="2"] .kg,#tbl[data-tier="2"] .pwr,
  #tbl[data-tier="3"] .tq,#tbl[data-tier="3"] .kg,#tbl[data-tier="3"] .pwr{display:none}
  #tbl[data-tier="3"] .drv,#tbl[data-tier="3"] .eng{display:none}
  @media (max-width:1180px){
    .bar-in{gap:10px}
    .find{max-width:none;flex:1 1 200px}
    .tally{font-size:12.5px}
    .lang-lab{display:none}   /* 空间不够时先收掉说明文字，控件本身保留 */
  }
  /* 1380 起让等级筛选条独占一行：加了「车名显示 / 简繁」之后 1280、1366
     这类笔记本宽度会把最后两个按钮挤到第二行，反而是更难看的两行；
     整体换行后第一行是纯控件、第二行是等级条，结构更清楚。 */
  @media (max-width:1380px){
    .chips{order:9;width:100%;overflow-x:auto;padding-bottom:2px;scrollbar-width:none}
    .chips::-webkit-scrollbar{display:none}
    .bar-in{row-gap:8px}
  }
  @media (max-width:980px){
    .car-name{font-size:17px}
    .dstats{grid-template-columns:repeat(3,1fr)}
    .dstats>div:nth-child(4){border-left:0}
    .dstats>div:nth-child(-n+3){border-bottom:1px solid var(--rule-soft)}
  }
  @media (max-width:860px){
    .views{display:none}
    .sheet.on{display:none}
    .nav-links{display:none}
    .grid2{grid-template-columns:minmax(0,1fr)}
    .foot-top{grid-template-columns:1fr;gap:32px}
    .dh,.dbody{padding-left:20px;padding-right:20px}
    .dh h2{padding-right:48px}
    .x{right:16px;top:20px}
    .dhero{height:220px}
    .thumbcell img{display:none}
  }
  @media (max-width:760px){
    .hero{min-height:100svh;justify-content:flex-start}
    .result{flex-wrap:wrap;font-size:14.5px;gap:8px 12px}
    .result button{margin-left:0;width:100%;justify-content:center;text-align:center;padding:12px 18px;font-size:15px}
    .hero-bg{position:relative;inset:auto;height:44svh;object-position:46% 44%}
    .hero-veil{background:linear-gradient(180deg,rgba(9,9,11,.52) 0%,rgba(9,9,11,0) 30%)}
    .hero-in{
      background:var(--dark);flex:1;padding:20px var(--gut) 20px;max-width:none;
      display:flex;flex-direction:column;justify-content:flex-start;
    }
    .kicker{font-size:10.5px;letter-spacing:.14em}
    .hero-logo{margin-top:14px;width:168px}
    .hero h1{margin-top:14px;font-size:clamp(34px,9vw,40px)}
    .hero-lead{font-size:14px;line-height:1.55;margin-top:8px}
    .hero-acts{margin-top:14px}
    .hero-acts .btn{width:100%;justify-content:center;height:44px}
    .hero-acts .btn--ghost{display:none}
    /* 网站说明是声明入口，手机上也要留着；并排比对仍隐藏 */
    .hero-acts #heroAbout{display:inline-flex;width:auto;height:38px;padding:0 16px;margin-top:2px}
    .facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px 10px;margin-top:14px;padding-top:12px}
    .facts>div{padding:0;border:0;flex:none}
    .facts dd{font-size:21px}
    .facts dt{font-size:11px;letter-spacing:.06em}
    .hero-build{margin-top:7px;font-size:10px;line-height:1.4;gap:2px 14px;letter-spacing:.04em}
    .nav{height:58px}
    .nav-mark span{display:none}
    .bar-in{padding:9px 0;gap:8px}
    .bar-mark{display:none}
    .find{order:1;flex:1 1 auto;max-width:none}
    .more{order:2}
    .chips{order:3;flex:1 0 100%;width:100%;overflow-x:auto;padding:2px 0 3px;margin:0}
    .sel{order:4;flex:1 1 0}
    .sel select{width:100%;min-width:0}
    .views{display:none}
    .lang{order:5;padding:2px}
    .lang button{height:32px;min-width:30px;padding:0 5px;font-size:12px}
    .doc-switch{order:6;padding:2px}
    .doc-switch>span,.doc-switch>a{height:32px;min-width:28px;padding:0 5px;font-size:12px}
    .icon-btn{order:7;width:38px;height:38px}
    .sel select{height:38px}
    .tally{display:none}
    .find input{height:40px}
    .sel select{height:40px;padding-right:28px}
    .chips .chip{height:34px;min-width:36px}
    .cat{padding:24px 0 64px}
    .catbar{gap:10px;padding-bottom:14px;margin-bottom:18px}
    .catbar .lab{display:none}
    .seg button{height:30px;padding:0 10px;font-size:12.5px}
    .npctog{font-size:12px;gap:6px}
    .cars{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:26px 14px}
    .car-stage{height:104px;padding-bottom:4px}
    .car-meta{margin-top:11px;font-size:11.5px;gap:6px}
    .car-name{margin-top:6px;font-size:14.5px;line-height:1.3;min-height:2.6em}
    .car-nums{margin-top:9px;padding-top:8px}
    .car-nums dt{font-size:10px;letter-spacing:.04em}
    .car-nums dd{font-size:15px}
    .car-add{display:none}
    .brand-h{gap:12px;padding-bottom:16px;margin-bottom:18px}
    .make{width:34px;height:34px}
    .brand-name{font-size:22px}
    .brand-n{font-size:12px}
    .brand{padding-bottom:40px}
    .selbar{left:12px;right:12px;bottom:12px;transform:translateY(180%);gap:8px;padding:10px 12px}
    .selbar.on{transform:none}
    .selbar span,.selbar .clear{font-size:12.5px}
    .selbar .go{padding:0 12px;font-size:13px}
    .selbar .line{padding:0 10px;font-size:12.5px}
    .modal{padding:12px}
    .box{max-height:calc(100vh - 24px)}
    .about-body{padding:24px 20px 26px}
    .about-body h3{font-size:21px}
    .about-body p{font-size:14px;line-height:1.8}
    /* 小屏改成上下堆叠，别把说明挤在 220px 的窄列里 */
    .about-list>div{grid-template-columns:1fr;gap:3px;padding:11px 0}
    .about-body .about-note{font-size:12px}
    .about-author{padding:16px}
    .about-author .about-link{width:100%;justify-content:center;padding:12px 16px}
    .cmp-h,.cmp-b{padding-left:16px;padding-right:16px}
  }
  /* 矮屏手机（360×780 一类）：首屏再收一档，保证版本信息也落在一屏内 */
  @media (max-width:760px) and (max-height:820px){
    .hero-bg{height:39svh}
    .hero-in{padding:16px var(--gut) 14px}
    .hero-logo{margin-top:10px;width:150px}
    .hero h1{margin-top:10px}
    .hero-acts{margin-top:11px}
    .hero-acts .btn{height:40px}
    .facts{margin-top:10px;padding-top:10px;gap:9px 10px}
  }
  @media (min-width:761px) and (max-width:1080px){
    .hero-bg{object-position:26% 50%}
    .cars{grid-template-columns:repeat(auto-fill,minmax(222px,1fr));gap:32px 20px}
    .car-stage{height:140px}
    .car-name{font-size:16.5px}
  }
  @media (prefers-reduced-motion:reduce){
    *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important}
    .hero-in>*{animation:none;opacity:1}
  }
</style>
</head>
<body>

<a class="skip" href="#catalogue">跳到车辆清单</a>

<header class="hero" id="top">
  <img class="hero-bg" src="assets/img/hero.webp" alt="" width="2560" height="1066" fetchpriority="high" decoding="async">
  <div class="hero-veil" aria-hidden="true"></div>

  <nav class="nav" aria-label="主导航">
    <a class="nav-mark" href="#top"><img src="assets/img/mark.png" alt="" width="22" height="22">车辆索引</a>
    <div class="nav-links">
      <a href="#catalogue">车鉴</a>
      <a href="#catalogue" data-view="table">数据表</a>
      <button id="navCompare">并排比对</button>
      <button id="navGlossary">字段说明</button>
      <button id="navAuth" class="nav-auth" aria-haspopup="dialog">登录</button>
    </div>
  </nav>

  <div class="wrap hero-in">
    <p class="kicker">Forza Horizon 6 · 车辆数据库</p>
    <img class="hero-logo" src="assets/img/logo.webp" alt="Forza Horizon 6" width="760" height="185">
    <h1>车辆索引</h1>
    <p class="hero-lead">每一台车的数据都在这里</p>
    <div class="hero-acts">
      <a class="btn btn--solid" href="#catalogue">浏览全部车辆
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
      </a>
      <button class="btn btn--ghost" id="heroCompare">并排比对</button>
      <button class="btn btn--ghost" id="heroAbout">网站说明</button>
    </div>
    <dl class="facts" id="facts"></dl>
    <p class="hero-build" id="build"></p>
  </div>
</header>

<div class="bar" id="bar">
  <div class="wrap bar-in">
    <a class="bar-mark" href="#top" aria-label="回到顶部"><img src="assets/img/mark-ink.png" alt="" width="24" height="24"
      data-light="assets/img/mark-ink.png" data-dark="assets/img/mark.png"></a>

    <label class="find">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg>
      <input id="q" type="search" placeholder="搜车名、品牌、ID、引擎或功能" autocomplete="off" aria-label="搜索车辆">
      <kbd>/</kbd>
    </label>

    <div class="chips" id="chips" role="group" aria-label="按等级筛选"></div>

    <div class="views" role="group" aria-label="切换视图">
      <button data-view="gallery" class="on" aria-pressed="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
        <span>车鉴</span>
      </button>
      <button data-view="table" aria-pressed="false">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
        <span>数据表</span>
      </button>
    </div>

    <span class="lang-lab" id="langLab">车名显示</span>
    <div class="lang" role="group" aria-labelledby="langLab">
      <button data-lang="zh" class="on" aria-pressed="true">中</button>
      <button data-lang="en" aria-pressed="false">EN</button>
    </div>

    <!-- 简 / 繁是两个独立网页，这里只做跳转；当前页一侧用 span，避免参与页内语言切换 -->
    <div class="doc-switch" id="docSwitch" role="group" aria-label="简繁版本">__DOCSW__</div>

    <output class="tally num" id="count" aria-live="polite"></output>

    <button class="icon-btn" id="themeBtn" aria-label="切换深色配色" aria-pressed="false">
      <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4"/></svg>
      <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>
    </button>

    <div class="more">
      <button class="more-btn" id="moreBtn" aria-label="更多工具" aria-expanded="false">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="19" cy="12" r="1.4"/></svg>
      </button>
      <div class="menu" id="moreMenu">
        <button data-act="curves">轮胎曲线库<kbd>41</kbd></button>
        <button data-act="glossary">字段说明<kbd>199</kbd></button>
        <button data-act="compare">并排比对</button>
        <button data-act="about">网站说明</button>
      </div>
    </div>
  </div>
</div>

<main class="cat" id="catalogue">
  <div class="wrap">
    <h2 class="sr">全部车辆</h2>
    <div class="catbar">
      <span class="lab">分组</span>
      <div class="seg" id="groupBy" role="group" aria-label="车鉴分组方式">
        <button data-g="brand" class="on" aria-pressed="true">品牌</button>
        <button data-g="bucket" aria-pressed="false">类型</button>
        <button data-g="tier" aria-pressed="false">强度分级</button>
        <button data-g="acq" aria-pressed="false">获取</button>
      </div>
      <span class="catbar-sep"></span>
      <div class="sel"><select id="fBk" aria-label="按类型筛选"><option value="">全部类型</option></select></div>
      <div class="sel"><select id="fDrv" aria-label="按驱动筛选（一级）"><option value="">全部驱动</option></select></div>
      <div class="sel sel--sub"><select id="fPlace" aria-label="按引擎位置筛选（驱动二级）" title="驱动 → 引擎位置"><option value="">引擎位置</option></select></div>
      <div class="sel"><select id="fCtry" aria-label="按产地筛选"><option value="">全部产地</option></select></div>
      <div class="sel"><select id="fBrand" aria-label="按品牌筛选"><option value="">全部品牌</option></select></div>
      <div class="sel"><select id="fAcq" aria-label="按获取途径筛选"><option value="">全部获取</option></select></div>
      <div class="toggrp">
        <label class="npctog"><input type="checkbox" id="fWide" class="chk"> 仅宽体套件 <b id="wideN">0</b></label>
        <label class="npctog"><input type="checkbox" id="fFav" class="chk"> 只看收藏 <b id="favN">0</b></label>
        <label class="npctog"><input type="checkbox" id="showNpc" class="chk"> 显示 NPC / 街车 <b id="npcN">24</b></label>
      </div>
    </div>

    <div class="result" id="result"><span id="resultText"></span><button id="clearFilters">清空筛选</button></div>

    <div id="gallery"></div>
    <div class="empty" id="empty">
      <h3>没有匹配的车辆</h3>
      <p>换个关键词，或把这些筛选条件清掉。</p>
      <button class="btn btn--ink" id="emptyClear">清空筛选</button>
    </div>

    <section class="sheet" id="sheet" aria-label="车辆数据表">
      <p class="tbl-hint">点表头排序，点一行展开全部 <b>151</b> 项字段；悬浮车名可看全称。金额单位为游戏内 CR。引擎带 <sup>*</sup> 的名称由 EngineConfigID / AspirationTypeId / Displacement 推断。</p>
      <table id="tbl">
        <colgroup></colgroup>
        <thead>
          <tr class="grp">
            <th colspan="3" data-cols="pick,yr,nm">车辆</th>
            <th colspan="7" data-cols="tier,cls,pi,hp,tq,kg,pwr">动力与分级</th>
            <th colspan="4" data-cols="t60,tsm,latg,brk">性能</th>
            <th colspan="2" data-cols="drv,eng">配置</th>
            <th colspan="4" class="tt" data-cols="tdrv,tdiff,ttire,trole">Meta 改装后数据</th>
            <th colspan="1" data-cols="acq">获取方式</th>
          </tr>
          <tr class="cols">
            <th class="pick"></th>
            <th class="yr l" data-k="year">年份</th>
            <th class="nm l" data-k="name">车名</th>
            <th class="tier" data-k="tier">强度分级</th>
            <th data-k="cls">等级</th>
            <th data-k="pi">PI</th>
            <th class="hp" data-k="hp">马力<i>hp</i></th>
            <th class="tq" data-k="nm">扭矩<i>N·m</i></th>
            <th class="kg" data-k="kg">车重<i>kg</i></th>
            <th class="pwr" data-k="pwr">推重比<i>hp/t</i></th>
            <th class="t60" data-k="t60">0–60<i>s</i></th>
            <th class="tsm" data-k="tsm">极速<i>km/h</i></th>
            <th class="latg" data-k="latg">横向 G<i>g</i></th>
            <th class="brk" data-k="brk">刹车<i>m</i></th>
            <th class="drv l" data-k="drv">驱动</th>
            <th class="l eng" data-k="eng">引擎</th>
            <th class="tt" data-k="tdrv">驱动<i>Meta</i></th>
            <th class="tt" data-k="tdiff">难度</th>
            <th class="tt" data-k="ttire">轮胎</th>
            <th class="tt" data-k="trole">定位</th>
            <th class="l acq" data-k="acq">车辆获取方式</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </section>
  </div>
</main>

<footer class="foot">
  <div class="wrap">
    <div class="foot-top">
      <div>
        <div class="foot-brand"><img src="assets/img/mark.png" alt="" width="34" height="34"><strong>车辆索引</strong></div>
        <p>Forza Horizon 6 全车辆数据库。数据取自游戏本体数据表，性能项为游戏内模拟值，不含改装后的结果。</p>
      </div>
      <div>
        <h3>浏览</h3>
        <ul>
          <li><a href="#catalogue">全部车辆</a></li>
          <li><button data-act="glossary">字段说明</button></li>
          <li><button data-act="curves">轮胎曲线库</button></li>
          <li><button data-act="compare">并排比对</button></li>
          <li><button data-act="about">网站说明</button></li>
          <li><a href="feedback.html">问题反馈</a></li>
        </ul>
      </div>
      <div>
        <h3>单位</h3>
        <ul>
          <li>马力 hp · 扭矩 N·m</li>
          <li>车重 kg · 推重比 hp/t</li>
          <li>0–60 mph 秒 · 极速 km/h</li>
          <li>刹车 100–0 mph 米 · 价格 CR</li>
        </ul>
      </div>
    </div>
    <div class="foot-bot">
      <span>来源：FH6 gamedbRC 车辆主表 + 引擎 / 车身 / 轮胎 / 改装子表</span>
      <span>头图与车辆渲染图来自游戏内素材，版权归 Microsoft / Playground Games 所有</span>
    </div>
  </div>
</footer>

<div class="selbar" id="selbar">
  <span>已选 <b id="selN">0</b> 台</span>
  <button class="line" id="btnCopy" title="按「年份 + 车名」复制所选车辆，每台一行">复制车名</button>
  <button class="go" id="btnCompare" disabled>并排比对</button>
  <button class="clear" id="btnClear">清空</button>
</div>

<div class="scrim" id="scrim"></div>

<aside class="drawer" id="drawer" aria-label="车辆详情" aria-hidden="true">
  <div class="dh">
    <button class="x" id="btnClose" aria-label="关闭详情">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
    <span class="cls" id="dCls"></span>
    <h2 id="dTitle"></h2>
    <p class="dh-meta" id="dMeta"></p>
    <button class="dadd" id="dAdd" aria-pressed="false">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
      <span>加入比对</span>
    </button>
  </div>
  <div class="dbody" id="dBody"></div>
</aside>

<div class="modal" id="glossary" role="dialog" aria-modal="true" aria-label="字段说明">
  <div class="box">
    <div class="mh">
      <h2>字段说明</h2><span class="note" id="gCount"></span>
      <div class="grow"></div>
      <input id="gq" type="search" placeholder="搜索字段或说明" aria-label="搜索字段">
      <button class="btn btn--line" id="btnGClose">关闭</button>
    </div>
    <div class="mb">
      <table>
        <thead><tr><th style="width:92px">表</th><th style="width:208px">字段</th><th style="width:132px">中文名</th><th style="width:96px">单位</th><th>说明</th></tr></thead>
        <tbody id="gBody"></tbody>
      </table>
    </div>
  </div>
</div>

<div class="modal" id="curves" role="dialog" aria-modal="true" aria-label="轮胎曲线">
  <div class="box">
    <div class="mh">
      <h2>轮胎曲线</h2>
      <select id="cmpSel" aria-label="选择轮胎配方" style="min-width:260px"></select>
      <span class="note">92 项物理参数</span>
      <div class="grow"></div>
      <button class="btn btn--line" id="btnCClose">关闭</button>
    </div>
    <div class="mb">
      <div id="cBody" style="padding-top:8px"></div>
    </div>
  </div>
</div>

<div class="modal" id="about" role="dialog" aria-modal="true" aria-label="网站说明">
  <div class="box about-box">
    <div class="mh">
      <h2>网站说明</h2>
      <div class="grow"></div>
      <button class="btn btn--line" id="btnAboutClose">关闭</button>
    </div>
    <div class="mb about-body">
      <div class="about-mark">
        <img src="assets/img/mark-ink.png" alt="" width="30" height="30"
          data-light="assets/img/mark-ink.png" data-dark="assets/img/mark.png">
        <span>FAN-MADE · 非官方</span>
      </div>
      <h3>关于本站</h3>
      <p class="about-lead">这是一个由粉丝制作的《Forza Horizon 6》社区数据库网站，旨在帮助玩家探索游戏中的车辆、替换引擎与轮胎数据。</p>
      <dl class="about-list">
        <div><dt>完整数据</dt><dd>每台车 <b>151 项</b>底层字段，可同时勾选最多 4 台并排比对，差异一目了然。</dd></div>
        <div><dt>获取方式</dt><dd>标注每台车是<b>车展、季节赛、车辆通行证、车房宝物</b>还是幸运转盘获得；Car Pass 车辆额外标出具体<b>上线日期</b>。</dd></div>
        <div><dt>引擎增压</dt><dd>「可选改装引擎」逐条标出该引擎支持的增压升级（单/双/四涡轮、<b>离心机增</b>、<b>正排量机增</b>）与档位；点任意引擎可反查所有能装它的车型。</dd></div>
        <div><dt>悬挂转向</dt><dd>前后悬挂结构含英文原名与中文对照、转向手感配置、最大前轮转角；支持<b>后轮转向</b>的车型单独列出转角比例与介入车速。</dd></div>
        <div><dt>驾驶模式</dt><dd>列出支持<b>主动驾驶模式</b>切换的车型，以及切换时改变的离地高度、弹簧刚度、牵引力控制与驱动形式。</dd></div>
        <div><dt>宽体胎宽</dt><dd>宽体套件的价格与<b>实际加宽量</b>，并给出改装前后可用的最大前、后轮胎宽。</dd></div>
        <div><dt>轮胎配方</dt><dd>详情页列出该车可选的全部 41 种配方档位，点开可看 92 项曲线参数。</dd></div>
        <div><dt>功能搜索</dt><dd>搜索框直接输入<b>「宽体套件」「离心机增」「后轮转向」「主动驾驶模式」</b>等关键字，即可筛出具备该功能的全部车辆。</dd></div>
        <div><dt>筛选分组</dt><dd>按品牌、车辆类型、驱动形式、引擎位置、产地、获取途径筛选，车鉴支持按品牌 / 类型 / 上线日期 / 获取方式分组。</dd></div>
        <div><dt>语言主题</dt><dd>简体 / 繁体两套页面 × 明暗两套配色，车名与品牌名可随时切换中英显示。</dd></div>
      </dl>
      <p class="about-note">车辆数据与车辆渲染图来自游戏内原始素材，版权归 Microsoft / Playground Games 所有。</p>
      <p class="about-note">车辆线上强度评级数据来自社区玩家总结的
        <a href="https://docs.qq.com/sheet/DYWZVRWR0dnh3aHhZ" target="_blank" rel="noopener noreferrer">《地平线6线上车辆调校推荐》</a>
        表格，感谢原表作者 Noa Miyako 及所有参与整理的调校师。分级仅代表线上强度参考，随版本与调校更新会变化。</p>
      <div class="about-author">
        <p>本站由 <b>STWU</b> 独立制作与维护，数据与功能仍在持续更新。发现数据错误、想补充车型，或有任何使用问题与建议，欢迎到 B 站主页留言反馈。</p>
        <a class="about-link" href="https://space.bilibili.com/883100" target="_blank" rel="noopener noreferrer">关注 STWU 的 B 站主页<i aria-hidden="true">↗</i></a>
      </div>
    </div>
  </div>
</div>

<div class="cmp" id="cmp" aria-label="并排比对">
  <div class="cmp-h">
    <h2>并排比对</h2>
    <p id="cmpInfo"></p>
    <div class="grow"></div>
    <button class="btn btn--ink" id="btnCmpClose">退出比对</button>
  </div>
  <div class="cmp-b"><table id="cmpTbl"><thead></thead><tbody></tbody></table></div>
</div>

<script>
"use strict";
const DATA = __DATA__;
const DEFAULT_LANG = "__LANG__", DEFAULT_THEME = "__THEME__";
const COLS = DATA.cols, ROWS = DATA.rows, FULL = DATA.full, FROWS = DATA.fullRows, GROUPS = DATA.groups;
const FI = {}; FULL.forEach((f, i) => FI[f.n] = i);
/* 全库 691 台取值完全相同的字段（25 个）：详情页默认折叠 */
const UNIFORM = new Set(DATA.uniform || []);

/* 强度分级（来自调校推荐表）：tier[cid] = [[强度序号, 组别序号], ...]，首个是主标签 */
const TIER = DATA.tier || {};
const TIER_NAMES = DATA.tierNames || [];
const TIER_GROUPS = DATA.tierGroups || [];
const TIER_IMG = ["meta-plus", "meta", "t0-5", "t1", "t1-5", "t2", "t3", "unknown"];
const tierOf = c => { const t = TIER[String(c.id)]; return t && t.length ? t[0][0] : 99; };
const tierGroupOf = c => { const t = TIER[String(c.id)]; return t && t.length ? TIER_GROUPS[t[0][1]] || "" : ""; };
const tierName = c => (tierOf(c) < 99 ? TIER_NAMES[tierOf(c)] : "未分级");
const tierImg = c => (tierOf(c) < 99 ? `assets/tier/${TIER_IMG[tierOf(c)]}.png` : "");
/* 漂移分级：只有 S–D 五档，徽章是另一套图 */
const DRIFT_IMG = { S: "s", A: "a", B: "b", C: "c", D: "d" };
const DRIFT_TIERS = ["S", "A", "B", "C", "D"];
/* 车卡红框位置的小徽章 */
const tierBadge = c => (tierOf(c) < 99
  ? `<span class="tierb" title="${esc(tierTip(c))}"><img src="assets/tier/${TIER_IMG[tierOf(c)]}.png" alt="${esc(tierName(c))}" loading="lazy"></span>`
  : "");
/* 徽章悬浮说明：强度 + 组别 + 原表备注 */
function tierTip(c) {
  const n = (DATA.tierRows || {})[String(c.id)];
  const note = n && n.length && n[0][6] ? `｜${n[0][6]}` : "";
  return `竞速强度 ${tierName(c)} · ${tierGroupOf(c) || "未分组"}${note}`;
}
const cars = ROWS.map(r => { const o = {}; COLS.forEach((k, i) => o[k] = r[i]); return o; });
const byId = new Map();
cars.forEach((c, i) => { c._i = i; byId.set(c.id, c); });

/* 等级配色取自游戏内徽章：色块 + 白色/深色字按对比度取 */
const CLASS = {
  D:  ["#41bdf3", "#0b0b0e"],
  C:  ["#ffc533", "#0b0b0e"],
  B:  ["#fe632d", "#0b0b0e"],
  A:  ["#ff1a45", "#0b0b0e"],
  S1: ["#b860e8", "#0b0b0e"],
  S2: ["#175edc", "#ffffff"],
  R:  ["#d51a9b", "#ffffff"],
  X:  ["#19d857", "#0b0b0e"],
};
const ccOf = c => (CLASS[c] || ["#6e6e76", "#ffffff"])[0];
const ctOf = c => (CLASS[c] || ["#6e6e76", "#ffffff"])[1];
const nf = n => (n === null || n === undefined || n === "") ? "—" : (typeof n === "number" ? n.toLocaleString("en-US") : n);
const esc = s => String(s ?? "").replace(/[<>&"]/g, m => ({"<":"&lt;",">":"&gt;","&":"&amp;","\"":"&quot;"}[m]));
const $ = id => document.getElementById(id);

/* ── 品牌分组 ─────────────────────────────────────── */
const brandMap = new Map();
cars.forEach(c => {
  if (!brandMap.has(c.mkid)) brandMap.set(c.mkid, {id: c.mkid, code: c.code || "", logo: c.logo || "", zh: c.brand || "其他", en: c.brand_en || c.brand || "Other", list: []});
  brandMap.get(c.mkid).list.push(c);
});
const brands = [...brandMap.values()];

const S = {q: "", cls: "", tgrp: "", drift: "", drv: "", place: "", brand: "", ctry: "", bk: "", acq: "", eng: "", engName: "", sort: "pi", desc: true, view: "gallery", sel: new Set(), lang: "zh", group: "brand", npc: false, wide: false, fav: false};

/* 分级（含后台覆盖）取值，供筛选与车鉴分组共用 */
const effRace = c => {
  const o = OVR[String(c.id)], t = TIER[String(c.id)];
  return {
    tier: (o && o.race_tier) || (t ? TIER_NAMES[t[0][0]] : ""),
    group: (o && o.race_group) || (t ? TIER_GROUPS[t[0][1]] : ""),
  };
};
const effDrift = c => (OVR[String(c.id)] || {}).drift_tier || "";

/* 每台车可用（原厂 + 可换装）的引擎集合，点引擎时用来筛车 */
const ENG_BY_CAR = new Map();
Object.entries(DATA.swaps || {}).forEach(([cid, rows]) => {
  ENG_BY_CAR.set(+cid, new Set(rows.map(r => String(r[8]))));
});
const CTRIES = DATA.countries || [];

const BUCKETS = DATA.buckets || [];
const BK = {}; BUCKETS.forEach(b => BK[b.id] = b);
const SWAPS = DATA.swaps || {};
const PLAYABLE = () => cars.filter(c => !c.npc).length;
const bkName = b => S.lang === "en" ? (b.en || b.zh) : b.zh;

/* ── 驱动 / 引擎位置（驱动是一级、引擎位置是二级） ───── */
/* 语言包里 FWD 没翻译、RWD 译作「后轮驱动」，不统一，这里自己定一套 */
const DRIVE_LABEL = {FWD: "前驱", RWD: "后驱", AWD: "四驱"};
const PLACE_LABEL = {1: "前置引擎", 2: "中置引擎", 3: "后置引擎"};
/* 分组条里的下拉一律中文（全部类型 / 全部驱动 / 全部产地…），位置也保持一致，
   否则会出现「引擎位置 + Front/Mid/Rear」这种混排 */
const placeCode = n => PLACE_LABEL[n] || n;

/* ── 获取途径：赛季备注 / Carpass车辆 ───────────────── */
/* Excel 与官方 forza.net 两套叫法都在用，这里一起收：后者多了 Seasonal /
   Collection Journal / Autoshow DLC / Treasure / Loyalty 等。 */
const ACQ_MAP = {
  Autoshow: "车展", "Autoshow DLC": "车展 DLC", Wheelspin: "幸运转盘",
  Seasonal: "季节赛", "Horizon Festival": "季节赛",
  "Collection Journal": "收藏日志", "Discover Japan": "探索日本",
  "Barn Find": "车房宝物", "Treasure Car": "宝藏车", Treasure: "宝藏车",
  "Car Pass": "车辆通行证", "Car Mastery": "车辆精通",
  "VIP Membership": "VIP 会员", VIP: "VIP 会员",
  "Welcome Pack": "欢迎包", "Pre-Order Bonus": "预购奖励", "Preorder Bonus": "预购奖励",
  Aftermarket: "改装车", "Promo DLC": "推广 DLC", Loyalty: "系列忠诚奖励",
  "Partnership DLC": "合作 DLC", "Series History": "季节赛历史奖励",
  "Time Attack Car Pack": "计时赛车辆包",
  "Italian Passion Car Pack": "意大利激情车辆包",
};
/* 官方已把这档改称 Seasonal，英文显示跟着改，中文两套都落到「季节赛」 */
const ACQ_EN_MAP = {"Horizon Festival": "Seasonal"};
/* 获取方式：多个赛季合并成「第 1/4/7 赛季」，其余途径逐段翻译；
   EN 模式给原文（旧称换成官方新称）。未收录的车给「—」，不伪装成某种获取方式。 */
const acqText = c => {
  const raw = String(c.acq || "").trim();
  /* 街车 / NPC 剧情车在官方列表里也没有获取途径，明确写「不可获取」而不是留空 */
  if (!raw) return c.npc ? "不可获取" : "—";
  if (S.lang === "en") return raw.split(/\s*\/\s*/).map(x => ACQ_EN_MAP[x] || x).join(" / ");
  const sea = [], other = [];
  raw.split(/\s*\/\s*/).forEach(x => {
    const m = /^Series (\d+)$/.exec(x);
    if (m) sea.push(m[1]); else other.push(ACQ_MAP[x] || x);
  });
  if (sea.length) other.push(`第 ${sea.join("/")} 赛季`);
  return other.join(" / ");
};
const seasonList = c => (c.sea || []).slice().sort((a, b) => a - b);
const seasonLabel = c => {
  const s = seasonList(c);
  return s.length ? (S.lang === "en" ? `Series ${s.join("/")}` : `第 ${s.join("/")} 赛季`) : "";
};
const seasonNote = c => {
  const l = seasonLabel(c);
  return l ? (S.lang === "en" ? `Added in ${l}` : `${l}加入`) : "";
};
const engGuessTip = "原厂引擎名在数据库中缺失，由 EngineConfigID / AspirationTypeId / Displacement 推断";

const LANG_KEY = "fh6.lang", THEME_KEY = "fh6.theme";
/* 繁体版整页是 zh-Hant，切到「中」时别把它写回 zh-CN */
const DOC_HANT = /^zh[-_]hant/i.test(document.documentElement.lang || "");
const COLL = () => S.lang === "zh" ? "zh-Hans-CN" : "en";
const nm = c => S.lang === "zh" ? c.name : c.name_en;
const bn = b => S.lang === "zh" ? b.zh : b.en;
const brandCmp = (a, b) => bn(a).localeCompare(bn(b), COLL(), {numeric: true});
/* 「#55 Mazda 787B」这类涂装车名排序时去掉 #编号，按 Mazda 参与比较 */
const sortName = c => nm(c).replace(/^#\s*\d+\s*/, "");
const carCmp = (a, b) => sortName(a).localeCompare(sortName(b), COLL(), {numeric: true})
  || nm(a).localeCompare(nm(b), COLL());

function sortBrands() {
  brands.sort(brandCmp);
  brands.forEach(b => b.list.sort(carCmp));
}
sortBrands();

/* ── 头图统计 ─────────────────────────────────────── */
$("facts").innerHTML = [
  ["可驾驶车辆", DATA.meta.total - (DATA.meta.npc || 0)], ["品牌", DATA.meta.brands],
  ["每车字段", DATA.meta.fields],
  ["改装引擎", DATA.meta.swapEngines, `原厂 ${DATA.meta.stockEngines} 台`,
    `引擎库 ${DATA.meta.engineTotal} 台 · 置换组合 ${DATA.meta.swapCombos} 条 · 原厂引擎 ${DATA.meta.stockEngines} 台`],
  ["轮胎配方", DATA.meta.compounds]
].map(([k, v, sub, tip]) =>
  `<div${tip ? ` title="${tip}"` : ""}><dd class="num">${v}</dd><dt>${k}${sub ? `<em>${sub}</em>` : ""}</dt></div>`
).join("");

$("build").innerHTML =
  `<span>游戏版本 <b>${esc(DATA.meta.gameVersion || "—")}</b></span>`
  + `<span>上次更新时间 <b>${esc(DATA.meta.updated || "—")}</b></span>`;

$("count").innerHTML = `<b>${cars.length}</b> / ${cars.length} 台`;

/* ── 筛选器 ───────────────────────────────────────── */
const chips = $("chips");
/* 等级筛选：按钮下拉，菜单里按等级分组列出「线上强度组别」（S1 → S1 800公路/泥地/越野） */
const clsClasses = Object.keys(CLASS).filter(c => cars.some(x => x.cls === c));
const grpOfCls = c => TIER_GROUPS.filter(g => g.split(/\s+/)[0] === c);

function buildClsMenu() {
  const rows = [`<button class="all" data-cls="" data-grp="">全部等级</button>`];
  clsClasses.forEach(c => {
    const groups = grpOfCls(c);
    if (!groups.length) {
      rows.push(`<button class="gi" data-cls="${c}" data-grp="" style="--cc:${ccOf(c)};--ct:${ctOf(c)}">
        <span class="dot"></span>${c} 级 · 全部</button>`);
      return;
    }
    rows.push(`<div class="gh" style="--cc:${ccOf(c)}">${c} 级</div>`);
    rows.push(`<button class="gi" data-cls="${c}" data-grp="" style="--cc:${ccOf(c)};--ct:${ctOf(c)}">
      <span class="dot"></span>${c} 级 · 全部</button>`);
    groups.forEach(g => rows.push(
      `<button class="gi" data-cls="${c}" data-grp="${esc(g)}" style="--cc:${ccOf(c)};--ct:${ctOf(c)}">
        <span class="dot"></span>${esc(g)}</button>`));
  });
  return rows.join("");
}

chips.innerHTML = `<div class="clsdd" id="clsDD">
    <button class="chip on" id="clsBtn" aria-haspopup="listbox" aria-expanded="false">
      <span class="dot" style="--cc:var(--ink)"></span><span id="clsLbl">全部等级</span>
    </button>
    <div class="clsmenu" id="clsMenu" role="listbox">${buildClsMenu()}</div>
  </div>
  <div class="clsdd" id="driftDD">
    <button class="chip" id="driftBtn" aria-haspopup="listbox" aria-expanded="false">
      <span class="dot" style="--cc:var(--steel)"></span><span id="driftLbl">漂移强度</span>
    </button>
    <div class="clsmenu" id="driftMenu" role="listbox" style="width:180px">
      <button class="all" data-drift="">全部漂移强度</button>
      ${DRIFT_TIERS.map(t => `<button class="gi" data-drift="${t}">
        <img src="assets/tier/drift/${DRIFT_IMG[t]}.png" alt="" style="height:16px;width:31px;object-fit:contain">
        ${t} 级</button>`).join("")}
    </div>
  </div>`;

const closeDD = () => document.querySelectorAll(".clsdd.open").forEach(d => {
  d.classList.remove("open");
  d.querySelector("button").setAttribute("aria-expanded", "false");
});
document.addEventListener("click", e => { if (!e.target.closest(".clsdd")) closeDD(); });

$("clsBtn").onclick = e => {
  e.stopPropagation();
  const dd = $("clsDD"); const open = dd.classList.toggle("open");
  $("clsBtn").setAttribute("aria-expanded", String(open));
  $("driftDD").classList.remove("open");
};
$("driftBtn").onclick = e => {
  e.stopPropagation();
  const dd = $("driftDD"); const open = dd.classList.toggle("open");
  $("driftBtn").setAttribute("aria-expanded", String(open));
  $("clsDD").classList.remove("open");
};
$("clsMenu").addEventListener("click", e => {
  const b = e.target.closest("[data-cls]"); if (!b) return;
  S.cls = b.dataset.cls; S.tgrp = b.dataset.grp || "";
  const lbl = S.tgrp || (S.cls ? `${S.cls} 级` : "全部等级");
  $("clsLbl").textContent = lbl;
  const cc = S.cls ? ccOf(S.cls) : "var(--ink)";
  $("clsBtn").style.setProperty("--cc", cc);
  $("clsBtn").classList.toggle("on", !!S.cls);
  closeDD(); apply();
});
$("driftMenu").addEventListener("click", e => {
  const b = e.target.closest("[data-drift]"); if (!b) return;
  S.drift = b.dataset.drift || "";
  $("driftLbl").textContent = S.drift ? `漂移 ${S.drift}` : "漂移强度";
  $("driftBtn").classList.toggle("on", !!S.drift);
  closeDD(); apply();
});

[["fBk", "bk"], ["fDrv", "drv"], ["fBrand", "brand"], ["fCtry", "ctry"], ["fAcq", "acq"]].forEach(([id, key]) => {
  const el = $(id);
  if (key === "drv") {
    fillDrvSelect();
    fillPlaceSelect();
  } else if (key === "brand") {
    fillBrandSelect();
  } else if (key === "bk") {
    fillBucketSelect();
  } else if (key === "acq") {
    fillAcqSelect();
  } else {
    fillCtrySelect();
  }
  el.addEventListener("change", () => {
    S[key] = el.value;
    /* 换一级驱动时二级位置归零，并只保留该驱动下真实存在的引擎位置 */
    if (key === "drv") { S.place = ""; fillPlaceSelect(); }
    apply();
  });
});

$("fPlace").addEventListener("change", e => { S.place = e.target.value; apply(); });

/* 计数口径跟着 NPC 开关走，否则会出现「下拉写 424、选完只剩 420」。
   用函数声明（不是 const 箭头），因为下面的 forEach 会在定义处之前调用它。 */
function acqPool() { return cars.filter(c => S.npc || !c.npc); }

function fillDrvSelect() {
  const el = $("fDrv"), keep = S.drv;
  const order = ["FWD", "RWD", "AWD"];
  const pool = acqPool();
  el.innerHTML = `<option value="">全部驱动</option>` +
    order.filter(d => pool.some(c => c.drv === d)).map(d => {
      const n = pool.filter(c => c.drv === d).length;
      return `<option value="${d}">${DRIVE_LABEL[d] || d} ${d} · ${n}</option>`;
    }).join("");
  el.value = keep || "";
}

/* 二级：引擎位置。候选与该驱动下的真实组合对齐，某一级为「全部驱动」时列全部位置 */
function fillPlaceSelect() {
  const el = $("fPlace"), keep = S.place;
  const base = acqPool();
  const pool = S.drv ? base.filter(c => c.drv === S.drv) : base;
  const ids = [...new Set(pool.map(c => String(c.place || "")))]
    .filter(Boolean).sort((a, b) => +a - +b);
  el.innerHTML = `<option value="">引擎位置</option>` +
    ids.map(p => {
      const n = pool.filter(c => String(c.place) === p).length;
      return `<option value="${p}">${placeCode(+p)} · ${n}</option>`;
    }).join("");
  el.value = ids.includes(keep) ? keep : "";
  if (!el.value) S.place = "";
}

function fillAcqSelect() {
  const el = $("fAcq"), keep = S.acq;
  const cpN = cars.filter(c => c.cp).length;
  const seaN = cars.filter(c => seasonList(c).length).length;
  el.innerHTML = `<option value="">全部获取</option>`
    + `<option value="cp">Carpass车辆 · ${cpN}</option>`
    + `<optgroup label="赛季更新"><option value="series">赛季更新（全部）· ${seaN}</option>`
    + [1, 2, 3, 4, 5, 6, 7].map(n =>
        `<option value="s${n}">第 ${n} 赛季 · ${cars.filter(c => (c.sea || []).includes(n)).length}</option>`).join("")
    + `</optgroup>`;
  el.value = keep || "";
}

$("q").addEventListener("input", e => { S.q = e.target.value; apply(); });

function fillCtrySelect() {
  const el = $("fCtry"), keep = S.ctry;
  const groups = new Map();
  CTRIES.forEach(x => {
    if (!groups.has(x.rn)) groups.set(x.rn, []);
    groups.get(x.rn).push(x);
  });
  el.innerHTML = `<option value="">全部产地</option>` +
    [...groups.entries()].map(([rn, list]) =>
      `<optgroup label="${esc(rn)}">` + list.map(x =>
        `<option value="${x.id}">${esc(x.n)} · ${x.c}</option>`).join("") + `</optgroup>`).join("");
  el.value = keep ? String(keep) : "";
}

function fillBucketSelect() {
  const el = $("fBk"), keep = S.bk;
  const opts = BUCKETS.filter(b => cars.some(c => c.bk === b.id));
  el.innerHTML = `<option value="">全部类型</option>` + opts.map(b => {
    const n = cars.filter(c => c.bk === b.id).length;
    return `<option value="${b.id}">${esc(bkName(b))} · ${n}</option>`;
  }).join("");
  el.value = keep ? String(keep) : "";
}

function fillBrandSelect() {
  const el = $("fBrand"), keep = S.brand;
  el.innerHTML = `<option value="">全部品牌</option>`;
  brands.forEach(b => el.insertAdjacentHTML("beforeend",
    `<option value="${b.id}">${esc(bn(b))} · ${b.list.length}</option>`));
  el.value = keep ? String(keep) : "";
}

/* ── 车鉴 ─────────────────────────────────────────── */
const gallery = $("gallery");
const cardOf = new Map();
const secOf = new Map();

function flagsHTML(c) {
  if (!c.cp && !seasonList(c).length && !c.wide) return "";
  return (c.wide ? `<span class="flag flag--wide" title="支持宽体套件改装">宽体</span>` : "")
    + (c.cp ? `<span class="flag flag--cp" title="通过 Car Pass 获得">Carpass车辆</span>` : "")
    + (seasonNote(c) ? `<span class="flag flag--sea" title="${esc(c.acq || "")}">${esc(seasonNote(c))}</span>` : "");
}

/* 某个引擎支持哪些增压升级：DATA.asp 以 engineId 为键，值为各类的等级数组。
   TurboQuad 目前是空表，但键位保留，有数据就会自动显示出来。 */
const ASP_LABEL = {ts: "单涡轮", tt: "双涡轮", tq: "四涡轮",
                   dsc: "正排量机增", csc: "离心机增"};
const ASP_ORDER = ["ts", "tt", "tq", "dsc", "csc"];
function aspHTML(eid) {
  const a = (DATA.asp || {})[String(eid)];
  if (!a) return "";
  const rng = v => (v.length > 1 ? `${v[0]}–${v[v.length - 1]}` : String(v[0]));
  const bits = ASP_ORDER.filter(k => a[k]).map(k =>
    `<i class="${k === "csc" ? "csc" : ""}" title="${ASP_LABEL[k]}：可升级至 Lv ${a[k].join(" / ")}">${ASP_LABEL[k]} ${rng(a[k])}</i>`
  );
  return bits.length ? `<span class="asp">${bits.join("")}</span>` : "";
}

/* 悬挂结构：真正的结构名在 List_SuspensionPhysicsType.Path 的文件名里
   （ROAD_Wishbone.xml → Wishbone），List_SuspensionType 的 6 个词做中文归类参考。
   键按长度降序匹配，避免 trailingarm 抢在 trailinglateral 前面。 */
const SUSP_CN = {
  independent: "独立悬挂", independant: "独立悬挂", solid: "整体桥",
  wishbone: "双叉臂", strut: "麦弗逊滑柱", fivelink: "五连杆", fourlink: "四连杆",
  multilink: "多连杆", trailinglateral: "斜置拖曳臂", trailingbeam: "扭力梁",
  trailingarm: "拖曳臂", trailarm: "拖曳臂", trailbeam: "扭力梁", traillat: "斜置拖曳臂",
  swingaxle: "摆动半轴", panhardrod: "潘哈德杆整体桥",
  torsion: "扭杆弹簧", leaf: "钢板弹簧", articulated: "关节式独立悬挂",
};
const SUSP_KEYS = Object.keys(SUSP_CN).sort((a, b) => b.length - a.length);

function suspName(tid) {
  const t = (DATA.suspType || {})[String(tid)];
  if (!t) return null;
  const m = /([A-Za-z0-9_]+)\.xml$/i.exec(t.p || "");
  let raw = m ? m[1] : (t.n || "");
  raw = raw
    .replace(/^(ROAD|RACE|RALLY|DRIFT|TRUCK|SPORT|VINTAGE|OFFROAD|MONSTER)_/i, "")
    .replace(/^[FR]_/i, "")
    .replace(/_(FWD|RWD|AWD)$/i, "")
    .replace(/_L\d$/i, "")     // 先去 _L1 这类版本号，才轮得到 _F/_R
    .replace(/_[FR]$/i, "")
    .replace(/_L\d$/i, "")
    .replace(/_/g, " ");
  const key = raw.toLowerCase().replace(/[^a-z]/g, "");
  const hit = SUSP_KEYS.find(k => key.includes(k));
  return { raw: raw || t.n || "—", cn: hit ? SUSP_CN[hit] : "" };
}

const STEER_CN = {
  Default: "默认", Drift: "漂移", MonsterTruck: "大脚车", HighDownforce: "高下压力",
  Sierra: "越野", "HighDownforce_3.5": "高下压力 3.5",
  "HighDownforceSlowSteering_3.5": "高下压力慢转向 3.5",
};
const RS_CN = {
  MonsterTruck: "大脚车", Modern: "现代", Retro: "复古", AWD_Race: "AWD 赛车",
  IE: "内部调校", Truck: "卡车", Race: "赛车",
  GMC_HummerEV_22: "悍马 EV", FAF_FlipCarFastX_22: "速激翻转车",
};
const MOD_CN = {AeroMod: "空气动力", SuspensionMod: "悬挂", EngineMod: "发动机",
                DriveTrainMod: "传动", ChassisMod: "底盘"};
const OV_CN = {
  GameTorqueScale: "动力输出", ZeroThrottleTorqueScale: "松油扭矩",
  RearTorqueSplit: "后轴扭矩分配", DriveType: "驱动形式",
  TCProfileID: "牵引力控制", FrontRideHeight: "前离地高度",
  RearRideHeight: "后离地高度", FrontSpringK: "前弹簧刚度",
  RearSpringK: "后弹簧刚度", DampenBumpRate: "压缩阻尼",
  DampenReboundRate: "回弹阻尼",
};

function cardHTML(c) {
  return `<article class="car" data-id="${c.id}" style="--cc:${ccOf(c.cls)};--ct:${ctOf(c.cls)}">
    <a class="car-link" href="#id=${c.id}" data-open="${c.id}" aria-label="${esc(nm(c))} 详情">
      <div class="car-stage"><img src="assets/car/${c.id}.webp" alt="" loading="lazy" decoding="async" style="--mh:${c.mh || 110}px" onerror="this.style.visibility='hidden'"><div class="car-flags">${flagsHTML(c)}</div></div>
      <div class="car-meta"><span class="plate"><b>${c.cls || "–"}</b><i>${c.pi ?? "—"}</i></span><span>${c.year}</span><span>${c.drv || "—"}</span>${tierBadge(c)}<span class="csoc"></span></div>
      <h4 class="car-name">${esc(nm(c))}</h4>
      <dl class="car-nums">
        <div><dt>马力</dt><dd>${nf(c.hp)}</dd></div>
        <div><dt>车重</dt><dd>${nf(c.kg)}<i>kg</i></dd></div>
        <div><dt>120 mph G</dt><dd>${Number(c.latg120 || 0).toFixed(2)}</dd></div>
      </dl>
    </a>
    <button class="car-add" data-sel="${c.id}" aria-label="把 ${esc(nm(c))} 加入比对" aria-pressed="false">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg>
    </button>
  </article>`;
}

/* 所有车卡只建一次，分组时搬动节点，不重建 DOM */
const holder = document.createElement("div");
holder.innerHTML = cars.map(cardHTML).join("");
cars.forEach(c => {
  const el = holder.querySelector(`.car[data-id="${c.id}"]`);
  cardOf.set(c.id, {
    el,
    nameEl: el.querySelector(".car-name"),
    flagEl: el.querySelector(".car-flags"),
    link: el.querySelector(".car-link"),
    add: el.querySelector(".car-add"),
  });
});

const npcCars = cars.filter(c => c.npc);

function groupList() {
  const pool = cars.filter(c => S.npc || !c.npc);
  if (S.group === "acq") {
    /* 通行证车辆单独成段，不与赛季车混排；一台车只落在一个段里 */
    const map = new Map();
    pool.forEach(c => {
      const k = c.cp ? "cp" : (seasonList(c).length ? "series" : (c.acq ? "general" : "unknown"));
      if (!map.has(k)) map.set(k, []);
      map.get(k).push(c);
    });
    const defs = [
      ["cp", "Carpass车辆", "CAR PASS"],
      ["series", "赛季更新车辆", "SERIES UPDATES"],
      ["general", "常规获取", "AUTOSHOW / WHEELSPIN / BARN FIND"],
      ["unknown", "未收录获取途径", "NOT LISTED"],
    ];
    return defs.filter(([k]) => map.has(k)).map(([k, title, en]) => ({
      key: "a" + k, title, en: S.lang === "en" ? "" : en, cars: map.get(k),
    }));
  }
  if (S.group === "bucket") {
    const map = new Map();
    pool.forEach(c => {
      const k = c.bk || 0;
      if (!map.has(k)) map.set(k, []);
      map.get(k).push(c);
    });
    return BUCKETS.filter(b => map.has(b.id)).map(b => ({
      key: "b" + b.id, title: bkName(b), en: S.lang === "en" ? "" : b.en, cars: map.get(b.id),
    }));
  }
  if (S.group === "tier") {
    /* 按竞速强度分级分组：Meta+ → 未知，未收录的单独一段排最后 */
    const map = new Map();
    pool.forEach(c => {
      const k = tierOf(c);
      if (!map.has(k)) map.set(k, []);
      map.get(k).push(c);
    });
    return [...map.keys()].sort((a, b) => a - b).map(k => {
      const list = map.get(k).slice().sort((a, b) => (b.pi || 0) - (a.pi || 0) || carCmp(a, b));
      return {
        key: "t" + k,
        title: k < 99 ? TIER_NAMES[k] : "未分级",
        img: k < 99 ? TIER_IMG[k] : null,
        en: S.lang === "en" ? `${list.length} cars` : `${list.length} 台 · 竞速强度`,
        cars: list,
      };
    });
  }
  if (S.group === "date") {
    const map = new Map();
    pool.forEach(c => {
      const k = c.dt ? c.dt.slice(0, 7) : "";
      if (!map.has(k)) map.set(k, []);
      map.get(k).push(c);
    });
    return [...map.keys()].sort().reverse().map(k => {
      const list = map.get(k).slice().sort((a, b) => (b.dt || "").localeCompare(a.dt || "") || carCmp(a, b));
      return {
        key: "d" + (k || "launch"),
        title: k ? k.replace("-", " 年 ") + " 月" : (S.lang === "en" ? "Launch line-up" : "首发车辆"),
        en: k ? `${k} · ${list.length} 台新增` : "LAUNCH LINE-UP",
        cars: list,
      };
    });
  }
  const map = new Map();
  pool.forEach(c => {
    if (!map.has(c.mkid)) map.set(c.mkid, []);
    map.get(c.mkid).push(c);
  });
  return brands.filter(b => map.has(b.id)).sort(brandCmp).map(b => ({
    key: "m" + b.id, title: bn(b), en: "", cars: map.get(b.id), brand: b,
  }));
}

function makeSection(g) {
  const sec = document.createElement("section");
  sec.className = "brand";
  sec.id = "sec-" + g.key;
  sec.dataset.key = g.key;
  const logo = g.brand && g.brand.logo
    ? `<span class="make"><img src="assets/make/${esc(g.brand.logo)}.webp" alt="" loading="lazy"
        data-light="assets/make/${esc(g.brand.logo)}.webp"
        data-dark="${(DATA.meta.logoDark || []).includes(g.brand.logo) ? "assets/make/d/" + esc(g.brand.logo) + ".webp" : ""}"
        onerror="this.remove()"></span>` : "";
  const en = g.en ? `<small>${esc(g.en)}</small>` : "";
  const brandAttr = g.brand ? ` data-brand="${g.brand.id}"` : "";
  sec.innerHTML = `<header class="brand-h">
      ${logo}
      <h3 class="brand-name">${g.img ? `<img class="gh-badge" src="assets/tier/${g.img}.png" alt="${esc(g.title)}">` : `<span class="cn">${esc(g.title)}</span>`}${en}</h3>
      <span class="brand-line"></span>
      <button class="brand-n"${brandAttr}><b>${g.cars.length}</b> 台</button>
    </header><div class="cars"></div>`;
  const grid = sec.querySelector(".cars");
  grid.append(...g.cars.slice().sort(carCmp).map(c => cardOf.get(c.id).el));
  return sec;
}

function renderGallery() {
  const groups = groupList();
  if (S.npc && npcCars.length) {
    groups.push({
      key: "npc", title: "NPC / 街车",
      en: S.lang === "en" ? "Not obtainable" : "Not obtainable",
      cars: npcCars,
    });
  }
  secOf.clear();
  gallery.textContent = "";
  const frag = document.createDocumentFragment();
  groups.forEach(g => {
    const sec = makeSection(g);
    frag.appendChild(sec);
    secOf.set(g.key, {el: sec, countEl: sec.querySelector(".brand-n b"), cars: g.cars});
  });
  gallery.appendChild(frag);
  apply();
}

/* ── 数据表 ───────────────────────────────────────── */
let tblBuilt = false;
let builtMode = null;
let TROWS = [];
const TIER_ROWS = DATA.tierRows || {};
const rowsOf = c => TIER_ROWS[String(c.id)] || [];
const tierMode = () => !!(S.tgrp || S.cls);
const rowOf = new Map();

/* 一列同时承载 Acquired via 与 Car Pass 加入日期：主行获取方式，小字补日期 */
const acqTip = c => `${acqText(c)}${c.dt ? " · 加入 " + c.dt : ""}`;
const acqHTML = c => `${esc(acqText(c))}${c.dt ? `<em class="sub">加入 ${esc(c.dt)}</em>` : ""}`;

function rowHTML(c, e, mode) {
  const v = Math.max(4, Math.min(100, (c.pi - 100) / 898 * 100)).toFixed(0);
  const ti = e ? e[0] : tierOf(c);
  const grp = e ? (TIER_GROUPS[e[1]] || "") : tierGroupOf(c);
  const badge = ti < 99
    ? `<span class="tierb"><img src="assets/tier/${TIER_IMG[ti]}.png" alt="${esc(TIER_NAMES[ti])}"></span>` : "";
  const note = e && e[6] ? ` title="${esc(e[6])}"` : "";
  const tt = mode
    ? `<td class="tt">${esc(e && e[2] || "—")}</td><td class="tt">${esc(e && e[3] || "—")}</td>
       <td class="tt">${esc(e && e[4] || "—")}</td><td class="tt">${esc(e && e[5] || "—")}</td>`
    : `<td class="tt"></td><td class="tt"></td><td class="tt"></td><td class="tt"></td>`;
  return `<tr data-id="${c.id}" data-ti="${ti}" style="--cc:${ccOf(c.cls)};--ct:${ctOf(c.cls)}">
      <td class="pick"><input type="checkbox" class="chk" data-sel="${c.id}" aria-label="选择 ${esc(nm(c))}"></td>
      <td class="yr">${c.year}</td>
      <td class="nm" title="${esc(nm(c))}"><div class="thumbcell"><img src="assets/car/${c.id}.webp" alt="" loading="lazy" decoding="async" onerror="this.remove()"><span class="nmtext">${esc(nm(c))}</span></div></td>
      <td class="tier"${note}><div class="tcell">${badge}<i>${esc(grp || "—")}</i></div></td>
      <td class="cls"><span class="cls">${c.cls || "–"}</span></td>
      <td class="pi"><b>${c.pi ?? "—"}</b><i style="--v:${v}%"></i></td>
      <td class="hp">${nf(c.hp)}</td>
      <td class="tq">${nf(c.nm)}</td>
      <td class="kg">${nf(c.kg)}</td>
      <td class="pwr">${c.pwr}</td>
      <td class="t60">${Number(c.t60).toFixed(2)}</td>
      <td class="tsm">${nf(c.tsm)}</td>
      <td class="latg">${Number(c.latg).toFixed(2)}</td>
      <td class="brk">${Number(c.brk).toFixed(1)}</td>
      <td class="drv">${c.drv || "—"}</td>
      <td class="eng" title="${esc(c.eng || "—")}">${esc(c.eng || "—")}${c.eg ? `<sup class="guess" title="${engGuessTip}">*</sup>` : ""}</td>
      ${tt}
      <td class="acq" title="${esc(acqTip(c))}">${acqHTML(c)}</td>
    </tr>`;
}

/* 表格行：普通模式一车一行；启用等级/组别筛选后改为「一车一等级一行」，
   并露出右侧「Meta 改装后数据」四列（驱动/难度/轮胎/定位） */
function buildTable(force) {
  const mode = tierMode();
  if (tblBuilt && !force && mode === builtMode) return;
  builtMode = mode; tblBuilt = true;
  document.body.classList.toggle("tiermode", mode);
  TROWS = [];
  cars.filter(matches).forEach(c => {
    const list = rowsOf(c);
    if (!mode || !list.length) { TROWS.push({ c, e: null }); return; }
    list.forEach(e => {
      if (S.tgrp && TIER_GROUPS[e[1]] !== S.tgrp) return;
      TROWS.push({ c, e });
    });
  });
  const body = $("tbody");
  body.innerHTML = TROWS.map(r => rowHTML(r.c, r.e, mode)).join("");
  [...body.children].forEach((tr, i) => {
    TROWS[i].tr = tr;
    if (!rowOf.has(+tr.dataset.id)) rowOf.set(+tr.dataset.id, {
      tr, nameEl: tr.querySelector(".nmtext"), nmTd: tr.querySelector("td.nm"),
      chk: tr.querySelector("input.chk"), acqEl: tr.querySelector("td.acq"),
    });
  });
  sortTable();
}

function sortTable() {
  if (!tblBuilt) return;
  const k = S.sort;
  document.querySelectorAll("#tbl thead th").forEach(x => x.classList.remove("on", "asc"));
  const head = document.querySelector(`#tbl thead th[data-k="${k}"]`);
  if (head) { head.classList.add("on"); if (!S.desc) head.classList.add("asc"); }
  const TT = { tdrv: 2, tdiff: 3, ttire: 4, trole: 5 };
  const cmp = (a, b) => {
    if (k === "tier") {
      const ta = a.e ? a.e[0] : 99, tb = b.e ? b.e[0] : 99;
      return ta - tb || (b.c.pi || 0) - (a.c.pi || 0);
    }
    if (k in TT) {
      const ia = a.e ? TT[k] : null, ib = b.e ? TT[k] : null;
      const va = ia === null ? "\uffff" : String(a.e[ia] || "\uffff");
      const vb = ib === null ? "\uffff" : String(b.e[ib] || "\uffff");
      return va.localeCompare(vb, COLL());
    }
    if (k === "name") {
      return sortName(a.c).localeCompare(sortName(b.c), COLL(), {numeric: true})
        || nm(a.c).localeCompare(nm(b.c), COLL());
    }
    if (k === "acq") {
      const r = (a.c.acq ? acqText(a.c) : "\uffff").localeCompare(b.c.acq ? acqText(b.c) : "\uffff", COLL(), {numeric: true});
      return r;
    }
    let va = a.c[k], vb = b.c[k];
    if (k === "t60") { va = va || 999; vb = vb || 999; }
    if (typeof va === "string" || typeof vb === "string") {
      va = String(va || ""); vb = String(vb || "");
      return va.localeCompare(vb, COLL());
    }
    return (va || 0) - (vb || 0);
  };
  TROWS.sort((a, b) => (S.desc ? -cmp(a, b) : cmp(a, b)));
  const body = $("tbody");
  body.append(...TROWS.map(r => r.tr));
}

document.querySelectorAll("#tbl thead th[data-k]").forEach(th => {
  th.addEventListener("click", () => {
    const k = th.dataset.k;
    if (S.sort === k) S.desc = !S.desc;
    else { S.sort = k; S.desc = !["name", "drv", "eng", "cls", "acq"].includes(k); }
    document.querySelectorAll("#tbl thead th").forEach(x => x.classList.remove("on", "asc"));
    th.classList.add("on"); if (!S.desc) th.classList.add("asc");
    sortTable();
  });
});

/* ── 过滤与视图 ───────────────────────────────────── */
/* 功能关键词索引：让搜索框能按「宽体套件 / 离心机增 / 后轮转向 / 主动驾驶模式」
   直接筛出具备该功能的车辆。后轮转向和驾驶模式不在 ROWS 里，靠 DATA 反查，
   所以这里预生成一次字符串随时比对，避免每次输入都重新拼。
   简繁两套写法都写进来：繁体版整页会被转成繁体，只写简体的话繁体版就搜不到。 */
const FEAT_OF = new Map();
cars.forEach(c => {
  const bits = [];
  if (c.wide) bits.push("宽体套件", "宽体", "寬體套件", "寬體", "widebody", "wide body");
  if (c.csc) bits.push("离心机增升级", "离心机增", "離心機增升級", "離心機增", "csc upgrade");
  const sp = (DATA.susp || {})[String(c.id)];
  if (sp && sp.rs) bits.push("后轮转向", "四轮转向", "後輪轉向", "四輪轉向", "rear steer", "rear wheel steering");
  if ((DATA.driveMode || {})[String(c.id)]) bits.push("主动驾驶模式", "驾驶模式", "主動駕駛模式", "駕駛模式", "drive mode");
  FEAT_OF.set(c.id, bits.join(" "));
});
function featText(c) { return FEAT_OF.get(c.id) || ""; }

function matches(c) {
  if (!S.npc && c.npc) return false;
  if (S.wide && !c.wide) return false;   // 宽体筛选：只看有可选车身套件的车
  if (S.fav && MY.garage.get(String(c.id)) !== "favorite") return false;  // 只看收藏
  /* 选了具体组别时只按组别筛（车子的原厂等级可能与该组别不同） */
  if (S.tgrp) { if (effRace(c).group !== S.tgrp) return false; }
  else if (S.cls && c.cls !== S.cls) return false;
  if (S.drift && effDrift(c) !== S.drift) return false;
  if (S.ctry && String(c.ctry) !== S.ctry) return false;
  if (S.bk && String(c.bk) !== S.bk) return false;
  if (S.eng) {
    const set = ENG_BY_CAR.get(c.id);
    if (!set || !set.has(S.eng)) return false;
  }
  if (S.drv && c.drv !== S.drv) return false;
  if (S.place && String(c.place || "") !== S.place) return false;
  if (S.brand && String(c.mkid) !== String(S.brand)) return false;
  if (S.acq === "cp") { if (!c.cp) return false; }
  else if (S.acq === "series") { if (!seasonList(c).length) return false; }
  else if (/^s\d$/.test(S.acq)) { if (!seasonList(c).includes(+S.acq.slice(1))) return false; }
  if (!S.q) return true;
  const q = S.q.trim().toLowerCase();
  return String(c.id).includes(q)
    || (c.name || "").toLowerCase().includes(q)
    || (c.name_en || "").toLowerCase().includes(q)
    || (c.brand || "").toLowerCase().includes(q)
    || (c.brand_en || "").toLowerCase().includes(q)
    || (c.eng || "").toLowerCase().includes(q)
    || (c.acq || "").toLowerCase().includes(q)
    || (c.cp ? "carpass 车辆通行证" : "").includes(q)
    || featText(c).includes(q);
}

let visible = 0;

function apply() {
  if (tblBuilt) buildTable(true);
  const q = S.q.trim();
  let n = 0;
  cars.forEach(c => {
    const ok = matches(c);
    c._vis = ok;
    const card = cardOf.get(c.id); if (card) card.el.classList.toggle("hide", !ok);
    if (tblBuilt) { const row = rowOf.get(c.id); if (row) row.tr.classList.toggle("hide", !ok); }
    if (ok) n++;
  });
  visible = n;

  secOf.forEach(rec => {
    let k = 0;
    rec.cars.forEach(c => { if (c._vis) k++; });
    rec.el.classList.toggle("hide", k === 0);
    rec.countEl.textContent = k;
  });

  const total = S.npc ? cars.length : PLAYABLE();
  $("count").innerHTML = `<b>${n}</b> / ${total} 台`;
  $("empty").classList.toggle("on", n === 0);
  /* 必须尊重当前视图：切语言 / 改筛选都会走到这里，若只按 n>0 就显示车鉴，
     数据表模式会被悄悄顶回车鉴。 */
  gallery.hidden = S.view === "table" || n === 0;

  const active = !!(q || S.cls || S.tgrp || S.drift || S.drv || S.place || S.brand || S.ctry || S.bk || S.acq || S.eng || S.wide);
  $("result").classList.toggle("on", active);
  if (active) {
    const bits = [];
    if (q) bits.push(`“${esc(q)}”`);
    if (S.tgrp) bits.push(S.tgrp); else if (S.cls) bits.push(`${S.cls} 级`);
    if (S.drift) bits.push(`漂移 ${S.drift}`);
    if (S.drv) bits.push(`${DRIVE_LABEL[S.drv] || S.drv} ${S.drv}`);
    if (S.place) bits.push(placeCode(+S.place));
    if (S.brand) {
      const b = brands.find(y => String(y.id) === String(S.brand));
      if (b) bits.push(esc(bn(b)));
    }
    if (S.ctry) { const x = CTRIES.find(y => String(y.id) === S.ctry); if (x) bits.push(esc(x.n)); }
    if (S.bk) { const b = BK[+S.bk]; if (b) bits.push(esc(bkName(b))); }
    if (S.wide) bits.push("宽体套件");
    if (S.acq === "cp") bits.push("Carpass车辆");
    else if (S.acq === "series") bits.push("赛季更新");
    else if (/^s\d$/.test(S.acq)) bits.push(`第 ${S.acq.slice(1)} 赛季`);
    if (S.eng) bits.push(`引擎 ${esc(S.engName)}`);
    $("resultText").innerHTML = `筛选：${bits.join(" · ")} — <b>${n}</b> 台匹配`;
  }
  if (S.view === "table" && tblBuilt) sortTable();
}

function clearFilters() {
  S.q = ""; S.cls = ""; S.tgrp = ""; S.drift = ""; S.drv = ""; S.place = ""; S.brand = ""; S.ctry = ""; S.bk = ""; S.acq = ""; S.eng = ""; S.engName = "";
  S.wide = false; $("fWide").checked = false;
  S.fav = false; $("fFav").checked = false;
  $("q").value = ""; $("fDrv").value = ""; $("fPlace").value = ""; $("fBrand").value = ""; $("fCtry").value = "";
  $("fBk").value = ""; $("fAcq").value = "";
  [...chips.children].forEach((x, i) => x.classList.toggle("on", i === 0));
  apply();
}
$("clearFilters").onclick = clearFilters;
$("emptyClear").onclick = clearFilters;

function setView(v) {
  if (v === "table" && window.innerWidth < 861) return;
  S.view = v;
  document.querySelectorAll(".views button").forEach(b => {
    const on = b.dataset.view === v;
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", on);
  });
  if (v === "table") { buildTable(); apply(); requestAnimationFrame(syncTable); }
  $("gallery").hidden = v === "table" || visible === 0;
  $("sheet").classList.toggle("on", v === "table");
  document.body.classList.toggle("is-table", v === "table");
}
document.querySelectorAll(".views button").forEach(b => b.addEventListener("click", () => setView(b.dataset.view)));
document.querySelector('.nav-links a[data-view="table"]').addEventListener("click", e => { e.preventDefault(); setView("table"); document.getElementById("catalogue").scrollIntoView(); });

$("catalogue").addEventListener("click", e => {
  const brandBtn = e.target.closest(".brand-n[data-brand]");
  if (brandBtn && brandBtn.dataset.brand) {
    S.brand = brandBtn.dataset.brand; $("fBrand").value = S.brand; apply();
    window.scrollTo({top: $("bar").offsetTop, behavior: "smooth"});
  }
});

$("groupBy").addEventListener("click", e => {
  const b = e.target.closest("button[data-g]"); if (!b) return;
  S.group = b.dataset.g;
  [...$("groupBy").children].forEach(x => {
    const on = x === b;
    x.classList.toggle("on", on);
    x.setAttribute("aria-pressed", on);
  });
  renderGallery();
});

$("showNpc").addEventListener("change", e => {
  S.npc = e.target.checked;
  fillDrvSelect();
  fillPlaceSelect();
  syncWideN();
  renderGallery();
});

/* 宽体套件开关：车鉴与数据表共用同一套 matches()，两边都会生效 */
$("fWide").addEventListener("change", e => {
  S.wide = e.target.checked;
  apply();
});

/* 只看收藏：收藏状态来自 /api/garage，未登录时数量为 0 */
$("fFav").addEventListener("change", e => {
  S.fav = e.target.checked;
  apply();
});

function syncFavN() {
  const n = [...MY.garage.values()].filter(v => v === "favorite").length;
  const el = $("favN");
  if (el) el.textContent = n;
  if (!n && S.fav) { S.fav = false; const cb = $("fFav"); if (cb) cb.checked = false; }
}
/* 首次值由 bootAuth 在拿到 /api/garage 后调用；此处不能提前调用，
   MY 在第 3097 行才声明，提前调用会触发 TDZ ReferenceError 让整段脚本中断。 */

/* 开关旁的台数必须和勾选后的结果一致：NPC / 街车默认隐藏，
   若按全库 111 写死，勾上却只剩 106，会被当成漏筛。 */
function syncWideN() {
  $("wideN").textContent = acqPool().filter(c => c.wide).length;
}
syncWideN();

/* ── 选择与比对 ───────────────────────────────────── */
function toggleSel(id, on) {
  if (on === undefined) on = !S.sel.has(id);
  if (on && S.sel.size >= 4) { flashBar(); return; }
  if (on) S.sel.add(id); else S.sel.delete(id);
  const card = cardOf.get(id);
  if (card) {
    card.el.classList.toggle("on", on);
    const b = card.add;
    b.setAttribute("aria-pressed", on);
    b.innerHTML = on
      ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5l4.5 4.5L19 7"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg>';
  }
  if (tblBuilt) {
    const row = rowOf.get(id);
    if (row) { row.tr.classList.toggle("on", on); row.chk.checked = on; }
  }
  $("selN").textContent = S.sel.size;
  $("selbar").classList.toggle("on", S.sel.size > 0);
  $("btnCompare").disabled = S.sel.size < 2;
  if (!S.sel.size) resetCopyBtn();
}

/* ── 一键复制所选车辆全称（年份 + 车名，每台一行） ─────── */
let copyTimer = 0;
function resetCopyBtn() {
  const b = $("btnCopy");
  clearTimeout(copyTimer);
  b.textContent = "复制车名";
  b.classList.remove("done");
}
async function copySelected() {
  const ids = [...S.sel];
  if (!ids.length) return;
  const text = ids.map(id => byId.get(id))
    .filter(Boolean).map(c => `${c.year} ${nm(c)}`).join("\n");
  let ok = false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      ok = true;
    } else {
      /* file:// 或非安全上下文没有 Clipboard API，退回临时 textarea */
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0";
      document.body.appendChild(ta);
      ta.select();
      ok = document.execCommand("copy");
      ta.remove();
    }
  } catch { ok = false; }
  const b = $("btnCopy");
  b.textContent = ok ? `已复制 ${ids.length} 台` : "复制失败，请重试";
  b.classList.toggle("done", ok);
  clearTimeout(copyTimer);
  copyTimer = setTimeout(resetCopyBtn, 1900);
}
$("btnCopy").onclick = copySelected;

function flashBar() {
  const b = $("selbar");
  b.animate([{transform: "translate(-50%,0)"}, {transform: "translate(calc(-50% - 6px),0)"}, {transform: "translate(calc(-50% + 6px),0)"}, {transform: "translate(-50%,0)"}], {duration: 260, easing: "ease-in-out"});
}
$("btnClear").onclick = () => {
  [...S.sel].forEach(id => toggleSel(id, false));
};
document.addEventListener("click", e => {
  const add = e.target.closest(".car-add");
  if (add) { e.preventDefault(); e.stopPropagation(); toggleSel(+add.dataset.sel); return; }
  const open = e.target.closest("[data-open]");
  if (open) { e.preventDefault(); openCar(+open.dataset.open); }
});
$("tbody").addEventListener("click", e => {
  const cb = e.target.closest("input.chk");
  if (cb) { e.stopPropagation(); toggleSel(+cb.dataset.sel, cb.checked); return; }
  const tr = e.target.closest("tr");
  if (tr) openCar(+tr.dataset.id);
});

/* ── 中英切换 ─────────────────────────────────────── */
function applyLang(lang, save) {
  S.lang = lang === "en" ? "en" : "zh";
  document.querySelectorAll(".lang button").forEach(b => {
    const on = b.dataset.lang === S.lang;
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", on);
  });
  document.documentElement.lang = S.lang === "zh" ? (DOC_HANT ? "zh-Hant" : "zh-CN") : "en";

  sortBrands();
  cars.forEach(c => {
    const rec = cardOf.get(c.id);
    if (!rec) return;
    rec.nameEl.textContent = nm(c);
    rec.flagEl.innerHTML = flagsHTML(c);
    rec.link.setAttribute("aria-label", `${nm(c)} 详情`);
    rec.add.setAttribute("aria-label", `把 ${nm(c)} 加入比对`);
    if (tblBuilt) {
      const row = rowOf.get(c.id);
      if (row) {
        row.nameEl.textContent = nm(c);
        row.nmTd.title = nm(c);              // 悬浮全称跟着车名语言走
        row.chk.setAttribute("aria-label", `选择 ${nm(c)}`);
        row.acqEl.innerHTML = acqHTML(c);
        row.acqEl.title = acqTip(c);
      }
    }
  });
  fillBrandSelect();
  fillBucketSelect();
  fillPlaceSelect();          // 位置名随语言切 Front / Mid / Rear
  renderGallery();
  if (S.view === "table" && tblBuilt) sortTable();
  apply();
  if (drawer.classList.contains("on") && curCar) openCar(curCar.id);
  if ($("cmp").classList.contains("on")) openCompare();
  if (save) localStorage.setItem(LANG_KEY, S.lang);
}
document.querySelectorAll(".lang button").forEach(b => {
  b.onclick = () => applyLang(b.dataset.lang, true);
});

/* ── 深浅配色 ─────────────────────────────────────── */
function applyLogoTheme(dark) {
  document.querySelectorAll(".make img, .bar-mark img, .about-mark img").forEach(img => {
    if (!img.dataset.dark) return;
    img.src = dark ? img.dataset.dark : img.dataset.light;
  });
}

function setTheme(t, save) {
  const dark = t === "dark";
  if (dark) document.documentElement.dataset.theme = "dark";
  else document.documentElement.removeAttribute("data-theme");
  const btn = $("themeBtn");
  btn.setAttribute("aria-pressed", dark);
  btn.setAttribute("aria-label", dark ? "切换浅色配色" : "切换深色配色");
  applyLogoTheme(dark);
  if (save) localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
}
$("themeBtn").onclick = () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark", true);

/* ── 车卡图的兜底 ─────────────────────────────────── */
document.querySelectorAll(".car-stage img").forEach(img => {
  img.addEventListener("error", () => { img.closest(".car").classList.add("nopic"); img.remove(); });
});

/* ── 抽屉 ─────────────────────────────────────────── */
const drawer = $("drawer"), scrim = $("scrim");
let curCar = null;
const FK = DATA.fk || {};

function prettyCompound(n) {
  return String(n)
    .replace(/^\d+_/, "")
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim();
}

function fmt(v) {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "number") {
    if (Number.isInteger(v)) return v.toLocaleString("en-US");
    return Math.abs(v) >= 100 ? v.toFixed(1) : String(+v.toPrecision(4));
  }
  return esc(v);
}
function fmtField(f, v) {
  const plain = /^(Year|.*Id|.*ID)$/.test(f.n);
  const base = plain ? (v === null || v === undefined || v === "" ? "—" : esc(v)) : fmt(v);
  const m = FK[f.n];
  /* 外键类字段：把中文含义提到主位，原始编号降成后面的小字备注。
     例：产地大区「2 欧洲」→「欧洲 2」 */
  if (m && m[String(v)] && String(v) !== "") return `${esc(m[String(v)])} <i>${base}</i>`;
  return base;
}

function openCar(id) {
  const c = cars.find(x => x.id === id); if (!c) return;
  curCar = c;
  $("dCls").textContent = c.cls || "–";
  $("dCls").style.setProperty("--cc", ccOf(c.cls));
  $("dCls").style.setProperty("--ct", ctOf(c.cls));
  $("dTitle").textContent = nm(c);
  const bk = BK[c.bk];
  $("dMeta").innerHTML = `<span>ID <b>${c.id}</b></span><span>${c.year}</span><span>${esc(S.lang === "zh" ? c.brand : c.brand_en)}</span>`
    + `<span>PI <b>${c.pi}</b></span><span>${c.drv}${c.place ? " · " + esc(placeCode(c.place)) : ""}</span>`
    + `<span>${esc(c.eng || "纯电")}${c.eg ? `<sup class="guess" title="${engGuessTip}">*</sup>` : ""}</span>`
    + (bk ? `<span>${esc(bkName(bk))}</span>` : "")
    + (c.cp ? `<span title="通过 Car Pass 获得"><b>Carpass车辆</b>${c.dt ? `<i>加入 ${esc(c.dt)}</i>` : ""}</span>` : "")
    + (seasonNote(c) ? `<span title="${esc(c.acq || "")}"><b>${esc(seasonNote(c))}</b></span>` : "")
    + (c.acq && !c.cp && String(c.acq).split(/\s*\/\s*/).some(x => !/^Series \d+$/.test(x))
        ? `<span title="${esc(c.acq)}">获取 <b>${esc(acqText(c))}</b></span>` : "");

  const vals = FROWS[c._i];
  const secs = GROUPS.map(() => []);
  FULL.forEach((f, i) => {
    if (["DisplayName", "ModelShort", "MakeName"].includes(f.n)) return;
    secs[f.g].push([f, vals[i]]);
  });

  let html = `<div class="dhero"><img style="--mh:${c.mh2 || 300}px" src="assets/car/big/${c.id}.webp" alt="${esc(nm(c))}" loading="eager" onerror="this.parentNode.style.display='none'"></div>
    <dl class="dstats">
      <div><dt>PI</dt><dd>${c.pi ?? "—"}</dd></div>
      <div><dt>马力</dt><dd>${nf(c.hp)}<span>hp</span></dd></div>
      <div><dt>扭矩</dt><dd>${nf(c.nm)}<span>N·m</span></dd></div>
      <div><dt>车重</dt><dd>${nf(c.kg)}<span>kg</span></dd></div>
      <div><dt>0–60</dt><dd>${Number(c.t60).toFixed(2)}<span>s</span></dd></div>
      <div><dt>极速</dt><dd>${nf(c.tsm)}<span>km/h</span></dd></div>
    </dl>
    ${tierOf(c) < 99 ? `<div class="dtier">
      <span class="dti"><img src="${tierImg(c)}" alt=""><span><b>竞速强度 ${esc(tierName(c))}</b>${esc(tierGroupOf(c))} · 改装等级</span></span>
      ${(TIER[String(c.id)] || []).slice(1).map(([ti, gi]) => `<span class="dti"><img src="assets/tier/${TIER_IMG[ti]}.png" alt=""><span><b>${esc(TIER_NAMES[ti])}</b>${esc(TIER_GROUPS[gi] || "")}</span></span>`).join("")}
    </div>` : ""}
    <div class="dfind">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg>
      <input id="dfilter" type="search" placeholder="在这台车的 151 项字段里找，例如 下压力" aria-label="筛选字段">
    </div>
    <label class="duni"><input type="checkbox" id="dUni" class="chk" checked>
      折叠全库统一数据 <b>${UNIFORM.size}</b></label>
    <div class="dact" id="dAct"></div>
    <section class="tunebox" id="dTune"></section>`;

  /* 字段分组不在这里渲染：改装件（引擎 / 宽体 / 轮胎）要先上，见下方 */

  const sw = SWAPS[String(c.id)] || [];
  if (sw.length) {
    const stock = sw.filter(r => r[5]);
    const rest = sw.filter(r => !r[5]);
    const row = (r, i) => {
      const [lvl, ename, donor, price, mass, isStock, hp, tor] = r;
      const src = isStock ? "原厂引擎" : (donor && byId.has(donor) ? nm(byId.get(donor)) : "—");
      return `<tr class="${isStock ? "isstock" : ""}" data-eid="${r[8] ?? ""}" data-ename="${esc(ename)}"${r[8] ? ' title="点击筛选使用这台引擎的车"' : ""}>
        <td><span class="lv">${isStock ? "原厂" : "Lv " + lvl}</span></td>
        <td class="wrap englink">${esc(ename)}${aspHTML(r[8] ?? "")}</td>
        <td class="src">${esc(src)}</td>
        <td>${hp ? nf(hp) : "—"}</td>
        <td>${tor ? nf(tor) : "—"}</td>
        <td>${isStock ? "—" : nf(price)}</td>
        <td>${isStock ? "—" : (mass > 0 ? "+" : "") + nf(mass)}</td></tr>`;
    };
    html += `<section class="sec"><h3><span>可选改装引擎</span><em>${sw.length} 项 · 含原厂</em></h3><div class="tirewrap">
      <table class="tire swp">
      <colgroup><col style="width:58px"><col style="width:142px"><col><col style="width:64px"><col style="width:70px"><col style="width:78px"><col style="width:70px"></colgroup>
      <thead><tr><th>等级</th><th class="wrap">引擎</th><th class="wrap">出处</th>
      <th>马力</th><th>扭矩</th><th>价格</th><th>质量差</th></tr></thead><tbody>
      ${stock.map(row).join("")}${rest.map(row).join("")}
      </tbody></table>
      <p class="hint">价格单位 CR，质量差为换装后相对原厂的变化（kg）；马力和扭矩为引擎台架值。点引擎名可筛出同款引擎的车。</p></div></section>`;
  }

  /* 宽体套件：除车宽外，前后轮距、轴距、离地高度和可用胎宽也会随车身变化，
     所以列是按「这套车身上真正发生变化的字段」动态生成的，没变化的列不占位。 */
  const wf = (DATA.wideFull || {})[String(c.id)];
  const wd = (DATA.wide || {})[String(c.id)] || [];
  if (wf && wf.k.length) {
    const OFFSET = 3;              // 套件行前三项：等级、价格、质量差
    const ALL = [
      { i: 0, n: "车宽", u: "m" }, { i: 1, n: "车长", u: "m" }, { i: 2, n: "车高", u: "m" },
      { i: 3, n: "轴距", u: "m" }, { i: 4, n: "前轮距", u: "m" }, { i: 5, n: "后轮距", u: "m" },
      { i: 6, n: "前离地", u: "m" }, { i: 7, n: "后离地", u: "m" },
      { i: 8, n: "最大前胎宽", u: "mm" }, { i: 9, n: "最大后胎宽", u: "mm" },
    ];
    const base = wf.s;
    /* 几何量 5 mm 以内、胎宽 0.5 mm 以内视为没变——数据里有 1 mm 级别的噪声 */
    const eps = c => (c.u === "mm" ? 0.5 : 0.005);
    let cols = ALL.filter(c => wf.k.some(r => Math.abs((r[OFFSET + c.i] || 0) - (base[c.i] || 0)) > eps(c)));
    const massCol = wf.k.some(r => Math.abs(r[2] || 0) > 0.01);
    /* 有些套件只换外观件，几何与胎宽全都一模一样：此时退回一组基准列，
       否则表里只剩「套件 / 价格」两列，看起来像数据没加载 */
    const noChange = cols.length === 0 && !massCol;
    if (cols.length === 0) cols = ALL.filter(c => [0, 4, 5, 8, 9].includes(c.i));
    const fmtCell = (cur, b, u) => {
      const d = cur - b;
      const val = u === "mm" ? Math.round(cur) : cur.toFixed(2);
      if (Math.abs(d) <= (u === "mm" ? 0.5 : 0.005)) return `${val}<i>—</i>`;
      const delta = u === "mm" ? Math.round(d) : (d * 100).toFixed(1);
      return `${val}<em>${d > 0 ? "+" : ""}${delta}</em>`;
    };
    const plain = (v, u) => (u === "mm" ? Math.round(v) : v.toFixed(2));
    const massCell = m => (Math.abs(m) > 0.01 ? `<em>${m > 0 ? "+" : ""}${m}</em>` : "—");
    html += `<section class="sec"><h3><span>宽体套件</span><em>${wd.length} 套可选</em></h3><div class="tirewrap">
      <table class="tire wbody">
      <thead><tr><th>套件</th><th>价格</th>${massCol ? "<th>质量</th>" : ""}${cols.map(c => `<th>${c.n}</th>`).join("")}</tr></thead><tbody>
      <tr class="stock"><td><span class="lv">原厂</span></td><td>—</td>${massCol ? "<td>—</td>" : ""}
        ${cols.map(c => `<td>${plain(base[c.i], c.u)}</td>`).join("")}</tr>
      ${wf.k.map((r, i) => `<tr>
        <td><span class="lv" title="游戏内等级 Lv ${r[0]}">#${i + 1}</span></td>
        <td>${nf(r[1])}</td>${massCol ? `<td>${massCell(r[2] || 0)}</td>` : ""}
        ${cols.map(c => `<td>${fmtCell(r[OFFSET + c.i], base[c.i], c.u)}</td>`).join("")}
      </tr>`).join("")}
      </tbody></table>
      <p class="hint">上排为原厂车身基准，下面每行是改装后的实测数值，小字为相对原厂的变化量
      （几何项 + 表示加宽/加长，单位 cm；胎宽 + 表示该车身可用的最大胎宽提高，单位 mm；质量为 kg）。${
        noChange ? "该套件只改外观件，车身尺寸、胎宽上限与原厂完全一致。" : ""}</p></div></section>`;
  }

  const ts = DATA.tires[String(c.id)] || [];
  if (ts.length) {
    const at = (cv, n) => { const i = DATA.curveSchema.findIndex(s => s.n === n); return i < 0 || !cv ? "—" : cv[i]; };
    html += `<section class="sec"><h3><span>可选轮胎配方</span><em>${ts.length} 档</em></h3><div class="tirewrap">
      <table class="tire"><thead><tr><th>档位</th><th class="wrap">配方</th><th class="wrap">干胎型号</th><th>前 / 后胎压</th><th>价格</th><th>侧向峰值</th><th>纵向峰值</th><th>平台</th><th>末端</th></tr></thead><tbody>`;
    ts.forEach(t => {
      const [lv, cid, model, , fp, rp, price, stk] = t;
      const cv = DATA.curves[String(cid)] || [];
      html += `<tr data-curve="${cid}">
        <td><span class="lv">${lv}</span>${stk ? '<span class="stk">原厂</span>' : ""}</td>
        <td class="wrap">${esc(prettyCompound(DATA.curveName[String(cid)] || cid))}</td>
        <td class="wrap" style="color:var(--steel)">${esc(String(model || "—").replace(/_/g, " "))}</td>
        <td>${fp}/${rp}</td>
        <td>${nf(price)}</td>
        <td>${at(cv, "Asph_LatSlipPeak1")}°</td>
        <td>${at(cv, "Asph_LongSlipPeak1")}%</td>
        <td>${at(cv, "Asph_LatFlat1")}</td>
        <td>${at(cv, "Asph_LatEnd1")}</td></tr>`;
    });
    html += `</tbody></table><p class="hint">点任意一行查看该配方的完整 92 项曲线参数<span class="only-m"> · 表格可左右滑动</span></p></div></section>`;
  }

  /* 线上分级明细：一台车可能出现在多张分级表里，逐行列出驱动/难度/轮胎/定位/备注 */
  const trs = rowsOf(c);
  if (trs.length) {
    html += `<section class="sec"><h3><span>线上强度分级</span><em>${trs.length} 个组别</em></h3><div class="tirewrap">
      <table class="tire ttune"><thead><tr>
        <th>强度</th><th>性能组别</th><th>驱动</th><th>难度</th><th>轮胎</th><th>定位</th><th class="nt">备注</th>
      </tr></thead><tbody>
      ${trs.map(r => `<tr>
        <td><img class="tbadge" src="assets/tier/${TIER_IMG[r[0]]}.png" alt="${esc(TIER_NAMES[r[0]])}"></td>
        <td>${esc(TIER_GROUPS[r[1]] || "—")}</td>
        <td>${esc(r[2] || "—")}</td><td>${esc(r[3] || "—")}</td>
        <td>${esc(r[4] || "—")}</td><td>${esc(r[5] || "—")}</td>
        <td class="nt">${esc(r[6] || "—")}</td></tr>`).join("")}
      </tbody></table>
      <p class="hint">同一台车若在不同改装等级下都有推荐，会分多行列出；备注为原表作者对该调校的说明。</p></div></section>`;
  }

  /* 空气动力学套件：尾翼改装的阻力/下压力曲线（List_UpgradeRearWing + List_AeroPhysics） */
  const ae = (DATA.aero || {})[String(c.id)];
  if (ae && ae.k.length) {
    const num = v => (v === null || v === undefined ? 0 : Number(v));
    const pair = (a, b) => (Math.abs(a) < 1e-9 && Math.abs(b) < 1e-9
      ? "—" : `${num(a).toFixed(1)} <i>→</i> ${num(b).toFixed(1)}`);
    const dsCell = (v) => {
      const d = (num(v) - 1) * 100;
      return `×${num(v).toFixed(3)}${Math.abs(d) < 0.05 ? "" : `<em>${d > 0 ? "+" : ""}${d.toFixed(1)}%</em>`}`;
    };
    const st = ae.s;
    const rowOf = (r, stock) => `<tr class="${stock ? "isstock" : ""}">
        <td><span class="lv">${stock ? "原厂" : "Lv " + r[0]}</span></td>
        <td>${stock ? "—" : nf(r[1])}</td>
        <td>${stock ? "—" : (r[2] > 0 ? "+" : "") + num(r[2]).toFixed(1)}</td>
        <td>${dsCell(r[3])}</td>
        <td>${num(r[4]).toFixed(2)}</td>
        <td>${pair(r[7], r[8])}</td>
        <td>${pair(r[5], r[6])}</td>
        <td>${num(r[9]).toFixed(1)}<i>°</i></td></tr>`;
    html += `<section class="sec"><h3><span>空气动力学套件</span><em>${ae.k.length} 档可选</em></h3><div class="tirewrap">
      <table class="tire swp awing">
      <thead><tr><th>套件</th><th>价格</th><th>质量</th><th>风阻缩放</th><th>稳定性</th>
      <th>下压力<em>低 → 高攻角</em></th><th>空气阻力<em>低 → 高攻角</em></th><th>零攻角</th></tr></thead><tbody>
      ${st ? rowOf(st, true) : ""}${ae.k.map(r => rowOf(r, false)).join("")}
      </tbody></table>
      <p class="hint">下压力与空气阻力取自 List_AeroPhysics，是尾翼攻角滑杆两端的标定值；
      风阻缩放为该套件对整车风阻的乘数（&lt;1 表示更省风），稳定性数值越低越不易被侧风扰动。</p></div></section>`;
  }

  /* 车辆悬挂：前后结构 / 转向手感 / 后轮转向（支持的车型才出标签块） */
  const spx = (DATA.susp || {})[String(c.id)];
  if (spx) {
    const sf = suspName(spx.f) || {raw: "—", cn: ""};
    const sr = suspName(spx.r) || {raw: "—", cn: ""};
    const ss = (DATA.steerSet || {})[String(spx.st)];
    const rs = spx.rs ? (DATA.rearSteer || {})[String(spx.rs)] : null;
    html += `<section class="sec"><h3><span>车辆悬挂</span><em>${
      rs ? "支持后轮转向" : "常规悬挂"}</em></h3><div class="grid2">
      <div class="kv"><span>前悬挂结构</span><b>${esc(sf.cn || sf.raw)}${sf.cn ? ` <i>${esc(sf.raw)}</i>` : ""}</b></div>
      <div class="kv"><span>后悬挂结构</span><b>${esc(sr.cn || sr.raw)}${sr.cn ? ` <i>${esc(sr.raw)}</i>` : ""}</b></div>
      <div class="kv"><span>转向手感配置</span><b>${esc(STEER_CN[ss && ss.n] || (ss && ss.n) || "—")}${
        ss ? ` <i>${esc(String(ss.n).replace(/_/g, " "))}</i>` : ""}</b></div>
      <div class="kv"><span>最大前轮转角</span><b>${spx.a ?? "—"}<em>°</em></b></div>
    </div>`;
    if (rs) {
      html += `<div class="rsteer">
        <div class="rh"><span class="tag">后轮转向</span><em>${esc(RS_CN[rs.n] || rs.n)} · ${esc(rs.n)}</em></div>
        <div class="kv"><span>后轮转角比例</span><b>前轮 × ${rs.frac}</b></div>
        <div class="kv"><span>反打时后轮转向</span><b>${rs.cs > 0 ? "允许" : "不介入"}</b></div>
        <div class="kv"><span>低速介入车速</span><b>${rs.ls} m/s<em>${Math.round(rs.ls * 3.6)} km/h</em></b></div>
        <div class="kv"><span>高速介入车速</span><b>${rs.hs} m/s<em>${Math.round(rs.hs * 3.6)} km/h</em></b></div>
      </div>`;
    }
    html += `</section>`;
  }

  /* 主动驾驶模式：只有少数车型配了这套配置，列出会调整的系统与具体数值 */
  const dm = (DATA.driveMode || {})[String(c.id)];
  if (dm) {
    const mods = (dm.mods || []).map(k => MOD_CN[k] || k).join(" · ");
    /* 前后成对排列，读起来能直接对比（前离地 / 后离地、前弹簧 / 后弹簧） */
    const OV_ORDER = ["FrontRideHeight", "RearRideHeight", "FrontSpringK", "RearSpringK",
                      "TCProfileID", "DriveType", "RearTorqueSplit",
                      "DampenBumpRate", "DampenReboundRate"];
    const OV_UNIT = {FrontRideHeight: "m", RearRideHeight: "m"};
    const ovs = Object.keys(dm.ov || {})
      .map(k => [k.replace(/_Override$/, ""), dm.ov[k]])
      .sort((a, b) => {
        const ia = OV_ORDER.indexOf(a[0]), ib = OV_ORDER.indexOf(b[0]);
        return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
      });
    html += `<section class="sec"><h3><span>主动驾驶模式</span><em>可切换</em></h3>
      <div class="grid2">
        <div class="kv kv--wide"><span>调整的系统</span><b>${esc(mods || "—")}</b></div>
        ${dm.drag ? `<div class="kv"><span>风阻系数</span><b>×${dm.drag}</b></div>` : ""}
        ${dm.df ? `<div class="kv"><span>下压力系数</span><b>×${dm.df}</b></div>` : ""}
        ${dm.dof ? `<div class="kv"><span>越野下压力系数</span><b>×${dm.dof}</b></div>` : ""}
        ${ovs.map(([n, v]) => `<div class="kv"><span>${esc(OV_CN[n] || n)}</span><b>${
          esc(String(v))}${OV_UNIT[n] ? `<em>${OV_UNIT[n]}</em>` : ""}</b></div>`).join("")}
      </div>
      <p class="hint">切换模式时上述参数会整体套用到该车，未列出的项目保持原厂设定。</p>
    </section>`;
  }

  /* 剩下的原始字段放在改装件之后；这 6 项是调校时真正会看的标定值，数值加粗 */
  const KEY_FIELDS = new Set([
    "GameTorqueScale", "GameDragScale",
    "Traction_Road", "Traction_OffRoad", "Traction_Snow",
    "BodyAeroLongitudinalDrag",
  ]);
  GROUPS.forEach((g, gi) => {
    if (!secs[gi].length) return;
    html += `<section class="sec" data-n="${secs[gi].length}"><h3><span>${g.replace(/^[①-⑫]\s*/, "")}</span><em>${secs[gi].length} 项</em></h3><div class="grid2">`;
    secs[gi].forEach(([f, v]) => {
      const key = KEY_FIELDS.has(f.n);
      /* 全库统一取值的字段默认折叠，省出空间给真正有差异的数据 */
      const uni = UNIFORM.has(f.n) ? " uni" : "";
      html += `<div class="kv${key ? " kv--key" : ""}${uni}" data-k="${esc(f.cn)}${esc(f.n)}" title="${esc(f.d || "")}">
        <span>${esc(f.cn)}</span><b>${fmtField(f, v)}${f.s && f.s !== "—" ? `<em>${esc(f.s)}</em>` : ""}</b></div>`;
    });
    /* 「质量、轮胎与尺寸」末尾补四行改装胎宽上限：胎宽档位挂在车身上，
       不属于 151 项原始字段，所以单独拼进这个网格 */
    if (/质量、轮胎与尺寸/.test(g)) {
      const tw = (DATA.tireW || {})[String(c.id)] || {};
      [["改装最大前胎宽", tw.sf], ["改装最大后胎宽", tw.sr],
       ["宽体后最大前胎宽", tw.wf], ["宽体后最大后胎宽", tw.wr]].forEach(([n, v]) => {
        html += `<div class="kv kv--key" data-k="${esc(n)}"><span>${esc(n)}</span><b>${
          v > 0 ? `${v}<em>mm</em>` : "—"}</b></div>`;
      });
    }
    html += `</div></section>`;
  });

  const da = $("dAdd");
  const syncAdd = () => {
    const on = S.sel.has(c.id);
    da.classList.toggle("on", on);
    da.setAttribute("aria-pressed", on);
    da.querySelector("span").textContent = on ? "已加入比对" : "加入比对";
    da.querySelector("svg").innerHTML = on
      ? '<path d="M5 12.5l4.5 4.5L19 7"/>'
      : '<path d="M12 5v14M5 12h14"/>';
  };
  da.onclick = () => { toggleSel(c.id); syncAdd(); };
  syncAdd();

  $("dBody").innerHTML = html;
  /* 折叠全库统一字段：勾选时把 .kv.uni 隐掉，整段都被隐掉的分组直接不显示，
     分组标题上的「N 项」跟着可见条数走，避免数字和内容对不上 */
  const applyUni = () => {
    const box = $("dUni");
    const on = !box || box.checked;
    document.querySelectorAll("#dBody .kv.uni").forEach(el => el.classList.toggle("off", on));
    document.querySelectorAll("#dBody section.sec[data-n]").forEach(sec => {
      const all = [...sec.querySelectorAll(".kv")];
      const vis = all.filter(el => !el.classList.contains("off") && !el.classList.contains("hide"));
      sec.classList.toggle("sec--empty", all.length > 0 && vis.length === 0);
      const em = sec.querySelector("h3 em");
      if (em) em.textContent = `${vis.length} / ${sec.dataset.n} 项`;
    });
  };
  const uniBox = $("dUni");
  if (uniBox) uniBox.onchange = applyUni;
  applyUni();
  renderSocial(c);
  paintDrift(c);
  /* 调校区改为常显：改成 section 后没有 toggle 事件，这里直接渲染 */
  renderTunes(c);
  $("dBody").scrollTop = 0;
  drawer.classList.add("on"); scrim.classList.add("on");
  drawer.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
  $("btnClose").focus({preventScroll: true});

  const df = $("dfilter");
  if (df) df.oninput = e => {
    const s = e.target.value.trim().toLowerCase();
    document.querySelectorAll("#dBody .kv").forEach(el => {
      el.classList.toggle("hide", !!s && !el.dataset.k.toLowerCase().includes(s));
    });
    applyUni();
  };
}

function closeCar() {
  drawer.classList.remove("on"); scrim.classList.remove("on");
  drawer.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}
$("btnClose").onclick = closeCar;
scrim.onclick = () => { closeCar(); closeModals(); };
$("dBody").addEventListener("click", e => {
  const eng = e.target.closest("tr[data-eid]");
  if (eng && eng.dataset.eid) {
    S.eng = String(eng.dataset.eid);
    S.engName = eng.dataset.ename || "";
    closeCar();
    apply();
    document.getElementById("catalogue").scrollIntoView({ behavior: "smooth" });
    return;
  }
  const tr = e.target.closest("tr[data-curve]");
  if (tr) openCurves(+tr.dataset.curve);
});

/* ── 比对 ─────────────────────────────────────────── */

/* 详情页里那些不在 151 项原始字段中的信息（增压升级、宽体、胎宽上限、悬挂、后轮转向、
   主动驾驶模式），比对表补一组固定行放在最前。num 行参与「更优」下划线高亮。 */
const twOf = c => (DATA.tireW || {})[String(c.id)] || {};
const spOf = c => (DATA.susp || {})[String(c.id)];
const CMP_EXTRA = [
  { n: "原厂引擎增压", html: c => {
      const st = (SWAPS[String(c.id)] || []).find(r => r[5]);
      return (st && aspHTML(st[8])) || "—";
    } },
  { n: "宽体套件", html: c => {
      const wd = (DATA.wide || {})[String(c.id)] || [];
      if (!wd.length) return "—";
      const mx = Math.max(...wd.map(r => Number(r[2]) || 0));
      return `${wd.length} 套${mx > 0 ? ` <i>最宽 +${mx} cm</i>` : ""}`;
    } },
  { n: "改装最大前胎宽", num: c => twOf(c).sf, unit: "mm", max: true },
  { n: "改装最大后胎宽", num: c => twOf(c).sr, unit: "mm", max: true },
  { n: "宽体后最大前胎宽", num: c => twOf(c).wf, unit: "mm", max: true },
  { n: "宽体后最大后胎宽", num: c => twOf(c).wr, unit: "mm", max: true },
  { n: "前悬挂结构", html: c => {
      const sp = spOf(c), s = sp && suspName(sp.f);
      if (!s) return "—";
      return `${esc(s.cn || s.raw)}${s.cn ? ` <i>${esc(s.raw)}</i>` : ""}`;
    } },
  { n: "后悬挂结构", html: c => {
      const sp = spOf(c), s = sp && suspName(sp.r);
      if (!s) return "—";
      return `${esc(s.cn || s.raw)}${s.cn ? ` <i>${esc(s.raw)}</i>` : ""}`;
    } },
  { n: "转向手感配置", html: c => {
      const sp = spOf(c), ss = sp && (DATA.steerSet || {})[String(sp.st)];
      if (!ss) return "—";
      return `${esc(STEER_CN[ss.n] || ss.n)} <i>${esc(String(ss.n).replace(/_/g, " "))}</i>`;
    } },
  { n: "最大前轮转角", num: c => Number((spOf(c) || {}).a || 0), unit: "°", max: true },
  { n: "后轮转向", html: c => {
      const sp = spOf(c);
      const rs = sp && sp.rs ? (DATA.rearSteer || {})[String(sp.rs)] : null;
      if (!rs) return "—";
      return `支持 <i>${esc(RS_CN[rs.n] || rs.n)} · 前轮 ×${rs.frac} · 介入 ${rs.ls}/${rs.hs} m/s</i>`;
    } },
  { n: "主动驾驶模式", html: c => {
      const dm = (DATA.driveMode || {})[String(c.id)];
      if (!dm) return "—";
      const mods = (dm.mods || []).map(k => MOD_CN[k] || k).join(" · ");
      return `支持${mods ? ` <i>${esc(mods)}</i>` : ""}`;
    } },
];

function openCompare() {
  const ids = [...S.sel];
  if (ids.length < 2) { $("selbar").classList.add("on"); return; }
  const list = ids.map(id => cars.find(c => c.id === id)).filter(Boolean);
  $("cmpInfo").textContent = `已选 ${list.length} 台 · 全量字段 · 下划线标出这一项更优的车`;
  document.querySelector("#cmpTbl thead").innerHTML = `<tr><th>字段</th>${list.map(c => {
    return `<th><b>${esc(nm(c))}</b><em>${c.year} · ${c.cls} 级 · PI ${c.pi}</em></th>`;
  }).join("")}</tr>`;

  let exRows = `<tr class="gth"><td colspan="${list.length + 1}">改装与底盘</td></tr>`;
  CMP_EXTRA.forEach(r => {
    const nums = r.num ? list.map(c => Number(r.num(c)) || 0) : null;
    let win = -1;
    if (nums && r.max) {
      const mx = Math.max(...nums);
      if (mx > 0 && mx !== Math.min(...nums)) win = nums.indexOf(mx);
    }
    exRows += `<tr><td class="f">${esc(r.n)}</td>` + list.map((c, i) =>
      `<td class="${i === win ? "win" : ""}"><span>${
        nums ? (nums[i] > 0 ? `${nums[i]}${r.unit ? `<em>${r.unit}</em>` : ""}` : "—") : r.html(c)
      }</span></td>`).join("") + `</tr>`;
  });

  const MAX = DATA.betterMax, MIN = DATA.betterMin;
  /* 默认就是全量字段：不再提供「精简 / 全部 151 项」切换 */
  const pick = FULL.filter(f =>
    !["DisplayName", "ModelShort", "MakeName", "MediaName", "Thumbnail", "MakeIcon"].includes(f.n));

  let rows = "", lastG = -1;
  pick.forEach(f => {
    if (f.g !== lastG) {
      rows += `<tr class="gth"><td colspan="${list.length + 1}">${GROUPS[f.g].replace(/^[①-⑫]\s*/, "")}</td></tr>`;
      lastG = f.g;
    }
    const k = FI[f.n];
    const vals = list.map(c => FROWS[c._i][k]);
    let win = -1;
    if (vals.length > 1 && vals.every(v => typeof v === "number")) {
      const mx = Math.max(...vals), mn = Math.min(...vals);
      if (mx !== mn) {
        if (MAX.includes(f.n)) win = vals.indexOf(mx);
        else if (MIN.includes(f.n)) win = vals.indexOf(mn);
      }
    }
    const tds = vals.map((v, i) => `<td class="${i === win ? "win" : ""}"><span>${fmtField(f, v)}${f.s && f.s !== "—" ? `<u>${esc(f.s)}</u>` : ""}</span></td>`).join("");
    rows += `<tr><td class="f">${esc(f.cn)}<em>${esc(f.n)}</em></td>${tds}</tr>`;
  });
  document.querySelector("#cmpTbl tbody").innerHTML = exRows + rows;
  $("cmp").classList.add("on");
  document.body.style.overflow = "hidden";
}
$("btnCompare").onclick = openCompare;
$("heroCompare").onclick = () => {
  if (S.sel.size >= 2) openCompare();
  else { document.getElementById("catalogue").scrollIntoView({behavior: "smooth"}); }
};
$("navCompare").onclick = () => $("heroCompare").click();
$("btnCmpClose").onclick = () => { $("cmp").classList.remove("on"); document.body.style.overflow = ""; };

/* ── 弹层 ─────────────────────────────────────────── */
const cmpsel = $("cmpSel");
Object.keys(DATA.curveName).sort((a, b) => +a - +b)
  .forEach(id => cmpsel.insertAdjacentHTML("beforeend", `<option value="${id}">${esc(DATA.curveName[id])}</option>`));

function renderCurve(id) {
  const cv = DATA.curves[String(id)] || [];
  $("cBody").innerHTML = `<div class="grid2">` + DATA.curveSchema.map((s, i) =>
    `<div class="kv"><span>${esc(s.cn)}<em>${s.n}</em></span><b>${fmt(cv[i])}</b></div>`).join("") + `</div>`;
}
cmpsel.onchange = e => renderCurve(e.target.value);

function openCurves(id) {
  const p = String(id ?? Object.keys(DATA.curveName)[0]);
  cmpsel.value = p; renderCurve(p);
  closeCar();
  $("curves").classList.add("on"); scrim.classList.add("on");
  document.body.style.overflow = "hidden";
}
$("btnCClose").onclick = closeModals;

const G = DATA.glossary;
$("gCount").textContent = `${G.length} 条`;
function renderG(q = "") {
  const s = q.trim().toLowerCase();
  $("gBody").innerHTML = G.filter(r =>
    !s || r[1].toLowerCase().includes(s) || (r[2] || "").toLowerCase().includes(s) || (r[4] || "").toLowerCase().includes(s)
  ).map(r => {
    const u = String(r[3] || "—"), i = u.indexOf("（");
    const unit = i > 0 ? `${u.slice(0, i)}<em>${u.slice(i)}</em>` : u;
    return `<tr><td class="t">${r[0]}</td><td class="k">${r[1]}</td>
      <td class="cn">${r[2] || "—"}</td><td class="t">${unit}</td><td>${r[4] || ""}</td></tr>`;
  }).join("");
}
function openGlossary() {
  renderG();
  $("glossary").classList.add("on"); scrim.classList.add("on");
  document.body.style.overflow = "hidden";
}
$("btnGClose").onclick = closeModals;
$("gq").oninput = e => renderG(e.target.value);
$("navGlossary").onclick = openGlossary;

/* ── 网站说明（独立弹窗） ─────────────────────────── */
function openAbout() {
  closeCar();
  $("about").classList.add("on"); scrim.classList.add("on");
  document.body.style.overflow = "hidden";
}
$("heroAbout").onclick = openAbout;
$("btnAboutClose").onclick = closeModals;

function closeModals() {
  $("glossary").classList.remove("on");
  $("curves").classList.remove("on");
  $("about").classList.remove("on");
  $("cmp").classList.remove("on");
  scrim.classList.remove("on");
  if (!drawer.classList.contains("on")) document.body.style.overflow = "";
}

/* ── 更多菜单 ─────────────────────────────────────── */
const moreBtn = $("moreBtn"), moreMenu = $("moreMenu");
moreBtn.onclick = e => {
  e.stopPropagation();
  const on = moreMenu.classList.toggle("on");
  moreBtn.setAttribute("aria-expanded", on);
};
moreMenu.addEventListener("click", e => {
  const b = e.target.closest("[data-act]"); if (!b) return;
  moreMenu.classList.remove("on"); moreBtn.setAttribute("aria-expanded", "false");
  const act = b.dataset.act;
  if (act === "curves") openCurves();
  if (act === "glossary") openGlossary();
  if (act === "about") openAbout();
  if (act === "compare") { if (S.sel.size >= 2) openCompare(); else document.getElementById("catalogue").scrollIntoView({behavior: "smooth"}); }
});
document.addEventListener("click", () => { moreMenu.classList.remove("on"); moreBtn.setAttribute("aria-expanded", "false"); });
document.querySelectorAll('.foot [data-act]').forEach(b => b.onclick = () => {
  const a = b.dataset.act;
  if (a === "curves") openCurves();
  if (a === "glossary") openGlossary();
  if (a === "about") openAbout();
  if (a === "compare") { if (S.sel.size >= 2) openCompare(); else document.getElementById("catalogue").scrollIntoView({behavior: "smooth"}); }
});

/* ── 键盘 ─────────────────────────────────────────── */
document.addEventListener("keydown", e => {
  if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
    e.preventDefault(); $("q").focus();
  }
  if (e.key === "Escape") {
    if (drawer.classList.contains("on")) closeCar();
    closeModals();
  }
});

/* ── 工具条高度 → 表头吸附位置 ─────────────────────── */
/* 合并 dt/cp 为单列 acq，省下的宽度全部让给车名列；980 以下改收起引擎列，
   让「车辆获取方式」在所有断点都可见，同时车名列不会窄到放不下名字。 */
const TW = {pick:46,yr:56,cls:52,pi:70,hp:66,tq:62,kg:66,pwr:64,t60:62,tsm:64,latg:58,brk:54,drv:54,eng:134,acq:136};
const TORDER = ["pick","yr","nm","cls","pi","hp","tq","kg","pwr","t60","tsm","latg","brk","drv","eng","acq"];
const THIDE = {1:["latg","brk"], 2:["latg","brk","tq","kg","pwr"], 3:["latg","brk","tq","kg","pwr","drv","eng"]};

function syncTable() {
  const w = innerWidth;
  const tier = w <= 980 ? 3 : w <= 1180 ? 2 : w <= 1360 ? 1 : 0;
  const off = THIDE[tier] || [];
  const tbl = $("tbl");
  tbl.dataset.tier = tier;
  /* 分组表头的 colspan 必须跟着可见列走，否则窄屏下会按原始列数把表格撑宽 */
  tbl.querySelectorAll("tr.grp th[data-cols]").forEach(th => {
    const n = th.dataset.cols.split(",").filter(k => !off.includes(k)).length;
    th.style.display = n ? "" : "none";
    if (n) th.colSpan = n;
  });
  /* 用容器的宽度算车名列，别用表格自身（表格溢出时会自洽地算错） */
  const box = tbl.parentElement || tbl;
  const avail = box.clientWidth || tbl.clientWidth;
  const fixed = TORDER.filter(k => k !== "nm" && !off.includes(k)).reduce((a, k) => a + TW[k], 0);
  const nmW = avail ? Math.max(180, avail - fixed) : 320;
  tbl.querySelector("colgroup").innerHTML = TORDER.filter(k => !off.includes(k))
    .map(k => `<col style="width:${k === "nm" ? nmW : TW[k]}px">`).join("");
}

function syncBar() {
  syncTable();
  const h = $("bar").offsetHeight;
  document.documentElement.style.setProperty("--barh", h + "px");
}
window.addEventListener("resize", syncBar);

/* ── 初始化 ───────────────────────────────────────── */
$("npcN").textContent = DATA.meta.npc || 0;
applyLang(localStorage.getItem(LANG_KEY) || DEFAULT_LANG, false);
renderGallery();
setTheme(localStorage.getItem(THEME_KEY) || document.documentElement.dataset.theme || DEFAULT_THEME, false);
apply();
syncBar();

/* 简繁开关指向的是同目录下的另一份页面（部署包里有），本地双击单个 HTML 时
   没有这个文件，直接收起来，避免点了 404。 */
if (!/^https?:$/.test(location.protocol)) {
  const ds = $("docSwitch");
  if (ds) ds.hidden = true;
}

const m = location.hash.match(/id=(\d+)/); if (m) setTimeout(() => openCar(+m[1]), 80);
const cm = location.hash.match(/cmp=([\d,]+)/);
if (cm) {
  cm[1].split(",").forEach(x => { if (!S.sel.has(+x)) toggleSel(+x, true); });
}
if (location.hash === "#fields") setTimeout(openGlossary, 100);
if (location.hash.startsWith("#curves")) { const cid = location.hash.split("=")[1]; setTimeout(() => openCurves(cid ? +cid : undefined), 100); }
if (location.hash === "#table") setTimeout(() => setView("table"), 60);
/* ── 玩家账号 / 收藏 / 评分 / 调校 ─────────────────────
   接口见 server/server.mjs；同源部署时 API_BASE 留空即可。
   服务端不可用时整块静默降级，站点核心功能（查车）不受影响。 */
const API_BASE = window.__FH6_API__ || "";
let ME = null;
const SOCIAL = {};                 // carId -> {fav, owned, wish, votes, avg}
const MY = { garage: new Map(), ratings: new Map() };
const OVR = {};                        // 后台改过的分级：carId -> {race_tier, race_group, drift_tier}

async function api(path, opt = {}) {
  const res = await fetch(API_BASE + path, {
    credentials: "include",
    ...opt,
    headers: { "Content-Type": "application/json", "X-CSRF": "1", ...(opt.headers || {}) },
  });
  if (!res.ok) throw Object.assign(new Error("HTTP " + res.status), { status: res.status });
  return res.json();
}

let API_OK = true;
async function bootAuth() {
  try { ME = await api("/api/me"); } catch { ME = null; API_OK = false; }
  if (ME) {
    try {
      const g = await api("/api/garage");
      g.garage.forEach(x => MY.garage.set(String(x.car_id), x.state));
      g.ratings.forEach(x => MY.ratings.set(String(x.car_id), x.score));
    } catch { /* 忽略：只影响「我的」状态 */ }
  }
  syncFavN();
  await refreshTiers();
  paintAuth();
  loadStats();
}

/* 分级覆盖：后台改完后必须重绘卡片，否则页面还是构建时烘焙的静态分级 */
async function refreshTiers() {
  try {
    const t = await api("/api/tiers");
    const list = t.overrides || [];
    Object.keys(OVR).forEach(k => delete OVR[k]);
    list.forEach(o => { OVR[String(o.car_id)] = o; });
    window.__ovrAt = Date.now();
    if (list.length) apply();   // 没有覆盖就不必重绘，静态分级已经画好了
  } catch { /* 接口不可用时沿用静态分级 */ }
}

/* 切回标签页时（间隔 > 60 秒）重新拉一次分级，管理员改完不用等缓存过期 */
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState !== "visible") return;
  if (Date.now() - (window.__ovrAt || 0) < 60000) return;
  refreshTiers(false);
});

async function loadStats() {
  const ids = cars.map(c => c.id);
  for (let i = 0; i < ids.length; i += 300) {
    try {
      const r = await api("/api/stats?ids=" + ids.slice(i, i + 300).join(","));
      Object.assign(SOCIAL, r.stats || {});
    } catch { return; }
  }
  paintStats();
}

function paintStats() {
  document.querySelectorAll(".car").forEach(el => {
    const s = SOCIAL[el.dataset.id];
    const box = el.querySelector(".csoc");
    if (!box) return;
    if (!s || (!s.fav && !s.votes)) { box.textContent = ""; return; }
    box.textContent = (s.fav ? "★ " + s.fav : "") + (s.votes ? (s.fav ? " · " : "") + s.avg.toFixed(1) + "★" : "");
  });
}

function paintAuth() {
  const b = $("navAuth");
  if (!b) return;
  if (!API_OK) { b.hidden = true; return; }
  if (!ME || !ME.user || !ME.user.logged_in) { b.textContent = "登录"; b.onclick = () => openLogin(); return; }
  const admin = ME.user.is_admin;
  b.textContent = admin ? "管理员" : (ME.user.is_display_name || ME.user.display_name || "我的");
  b.onclick = () => (admin ? (location.href = "admin.html") : openLogin());
}

function openLogin() {
  if (document.getElementById("loginBox")) return;
  const box = document.createElement("div");
  box.id = "loginBox";
  box.innerHTML = `<div class="lb-card">
      <h3>同步你的收藏</h3>
      <p>注册或登录后，收藏、评分与调校会跟账号绑定。</p>
      <div class="lb-tabs"><button data-tab="login" class="on">登录</button><button data-tab="register">注册</button></div>
      <div class="row"><input id="lbEmail" type="email" autocomplete="email" placeholder="you@example.com"></div>
      <div class="row"><input id="lbPw" type="password" autocomplete="current-password" placeholder="密码（至少 8 位）"></div>
      <div class="row" id="lbNameRow" hidden><input id="lbName" type="text" autocomplete="nickname" maxlength="40" placeholder="昵称（可选）"></div>
      <div class="row"><button id="lbGo">登录</button><button id="lbClose" class="ghost">稍后再说</button></div>
      <div class="row"><a class="lb-steam" href="${API_BASE}/auth/steam/start?next=${encodeURIComponent(location.pathname + location.search)}">使用 Steam 登录</a></div>
      <p class="lb-msg" id="lbMsg"></p>
    </div>`;
  document.body.appendChild(box);

  let mode = "login";
  const close = () => box.remove();
  box.addEventListener("click", e => { if (e.target === box) close(); });
  $("lbClose").onclick = close;

  box.querySelectorAll(".lb-tabs button").forEach(b => {
    b.onclick = () => {
      mode = b.dataset.tab;
      box.querySelectorAll(".lb-tabs button").forEach(x => x.classList.toggle("on", x === b));
      $("lbNameRow").hidden = mode !== "register";
      $("lbGo").textContent = mode === "register" ? "注册" : "登录";
      $("lbPw").autocomplete = mode === "register" ? "new-password" : "current-password";
      $("lbMsg").textContent = "";
    };
  });

  $("lbGo").onclick = async () => {
    const email = $("lbEmail").value.trim();
    const password = $("lbPw").value;
    const msg = $("lbMsg");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { msg.textContent = "邮箱格式不对"; return; }
    if (password.length < 8) { msg.textContent = "密码至少 8 位"; return; }
    msg.textContent = mode === "register" ? "注册中…" : "登录中…";
    $("lbGo").disabled = true;
    try {
      const body = { email, password };
      if (mode === "register") body.name = $("lbName").value.trim();
      await api(mode === "register" ? "/api/auth/register" : "/api/auth/login", {
        method: "POST", body: JSON.stringify(body)
      });
      location.reload();
    } catch (e) {
      $("lbGo").disabled = false;
      msg.textContent = e.status === 409 ? "该邮箱已注册，请直接登录"
        : e.status === 401 ? "邮箱或密码不正确"
        : e.status === 429 ? "尝试过于频繁，请稍后再试"
        : "操作失败，请稍后重试";
    }
  };
}

function renderSocial(c) {
  const box = $("dAct");
  if (!box) return;
  const id = String(c.id);
  const s = SOCIAL[id] || { fav: 0, votes: 0, avg: 0 };
  const fav = MY.garage.get(id) === "favorite";
  const myScore = MY.ratings.get(id) || 0;
  const canRate = ME && !ME.user.is_anonymous;
  box.innerHTML = `
    <button class="afav" id="dFav" aria-pressed="${fav}">★ <span>${fav ? "已收藏" : "收藏"}</span><b>${s.fav || 0}</b></button>
    <span class="arate" id="dRate" title="${canRate ? "点击评分" : "登录后可评分"}">
      ${[1, 2, 3, 4, 5].map(i => `<button data-s="${i}" class="${myScore >= i ? "on" : ""}" aria-label="${i} 星">★</button>`).join("")}
    </span>
    <span class="astat">${s.votes ? `<b>${s.avg.toFixed(1)}</b> · ${s.votes} 人评分` : "暂无评分"}</span>
    ${!canRate ? `<span class="alogin" id="dLoginTip">登录后可评分 / 上传调校</span>` : ""}
    ${ME && ME.user.is_admin ? `<a class="alogin" href="admin.html">分级后台</a>` : ""}`;

  $("dFav").onclick = async () => {
    if (!ME || !ME.user.logged_in) return openLogin();
    const now = MY.garage.get(id) === "favorite";
    try {
      if (now) { await api("/api/garage/" + id, { method: "DELETE" }); MY.garage.delete(id); s.fav = Math.max(0, (s.fav || 0) - 1); }
      else { await api("/api/garage/" + id, { method: "PUT", body: JSON.stringify({ state: "favorite" }) }); MY.garage.set(id, "favorite"); s.fav = (s.fav || 0) + 1; }
      SOCIAL[id] = s;
      renderSocial(c); paintStats(); syncFavN();
      if (S.fav) apply();
    } catch { alert("操作失败，请稍后再试"); }
  };
  $("dRate").querySelectorAll("button").forEach(b => {
    b.onclick = async () => {
      if (!canRate) return openLogin();
      try {
        const r = await api("/api/ratings/" + id, { method: "PUT", body: JSON.stringify({ score: +b.dataset.s }) });
        MY.ratings.set(id, +b.dataset.s);
        Object.assign(s, { votes: r.votes, avg: r.avg });
        SOCIAL[id] = s;
        renderSocial(c); paintStats();
      } catch { alert("评分失败，请稍后再试"); }
    };
  });
  const tip = $("dLoginTip");
  if (tip) tip.onclick = openLogin;
}

/* 漂移分级：只有后台配过才显示，用独立的 S/A/B/C/D 徽章 */
function paintDrift(c) {
  const o = OVR[String(c.id)];
  if (!o) return;
  /* 后台改过的竞速分级优先于静态表 */
  if (o.race_tier && TIER_NAMES.includes(o.race_tier)) {
    const first = document.querySelector("#dBody .dtier .dti");
    const img = TIER_IMG[TIER_NAMES.indexOf(o.race_tier)];
    if (first) {
      first.innerHTML = `<img src="assets/tier/${img}.png" alt="">
        <span><b>竞速强度 ${esc(o.race_tier)}</b>${esc(o.race_group || "")} · 改装等级</span>`;
    }
  }
  if (!o.drift_tier) return;
  const img = DRIFT_IMG[o.drift_tier];
  if (!img) return;
  const wrap = document.createElement("div");
  wrap.className = "dtier";
  wrap.innerHTML = `<span class="dti"><img src="assets/tier/drift/${img}.png" alt="">
      <span><b>漂移强度 ${esc(o.drift_tier)}</b>${o.race_group ? esc(o.race_group) : "漂移分级"}</span></span>`;
  const host = document.querySelector("#dBody .dtier");
  if (host) host.appendChild(wrap.firstElementChild);
  else $("dAct").after(wrap);
}

/* 调校：详情页里常显一块，按需拉取。
   结构按设计文档：9 位分享码 + 作者游戏 ID + 适用强度分级 + ≤100 字说明。 */
const fmtCode = v => String(v).replace(/\D/g, "").slice(0, 9).replace(/(\d{3})(?=\d)/g, "$1 ");

/* 分级顺序与首页等级菜单保持一致：按 D → C → B → A → S1 → S2 → R 分组，
   未归入任何等级的自定义分组排在最后 */
function tierGroupsOrdered() {
  const out = [], seen = new Set();
  clsClasses.forEach(c => grpOfCls(c).forEach(g => { if (!seen.has(g)) { seen.add(g); out.push(g); } }));
  [...(DATA.tierGroups || []), "漂移神车", "通用"].forEach(g => {
    if (!seen.has(g)) { seen.add(g); out.push(g); }
  });
  return out;
}

function tierMenuHTML() {
  const rows = [];
  const seen = new Set();
  clsClasses.forEach(c => {
    const gs = grpOfCls(c);
    if (!gs.length) return;
    rows.push(`<div class="gh" style="--cc:${ccOf(c)}">${c} 级</div>`);
    gs.forEach(g => {
      seen.add(g);
      rows.push(`<button class="gi" type="button" data-grp="${esc(g)}" style="--cc:${ccOf(c)};--ct:${ctOf(c)}"><span class="dot"></span>${esc(g)}</button>`);
    });
  });
  const rest = [...(DATA.tierGroups || []), "漂移神车", "通用"].filter(g => !seen.has(g));
  if (rest.length) {
    rows.push(`<div class="gh" style="--cc:var(--steel)">其他</div>`);
    rest.forEach(g => rows.push(`<button class="gi" type="button" data-grp="${esc(g)}" style="--cc:var(--steel);--ct:#fff"><span class="dot"></span>${esc(g)}</button>`));
  }
  return rows.join("");
}

function copyTip(anchor, text) {
  const r = anchor.getBoundingClientRect();
  const t = document.createElement("span");
  t.className = "copytip";
  t.textContent = text;
  t.style.left = r.left + r.width / 2 + "px";
  t.style.top = r.top - 8 + "px";
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 1200);
}

async function copyCode(el) {
  const code = el.dataset.code || "";
  try {
    await navigator.clipboard.writeText(code);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = code; ta.style.cssText = "position:fixed;opacity:0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } catch {}
    ta.remove();
  }
  el.classList.add("copied");
  copyTip(el, "已复制 " + code);
  setTimeout(() => el.classList.remove("copied"), 1200);
}

async function renderTunes(c) {
  const host = $("dTune");
  if (!host) return;
  const groups = tierGroupsOrdered();
  host.innerHTML = `<h3 class="tune-title">车辆调校</h3>
    <div class="tunelist" id="tuneList"><span class="ti">加载中…</span></div>`;
  if (ME && !ME.user.is_anonymous) {
    host.insertAdjacentHTML("beforeend", `
      <div class="tuneform">
        <div class="row">
          <input id="tuneCode" inputmode="numeric" autocomplete="off" maxlength="9" placeholder="9 位调校分享码（游戏内 FH6 分享码）">
          <input id="tuneAuthor" autocomplete="off" maxlength="32" placeholder="调校作者游戏 ID">
        </div>
        <div class="row">
          <div class="clsdd tsel" id="tuneDD">
            <button class="chip" type="button" id="tuneBtn" aria-haspopup="listbox" aria-expanded="false">
              <span class="dot" style="--cc:${ccOf(groups[0].split(/\s+/)[0])}"></span><span id="tuneLbl">${esc(groups[0])}</span>
            </button>
            <div class="clsmenu" id="tuneMenu" role="listbox">${tierMenuHTML()}</div>
          </div>
          <input id="tuneNote" maxlength="100" placeholder="说明（最多 100 字，所有玩家可见）">
          <button id="tunePost">上传</button>
        </div>
        <p class="tunemsg" id="tuneMsg"></p>
      </div>`);
    const msg = $("tuneMsg");
    /* 分享码输入：显示成 123 456 789，提交时仍取 9 位纯数字 */
    const codeEl = $("tuneCode");
    codeEl.addEventListener("input", () => {
      const d = codeEl.value.replace(/\D/g, "").slice(0, 9);
      codeEl.value = d.replace(/(\d{3})(?=\d)/g, "$1 ");
    });
    $("tuneNote").addEventListener("input", e => {
      const n = Array.from(e.target.value).length;
      msg.textContent = `${n} / 100`;
      if (n > 100) e.target.value = Array.from(e.target.value).slice(0, 100).join("");
    });

    /* 分级下拉：复用首页 .clsdd / .clsmenu 的样式与彩色圆点 */
    const dd = $("tuneDD"), dbtn = $("tuneBtn"), dmenu = $("tuneMenu");
    dd.dataset.grp = groups[0];
    dbtn.onclick = () => {
      dd.classList.toggle("open");
      dbtn.setAttribute("aria-expanded", dd.classList.contains("open") ? "true" : "false");
    };
    dmenu.onclick = ev => {
      const b = ev.target.closest(".gi");
      if (!b) return;
      dd.dataset.grp = b.dataset.grp;
      $("tuneLbl").textContent = b.dataset.grp;
      dbtn.querySelector(".dot").style.setProperty("--cc", b.style.getPropertyValue("--cc") || "var(--ink)");
      dmenu.querySelectorAll(".gi").forEach(x => x.classList.toggle("on", x === b));
      dd.classList.remove("open");
    };
    if (!window.__tuneDDClose) {
      window.__tuneDDClose = true;
      document.addEventListener("click", ev => {
        const d = $("tuneDD");
        if (d && !d.contains(ev.target)) d.classList.remove("open");
      });
    }

    $("tunePost").onclick = async () => {
      const share_code = codeEl.value.replace(/\D/g, "");
      const author_id = $("tuneAuthor").value.trim();
      const tier_group = dd.dataset.grp;
      const note = $("tuneNote").value.trim();
      if (!/^\d{9}$/.test(share_code)) { msg.textContent = "分享码必须是 9 位数字"; return; }
      if (Array.from(author_id).length < 2) { msg.textContent = "请填写作者游戏 ID"; return; }
      $("tunePost").disabled = true;
      try {
        await api("/api/tunes", { method: "POST", body: JSON.stringify({ car_id: c.id, share_code, author_id, tier_group, note, payload: {} }) });
        renderTunes(c);
      } catch (e) {
        msg.textContent = e.status === 409 ? "这台车已收录过该分享码" : e.status === 429 ? "上传过于频繁，稍后再试" : "上传失败，请检查填写内容";
        $("tunePost").disabled = false;
      }
    };
  }
  try {
    const r = await api("/api/tunes?carId=" + c.id);
    const list = $("tuneList");
    if (!list) return;
    const title = host.querySelector(".tune-title");
    if (title) title.textContent = r.tunes.length ? `车辆调校（${r.tunes.length}）` : "车辆调校";
    list.innerHTML = r.tunes.length ? r.tunes.map(t => `<div class="ti">
        <div class="ti-h"><b>${esc(t.tier_group)}</b>
        <code class="tune-code" data-code="${esc(t.share_code)}" title="点击复制分享码">${esc(fmtCode(t.share_code))}</code>
        <span>作者 ${esc(t.author_id)}</span></div>
        ${t.note ? `<p>${esc(t.note)}</p>` : ""}
      </div>`).join("") : `<span class="ti">还没有收录这台车的调校，来做第一个。</span>`;
    list.querySelectorAll(".tune-code").forEach(el => { el.onclick = () => copyCode(el); });
  } catch {
    const list = $("tuneList"); if (list) list.innerHTML = `<span class="ti">调校服务暂不可用</span>`;
  }
}

bootAuth();

</script>
</body>
</html>
"""
