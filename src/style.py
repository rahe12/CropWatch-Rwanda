"""Product UI: Inter, photo hero, district boards, status pills, sharp cards."""

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
}

html, body, [class*="css"], .stApp, p, h1, h2, h3, label, span, button, input, table {
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}
.stApp { background: var(--lp-surface); color: var(--lp-ink); }
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stAppDeployButton,
#MainMenu,
footer:not(.landing-footer),
[data-testid="stFooter"],
[data-testid="stHeaderActionElements"] { display: none !important; }
footer.landing-footer { display: block !important; }
.block-container, .stMainBlockContainer {
  padding: 0 !important;
  max-width: 100% !important;
}
.stMainBlockContainer > div > [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stElementToolbar"] { display: none !important; }
#cw-top { display: none; }

[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) {
  position: sticky;
  top: 0;
  z-index: 999;
  padding: 0 20px;
  align-items: center;
  min-height: 68px;
  gap: 12px;
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  justify-content: space-between !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.28);
  border-bottom: 2.5px solid #c4a35a;
  background: linear-gradient(180deg, #062314 0%, #082d1a 100%);
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:first-child {
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: 0 !important;
  max-width: none !important;
  display: flex !important;
  align-items: center !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:nth-child(2) {
  flex: 1 1 auto !important;
  width: auto !important;
  min-width: 0 !important;
  overflow: visible !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:nth-child(2) > [data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:nth-child(2) div[data-testid="stVerticalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  overflow: visible !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:nth-child(2) div.stElementContainer {
  width: auto !important;
  max-width: 100% !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:last-child {
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: 0 !important;
  max-width: none !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:last-child > [data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:last-child div[data-testid="stVerticalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 10px !important;
  width: auto !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) > [data-testid="stColumn"]:last-child div.stElementContainer {
  width: auto !important;
  flex: 0 0 auto !important;
  margin: 0 !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
}
.header-brand {
  display: inline-flex !important;
  flex-direction: row !important;
  align-items: center !important;
  gap: 10px !important;
  white-space: nowrap !important;
  text-decoration: none !important;
}
.header-crest {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 32px !important;
  height: 32px !important;
  flex: 0 0 32px !important;
}
.header-crest svg {
  width: 32px !important;
  height: 32px !important;
  display: block !important;
}
.header-title-box {
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  line-height: 1.15 !important;
}
.header-main-title {
  font-size: 14.5px !important;
  font-weight: 750 !important;
  letter-spacing: -0.02em !important;
  color: #ffffff !important;
  line-height: 1.2 !important;
}
.header-sub-tag {
  font-size: 9px !important;
  font-weight: 600 !important;
  color: #c4a35a !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  line-height: 1.2 !important;
}
.topbar-status-badge {
  display: inline-flex !important;
  align-items: center !important;
  gap: 7px !important;
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(196, 163, 90, 0.45) !important;
  border-radius: 999px !important;
  padding: 4px 10px !important;
  color: #e6f4ea !important;
  font-size: 11.5px !important;
  letter-spacing: 0.02em !important;
  white-space: nowrap !important;
  height: 28px !important;
  box-sizing: border-box !important;
}
.topbar-status-dot {
  width: 7px !important;
  height: 7px !important;
  border-radius: 50% !important;
  background-color: #22c55e !important;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.9) !important;
  flex-shrink: 0 !important;
  animation: statusPulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite !important;
}
@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.85); }
}
.topbar-status-text strong { color: #ffffff !important; font-weight: 700 !important; }
.topbar-status-text em { color: #e2c87d !important; font-style: normal !important; font-weight: 600 !important; }

.st-key-page_nav {
  position: static !important;
  background: transparent !important;
  border: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  width: auto !important;
  max-width: 100% !important;
  box-shadow: none !important;
}
.st-key-page_nav [data-testid="stWidgetLabel"],
.st-key-lang_nav [data-testid="stWidgetLabel"],
.st-key-role_nav [data-testid="stWidgetLabel"],
.st-key-alert_filter [data-testid="stWidgetLabel"],
.st-key-season_pick [data-testid="stWidgetLabel"],
.st-key-map_layer [data-testid="stWidgetLabel"] { display: none !important; }
.st-key-page_nav [data-testid="stButtonGroup"] {
  display: inline-flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 3px !important;
  width: auto !important;
  justify-content: center !important;
  align-items: center !important;
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
}
.st-key-page_nav [data-testid="stButtonGroup"] > div {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  flex: 0 0 auto !important;
}
.st-key-page_nav button {
  background: transparent !important;
  border: none !important;
  border-bottom: 2.5px solid transparent !important;
  box-shadow: none !important;
  color: #cfe3d5 !important;
  font-weight: 600 !important;
  font-size: 12.5px !important;
  letter-spacing: 0.01em !important;
  border-radius: 4px !important;
  padding: 5px 9px !important;
  min-height: 36px !important;
  height: 36px !important;
  margin: 0 !important;
  white-space: nowrap !important;
  flex: 0 0 auto !important;
  transition: all 0.16s ease-in-out !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.st-key-page_nav button:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  color: #ffffff !important;
  border-bottom: 2.5px solid rgba(196, 163, 90, 0.6) !important;
}
.st-key-page_nav button[aria-checked="true"] {
  color: #ffffff !important;
  background: rgba(196, 163, 90, 0.16) !important;
  border-bottom: 2.5px solid #c4a35a !important;
  font-weight: 750 !important;
  box-shadow: none !important;
}
.st-key-lang_nav {
  display: inline-flex !important;
  align-items: center !important;
  height: 28px !important;
  margin: 0 !important;
}
.st-key-lang_nav [data-testid="stButtonGroup"] {
  border: 1px solid rgba(196, 163, 90, 0.5) !important;
  border-radius: 999px !important;
  overflow: hidden !important;
  background: rgba(0, 0, 0, 0.25) !important;
  padding: 2px !important;
  gap: 2px !important;
  display: inline-flex !important;
  align-items: center !important;
  height: 28px !important;
  box-sizing: border-box !important;
  margin: 0 !important;
}
.st-key-lang_nav [data-testid="stButtonGroup"] > div {
  border-radius: 0 !important;
  background: transparent !important;
  height: 24px !important;
  display: flex !important;
  align-items: center !important;
}
.st-key-lang_nav button {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  color: #d1e7d8 !important;
  font-weight: 700 !important;
  font-size: 11px !important;
  border-radius: 999px !important;
  min-height: 22px !important;
  height: 22px !important;
  min-width: 32px !important;
  padding: 2px 7px !important;
  transition: all 0.15s ease !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.st-key-lang_nav button[aria-checked="true"] {
  background: #c4a35a !important;
  color: #062615 !important;
  font-weight: 800 !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2) !important;
}

.landing-brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 750;
  letter-spacing: -0.03em;
  color: #fff;
  white-space: nowrap;
}
.landing-brand > span { display: flex; flex-direction: column; line-height: 1.05; }
.landing-brand small {
  display: block;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #cfe3d4;
  margin-top: 2px;
}
.landing-brand svg { width: 30px; height: 30px; flex: 0 0 30px; }
.header-brand { font-size: 16px; gap: 8px; }
.header-brand small { display: none; }
.header-brand svg { width: 28px; height: 28px; flex: 0 0 28px; }
.landing-footer .landing-brand { font-size: 20px; gap: 12px; }
.landing-footer .landing-brand small { display: block; font-size: 11px; }

.st-key-alert_filter,
.st-key-season_pick,
.st-key-district_pick,
.st-key-soil_district,
.st-key-watch_district,
.st-key-chat_district {
  max-width: 1320px;
  margin: 0 auto !important;
  padding: 8px 40px 4px;
}
.st-key-alert_filter [data-testid="stButtonGroup"],
.st-key-season_pick [data-testid="stButtonGroup"] {
  gap: 0 !important;
  border: 1px solid var(--lp-line);
  border-radius: 2px;
  overflow: hidden;
  background: #fff;
}
.st-key-alert_filter button,
.st-key-season_pick button {
  background: #fff !important;
  border: 0 !important;
  border-right: 1px solid var(--lp-line) !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  color: var(--lp-ink) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  min-height: 44px !important;
  padding: 10px 16px !important;
}
.st-key-alert_filter button[aria-checked="true"],
.st-key-season_pick button[aria-checked="true"] {
  background: var(--lp-ink) !important;
  color: #fff !important;
}
[data-testid="stSelectbox"] label p {
  font-size: 12px !important;
  font-weight: 650 !important;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--lp-muted) !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  min-height: 52px;
  border: 1px solid var(--lp-ink) !important;
  border-radius: 2px !important;
  background: #fff !important;
  box-shadow: none !important;
}

.page-band {
  background: linear-gradient(180deg, #edf5ee 0%, #ffffff 92%);
  border-bottom: 1px solid var(--lp-line);
  padding: 38px 40px 30px;
}
.page-band .inner, .inner-wrap {
  max-width: 1320px;
  margin: 0 auto;
}
.inner-wrap { padding: 28px 40px 56px; }
.page-band-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}
.page-band-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.page-band-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 650;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(13, 79, 43, 0.08);
  color: #0d4f2b;
  border: 1px solid rgba(13, 79, 43, 0.2);
}
.page-band h1 {
  margin: 0 0 12px;
  font-size: clamp(28px, 3.4vw, 44px);
  font-weight: 750;
  letter-spacing: -0.035em;
  line-height: 1.1;
  color: var(--lp-ink);
  max-width: 28ch;
}
.page-band .lead {
  margin: 0 0 18px;
  max-width: 78ch;
  color: #384234;
  font-size: 16.5px;
  line-height: 1.6;
}
.page-desc-card {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1.8fr);
  gap: 16px;
  background: #ffffff;
  border: 1px solid var(--lp-line);
  border-left: 4px solid #1f8a3a;
  border-radius: 4px;
  padding: 14px 18px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}
.page-desc-item {
  font-size: 13px;
  line-height: 1.5;
  color: #2b3327;
}
.page-desc-item strong {
  display: block;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--lp-green);
  margin-bottom: 3px;
  font-weight: 700;
}
.guide-card {
  background: #ffffff;
  border: 1px solid #d5ddd0;
  border-top: 3px solid #c4a35a;
  border-radius: 4px;
  padding: 16px 20px;
  margin: 20px 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.guide-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.guide-card-head h4 {
  margin: 0;
  font-size: 13.5px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #0d4f2b;
  text-transform: uppercase;
}
.guide-card-body {
  margin: 0;
  font-size: 13.5px;
  line-height: 1.6;
  color: #434c3e;
}

.photo-hero {
  position: relative;
  background-color: #123b24;
  background-image:
    linear-gradient(90deg, rgba(0,38,15,.9) 0%, rgba(0,38,15,.76) 34%, rgba(0,38,15,.18) 66%, rgba(0,38,15,.06) 100%),
    var(--hero-image);
  background-size: cover;
  background-position: center;
  padding: 96px 0 108px;
  color: #fff;
}
.photo-hero::after {
  content: "";
  position: absolute;
  inset: auto 0 -1px;
  height: 22px;
  background: #fff;
  clip-path: ellipse(58% 100% at 50% 100%);
}
.landing-shell {
  box-sizing: border-box;
  width: 100%;
  max-width: 1560px;
  padding-inline: 48px;
  margin-inline: auto;
}
.landing-hero-grid {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 56px;
  align-items: center;
}
.landing-eyebrow {
  margin: 0 0 22px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: #e0efdc;
}
.photo-hero h1 {
  margin: 0 0 22px;
  color: #fff;
  font-size: clamp(36px, 4.4vw, 64px);
  font-weight: 800;
  letter-spacing: -0.045em;
  line-height: 1.05;
  max-width: 22ch;
}
.photo-hero .lead {
  margin: 0 0 32px;
  color: #fff;
  font-size: clamp(18px, 1.7vw, 24px);
  line-height: 1.4;
  max-width: 40ch;
}
.landing-actions { display: flex; flex-wrap: wrap; gap: 14px; }
.photo-hero .landing-actions { margin: 0; }
.cta-band .landing-actions { margin-top: 24px; }
.landing-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 56px;
  padding: 14px 20px;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}
.hero-primary { background: #fff; color: #082b1d; border: 1px solid #fff; }
.hero-primary:hover { background: #e8f3ea; color: #082b1d; }
.hero-secondary { background: rgba(0,30,12,.28); color: #fff; border: 2px solid #fff; }
.hero-secondary:hover { background: rgba(255,255,255,.16); color: #fff; }

.landing-prices {
  background: #fff;
  color: var(--lp-ink);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 40px #00190924;
}
.landing-prices header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22px 24px 18px;
}
.landing-prices h2 {
  margin: 0;
  font-size: clamp(22px, 2vw, 30px);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.live-dot {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 650;
  color: var(--lp-green);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.live-dot::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--lp-green);
  box-shadow: 0 0 0 4px #008a2830;
}
.landing-prices table { width: 100%; border-collapse: collapse; text-align: left; }
.landing-prices th, .landing-prices td,
.data-card th, .data-card td {
  padding: 16px 18px;
  border-top: 1px solid var(--lp-line);
  font-size: 15px;
  vertical-align: middle;
}
.landing-prices thead th, .data-card thead th {
  background: var(--lp-surface);
  font-size: 11px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-weight: 650;
  padding-block: 10px;
  color: var(--lp-muted);
}
.landing-prices tbody th { font-weight: 650; }
.landing-number { text-align: right; font-variant-numeric: tabular-nums; }
.landing-number strong { display: block; font-weight: 650; }
.landing-number span { display: block; color: var(--lp-muted); font-size: 12px; }
.landing-prices footer {
  border-top: 1px solid var(--lp-line);
  padding: 14px 24px;
  font-size: 13px;
  color: var(--lp-muted);
}

.landing-section {
  padding: 64px 0;
  border-bottom: 1px solid var(--lp-line);
  background: #fff;
}
.landing-section .landing-shell { max-width: 1320px; padding-inline: 40px; }
.kicker-green {
  color: var(--lp-hover);
  font-size: 13px;
  font-weight: 650;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0 0 12px;
}
.decision-heading h2, .landing-section h2, .block-title {
  margin: 0 0 12px;
  font-size: clamp(28px, 3vw, 40px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.15;
  color: var(--lp-ink);
}
.section-p, .decision-heading p {
  margin: 0;
  max-width: 72ch;
  color: var(--lp-muted);
  font-size: 17px;
  line-height: 1.6;
}
.decision-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 36px;
}
.decision-grid article { padding: 0 28px; border-left: 1px solid var(--lp-line); }
.decision-grid article:first-child { padding-left: 0; border-left: 0; }
.decision-number {
  display: block;
  color: var(--lp-hover);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.06em;
  margin-bottom: 16px;
}
.decision-grid h3 {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.3;
  color: var(--lp-ink);
}
.decision-grid p { font-size: 16px; color: var(--lp-muted); margin: 0; line-height: 1.55; }

.landing-stats { padding: 8px 0 40px; }
.landing-stats dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
}
.landing-stats dl > div {
  border-top: 1px solid var(--lp-ink);
  display: flex;
  flex-direction: row-reverse;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  padding: 22px 0 0;
}
.landing-stats dl > div + div { padding-left: 32px; }
.landing-stats dd {
  margin: 0;
  color: var(--lp-accent);
  font-size: 40px;
  font-weight: 750;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}
.landing-stats dt { font-size: 15px; color: var(--lp-muted); }

.logic-box {
  margin-top: 36px;
  padding: 28px;
  border: 1px solid var(--lp-line);
  background: var(--lp-surface);
}
.logic-box strong { display: block; margin-bottom: 12px; font-size: 16px; }
.logic-box ol { margin: 0; padding-left: 1.2rem; color: var(--lp-muted); }
.logic-box li { margin: 8px 0; line-height: 1.5; }

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 650;
  letter-spacing: 0.02em;
  border-radius: 2px;
  white-space: nowrap;
}
.status-pill.irrigation_gap { background: #fff6e5; color: var(--lp-amber); }
.status-pill.irrigate_now { background: #fde8e8; color: var(--lp-red); }
.status-pill.soil_rain, .status-pill.soil_watch { background: #f4eee6; color: var(--lp-soil); }
.status-pill.dry_watch { background: #eef2f6; color: #344054; }
.status-pill.stable, .status-pill.normal_monitoring { background: #edf5ee; color: var(--lp-hover); }
.status-pill.water_stress { background: #fde8e8; color: var(--lp-red); }
.status-pill.rainfall_watch { background: #fff6e5; color: var(--lp-amber); }
.status-pill.excess_rain { background: #f4eee6; color: var(--lp-soil); }
.status-pill.agronomist { background: #f3e8ff; color: #6d28d9; }
.intel-card {
  margin: 16px 0 8px;
  padding: 20px 22px;
  border: 1px solid var(--lp-line);
  background: #fff;
}
.intel-card dl { display: grid; grid-template-columns: 180px 1fr; gap: 10px 18px; margin: 12px 0 0; }
.intel-card dt { font-size: 12px; letter-spacing: 0.05em; text-transform: uppercase; color: var(--lp-muted); font-weight: 650; }
.intel-card dd { margin: 0; font-size: 15px; line-height: 1.5; }

.board {
  background: #fff;
  border: 1px solid var(--lp-line);
  padding: 32px;
  margin: 12px 0 28px;
}
.board-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}
.board-head h2 {
  margin: 0;
  font-size: clamp(28px, 3vw, 40px);
  font-weight: 750;
  letter-spacing: -0.03em;
}
.board-copy {
  margin: 0 0 12px;
  max-width: 78ch;
  font-size: 17px;
  line-height: 1.55;
  color: var(--lp-ink);
}
.board-action {
  margin: 0;
  font-size: 15px;
  font-weight: 650;
  color: var(--lp-hover);
}
.board-action:empty { display: none; }
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  background: var(--lp-line);
  border: 1px solid var(--lp-line);
  margin-top: 28px;
}
.kpi-row.five { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.kpi-row.six { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.kpi {
  background: #fff;
  padding: 18px 20px 16px;
}
.kpi span {
  display: block;
  font-size: 11px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--lp-muted);
  font-weight: 650;
  margin-bottom: 10px;
}
.kpi strong {
  display: block;
  font-size: 30px;
  font-weight: 750;
  letter-spacing: -0.03em;
  color: var(--lp-accent);
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}
.kpi small { color: var(--lp-muted); font-size: 12px; }

.week-panel { margin-top: 32px; }
.week-head h3 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.week-head p { margin: 0 0 20px; color: var(--lp-muted); font-size: 15px; }
.week-bars {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
}
.week-day {
  border: 1px solid var(--lp-line);
  background: var(--lp-surface);
  padding: 12px 8px 14px;
  text-align: center;
}
.week-day em {
  display: block;
  font-style: normal;
  font-size: 12px;
  font-weight: 650;
  color: var(--lp-muted);
  margin-bottom: 10px;
}
.week-track {
  height: 88px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  margin-bottom: 10px;
}
.week-track i {
  display: block;
  width: 28px;
  background: var(--lp-green);
  border-radius: 2px 2px 0 0;
}
.week-day strong {
  display: block;
  font-size: 16px;
  font-variant-numeric: tabular-nums;
}
.week-day span { display: block; font-size: 11px; color: var(--lp-muted); }
.week-day .week-bal { font-weight: 650; color: var(--lp-green); }

.data-card {
  border: 1px solid var(--lp-line);
  background: #fff;
  overflow: auto;
  margin: 12px 0 32px;
}
.data-card table { width: 100%; border-collapse: collapse; text-align: left; }
.data-card tbody th { font-weight: 650; }
.bar-cell { min-width: 120px; }
.bar-cell b {
  display: block;
  font-variant-numeric: tabular-nums;
  font-size: 14px;
  margin-bottom: 6px;
}
.bar-cell i {
  display: block;
  height: 6px;
  background: var(--lp-green);
  border-radius: 2px;
}

.note-box {
  margin: 8px 0 24px;
  padding: 20px 22px;
  border-left: 3px solid var(--lp-green);
  background: var(--lp-soft);
  color: var(--lp-ink);
  font-size: 16px;
  line-height: 1.55;
}
.split-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 8px 0 28px;
}
.split-cards article {
  border: 1px solid var(--lp-line);
  padding: 22px;
  background: #fff;
}
.split-cards h3 { margin: 0 0 8px; font-size: 16px; }
.split-cards p { margin: 0; color: var(--lp-muted); font-size: 15px; line-height: 1.5; }

.method-list { margin: 8px 0 8px; }
.method-list article {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 8px 20px;
  padding: 22px 0;
  border-bottom: 1px solid var(--lp-line);
}
.method-list .step {
  color: var(--lp-green);
  font-weight: 750;
  font-size: 14px;
  letter-spacing: 0.06em;
}
.method-list p {
  margin: 0;
  color: var(--lp-muted);
  font-size: 16px;
  line-height: 1.65;
}

.fresh-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin: 8px 0 28px;
}
.fresh-list article {
  border-top: 1px solid var(--lp-ink);
  padding-top: 16px;
}
.fresh-list span {
  display: block;
  font-size: 12px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--lp-muted);
  font-weight: 650;
  margin-bottom: 8px;
}
.fresh-list strong { font-size: 20px; letter-spacing: -0.02em; }

.landing-footer {
  display: block !important;
  background-color: #051d11;
  color: #c9dbcf;
  padding: 56px 40px 24px;
  margin-top: 0;
  border-top: 4px solid #c4a35a;
}
.landing-footer .landing-brand { color: #fff; margin-bottom: 12px; }
.landing-footer .landing-brand svg { width: 34px; height: 34px; }
.landing-footer-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) repeat(3, minmax(0, 1fr));
  gap: 40px 48px;
  max-width: 1320px;
  margin: 0 auto;
  align-items: start;
}
.landing-footer h2 {
  color: #ffffff;
  font-size: 12px;
  font-weight: 750;
  margin: 0 0 14px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  padding-bottom: 6px;
}
.landing-footer p, .landing-footer li {
  font-size: 13px;
  line-height: 1.6;
  margin: 0 0 8px;
  color: #c2d6c9;
}
.landing-footer ul { list-style: none; margin: 0; padding: 0; }
.landing-footer a {
  color: #dbebe1;
  text-decoration: none;
  transition: color 0.15s ease;
}
.landing-footer a:hover {
  color: #ffffff;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.footer-desc {
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 14px !important;
  color: #b7cebf;
}
.footer-nst2-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(196, 163, 90, 0.12);
  border: 1px solid rgba(196, 163, 90, 0.35);
  border-radius: 4px;
  color: #ebd79e;
  font-size: 11.5px;
  font-weight: 600;
  margin-bottom: 14px;
}
.footer-tagline-text {
  color: #ffffff !important;
  font-weight: 700;
  font-size: 13px !important;
  letter-spacing: 0.01em;
}
.footer-links li { margin-bottom: 6px; }
.footer-links a {
  display: inline-block;
  color: #c9dbcf;
  font-weight: 500;
}
.footer-links a:hover { color: #ffffff; }
.footer-partners-list li {
  margin-bottom: 10px;
  font-size: 12.5px;
  line-height: 1.45;
}
.footer-partners-list strong { color: #ffffff; }
.footer-legal-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 12px 14px;
}
.footer-legal-notice, .footer-legal-privacy {
  font-size: 12px !important;
  line-height: 1.55 !important;
  margin-bottom: 8px !important;
  color: #b2c9bb !important;
}
.footer-legal-privacy { margin-bottom: 0 !important; }
.footer-legal-card strong { color: #ffffff; }
.landing-footer-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  margin-top: 36px;
  padding-top: 20px;
}
.footer-bottom-inner {
  max-width: 1320px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 12px;
  color: #9cb5a5;
}
.footer-bottom-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.badge-tag {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 10.5px;
  color: #cfe2d5;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.kind-pill {
  display: inline-block;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 4px 8px;
  background: var(--lp-soft);
  color: var(--lp-green);
  margin-bottom: 10px;
}
.source-card {
  border: 1px solid var(--lp-line);
  background: #fff;
  padding: 24px;
  margin: 0 0 16px;
}
.source-card h3 { margin: 0 0 8px; font-size: 22px; }
.source-card dl { display: grid; grid-template-columns: 160px 1fr; gap: 8px 16px; margin: 16px 0 0; }
.source-card dt { font-size: 12px; letter-spacing: 0.05em; text-transform: uppercase; color: var(--lp-muted); font-weight: 650; }
.source-card dd { margin: 0; font-size: 15px; line-height: 1.5; }
.process-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-top: 28px;
}
.process-row.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.process-row article {
  background: #fff;
  border: 1px solid var(--lp-line);
  padding: 18px 16px;
}
.process-row span { display: block; color: var(--lp-accent); font-weight: 750; font-size: 12px; letter-spacing: 0.08em; margin-bottom: 10px; }
.process-row h3 { margin: 0 0 8px; font-size: 16px; }
.process-row p { margin: 0; color: var(--lp-muted); font-size: 14px; line-height: 1.5; }
.challenge-list { margin: 20px 0 0; padding: 0; list-style: none; }
.challenge-list li {
  padding: 14px 0;
  border-top: 1px solid var(--lp-line);
  font-size: 16px;
  line-height: 1.5;
}
.why-box {
  margin-top: 20px;
  padding: 18px 20px;
  border: 1px solid var(--lp-line);
  background: var(--lp-soft);
}
.why-box strong { display: block; margin-bottom: 8px; }
.why-box p { margin: 0 0 8px; font-size: 15px; line-height: 1.55; color: var(--lp-ink); }
.glossary { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; margin-top: 16px; }
.glossary p { margin: 0; padding: 10px 0; border-bottom: 1px solid var(--lp-line); font-size: 15px; }
.landing-copyright {
  max-width: 1320px;
  margin: 0 auto;
  border-top: 1px solid #ffffff26;
  padding: 22px 0;
  font-size: 12px;
}

.who-strip {
  max-width: 1320px;
  margin: 0 auto;
  padding: 10px 40px 0;
}
.who-strip p { font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--lp-muted); font-weight: 650; margin: 0 0 6px; }
.st-key-role_nav { max-width: 1320px; margin: 0 auto !important; padding: 0 40px 12px; }
.st-key-role_nav button {
  font-size: 13px !important;
  min-height: 36px !important;
  padding: 6px 12px !important;
}
.viewer {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 200px;
  gap: 16px;
  max-width: 1320px;
  margin: 0 auto 24px;
  padding: 0 40px;
  align-items: start;
}
.viewer-panel, .legend-card {
  border: 1px solid var(--lp-line);
  background: #fff;
  padding: 16px 16px 12px;
}
.viewer-panel h3, .legend-card h3 {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.viewer-panel p, .legend-card p { font-size: 13px; color: var(--lp-muted); line-height: 1.5; margin: 0 0 12px; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; margin: 6px 0; }
.legend-swatch { width: 14px; height: 14px; border-radius: 2px; flex: 0 0 14px; }
.phone-wrap { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 24px; align-items: start; margin-top: 28px; }
.feature-phone {
  width: 240px;
  background: #1a1d27;
  border-radius: 28px;
  padding: 18px 14px 22px;
  color: #d7f5d0;
}
.feature-phone .phone-bar { text-align: center; font-size: 11px; letter-spacing: 0.16em; margin-bottom: 10px; color: #8aa08a; }
.feature-phone .phone-screen {
  background: #0c1f12;
  min-height: 220px;
  padding: 12px;
  font-family: "Lucida Console", ui-monospace, monospace;
  font-size: 12px;
  line-height: 1.45;
  white-space: pre-wrap;
}
.policy-badge {
  display: inline-block;
  background: var(--lp-soft);
  color: var(--lp-green);
  font-size: 12px;
  font-weight: 650;
  padding: 8px 10px;
  margin: 8px 0 16px;
}
.st-key-map_layer { padding: 0 !important; margin: 0 !important; }
.cta-band {
  background: #0a3d22;
  color: #fff;
  padding: 56px 0 64px;
}
.cta-band .kicker-gold {
  color: #e8c878;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 13px;
  font-weight: 650;
  margin: 0 0 12px;
}
.cta-band h2 {
  color: #fff;
  font-size: clamp(24px, 2.6vw, 36px);
  max-width: 28ch;
  margin: 0;
  font-weight: 750;
  letter-spacing: -0.03em;
  line-height: 1.2;
}
[data-testid="stHorizontalBlock"]:has(.st-key-home_go_dash) {
  max-width: 1120px;
  margin: -80px auto 0;
  padding: 0 40px 48px;
  gap: 16px;
  position: relative;
  z-index: 6;
}
[data-testid="stDownloadButton"],
[data-testid="stHorizontalBlock"]:has(.st-key-dash_to_alerts),
[data-testid="stHorizontalBlock"]:has(.st-key-ussd_w),
.st-key-dash_district,
.st-key-dash_csv,
.st-key-dash_html,
.st-key-sim_district_select,
.st-key-ssit_district {
  max-width: 1320px;
  margin-left: auto !important;
  margin-right: auto !important;
  padding-left: 40px;
  padding-right: 40px;
}
[data-testid="stHorizontalBlock"]:has(.st-key-map_layer) {
  max-width: 1560px;
  margin: 0 auto 28px;
  padding: 12px 40px 8px;
  gap: 20px;
  background: #fff;
}
.st-key-home_go_alerts button,
.st-key-home_go_dash button {
  background: var(--lp-green) !important;
  color: #fff !important;
  border: 0 !important;
  border-radius: 4px !important;
  min-height: 56px !important;
  font-weight: 650 !important;
  font-size: 16px !important;
}
.st-key-home_go_advise button,
.st-key-home_go_sim button,
.st-key-home_go_method button {
  background: #fff !important;
  color: var(--lp-ink) !important;
  border: 1px solid var(--lp-ink) !important;
  border-radius: 4px !important;
  min-height: 56px !important;
  font-weight: 650 !important;
  font-size: 16px !important;
}
.st-key-home_go_alerts button:hover,
.st-key-home_go_dash button:hover { background: var(--lp-hover) !important; }
.st-key-home_go_advise button:hover,
.st-key-home_go_sim button:hover,
.st-key-home_go_method button:hover { background: var(--lp-soft) !important; }
[data-testid="stChatMessageAvatar"],
[data-testid="stChatMessage"] img { display: none !important; }
[data-testid="stChatMessage"] {
  border: 1px solid var(--lp-line);
  background: #fff;
  padding: 12px 16px !important;
  margin-bottom: 8px;
  max-width: 920px;
  margin-left: auto;
  margin-right: auto;
}
[data-testid="stChatInput"] { max-width: 920px; margin: 12px auto 40px; }
[data-testid="stHorizontalBlock"]:has(.st-key-q_week) {
  max-width: 920px;
  margin: 0 auto 12px;
  padding: 0 40px;
  gap: 10px;
}
.st-key-q_week button, .st-key-q_kit button, .st-key-q_soil button, .st-key-q_price button {
  border: 1px solid var(--lp-line) !important;
  background: #fff !important;
  color: var(--lp-ink) !important;
  border-radius: 999px !important;
  min-height: 40px !important;
  font-weight: 600 !important;
}
@media (max-width: 980px) {
  .viewer, .phone-wrap { grid-template-columns: 1fr; padding-inline: 20px; }
}

@media (min-width: 1280px) {
  .st-key-page_nav [data-testid="stButtonGroup"] {
    flex-wrap: nowrap !important;
    justify-content: center;
    gap: 4px;
  }
}
@media (max-width: 1180px) {
  .st-key-page_nav button { min-height: 34px !important; height: 34px !important; padding: 4px 8px !important; font-size: 12px !important; }
}
@media (max-width: 1040px) {
  .st-key-page_nav button { min-height: 32px !important; height: 32px !important; padding: 3px 6px !important; font-size: 11.5px !important; }
  .header-sub-tag { display: none !important; }
  .topbar-status-badge { padding: 3px 8px !important; font-size: 10.5px !important; }
}
@media (max-width: 980px) {
  [data-testid="stHorizontalBlock"]:has(.st-key-lang_nav):has(.st-key-page_nav) { padding-inline: 16px; }
  .landing-shell, .inner-wrap, .page-band { padding-inline: 20px; }
  [data-testid="stHorizontalBlock"]:has(.st-key-home_go_dash) { padding-inline: 20px; }
  .st-key-alert_filter, .st-key-season_pick, .st-key-district_pick, .st-key-soil_district, .st-key-watch_district { padding-inline: 20px; }
  .landing-hero-grid, .decision-grid, .landing-stats dl, .landing-footer-grid,
  .kpi-row, .kpi-row.five, .kpi-row.six, .week-bars, .split-cards, .fresh-list,
  .process-row, .source-card dl, .glossary { grid-template-columns: 1fr; }
  .photo-hero { padding-block: 48px 56px; }
  .photo-hero h1 { font-size: 42px; max-width: 18ch; }
  .decision-grid article, .decision-grid article:first-child {
    border-left: 0;
    border-top: 1px solid var(--lp-line);
    padding: 24px 0;
  }
  .landing-stats dl > div + div { padding-left: 0; }
}

/* AI Agronomic Copilot Styles */
.ai-telemetry-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  background: #ffffff;
  border: 1px solid #d5ddd0;
  border-radius: 8px;
  padding: 14px 18px;
  margin: 12px auto 18px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}
.ai-telemetry-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-right: 12px;
  border-right: 1px solid #eef2ec;
}
.ai-telemetry-card:last-child {
  border-right: none;
  padding-right: 0;
}
.ai-telemetry-label {
  font-size: 11px;
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #556353;
}
.ai-telemetry-val {
  font-size: 20px;
  font-weight: 800;
  color: #0d4f2b;
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.ai-telemetry-hint {
  font-size: 11px;
  color: #71816f;
}
.ai-welcome-box {
  background: #ffffff;
  border: 1px solid #cfe0d4;
  border-left: 4px solid #0d4f2b;
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.ai-side-card {
  background: #ffffff;
  border: 1px solid #d5ddd0;
  border-radius: 8px;
  padding: 16px 18px;
  margin-bottom: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.ai-side-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 750;
  color: #0d4f2b;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #edf1eb;
}
.ai-side-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  font-size: 12.5px;
  border-bottom: 1px dashed #f0f4ee;
}
.ai-side-stat:last-child {
  border-bottom: none;
}
.ai-side-stat-lbl {
  color: #556353;
}
.ai-side-stat-val {
  font-weight: 700;
  color: #1a1f16;
}
.ai-sms-screen {
  background: #0f2115;
  color: #a7f3d0;
  border: 1px solid #234830;
  border-radius: 6px;
  padding: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 8px;
  white-space: pre-wrap;
  word-break: break-word;
}
.st-key-btn_ai_yield button,
.st-key-btn_ai_insur button,
.st-key-btn_ai_market button,
.st-key-btn_ai_irrig button,
.st-key-btn_ai_soil button,
.st-key-btn_ai_pests button,
.st-key-btn_ai_sms button,
.st-key-btn_ai_week button {
  background: #ffffff !important;
  border: 1px solid #c9d6c4 !important;
  color: #0b3d21 !important;
  font-weight: 700 !important;
  font-size: 12px !important;
  border-radius: 8px !important;
  min-height: 42px !important;
  padding: 6px 10px !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
  transition: all 0.18s ease !important;
}
.st-key-btn_ai_yield button:hover,
.st-key-btn_ai_insur button:hover,
.st-key-btn_ai_market button:hover,
.st-key-btn_ai_irrig button:hover,
.st-key-btn_ai_soil button:hover,
.st-key-btn_ai_pests button:hover,
.st-key-btn_ai_sms button:hover,
.st-key-btn_ai_week button:hover {
  background: #0d4f2b !important;
  color: #ffffff !important;
  border-color: #0d4f2b !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 4px 12px rgba(13, 79, 43, 0.22) !important;
}

/* Real-Time Alert Telemetry & Triage */
.alert-telemetry-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  background: #ffffff;
  border: 1px solid var(--lp-line);
  border-radius: 8px;
  padding: 10px 18px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.telemetry-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #2c3a2f;
}
.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.pulse-dot.green {
  background-color: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.8);
  animation: statusPulse 2s infinite;
}
.pulse-dot.gold {
  background-color: #c4a35a;
  box-shadow: 0 0 6px rgba(196, 163, 90, 0.8);
}
.pulse-dot.blue {
  background-color: #2563eb;
  box-shadow: 0 0 6px rgba(37, 99, 235, 0.8);
}

.alert-triage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}
.alert-triage-card {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--lp-line);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  display: flex;
  flex-direction: column;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.alert-triage-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.07);
}
.alert-triage-card.critical { border-top: 4px solid #b42318; background: #fffbfa; }
.alert-triage-card.high { border-top: 4px solid #d97706; background: #fffdf5; }
.alert-triage-card.soil { border-top: 4px solid #2563eb; background: #f8faff; }
.alert-triage-card.stable { border-top: 4px solid #16a34a; background: #f6fcf8; }

.triage-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.triage-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--lp-muted);
}
.triage-count {
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
}
.alert-triage-card.critical .triage-count { color: #b42318; }
.alert-triage-card.high .triage-count { color: #d97706; }
.alert-triage-card.soil .triage-count { color: #2563eb; }
.alert-triage-card.stable .triage-count { color: #16a34a; }
.triage-desc {
  font-size: 12px;
  color: #3f4e43;
  margin-top: 4px;
  line-height: 1.35;
}

/* Provable Evidence Box */
.provable-evidence-box {
  background: #ffffff;
  border: 1.5px solid #c4a35a;
  border-radius: 8px;
  margin-top: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(196, 163, 90, 0.08);
}
.evidence-math-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1px;
  background: #e5ece2;
  border-bottom: 1px solid #e5ece2;
}
.evidence-math-cell {
  background: #ffffff;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.math-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #4a5a4e;
  margin-bottom: 4px;
}
.math-value {
  font-size: 18px;
  font-weight: 800;
  color: #062615;
  margin-bottom: 2px;
}
.math-formula {
  font-size: 11px;
  color: #6c7d70;
  font-family: monospace;
}
.evidence-audit-footer {
  padding: 12px 18px;
  background: #f7faf6;
}
.evidence-stamp {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.stamp-icon {
  font-size: 20px;
  line-height: 1;
}
.evidence-stamp strong {
  display: block;
  font-size: 11.5px;
  font-weight: 750;
  color: #0d4f2b;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 2px;
}
.evidence-stamp p {
  margin: 0;
  font-size: 11.5px;
  line-height: 1.45;
  color: #3b4e40;
}
.evidence-stamp code {
  background: #e8efe7;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 10.5px;
  color: #0d4f2b;
}
"""


def inject():
    encoded = base64.b64encode(HERO.read_bytes()).decode("ascii")
    css = CSS.replace("var(--hero-image)", f'url("data:image/jpeg;base64,{encoded}")')
    return f"<style>{css}</style>"
