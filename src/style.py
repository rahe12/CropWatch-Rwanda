"""CropWatch Rwanda UI: one page grid, a clean topbar, a verdict card and a slim footer."""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERO = ROOT / "assets" / "hero.jpg"

CSS = r"""
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");

:root {
  --lp-ink: #1a1f16;
  --lp-muted: #4a5346;
  --lp-green: #0d4f2b;
  --lp-accent: #1f8a3a;
  --lp-hover: #0a3d22;
  --lp-soft: #f3f6f0;
  --lp-surface: #f7f6f2;
  --lp-line: #d5ddd0;
  --lp-amber: #9a5700;
  --lp-red: #b42318;
  --lp-soil: #7a4e22;
  --lp-gold: #c4a35a;
  /* tokens used by the About page */
  --accent: #c4a35a;
  --gold-soft: #8a6d2b;
  --text: #1a1f16;
  /* verdict tones */
  --tone-act: #b42318;
  --tone-watch: #d97706;
  --tone-soil: #7a4e22;
  --tone-ok: #16a34a;
  /* layout grid: every page aligns to the same left and right edge */
  --page-w: 1320px;
  --gut: 40px;
  --bar-h: 76px;
}

html, body, [class*="css"], .stApp, p, h1, h2, h3, label, button, input, table {
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}
[data-testid="stIconMaterial"],
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpander"] summary svg,
.material-icons, .material-symbols-rounded, .material-symbols-outlined {
  font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
}
html { scroll-behavior: smooth; }
.stApp { background: var(--lp-surface); color: var(--lp-ink); font-size: 16px; }

/* ---------- Streamlit chrome off ---------- */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stAppDeployButton, #MainMenu,
footer:not(.landing-footer), [data-testid="stFooter"],
[data-testid="stHeaderActionElements"], [data-testid="stElementToolbar"] { display: none !important; }
footer.landing-footer { display: block !important; }
.block-container, .stMainBlockContainer { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
#cw-top { display: block; height: 0; overflow: hidden; }

/* keyboard focus must always be visible */
button:focus-visible, [role="radio"]:focus-visible, a:focus-visible, input:focus-visible {
  outline: 3px solid #c4a35a !important;
  outline-offset: 2px !important;
}
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}

/* ======================================================================
   TOPBAR
   One grid row: brand | page navigation (centred) | season badge | language.
   Its left and right edges line up with the page content below.
   ====================================================================== */
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) {
  position: sticky !important;
  top: 0 !important;
  z-index: 9999 !important;
  display: grid !important;
  grid-template-columns: auto minmax(0, 1fr) auto auto !important;
  align-items: center !important;
  column-gap: 20px !important;
  row-gap: 0 !important;
  height: var(--bar-h) !important;
  min-height: var(--bar-h) !important;
  padding: 0 max(24px, calc((100% - var(--page-w)) / 2 + var(--gut))) !important;
  box-sizing: border-box !important;
  background:
    radial-gradient(120% 220% at 0% 0%, rgba(31,138,58,.22) 0%, rgba(31,138,58,0) 55%),
    linear-gradient(180deg, #08311d 0%, #052313 100%) !important;
  border-bottom: 1px solid rgba(196,163,90,.5) !important;
  box-shadow: 0 10px 28px rgba(0,20,8,.28) !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav)::after {
  content: "";
  position: absolute; left: 0; right: 0; bottom: -1px; height: 2px;
  background: linear-gradient(90deg, rgba(196,163,90,0) 0%, #c4a35a 20%, #e8c878 50%, #c4a35a 80%, rgba(196,163,90,0) 100%);
  pointer-events: none;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > div {
  display: flex !important;
  align-items: center !important;
  width: auto !important;
  min-width: 0 !important;
  flex: none !important;
  height: 100% !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > div:nth-child(2) { justify-content: center !important; }
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > div:nth-child(3),
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > div:nth-child(4) { justify-content: flex-end !important; }
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) div[data-testid="stVerticalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  width: auto !important;
  max-width: 100% !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) div.stElementContainer {
  width: auto !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* brand */
.header-brand {
  display: inline-flex; align-items: center; gap: 14px; white-space: nowrap;
  text-decoration: none !important; color: inherit !important;
}
.header-crest {
  height: 48px; width: auto; flex: 0 0 auto; max-width: 168px;
  border-radius: 8px; overflow: hidden; background: #fff;
  box-shadow: 0 0 0 2px rgba(196,163,90,.18), 0 4px 12px rgba(0,0,0,.35);
  transition: transform .2s ease;
}
.header-brand:hover .header-crest { transform: scale(1.04); }
.header-crest img { height: 48px; width: auto; max-width: 168px; display: block; object-fit: contain; }
.header-title-box { display: flex; flex-direction: column; line-height: 1.2; }
.header-main-title { font-size: 19px; font-weight: 800; letter-spacing: -.025em; color: #fff; }
.header-sub-tag { margin-top: 3px; font-size: 12px; font-weight: 600; color: #e2c87d; letter-spacing: .01em; }

/* season badge */
.topbar-status-badge {
  display: inline-flex; align-items: center; gap: 9px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(196,163,90,.40);
  border-radius: 999px; padding: 0 16px; height: 36px;
  color: #d6e8dc; font-size: 13px; white-space: nowrap; box-sizing: border-box;
}
.topbar-status-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34,197,94,.22), 0 0 8px rgba(34,197,94,.9);
  animation: statusPulse 2.2s ease-in-out infinite;
}
@keyframes statusPulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }
.topbar-status-text strong { color: #fff; font-weight: 700; }

/* page navigation */
.st-key-page_nav { background: transparent !important; border: 0 !important; padding: 0 !important; max-width: 100% !important; }
.st-key-page_nav [data-testid="stWidgetLabel"], .st-key-lang_nav [data-testid="stWidgetLabel"],
.st-key-alert_filter [data-testid="stWidgetLabel"], .st-key-season_pick [data-testid="stWidgetLabel"],
.st-key-map_layer [data-testid="stWidgetLabel"] { display: none !important; }
.st-key-page_nav [data-testid="stButtonGroup"] {
  display: inline-flex !important; flex-wrap: nowrap !important; gap: 2px !important;
  align-items: center !important;
  background: rgba(0,0,0,.24) !important;
  border: 1px solid rgba(255,255,255,.10) !important;
  border-radius: 999px !important;
  padding: 4px !important;
  overflow-x: auto; scrollbar-width: none; max-width: 100%;
}
.st-key-page_nav [data-testid="stButtonGroup"]::-webkit-scrollbar { display: none; }
.st-key-page_nav [data-testid="stButtonGroup"] > div { background: transparent !important; border: 0 !important; box-shadow: none !important; flex: 0 0 auto !important; }
.st-key-page_nav button {
  position: relative;
  background: transparent !important; border: 0 !important; box-shadow: none !important;
  color: #cfe3d6 !important; font-weight: 600 !important; font-size: 14.5px !important;
  border-radius: 999px !important; padding: 0 20px !important;
  min-height: 40px !important; height: 40px !important; white-space: nowrap !important;
  transition: background .18s ease, color .18s ease, box-shadow .18s ease !important;
}
.st-key-page_nav button:hover { background: rgba(255,255,255,.10) !important; color: #fff !important; }
.st-key-page_nav button[aria-checked="true"] {
  color: #062615 !important;
  background: linear-gradient(180deg, #e2c87d 0%, #c4a35a 100%) !important;
  font-weight: 750 !important;
  box-shadow: 0 2px 10px rgba(196,163,90,.35) !important;
}
.st-key-page_nav button[aria-checked="true"] p { color: #062615 !important; }

/* language switch */
.st-key-lang_nav { display: inline-flex !important; height: 36px !important; margin: 0 !important; }
.st-key-lang_nav [data-testid="stButtonGroup"] {
  border: 1px solid rgba(196,163,90,.45) !important; border-radius: 999px !important;
  background: rgba(0,0,0,.26) !important; padding: 3px !important; gap: 2px !important;
  display: inline-flex !important; height: 36px !important; box-sizing: border-box !important;
}
.st-key-lang_nav [data-testid="stButtonGroup"] > div { background: transparent !important; display: flex !important; align-items: center !important; }
.st-key-lang_nav button {
  background: transparent !important; border: 0 !important; box-shadow: none !important;
  color: #d1e7d8 !important; font-weight: 700 !important; font-size: 12.5px !important; letter-spacing: .04em;
  border-radius: 999px !important; min-height: 28px !important; height: 28px !important;
  min-width: 40px !important; padding: 2px 12px !important;
  transition: background .18s ease, color .18s ease !important;
}
.st-key-lang_nav button:hover { background: rgba(255,255,255,.10) !important; color: #fff !important; }
.st-key-lang_nav button[aria-checked="true"] { background: var(--lp-gold) !important; color: #062615 !important; font-weight: 800 !important; }
.st-key-lang_nav button[aria-checked="true"] p { color: #062615 !important; }

/* ======================================================================
   PAGE GRID
   page band (full width) then .st-key-page_body (aligned container)
   ====================================================================== */
.page-band {
  background: linear-gradient(180deg, #edf5ee 0%, #fff 95%);
  border-bottom: 1px solid var(--lp-line);
  padding: 36px 0 28px;
}
.page-band .inner {
  max-width: var(--page-w); margin: 0 auto; padding-inline: var(--gut); box-sizing: border-box;
}
.page-band h1 {
  margin: 0 0 10px; font-size: clamp(28px, 3.2vw, 42px); font-weight: 750;
  letter-spacing: -.035em; line-height: 1.12; color: var(--lp-ink); max-width: 26ch;
}
.page-band .lead { margin: 0; max-width: 70ch; color: #384234; font-size: 17px; line-height: 1.55; }

/* every non-home page sits inside this container */
.st-key-page_body {
  width: 100%; max-width: var(--page-w); min-height: 55vh;
  margin: 0 auto !important; padding: 32px var(--gut) 64px !important; box-sizing: border-box;
}
/* give widgets and blocks breathing room (the global gap is 0) */
[data-testid="stMainBlockContainer"] .st-key-page_body,
[data-testid="stMainBlockContainer"] .st-key-page_body [data-testid="stVerticalBlock"] { gap: 16px !important; }
.st-key-page_body [data-testid="stHorizontalBlock"] { gap: 16px !important; }

/* html blocks that live inside the page body */
.inner-wrap { max-width: none; margin: 0; padding: 4px 0 12px; }
.st-key-page_body .inner-wrap:empty { display: none; }

/* section headings: sentence case, no shouting */
.kicker-green { color: var(--lp-green); font-size: 16px; font-weight: 700; margin: 0 0 8px; }
.section-p { margin: 0 0 16px; max-width: 72ch; color: var(--lp-muted); font-size: 16px; line-height: 1.6; }
.section-title { margin: 0 0 8px; font-size: clamp(24px, 2.4vw, 32px); font-weight: 750; letter-spacing: -.03em; line-height: 1.2; }

/* district pickers: one width everywhere */
.st-key-district_pick, .st-key-soil_district, .st-key-watch_district, .st-key-dash_district,
.st-key-sim_district_select, .st-key-ssit_district, .st-key-chat_district { max-width: 420px; }
[data-testid="stSelectbox"] label p { font-size: 14px !important; font-weight: 650 !important; color: var(--lp-ink) !important; }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  min-height: 52px; border: 1.5px solid var(--lp-ink) !important; border-radius: 6px !important;
  background: #fff !important; box-shadow: none !important; font-size: 16px;
}
.st-key-alert_filter [data-testid="stButtonGroup"], .st-key-season_pick [data-testid="stButtonGroup"] {
  gap: 0 !important; border: 1px solid var(--lp-line); border-radius: 6px; overflow: hidden; background: #fff;
}
.st-key-alert_filter button, .st-key-season_pick button {
  background: #fff !important; border: 0 !important; border-right: 1px solid var(--lp-line) !important;
  border-radius: 0 !important; box-shadow: none !important; color: var(--lp-ink) !important;
  font-weight: 600 !important; font-size: 14px !important; min-height: 44px !important; padding: 8px 14px !important;
}
.st-key-alert_filter button[aria-checked="true"], .st-key-season_pick button[aria-checked="true"] {
  background: var(--lp-ink) !important; color: #fff !important;
}

/* secondary buttons and downloads share one look */
[data-testid="stDownloadButton"] button,
[class*="st-key-dash_to_"] button, [class*="st-key-dl_"] button,
.st-key-alert_html button, .st-key-dash_html button, .st-key-dash_csv button, .st-key-soil_csv button {
  background: #fff !important; color: var(--lp-ink) !important; border: 1.5px solid var(--lp-ink) !important;
  border-radius: 6px !important; min-height: 48px !important; font-weight: 650 !important; font-size: 15px !important;
}
[data-testid="stDownloadButton"] button:hover,
[class*="st-key-dash_to_"] button:hover, [class*="st-key-dl_"] button:hover { background: var(--lp-soft) !important; }

/* tabs and expanders line up with the page grid */
[data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--lp-line); padding: 0; }
[data-baseweb="tab-list"] button p { font-size: 15px !important; font-weight: 650 !important; }
[data-baseweb="tab-panel"] { padding: 24px 0 0 !important; }
[data-testid="stExpander"] { width: 100%; border: 1px solid var(--lp-line) !important; border-radius: 8px !important; background: #fff; margin: 0 !important; }
[data-testid="stExpander"] summary p { font-size: 16px !important; font-weight: 650 !important; }

/* ---------- Home hero ---------- */
.photo-hero {
  position: relative; background-color: #123b24;
  background-image:
    linear-gradient(90deg, rgba(0,38,15,.92) 0%, rgba(0,38,15,.78) 38%, rgba(0,38,15,.25) 70%, rgba(0,38,15,.10) 100%),
    var(--hero-image);
  background-size: cover; background-position: center;
  padding: 72px 0 128px; color: #fff;
}
.landing-shell { box-sizing: border-box; width: 100%; max-width: var(--page-w); padding-inline: var(--gut); margin-inline: auto; }
.landing-hero-grid { display: grid; grid-template-columns: 1.05fr .95fr; gap: 56px; align-items: center; }
.photo-hero h1 {
  margin: 0 0 18px; color: #fff; font-size: clamp(34px, 4.2vw, 58px); font-weight: 800;
  letter-spacing: -.04em; line-height: 1.06; max-width: 20ch;
}
.photo-hero .lead { margin: 0; color: #fff; font-size: clamp(18px, 1.6vw, 22px); line-height: 1.45; max-width: 42ch; }
.hero-eyebrow { margin: 0 0 14px; color: #e2c87d; font-size: 15px; font-weight: 700; }
.hero-points { list-style: none; margin: 22px 0 0; padding: 0; display: flex; flex-wrap: wrap; gap: 10px; }
.hero-points li { background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.28); color: #fff; font-size: 14px; font-weight: 600; padding: 7px 14px; border-radius: 999px; }
.hero-steps { list-style: none; margin: 24px 0 0; padding: 0; display: grid; gap: 10px; max-width: 46ch; }
.hero-steps li { display: flex; align-items: center; gap: 12px; font-size: 16px; font-weight: 600; color: #fff; }
.hero-steps b { flex: 0 0 28px; height: 28px; border-radius: 50%; background: var(--lp-gold); color: #062615; display: grid; place-items: center; font-size: 14px; font-weight: 800; }
.hero-facts { display: flex; flex-wrap: wrap; gap: 0; margin: 28px 0 0; padding-top: 18px; border-top: 1px solid rgba(255,255,255,.25); max-width: 46ch; }
.hero-facts > div { padding-right: 22px; margin-right: 22px; border-right: 1px solid rgba(255,255,255,.2); }
.hero-facts > div:last-child { border-right: 0; margin-right: 0; padding-right: 0; }
.hero-facts dd { margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -.03em; color: #fff; line-height: 1; }
.hero-facts dt { margin-top: 4px; font-size: 12px; font-weight: 600; color: #cfe3d4; }
.landing-prices { background: #fff; color: var(--lp-ink); border-radius: 12px; overflow: hidden; box-shadow: 0 16px 40px rgba(0,25,9,.28); }
.landing-prices header { display: flex; justify-content: space-between; align-items: center; padding: 18px 22px 14px; }
.landing-prices h2 { margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -.02em; }
.live-dot { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 650; color: var(--lp-green); }
.live-dot::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--lp-green); box-shadow: 0 0 0 4px rgba(0,138,40,.2); }
.landing-prices table { width: 100%; border-collapse: collapse; text-align: left; }
.landing-prices th, .landing-prices td, .data-card th, .data-card td {
  padding: 14px 16px; border-top: 1px solid var(--lp-line); font-size: 15px; vertical-align: middle;
}
.landing-prices thead th, .data-card thead th {
  background: var(--lp-surface); font-size: 13px; font-weight: 650; padding-block: 10px; color: var(--lp-muted);
}
.landing-number { text-align: right; font-variant-numeric: tabular-nums; }
.landing-number strong { display: block; font-weight: 650; }
.landing-number span { display: block; color: var(--lp-muted); font-size: 13px; }

/* the district picker overlaps the hero: the one action on the home page */
.st-key-home_pick {
  position: relative; z-index: 6;
  width: calc(100% - var(--gut) * 2); max-width: 1240px; margin: -88px auto 0 !important;
  padding: 24px 32px 28px !important; box-sizing: border-box;
  background: #fff; border: 1px solid var(--lp-line); border-radius: 14px;
  box-shadow: 0 18px 48px rgba(0,25,9,.18);
}
.st-key-home_pick .pick-title { margin: 0 0 4px; font-size: 22px; font-weight: 750; letter-spacing: -.02em; }
.st-key-home_pick .pick-sub { margin: 0 0 14px; color: var(--lp-muted); font-size: 15px; }
.st-key-home_pick [data-testid="stSelectbox"] { margin-bottom: 8px; max-width: 420px; }

/* ---------- Verdict card (the answer) ---------- */
.verdict {
  --tone: var(--tone-ok);
  display: grid; grid-template-columns: 64px 1fr auto; gap: 24px; align-items: center;
  margin: 8px 0 12px; padding: 24px 28px; background: #f6fcf8;
  border: 1px solid var(--lp-line); border-left: 8px solid var(--tone); border-radius: 10px;
}
.verdict.act   { --tone: var(--tone-act);   background: #fffbfa; }
.verdict.watch { --tone: var(--tone-watch); background: #fffdf5; }
.verdict.soil  { --tone: var(--tone-soil);  background: #fdfaf6; }
.verdict.ok    { --tone: var(--tone-ok);    background: #f6fcf8; }
.verdict-icon { font-size: 48px; line-height: 1; text-align: center; }
.verdict-district { margin: 0 0 2px; font-size: 15px; font-weight: 650; color: var(--lp-muted); }
.verdict-title { margin: 0 0 6px; font-size: clamp(26px, 3vw, 36px); font-weight: 800; letter-spacing: -.03em; color: var(--tone); line-height: 1.12; }
.verdict-action { margin: 0; font-size: 17px; line-height: 1.5; max-width: 58ch; color: var(--lp-ink); }
.verdict-stats { display: flex; gap: 28px; margin: 0; }
.verdict-stats dt { font-size: 13px; font-weight: 600; color: var(--lp-muted); margin-bottom: 2px; }
.verdict-stats dd { margin: 0; font-size: 30px; font-weight: 800; font-variant-numeric: tabular-nums; letter-spacing: -.02em; }
.verdict-stats small { display: block; font-size: 12px; color: var(--lp-muted); font-weight: 500; }

/* ---------- Home sections ---------- */
.landing-section { padding: 48px 0 56px; background: #fff; border-bottom: 1px solid var(--lp-line); }
.landing-section.alt { background: var(--lp-soft); padding: 48px 0 8px; border-bottom: 0; }
.landing-stats { padding: 0 0 8px; }
.landing-stats dl { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 0; margin: 0; }
.landing-stats dl > div { border-top: 2px solid var(--lp-ink); padding: 18px 24px 0 0; }
.landing-stats dl > div + div { padding-left: 24px; }
.landing-stats dd { margin: 0 0 4px; color: var(--lp-accent); font-size: 42px; font-weight: 800; letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
.landing-stats dt { font-size: 15px; color: var(--lp-muted); }

.problem-band {
  display: grid; grid-template-columns: 1fr 1.2fr; gap: 48px; align-items: start;
  margin-top: 44px; padding: 28px 32px; background: var(--lp-soft);
  border-left: 6px solid var(--lp-green); border-radius: 0 10px 10px 0;
}
.problem-band .section-title { margin: 0; max-width: 22ch; }
.problem-band .section-p { margin: 0; max-width: none; }

.process-row { display: grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 14px; margin-top: 20px; }
.process-row.three { grid-template-columns: repeat(3, minmax(0,1fr)); }
.process-row article { background: #fff; border: 1px solid var(--lp-line); border-radius: 8px; padding: 20px; }
.process-row span { display: block; color: var(--lp-accent); font-weight: 800; font-size: 14px; margin-bottom: 8px; }
.process-row h3 { margin: 0 0 8px; font-size: 18px; }
.process-row p { margin: 0; color: var(--lp-muted); font-size: 15px; line-height: 1.55; }
.decision-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); margin-top: 24px; }
.decision-grid article { padding: 0 28px; border-left: 1px solid var(--lp-line); }
.decision-grid article:first-child { padding-left: 0; border-left: 0; }
.decision-grid h3 { margin: 0 0 8px; font-size: 20px; font-weight: 650; }
.decision-grid p { font-size: 15px; color: var(--lp-muted); margin: 0; line-height: 1.55; }

/* feature cards: Streamlit containers so the buttons keep session state */
.st-key-feature_grid { max-width: var(--page-w); margin: 0 auto !important; padding: 20px var(--gut) 48px; box-sizing: border-box; background: transparent; }
.st-key-feature_grid [data-testid="stHorizontalBlock"] { gap: 18px !important; margin-bottom: 18px; }
[class*="st-key-featcard_"] {
  background: #fff; border: 1px solid var(--lp-line); border-top: 4px solid var(--lp-green);
  border-radius: 10px; padding: 22px 22px 14px !important; height: 100%;
  box-shadow: 0 2px 10px rgba(13,79,43,.06); transition: transform .15s ease, box-shadow .15s ease;
}
[class*="st-key-featcard_"]:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(13,79,43,.14); }
.feature-icon { font-size: 34px; line-height: 1; margin-bottom: 10px; }
[class*="st-key-featcard_"] h3 { margin: 0 0 8px; font-size: 20px; font-weight: 750; letter-spacing: -.02em; }
[class*="st-key-featcard_"] p { margin: 0 0 12px; color: var(--lp-muted); font-size: 15px; line-height: 1.55; min-height: 70px; }
[class*="st-key-featbtn_"] button {
  background: transparent !important; border: 0 !important; box-shadow: none !important;
  color: var(--lp-green) !important; font-weight: 700 !important; font-size: 15px !important;
  padding: 4px 0 !important; min-height: 32px !important;
}
[class*="st-key-featbtn_"] button:hover { color: var(--lp-accent) !important; text-decoration: underline; }

/* trust strip with source chips */
.trust-strip {
  display: flex; justify-content: space-between; align-items: center; gap: 32px;
  margin-top: 48px; padding: 24px 28px; border: 1px solid var(--lp-line); border-radius: 10px; background: #fff;
}
.src-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.src-chips span { padding: 6px 14px; border-radius: 999px; background: var(--lp-soft); border: 1px solid var(--lp-line); color: var(--lp-green); font-size: 13px; font-weight: 700; }

.cta-band { background: #0a3d22; color: #fff; padding: 44px 0 56px; }
.cta-band h2 { color: #fff; font-size: clamp(24px, 2.6vw, 34px); max-width: 28ch; margin: 0 0 10px; font-weight: 750; letter-spacing: -.03em; line-height: 1.2; }
.cta-band .section-p { color: #d6e3dc; }

/* primary action buttons */
.st-key-home_go_alerts button, .st-key-cta_go_alerts button, .st-key-ask_ai_btn button {
  background: var(--lp-green) !important; color: #fff !important; border: 0 !important;
  border-radius: 6px !important; min-height: 52px !important; font-weight: 650 !important; font-size: 16px !important;
}
.st-key-home_go_alerts button:hover, .st-key-cta_go_alerts button:hover, .st-key-ask_ai_btn button:hover { background: var(--lp-hover) !important; }
.st-key-home_go_district button, .st-key-home_go_advise button, .st-key-cta_go_district button, .st-key-cta_go_advise button,
.st-key-home_ask_ai button {
  background: #fff !important; color: var(--lp-ink) !important; border: 1.5px solid var(--lp-ink) !important;
  border-radius: 6px !important; min-height: 52px !important; font-weight: 650 !important; font-size: 16px !important;
}
.st-key-home_go_district button:hover, .st-key-home_go_advise button:hover, .st-key-cta_go_district button:hover,
.st-key-cta_go_advise button:hover, .st-key-home_ask_ai button:hover { background: var(--lp-soft) !important; }
[data-testid="stHorizontalBlock"]:has(.st-key-home_go_alerts) { margin: 16px 0 0; gap: 14px; }
[data-testid="stHorizontalBlock"]:has(.st-key-cta_go_alerts) {
  width: calc(100% - var(--gut) * 2); max-width: 1240px; margin: -28px auto 0; padding: 0 0 48px; gap: 14px; position: relative; z-index: 6;
}

/* ---------- Status pills ---------- */
.status-pill { display: inline-flex; align-items: center; padding: 5px 11px; font-size: 13px; font-weight: 650; border-radius: 4px; white-space: nowrap; }
.status-pill.irrigation_gap { background: #fff6e5; color: var(--lp-amber); }
.status-pill.irrigate_now, .status-pill.water_stress { background: #fde8e8; color: var(--lp-red); }
.status-pill.soil_rain, .status-pill.soil_watch, .status-pill.excess_rain { background: #f4eee6; color: var(--lp-soil); }
.status-pill.dry_watch { background: #eef2f6; color: #344054; }
.status-pill.stable, .status-pill.normal_monitoring { background: #edf5ee; color: var(--lp-hover); }
.status-pill.rainfall_watch { background: #fff6e5; color: var(--lp-amber); }
.status-pill.agronomist { background: #f3e8ff; color: #6d28d9; }

/* ---------- Cards, KPIs, tables ---------- */
.board { background: #fff; border: 1px solid var(--lp-line); border-radius: 10px; padding: 28px; margin: 8px 0 24px; }
.board-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 10px; }
.board-head h2 { margin: 0; font-size: clamp(26px, 2.8vw, 36px); font-weight: 750; letter-spacing: -.03em; }
.board-copy { margin: 0 0 10px; max-width: 76ch; font-size: 17px; line-height: 1.55; }
.board-action { margin: 0; font-size: 16px; font-weight: 650; color: var(--lp-hover); }
.board-action:empty { display: none; }
.kpi-row { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 1px; background: var(--lp-line); border: 1px solid var(--lp-line); margin-top: 22px; border-radius: 6px; overflow: hidden; }
.kpi-row.five { grid-template-columns: repeat(5, minmax(0,1fr)); }
.kpi-row.six { grid-template-columns: repeat(3, minmax(0,1fr)); }
.kpi { background: #fff; padding: 16px 18px; }
.kpi span { display: block; font-size: 13px; color: var(--lp-muted); font-weight: 600; margin-bottom: 8px; }
.kpi strong { display: block; font-size: 28px; font-weight: 750; letter-spacing: -.03em; color: var(--lp-accent); font-variant-numeric: tabular-nums; line-height: 1.1; }
.kpi small { color: var(--lp-muted); font-size: 13px; }
.data-card { border: 1px solid var(--lp-line); background: #fff; overflow: auto; margin: 12px 0 28px; border-radius: 8px; }
.data-card table { width: 100%; border-collapse: collapse; text-align: left; }
.data-card tbody th { font-weight: 650; }
.bar-cell { min-width: 120px; }
.bar-cell b { display: block; font-variant-numeric: tabular-nums; font-size: 14px; margin-bottom: 6px; }
.bar-cell i { display: block; height: 6px; background: var(--lp-green); border-radius: 2px; }
.note-box { margin: 8px 0 20px; padding: 18px 20px; border-left: 4px solid var(--lp-green); background: var(--lp-soft); font-size: 16px; line-height: 1.55; border-radius: 0 6px 6px 0; }
.split-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 8px 0 24px; }
.split-cards article { border: 1px solid var(--lp-line); border-radius: 8px; padding: 20px; background: #fff; }
.split-cards h3 { margin: 0 0 8px; font-size: 17px; }
.split-cards p { margin: 0; color: var(--lp-muted); font-size: 15px; line-height: 1.5; }
.fresh-list { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 16px; margin: 8px 0 24px; }
.fresh-list article { border-top: 2px solid var(--lp-ink); padding-top: 14px; }
.fresh-list span { display: block; font-size: 13px; color: var(--lp-muted); font-weight: 600; margin-bottom: 6px; }
.fresh-list strong { font-size: 20px; letter-spacing: -.02em; }
.method-list article { display: grid; grid-template-columns: 56px 1fr; gap: 8px 20px; padding: 20px 0; border-bottom: 1px solid var(--lp-line); }
.method-list .step { color: var(--lp-green); font-weight: 800; font-size: 15px; }
.method-list p { margin: 0; color: var(--lp-muted); font-size: 16px; line-height: 1.65; }
.why-box { margin-top: 18px; padding: 16px 18px; border: 1px solid var(--lp-line); border-radius: 8px; background: var(--lp-soft); }
.why-box strong { display: block; margin-bottom: 6px; }
.why-box p { margin: 0 0 8px; font-size: 15px; line-height: 1.55; }
.glossary { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; margin-top: 14px; }
.glossary p { margin: 0; padding: 10px 0; border-bottom: 1px solid var(--lp-line); font-size: 15px; }
.kind-pill { display: inline-block; font-size: 13px; font-weight: 600; padding: 4px 10px; background: var(--lp-soft); color: var(--lp-green); margin-bottom: 10px; border-radius: 4px; }
.source-card { border: 1px solid var(--lp-line); border-radius: 8px; background: #fff; padding: 22px; margin: 0 0 14px; }
.source-card h3 { margin: 0 0 8px; font-size: 20px; }
.source-card dl { display: grid; grid-template-columns: 160px 1fr; gap: 8px 16px; margin: 14px 0 0; }
.source-card dt { font-size: 13px; color: var(--lp-muted); font-weight: 650; }
.source-card dd { margin: 0; font-size: 15px; line-height: 1.5; }
.policy-badge { display: inline-block; background: var(--lp-soft); color: var(--lp-green); font-size: 14px; font-weight: 650; padding: 8px 12px; margin: 8px 0 14px; border-radius: 4px; }

/* week forecast */
.week-panel { margin-top: 28px; }
.week-head h3 { margin: 0 0 4px; font-size: 20px; font-weight: 700; }
.week-head p { margin: 0 0 16px; color: var(--lp-muted); font-size: 15px; }
.week-bars { display: grid; grid-template-columns: repeat(7, minmax(0,1fr)); gap: 10px; }
.week-day { border: 1px solid var(--lp-line); border-radius: 6px; background: var(--lp-surface); padding: 12px 6px 14px; text-align: center; }
.week-day em { display: block; font-style: normal; font-size: 13px; font-weight: 650; color: var(--lp-muted); margin-bottom: 8px; }
.week-track { height: 88px; display: flex; align-items: flex-end; justify-content: center; margin-bottom: 8px; }
.week-track i { display: block; width: 26px; background: var(--lp-green); border-radius: 3px 3px 0 0; }
.week-day strong { display: block; font-size: 16px; font-variant-numeric: tabular-nums; }
.week-day span { display: block; font-size: 12px; color: var(--lp-muted); }
.week-day .week-bal { font-weight: 650; color: var(--lp-green); }
.harvest-strip { margin-top: 28px; padding-top: 8px; }
.harvest-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.harvest-cell { border: 1px solid var(--lp-line); border-radius: 10px; background: #fff; padding: 14px 16px; }
.harvest-cell span { display: block; font-size: 12.5px; font-weight: 650; color: var(--lp-muted); }
.harvest-cell strong { display: block; margin: 6px 0 4px; font-size: 22px; font-weight: 800; letter-spacing: -.03em; }
.harvest-cell span + strong + span { font-weight: 500; color: #3f4e43; font-size: 13px; line-height: 1.4; }
@media (max-width: 800px) { .harvest-grid { grid-template-columns: 1fr; } }

/* ---------- Alerts overview ---------- */
.alert-triage-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin: 8px 0 20px; }
.alert-triage-card { background: #fff; border-radius: 8px; padding: 14px 16px; border: 1px solid var(--lp-line); }
.alert-triage-card.critical { border-top: 4px solid #b42318; background: #fffbfa; }
.alert-triage-card.high { border-top: 4px solid #d97706; background: #fffdf5; }
.alert-triage-card.soil { border-top: 4px solid #7a4e22; background: #fdfaf6; }
.alert-triage-card.stable { border-top: 4px solid #16a34a; background: #f6fcf8; }
.triage-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; gap: 10px; }
.triage-title { font-size: 14px; font-weight: 650; color: var(--lp-ink); }
.triage-count { font-size: 30px; font-weight: 800; line-height: 1; }
.alert-triage-card.critical .triage-count { color: #b42318; }
.alert-triage-card.high .triage-count { color: #d97706; }
.alert-triage-card.soil .triage-count { color: #7a4e22; }
.alert-triage-card.stable .triage-count { color: #16a34a; }
.triage-desc { font-size: 13px; color: #3f4e43; line-height: 1.4; }
.map-controls-deck { background: transparent; border: 0; border-radius: 0; padding: 0 0 10px; border-bottom: 1px solid var(--lp-line); margin-bottom: 8px; }
.deck-header { display: flex; align-items: center; gap: 10px; }
.deck-icon { font-size: 22px; }
.deck-header strong { display: block; font-size: 15px; color: #062314; font-weight: 750; }
.deck-header small { display: block; font-size: 13px; color: #55705d; }
.map-side-label { margin: 14px 0 6px; font-size: 13px; font-weight: 750; color: var(--lp-green); letter-spacing: .01em; }
.map-frame-title { margin: 0 0 10px; font-size: 14px; font-weight: 750; color: #062314; }
.legend-card { border: 1px solid var(--lp-line); border-radius: 10px; background: #f7fbf8; padding: 14px 16px; margin-top: 8px; }
.legend-card h3 { margin: 0 0 8px; font-size: 13px; font-weight: 750; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 13.5px; margin: 6px 0; }
.legend-swatch { width: 14px; height: 14px; border-radius: 3px; flex: 0 0 14px; }
.st-key-alert_map_board {
  background: #fff; border: 1px solid var(--lp-line); border-radius: 16px;
  padding: 18px 18px 10px !important; margin: 8px 0 22px;
  box-shadow: 0 12px 32px rgba(13,79,43,.08);
}
.st-key-alert_map_board iframe {
  border-radius: 12px !important; border: 1px solid var(--lp-line) !important;
  box-shadow: none !important; background: #e7eee4 !important;
}
.st-key-alert_map_board [data-testid="stRadio"] label p { font-size: 13.5px !important; }
[data-testid="stCustomComponentV1"]:not([data-testid="stChatMessage"] *) iframe, iframe[title*="folium"], .folium-map iframe {
  border-radius: 12px !important; box-shadow: none !important; border: 1px solid var(--lp-line) !important;
}

/* evidence (hidden inside an expander by default) */
.provable-evidence-box { background: #fff; border: 1.5px solid var(--lp-gold); border-radius: 8px; margin-top: 12px; overflow: hidden; }
.evidence-math-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1px; background: #e5ece2; }
.evidence-math-cell { background: #fff; padding: 14px 16px; display: flex; flex-direction: column; justify-content: center; }
.math-label { font-size: 13px; font-weight: 650; color: #4a5a4e; margin-bottom: 4px; }
.math-value { font-size: 20px; font-weight: 800; color: #062615; margin-bottom: 2px; }
.math-formula { font-size: 13px; color: #6c7d70; }
.evidence-audit-footer { padding: 12px 18px; background: #f7faf6; }
.evidence-stamp { display: flex; align-items: flex-start; gap: 12px; }
.stamp-icon { font-size: 20px; line-height: 1; }
.evidence-stamp strong { display: block; font-size: 13px; font-weight: 750; color: var(--lp-green); margin-bottom: 2px; }
.evidence-stamp p { margin: 0; font-size: 13px; line-height: 1.5; color: #3b4e40; }
.evidence-stamp code { background: #e8efe7; padding: 1px 4px; border-radius: 3px; font-size: 12px; color: var(--lp-green); }

/* SMS / USSD phones */
.phone-wrap { display: grid; grid-template-columns: 240px minmax(0,1fr); gap: 24px; align-items: start; margin-top: 16px; }
.feature-phone { width: 240px; background: #1a1d27; border-radius: 28px; padding: 18px 14px 22px; color: #d7f5d0; }
.feature-phone .phone-bar { text-align: center; font-size: 12px; letter-spacing: .12em; margin-bottom: 10px; color: #8aa08a; }
.feature-phone .phone-screen { background: #0c1f12; min-height: 220px; padding: 12px; font-family: "Lucida Console", ui-monospace, monospace !important; font-size: 13px; line-height: 1.45; white-space: pre-wrap; }

/* ---------- ADVICE AI ---------- */
/* the conversation panel is one card: dark header, context chips, thread, composer */
.st-key-ai_chat {
  background: #fff; border: 1px solid var(--lp-line); border-radius: 16px;
  box-shadow: 0 10px 32px rgba(13,79,43,.10); overflow: hidden; padding: 0 0 20px !important;
}
.st-key-ai_chat > [data-testid="stElementContainer"],
.st-key-ai_chat > [data-testid="stHorizontalBlock"],
.st-key-ai_chat > [data-testid="stExpander"],
.st-key-ai_chat > [data-testid="stChatMessage"],
.st-key-ai_chat > [data-testid="stChatInput"] { margin-inline: 24px !important; width: calc(100% - 48px) !important; }
.st-key-ai_chat > [data-testid="stElementContainer"]:first-child { margin-inline: 0 !important; width: 100% !important; }

.ai-head {
  display: flex; align-items: center; gap: 14px; padding: 20px 24px;
  background: radial-gradient(120% 220% at 0% 0%, rgba(31,138,58,.30) 0%, rgba(31,138,58,0) 55%), linear-gradient(180deg, #08311d 0%, #052313 100%);
  border-bottom: 2px solid var(--lp-gold);
}
.ai-orb {
  width: 44px; height: 44px; flex: 0 0 44px; border-radius: 50%;
  display: grid; place-items: center;
  background: linear-gradient(180deg, #e8c878 0%, #c4a35a 100%);
  box-shadow: 0 0 0 4px rgba(196,163,90,.22), 0 6px 16px rgba(0,0,0,.30);
}
.ai-orb svg { width: 24px; height: 24px; }
.ai-orb.big { width: 72px; height: 72px; flex-basis: 72px; margin: 0 auto 16px; box-shadow: 0 0 0 8px rgba(196,163,90,.18), 0 10px 24px rgba(13,79,43,.22); }
.ai-orb.big svg { width: 38px; height: 38px; }
.ai-head-text { flex: 1 1 auto; min-width: 0; }
.ai-head-text h2 { margin: 0; color: #fff; font-size: 20px; font-weight: 800; letter-spacing: -.02em; line-height: 1.2; }
.ai-head-text p { margin: 2px 0 0; color: #b9d3c3; font-size: 14px; }
.ai-live {
  display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px;
  background: rgba(255,255,255,.08); border: 1px solid rgba(196,163,90,.40);
  color: #d6e8dc; font-size: 12.5px; font-weight: 600; white-space: nowrap;
}
.ai-live i { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,.22); animation: statusPulse 2.2s ease-in-out infinite; }

.ai-ctx { display: flex; flex-wrap: wrap; gap: 8px; padding: 14px 24px; background: var(--lp-soft); border-bottom: 1px solid var(--lp-line); }
.ai-ctx span { padding: 5px 12px; border-radius: 999px; background: #fff; border: 1px solid var(--lp-line); color: var(--lp-green); font-size: 13px; font-weight: 650; }

.ai-welcome { text-align: center; padding: 28px 8px 8px; }
.ai-welcome h3 { margin: 0 0 8px; font-size: clamp(22px, 2.4vw, 28px); font-weight: 800; letter-spacing: -.03em; color: var(--lp-ink); }
.ai-welcome p { margin: 0 auto; max-width: 54ch; color: var(--lp-muted); font-size: 15.5px; line-height: 1.6; }

/* suggestion cards */
[class*="st-key-btn_ai_"] button {
  background: #fff !important; border: 1px solid var(--lp-line) !important; color: var(--lp-ink) !important;
  border-radius: 12px !important; min-height: 78px !important; padding: 12px 14px !important;
  justify-content: flex-start !important; text-align: left !important;
  font-weight: 650 !important; font-size: 14px !important; line-height: 1.35;
  box-shadow: 0 1px 2px rgba(13,79,43,.05) !important;
  transition: border-color .15s ease, background .15s ease, box-shadow .15s ease !important;
}
[class*="st-key-btn_ai_"] button p { text-align: left !important; }
[class*="st-key-btn_ai_"] button:hover { background: var(--lp-soft) !important; border-color: var(--lp-green) !important; color: var(--lp-green) !important; box-shadow: 0 6px 16px rgba(13,79,43,.10) !important; }
.st-key-btn_clear_chat button, .st-key-btn_exp_disabled button { min-height: 48px !important; border-radius: 6px !important; font-weight: 650 !important; }

/* messages */
[data-testid="stChatMessage"] { background: transparent !important; border: 0 !important; padding: 10px 0 !important; margin: 0 !important; gap: 12px !important; }
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
  width: 36px !important; height: 36px !important; border-radius: 50% !important; font-size: 18px !important;
  background: var(--lp-soft) !important; border: 1px solid var(--lp-line) !important;
}
[data-testid="stChatMessageAvatarAssistant"] { background: linear-gradient(180deg, #e8c878 0%, #c4a35a 100%) !important; border-color: transparent !important; }
[data-testid="stChatMessage"]:has(.user-marker) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has(.user-marker) [data-testid="stChatMessageContent"] {
  background: var(--lp-green); color: #fff; border-radius: 16px 16px 4px 16px;
  padding: 12px 18px; max-width: 78%; width: fit-content; margin-left: auto;
}
[data-testid="stChatMessage"]:has(.user-marker) [data-testid="stChatMessageContent"] p,
[data-testid="stChatMessage"]:has(.user-marker) [data-testid="stChatMessageContent"] span { color: #fff !important; margin: 0; }
[data-testid="stChatMessage"]:has(.assistant-marker) [data-testid="stChatMessageContent"] {
  background: #f6faf6; border: 1px solid var(--lp-line); border-radius: 16px 16px 16px 4px; padding: 14px 20px; flex: 1 1 auto;
}
.ai-msg-label { margin: 0 0 6px; font-size: 13px; font-weight: 750; color: var(--lp-green); }
.ai-next { margin: 14px 0 6px; font-size: 13.5px; font-weight: 700; color: var(--lp-green); }
[data-testid="stChatMessage"] table { width: 100% !important; border-collapse: collapse !important; margin: 12px 0 !important; font-size: 14px !important; background: #fff; border: 1px solid var(--lp-line) !important; }
[data-testid="stChatMessage"] th { background: #eaf4ed !important; color: var(--lp-green) !important; font-weight: 700 !important; padding: 8px 12px !important; border-bottom: 2px solid #b7dcbe !important; text-align: left !important; }
[data-testid="stChatMessage"] td { padding: 8px 12px !important; border-bottom: 1px solid #eef2ec !important; }
[data-testid="stChatMessage"] blockquote { border-left: 3px solid var(--lp-green) !important; background: #fff !important; padding: 8px 14px !important; margin: 10px 0 !important; border-radius: 0 6px 6px 0 !important; }
[data-testid="stChatMessage"] iframe { border: 0 !important; box-shadow: none !important; background: transparent !important; height: 48px !important; margin: 6px 0 0 !important; }
[class*="st-key-chip_btn_"] button {
  border-radius: 999px !important; background: #fff !important; border: 1px solid #b7dcbe !important;
  color: var(--lp-green) !important; font-size: 13px !important; font-weight: 650 !important; padding: 5px 14px !important; min-height: 38px !important;
}
[class*="st-key-chip_btn_"] button:hover { background: var(--lp-green) !important; color: #fff !important; }

/* composer */
[data-testid="stChatInput"] { max-width: 100% !important; margin-top: 12px !important; }
[data-testid="stChatInput"] > div { border-radius: 28px !important; border: 1.5px solid #c2d6c6 !important; background: #fff !important; box-shadow: 0 4px 14px rgba(13,79,43,.08); }
[data-testid="stChatInput"] textarea { font-size: 15px !important; padding: 14px 18px !important; background: transparent !important; }
[data-testid="stChatInput"] > div:focus-within { border-color: var(--lp-green) !important; box-shadow: 0 0 0 3px rgba(13,79,43,.15) !important; }
.ai-foot { margin: 8px 24px 0; text-align: center; font-size: 12.5px; color: #71816f; }

/* context panel */
.ai-side-card { background: #fff; border: 1px solid var(--lp-line); border-radius: 12px; padding: 16px 18px; margin-bottom: 14px; }
.ai-side-card.soft { background: #f7fbf8; border-color: #c8dfcc; }
.ai-side-header { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 750; color: var(--lp-green); margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #edf1eb; }
.ai-side-stat { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; font-size: 14px; border-bottom: 1px dashed #edf1eb; gap: 12px; }
.ai-side-stat:last-child { border-bottom: 0; }
.ai-side-stat-lbl { color: #556353; }
.ai-side-stat-val { font-weight: 700; color: var(--lp-ink); text-align: right; }
.ai-tiles { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ai-tile { background: var(--lp-soft); border: 1px solid var(--lp-line); border-radius: 8px; padding: 10px 12px; }
.ai-tile span { display: block; font-size: 12.5px; color: var(--lp-muted); font-weight: 600; margin-bottom: 4px; }
.ai-tile strong { font-size: 20px; font-weight: 800; letter-spacing: -.02em; color: var(--lp-green); font-variant-numeric: tabular-nums; }
.ai-tile.warn strong { color: var(--lp-amber); }
.ai-tile.bad strong { color: var(--lp-red); }
.ai-flag { display: inline-block; padding: 3px 9px; border-radius: 4px; font-size: 12.5px; font-weight: 750; }
.ai-flag.warn { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
.ai-flag.good { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
.ai-sms-screen { background: #0f2115; color: #a7f3d0; border: 1px solid #234830; border-radius: 6px; padding: 12px; font-family: ui-monospace, Menlo, Consolas, monospace !important; font-size: 13px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
.ai-sms-meta { display: flex; justify-content: space-between; margin-top: 8px; font-size: 13px; color: #556353; }
.ai-sms-meta strong { color: var(--lp-green); }
.ai-contacts { font-size: 14px; line-height: 1.75; color: #2c3a2f; }
.ai-llm-note { font-size: 14px; color: #3b5240; margin: 0 0 12px; }

@media (max-width: 980px) {
  .ai-head { padding: 16px; }
  .ai-live { display: none; }
  .ai-ctx { padding: 12px 16px; }
  .st-key-ai_chat > [data-testid="stElementContainer"],
  .st-key-ai_chat > [data-testid="stHorizontalBlock"],
  .st-key-ai_chat > [data-testid="stExpander"],
  .st-key-ai_chat > [data-testid="stChatMessage"],
  .st-key-ai_chat > [data-testid="stChatInput"] { margin-inline: 14px !important; width: calc(100% - 28px) !important; }
  [data-testid="stChatMessage"]:has(.user-marker) [data-testid="stChatMessageContent"] { max-width: 90%; }
}

/* ======================================================================
   FOOTER
   brand and mission | platform links | data sources, then one bottom bar
   ====================================================================== */
.landing-footer {
  display: block !important;
  background: #051d11;
  color: #c2d6c9;
  border-top: 4px solid var(--lp-gold);
  padding: 0;
}
.footer-inner { max-width: var(--page-w); margin: 0 auto; padding-inline: var(--gut); box-sizing: border-box; }

.footer-main {
  display: grid;
  grid-template-columns: 1.8fr 1fr 1fr;
  gap: 40px 64px;
  padding: 48px 0 40px;
  align-items: start;
}
.landing-footer h2 {
  margin: 0 0 16px;
  font-size: 15px;
  font-weight: 700;
  color: #e2c87d;
}
.landing-footer ul { list-style: none; margin: 0; padding: 0; }
.landing-footer li { margin: 0 0 10px; font-size: 14.5px; line-height: 1.5; color: #c2d6c9; }
.landing-footer a { color: #e6f2ea; text-decoration: none; transition: color .15s ease; }
.landing-footer a:hover { color: var(--lp-gold); text-decoration: underline; text-underline-offset: 3px; }
.landing-footer .footer-more { display: inline-block; margin-top: 4px; font-size: 14px; font-weight: 650; color: #e2c87d; }

.landing-brand { display: inline-flex; align-items: center; gap: 12px; color: #fff; }
.landing-brand img {
  height: 48px; width: auto; max-width: 168px; flex: 0 0 auto;
  object-fit: contain; background: #fff; border-radius: 8px; padding: 2px;
}
.landing-brand > span { display: flex; flex-direction: column; line-height: 1.15; font-size: 19px; font-weight: 750; letter-spacing: -.02em; }
.landing-brand small { margin-top: 3px; font-size: 12.5px; font-weight: 500; color: #9cb5a5; letter-spacing: 0; }
.footer-mission { margin: 16px 0 0; max-width: 46ch; font-size: 14.5px; line-height: 1.65; color: #b7ccbe; }

.landing-copyright {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
  gap: 8px 24px; padding: 20px 0 28px;
  border-top: 1px solid rgba(255,255,255,.1);
  font-size: 13px; color: #9cb5a5;
}
.landing-copyright a { color: #e2c87d; font-weight: 650; }

/* ---------- Tablet / phone ---------- */
@media (max-width: 1280px) {
  .topbar-status-badge { display: none !important; }
  [data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) {
    grid-template-columns: auto minmax(0, 1fr) auto !important;
  }
}
@media (max-width: 1180px) {
  .header-sub-tag { display: none !important; }
  .footer-main { grid-template-columns: 1fr 1fr; gap: 36px 40px; }
  .footer-main > section:first-child { grid-column: 1 / -1; }
}
@media (max-width: 980px) {
  :root { --bar-h: 64px; --gut: 18px; }
  [data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) { column-gap: 10px !important; padding-inline: 12px !important; }
  .header-title-box { display: none; }
  .header-crest, .header-crest img { height: 40px; max-width: 132px; }
  .st-key-page_nav button { padding: 0 12px !important; font-size: 13px !important; min-height: 36px !important; height: 36px !important; }
  .photo-hero { padding: 40px 0 112px; }
  .photo-hero h1 { font-size: 36px; }
  .landing-hero-grid, .decision-grid, .landing-stats dl, .kpi-row, .kpi-row.five, .kpi-row.six,
  .split-cards, .fresh-list, .process-row, .process-row.three, .source-card dl, .glossary, .phone-wrap, .problem-band { grid-template-columns: 1fr; }
  .landing-hero-grid { gap: 28px; }
  .problem-band { gap: 14px; padding: 22px; }
  .trust-strip { flex-direction: column; align-items: flex-start; gap: 18px; }
  .src-chips { justify-content: flex-start; }
  .st-key-home_pick { margin-top: -80px !important; padding: 18px !important; }
  .st-key-page_body { padding-top: 24px !important; padding-bottom: 48px !important; }
  .verdict { grid-template-columns: 1fr; gap: 14px; padding: 20px; }
  .verdict-icon { text-align: left; font-size: 40px; }
  .verdict-stats { justify-content: space-between; gap: 12px; }
  .verdict-stats dd { font-size: 24px; }
  .week-bars { grid-template-columns: repeat(4, 1fr); }
  .decision-grid article, .decision-grid article:first-child { border-left: 0; border-top: 1px solid var(--lp-line); padding: 18px 0; }
  .landing-stats dl > div, .landing-stats dl > div + div { padding-left: 0; padding-bottom: 14px; }
  .ai-telemetry-strip { grid-template-columns: 1fr 1fr; }
  .hero-facts > div { padding-right: 14px; margin-right: 14px; }
  .hero-facts dd { font-size: 24px; }
  .footer-main { grid-template-columns: 1fr; gap: 28px; padding: 36px 0 28px; }
  .landing-copyright { flex-direction: column; align-items: flex-start; }
}
"""


def inject():
    css = CSS
    if HERO.exists():
        encoded = base64.b64encode(HERO.read_bytes()).decode("ascii")
        css = css.replace("var(--hero-image)", f'url("data:image/jpeg;base64,{encoded}")')
    else:
        css = css.replace(",\n    var(--hero-image)", "")
    return f"<style>{css}</style>"