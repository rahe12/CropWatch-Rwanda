"""Product UI: Inter, photo hero, district boards, status pills, sharp cards."""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERO = ROOT / "assets" / "hero.jpg"

CSS = r"""
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");

:root {
  --lp-ink: #080d25;
  --lp-muted: #475467;
  --lp-green: #008a28;
  --lp-hover: #006e20;
  --lp-soft: #edf5ee;
  --lp-surface: #f5f6f5;
  --lp-line: #d8deda;
  --lp-amber: #9a5700;
  --lp-red: #b42318;
  --lp-soil: #7a4e22;
}

html, body, [class*="css"], .stApp, p, h1, h2, h3, label, span, button, input, table {
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}
.stApp { background: #fff; color: var(--lp-ink); }
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stAppDeployButton,
#MainMenu,
footer,
[data-testid="stHeaderActionElements"] { display: none !important; }
.block-container, .stMainBlockContainer {
  padding: 0 !important;
  max-width: 100% !important;
}
.stMainBlockContainer > div > [data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stElementToolbar"] { display: none !important; }
#cw-top { display: none; }

[data-testid="stHorizontalBlock"]:has(.st-key-page_nav) {
  position: sticky;
  top: 0;
  z-index: 80;
  background: #fff;
  border-bottom: 1px solid var(--lp-line);
  padding: 0 40px;
  align-items: center;
  min-height: 76px;
  gap: 12px;
}
.st-key-page_nav [data-testid="stWidgetLabel"],
.st-key-lang_nav [data-testid="stWidgetLabel"],
.st-key-alert_filter [data-testid="stWidgetLabel"],
.st-key-season_pick [data-testid="stWidgetLabel"] { display: none !important; }
.st-key-page_nav [data-testid="stButtonGroup"] {
  flex-wrap: nowrap !important;
  gap: 2px !important;
}
.st-key-page_nav [data-testid="stButtonGroup"] > div {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.st-key-page_nav button {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  color: var(--lp-ink) !important;
  font-weight: 600 !important;
  font-size: 15px !important;
  border-radius: 0 !important;
  border-bottom: 2px solid transparent !important;
  padding: 22px 14px 20px !important;
  min-height: 76px !important;
  white-space: nowrap !important;
}
.st-key-page_nav button[aria-checked="true"] {
  color: var(--lp-green) !important;
  border-bottom-color: var(--lp-green) !important;
  background: transparent !important;
}
.st-key-lang_nav [data-testid="stButtonGroup"] {
  border: 1px solid var(--lp-ink);
  border-radius: 2px;
  overflow: hidden;
  gap: 0 !important;
  justify-content: flex-end;
}
.st-key-lang_nav [data-testid="stButtonGroup"] > div {
  border-radius: 0 !important;
  background: transparent !important;
}
.st-key-lang_nav button {
  background: #fff !important;
  border: 0 !important;
  box-shadow: none !important;
  color: var(--lp-ink) !important;
  font-weight: 650 !important;
  font-size: 13px !important;
  border-radius: 0 !important;
  min-height: 36px !important;
  min-width: 46px !important;
  padding: 8px 14px !important;
}
.st-key-lang_nav button[aria-checked="true"] {
  background: var(--lp-ink) !important;
  color: #fff !important;
}

.landing-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 25px;
  font-weight: 750;
  letter-spacing: -0.03em;
  color: var(--lp-ink);
  white-space: nowrap;
}
.landing-brand svg { width: 40px; height: 40px; flex: 0 0 40px; }

.st-key-alert_filter,
.st-key-season_pick,
.st-key-district_pick,
.st-key-soil_district,
.st-key-watch_district {
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
  background: linear-gradient(180deg, #edf5ee 0%, #ffffff 88%);
  border-bottom: 1px solid var(--lp-line);
  padding: 48px 40px 36px;
}
.page-band .inner, .inner-wrap {
  max-width: 1320px;
  margin: 0 auto;
}
.inner-wrap { padding: 28px 40px 56px; }
.page-band .kicker-green { margin-bottom: 14px; }
.page-band h1 {
  margin: 0 0 14px;
  font-size: clamp(36px, 4vw, 56px);
  font-weight: 750;
  letter-spacing: -0.04em;
  line-height: 1.05;
  color: var(--lp-ink);
  max-width: 18ch;
}
.page-band .lead {
  margin: 0;
  max-width: 62ch;
  color: var(--lp-muted);
  font-size: 18px;
  line-height: 1.55;
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
  font-size: clamp(44px, 5.2vw, 80px);
  font-weight: 800;
  letter-spacing: -0.045em;
  line-height: 1.02;
  max-width: 15ch;
}
.photo-hero .lead {
  margin: 0 0 32px;
  color: #fff;
  font-size: clamp(18px, 1.7vw, 24px);
  line-height: 1.4;
  max-width: 40ch;
}
.landing-actions { display: flex; flex-wrap: wrap; gap: 14px; }
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
}
.hero-primary { background: #fff; color: #082b1d; border: 1px solid #fff; }
.hero-secondary { background: rgba(0,30,12,.28); color: #fff; border: 2px solid #fff; }

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
  color: var(--lp-green);
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
.status-pill.stable { background: #edf5ee; color: var(--lp-hover); }

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
  color: var(--lp-green);
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
.week-day span { font-size: 11px; color: var(--lp-muted); }

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
  background-color: var(--lp-ink);
  color: #d6e3dc;
  padding: 52px 40px 22px;
  margin-top: 0;
}
.landing-footer .landing-brand { color: #fff; }
.landing-footer-grid {
  display: grid;
  grid-template-columns: minmax(0,4fr) minmax(0,2.5fr) minmax(0,2.5fr) minmax(0,3fr);
  gap: 32px;
  max-width: 1320px;
  margin: 0 auto 24px;
}
.landing-footer h2 { color: #fff; font-size: 14px; font-weight: 650; margin: 0 0 10px; letter-spacing: 0.04em; text-transform: uppercase; }
.landing-footer p { font-size: 14px; max-width: 32ch; line-height: 1.6; margin: 0 0 6px; }
.landing-copyright {
  max-width: 1320px;
  margin: 0 auto;
  border-top: 1px solid #ffffff26;
  padding: 22px 0;
  font-size: 12px;
}

@media (max-width: 980px) {
  [data-testid="stHorizontalBlock"]:has(.st-key-page_nav) { padding-inline: 16px; }
  .landing-shell, .inner-wrap, .page-band { padding-inline: 20px; }
  .st-key-alert_filter, .st-key-season_pick, .st-key-district_pick, .st-key-soil_district, .st-key-watch_district { padding-inline: 20px; }
  .landing-hero-grid, .decision-grid, .landing-stats dl, .landing-footer-grid,
  .kpi-row, .kpi-row.five, .week-bars, .split-cards, .fresh-list { grid-template-columns: 1fr; }
  .photo-hero { padding-block: 48px 56px; }
  .photo-hero h1 { font-size: 42px; max-width: 18ch; }
  .decision-grid article, .decision-grid article:first-child {
    border-left: 0;
    border-top: 1px solid var(--lp-line);
    padding: 24px 0;
  }
  .landing-stats dl > div + div { padding-left: 0; }
}
"""


def inject():
    encoded = base64.b64encode(HERO.read_bytes()).decode("ascii")
    css = CSS.replace("var(--hero-image)", f'url("data:image/jpeg;base64,{encoded}")')
    return f"<style>{css}</style>"
