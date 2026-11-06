import base64
import importlib
import json
import os
from pathlib import Path
from datetime import date, timedelta

import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import src.logic as logic_mod
import src.advise as advise_mod
import src.export_note as export_mod
import src.sources as sources_mod
import src.style as style_mod
import src.words as words_mod

importlib.reload(logic_mod)
importlib.reload(words_mod)
importlib.reload(style_mod)
importlib.reload(advise_mod)
importlib.reload(sources_mod)
importlib.reload(export_mod)

from src.advise import (
    answer,
    audio_speech_html,
    llm_status,
    pack,
    sms_text,
    classify,
    extract_district,
    get_followups,
)
from src.logic import district_share_whatif, drought_screen, national_ranking, ssit_plan
from src.export_note import html_report
from src.sources import KIND_LABEL, SOURCES
from src.style import inject
from src.words import TEXT

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
LOOKUPS = PROCESSED / "lookups"
APP_TABLES = PROCESSED / "app"
LOGO_PATH = ROOT / "assets" / "CropWatch Eco-Tech Emblem.png"
LOGO_URI = "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")

st.set_page_config(
    page_title="CropWatch Rwanda",
    page_icon=str(LOGO_PATH),
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(inject(), unsafe_allow_html=True)

if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "lang_nav" not in st.session_state:
    st.session_state.lang_nav = st.session_state.lang
if "page_nav" not in st.session_state:
    st.session_state.page_nav = "home"

# Language from the URL (brand and footer links reload the page with ?lang=...)
_qlang = st.query_params.get("lang")
if isinstance(_qlang, list):
    _qlang = _qlang[0] if _qlang else None
if _qlang in ("en", "rw") and st.session_state.get("_qlang_applied") != _qlang:
    st.session_state.lang = _qlang
    st.session_state.lang_nav = _qlang
    st.session_state._qlang_applied = _qlang


def tr(en, rw):
    """Pick the English or Kinyarwanda string for the current language."""
    return rw if st.session_state.lang == "rw" else en


FAO_CROP = {
    "Corn": ("Maize", "Ibigori"),
    "Sorghum": ("Sorghum", "Amasaka"),
    "Cassava": ("Cassava", "Imyumbati"),
    "Potato": ("Potato", "Ibirayi"),
    "Rice": ("Rice", "Umuceri"),
    "Bean": ("Bean", "Ibishyimbo"),
    "Beans, harvested green": ("Green beans", "Ibishyimbo byo kurya"),
    "Pea, dry": ("Dry pea", "Amashaza yumye"),
    "Wheat, bread": ("Wheat", "Ingano"),
    "Beet": ("Beet", "Beterave"),
    "Beet, sugar": ("Sugar beet", "Beterave y'isukari"),
    "Bergamot": ("Bergamot", "Bergamote"),
}


# --------------------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------------------
def load():
    status = pd.read_csv(APP_TABLES / "status.csv").iloc[0]
    matches = pd.read_csv(LOOKUPS / "crop_price_match.csv", dtype={"hs_heading": str})
    matches["hs_heading"] = matches["hs_heading"].str.replace(r"\.0$", "", regex=True).str.zfill(4)
    unmatched = pd.read_csv(LOOKUPS / "crops_without_a_price.csv")
    seasons = pd.read_csv(LOOKUPS / "seasons.csv")
    calendar = pd.read_csv(LOOKUPS / "maize_sorghum_calendar.csv")
    zones = pd.read_csv(LOOKUPS / "crop_calendar_zones.csv")
    rows = pd.read_csv(APP_TABLES / "survey_rows_by_season.csv")
    rain = pd.read_csv(PROCESSED / "rainfall" / "district_month_anomaly.csv")
    watch = pd.read_csv(APP_TABLES / "season_watch.csv")
    soil = pd.read_csv(APP_TABLES / "soil_season_a_2022.csv")
    alerts = pd.read_csv(APP_TABLES / "irrigation_alerts.csv")
    forecast = pd.read_csv(APP_TABLES / "forecast_7day.csv")

    # Dynamic date synchronization: if cached forecast starts before today, auto-align
    today_iso = date.today().isoformat()
    if not forecast.empty and "date" in forecast.columns and str(forecast["date"].min()) < today_iso:
        try:
            from src.prepare_alerts import update_alerts_and_forecast
            alerts, forecast = update_alerts_and_forecast(force=False)
        except Exception:
            pass
    exports_year = pd.read_csv(APP_TABLES / "maize_exports_by_year.csv")
    exports_partners = pd.read_csv(APP_TABLES / "maize_exports_partners.csv")

    benchmark = {}
    benchmark_path = APP_TABLES / "model_benchmark.json"
    if benchmark_path.exists():
        with open(benchmark_path, "r", encoding="utf-8") as f:
            benchmark = json.load(f)

    sim_base = pd.DataFrame()
    sim_path = APP_TABLES / "district_simulation_base.csv"
    if sim_path.exists():
        sim_base = pd.read_csv(sim_path)
    vegetation = pd.read_csv(PROCESSED / "vegetation" / "district_year.csv")

    return (
        status, matches, unmatched, seasons, calendar, zones, rows, rain, watch,
        soil, alerts, forecast, exports_year, exports_partners, benchmark, sim_base,
        vegetation,
    )


# --------------------------------------------------------------------------------------
# Small HTML helpers
# --------------------------------------------------------------------------------------
def page_body():
    """The aligned container every non-home page lives in (see .st-key-page_body in style.py)."""
    return st.container(key="page_body")


def show_table(frame):
    st.dataframe(frame, width="stretch", hide_index=True)


def alert_sentence(row, words):
    key = f"alert_{row['alert']}"
    return words[key].format(
        district=row["district"],
        pct=abs(row["rain_difference_pct"]),
        irrig=row["irrigated_pct"],
        week=row["forecast_week_mm"],
        concern=row["concern_pct"],
        protected=row["protected_pct"],
    )


def action_for(alert, words):
    if alert in {"irrigation_gap", "irrigate_now", "dry_watch"}:
        return words["action_irrigation"]
    if alert in {"soil_rain", "soil_watch"}:
        return words["action_soil"]
    return words["action_stable"]


def pill(alert, words):
    return f'<span class="status-pill {alert}">{words["label_" + str(alert)]}</span>'


def kpi(label, value, hint=""):
    extra = f"<small>{hint}</small>" if hint else ""
    return f'<div class="kpi"><span>{label}</span><strong>{value}</strong>{extra}</div>'


def opt_kpi(label, row, column, fmt):
    """KPI that shows a dash when the column is missing or empty."""
    if column in row.index and pd.notna(row.get(column)):
        return kpi(label, fmt.format(float(row[column])))
    return kpi(label, "—")


def data_table(headers, rows):
    head = "".join(f"<th>{item}</th>" for item in headers)
    body = []
    for row in rows:
        cells = []
        for index, cell in enumerate(row):
            tag = "th" if index == 0 else "td"
            cells.append(f"<{tag}>{cell}</{tag}>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="data-card"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def score_text(block, field):
    if not isinstance(block, dict) or field not in block or block[field] is None:
        return "—"
    value = block[field]
    if field == "r2":
        return f"{value:.3f}"
    return f"{value:.1f}"


def bar_cell(pct):
    width = max(0, min(100, float(pct)))
    return f'<div class="bar-cell"><b>{width:.0f}%</b><i style="width:{width:.0f}%"></i></div>'


def board(kicker, title, body, action, kpis, extra="", pill_html=""):
    return (
        '<section class="board">'
        '<div class="board-head"><div>'
        f'<p class="kicker-green">{kicker}</p><h2>{title}</h2></div>{pill_html}</div>'
        f'<p class="board-copy">{body}</p>'
        f'<p class="board-action">{action}</p>'
        f'<div class="kpi-row{" five" if len(kpis) == 5 else " six" if len(kpis) == 6 else ""}">{"".join(kpis)}</div>'
        f"{extra}</section>"
    )


# --------------------------------------------------------------------------------------
# The verdict card: the one answer a visitor needs first
# --------------------------------------------------------------------------------------
VERDICT_TONE = {
    "irrigate_now": ("act", "💧"),
    "irrigation_gap": ("act", "💧"),
    "dry_watch": ("watch", "👀"),
    "soil_rain": ("soil", "⛰️"),
    "soil_watch": ("soil", "⛰️"),
    "stable": ("ok", "✅"),
}


def verdict_card(row, words):
    tone, icon = VERDICT_TONE.get(str(row["alert"]), ("ok", "✅"))
    title = words.get("label_" + str(row["alert"]), str(row["alert"]))
    sentence = alert_sentence(row, words)
    action = action_for(str(row["alert"]), words)
    lbl_rain = tr("Rain vs usual", "Imvura ku isanzwe")
    lbl_week = tr("Rain next 7 days", "Imvura y'iminsi 7")
    lbl_irrig = tr("Irrigated land", "Ubutaka buhirwa")
    return (
        f'<section class="verdict {tone}">'
        f'<div class="verdict-icon">{icon}</div>'
        '<div class="verdict-main">'
        f'<p class="verdict-district">{row["district"]}</p>'
        f'<h2 class="verdict-title">{title}</h2>'
        f'<p class="verdict-action">{sentence} <strong>{action}</strong></p>'
        "</div>"
        '<dl class="verdict-stats">'
        f'<div><dt>{lbl_rain}</dt><dd>{float(row["rain_difference_pct"]):+.0f}%</dd></div>'
        f'<div><dt>{lbl_week}</dt><dd>{float(row["forecast_week_mm"]):.0f}<small>mm</small></dd></div>'
        f'<div><dt>{lbl_irrig}</dt><dd>{float(row["irrigated_pct"]):.0f}%</dd></div>'
        "</dl></section>"
    )


def district_select(label, names, key, fallback="Nyaruguru"):
    """District picker that remembers the choice across pages."""
    if key not in st.session_state:
        wanted = st.session_state.get("district", fallback)
        st.session_state[key] = wanted if wanted in names else names[0]
    chosen = st.selectbox(label, names, key=key)
    st.session_state.district = chosen
    return chosen


def jump(page_name, role=None):
    st.session_state.pending_page = page_name
    if role:
        st.session_state.role = role


def ai_prompt(district, alert):
    if st.session_state.lang == "rw":
        return f"Ntegurira ingamba zihutirwa zo kuhira n'uburyo bwo kwishingira umusaruro mu karere ka {district} gafite ikibazo cya {alert}."
    return (
        f"Generate an emergency agronomic response plan, supplementary irrigation schedule, "
        f"and parametric insurance assessment for {district} District's {alert} alert."
    )


def ask_ai(district, alert):
    st.session_state.chat_district = district
    st.session_state.pending_chat_prompt = ai_prompt(district, alert)
    st.session_state.pending_page = "advise"


# --------------------------------------------------------------------------------------
# Section builders
# --------------------------------------------------------------------------------------
def model_tables(benchmark, words):
    if not benchmark:
        return ""
    status_label = {
        "skip": words["status_skip"],
        "plot": words["status_plot"],
        "district-panel": words["status_panel"],
    }
    cover_rows = [
        [
            f"{row['year']} {row.get('season', '')}".strip(),
            status_label.get(row.get("status"), row.get("status", "—")),
            row.get("reason", ""),
        ]
        for row in benchmark.get("coverage", [])
    ]
    slice_rows = []
    for item in benchmark.get("slices", []):
        label = f"{item.get('year')} {item.get('season')}"
        if item.get("skipped"):
            slice_rows.append([
                label,
                str(item.get("n_model") or item.get("n_joined") or "—"),
                "—", "—", "—",
                item["skipped"],
            ])
            continue
        slice_rows.append([
            label,
            str(item.get("n_model", "—")),
            score_text(item.get("rain"), "r2"),
            score_text(item.get("district"), "r2"),
            score_text(item.get("forest"), "r2"),
            words["beats_yes"] if item.get("forest_beats_district") else words["beats_no"],
        ])
    pooled = benchmark.get("pooled") or {}
    shuffled = pooled.get("shuffled") or {}
    grouped = pooled.get("grouped_by_district") or {}
    pooled_rows = []
    for name, block in (
        (words["pooled_rain"], shuffled.get("rain")),
        (words["pooled_district"], shuffled.get("district")),
        (words["pooled_forest"], shuffled.get("forest")),
        (words["pooled_boost"], shuffled.get("boost")),
        (words["grouped_rain"], grouped.get("rain")),
        (words["grouped_district"], grouped.get("district")),
        (words["grouped_forest"], grouped.get("forest")),
    ):
        if not block:
            continue
        pooled_rows.append([
            name,
            score_text(block, "mae_kg_ha"),
            score_text(block, "rmse_kg_ha"),
            score_text(block, "r2"),
        ])
    panel = benchmark.get("district_panel") or {}
    panel_rows = []
    for name, block in ((words["panel_rain"], panel.get("rain")), (words["panel_forest"], panel.get("forest"))):
        if block:
            panel_rows.append([
                name,
                score_text(block, "mae_kg_ha"),
                score_text(block, "rmse_kg_ha"),
                score_text(block, "r2"),
            ])
    html = (
        f'<p class="kicker-green" style="margin-top:40px">{words["cover_title"]}</p>'
        f'<p class="section-p">{words["cover_lead"]}</p>'
        + (data_table([words["year_col"], words["cover_status"], words["cover_reason"]], cover_rows) if cover_rows else "")
        + f'<p class="kicker-green" style="margin-top:36px">{words["slice_title"]}</p>'
        f'<p class="section-p">{words["slice_lead"]}</p>'
        + (data_table(
            [words["year_col"], words["slice_n"], words["slice_rain_r2"], words["slice_district_r2"], words["slice_forest_r2"], words["slice_verdict"]],
            slice_rows,
        ) if slice_rows else "")
        + f'<p class="kicker-green" style="margin-top:36px">{words["pooled_title"]}</p>'
        f'<p class="section-p">{words["pooled_lead"]}</p>'
        + (data_table([words["model_col"], words["mae_col"], words["rmse_col"], words["r2_col"]], pooled_rows) if pooled_rows else "")
        + f'<p class="kicker-green" style="margin-top:36px">{words["panel_title"]}</p>'
        f'<p class="section-p">{words["panel_lead"]}</p>'
        + (data_table([words["model_col"], words["mae_col"], words["rmse_col"], words["r2_col"]], panel_rows) if panel_rows else "")
        + f'<div class="note-box">{words["sim_source_note"]}</div>'
    )
    return html


def week_panel(week, words):
    if week.empty:
        return ""
    max_mm = max(float(week["forecast_mm"].max()), 1.0)
    days = []
    for _, item in week.iterrows():
        height = 8 + 92 * (float(item["forecast_mm"]) / max_mm)
        day = pd.to_datetime(item["date"]).strftime("%d %b")
        days.append(
            f'<div class="week-day"><em>{day}</em>'
            f'<div class="week-track"><i style="height:{height:.0f}%"></i></div>'
            f'<strong>{float(item["forecast_mm"]):.1f}</strong>'
            f'<span>{float(item["rain_chance_pct"]):.0f}%</span>'
            + (f'<span>{float(item["et0_mm"]):.1f} ET₀</span>' if "et0_mm" in item and pd.notna(item.get("et0_mm")) else "")
            + (
                f'<span class="week-bal">{float(item["water_balance_mm"]):+.1f}</span>'
                if "water_balance_mm" in item and pd.notna(item.get("water_balance_mm"))
                else ""
            )
            + "</div>"
        )
    return (
        f'<div class="week-panel"><div class="week-head"><h3>{words["week_title"]}</h3>'
        f'<p>{words["week_lead"]}</p></div>'
        f'<div class="week-bars">{"".join(days)}</div></div>'
    )


def why_box(row, words):
    key = "why_" + str(row["alert"])
    body = words.get(key, words["why_stable"])
    climate = row["climate_class"] if "climate_class" in row and pd.notna(row.get("climate_class")) else ""
    climate_html = ""
    if climate:
        climate_html = (
            f'<p><strong>{words["climate_kicker"]}</strong> '
            f'{words.get("label_" + str(climate), climate)}</p>'
        )
    balance = ""
    if "water_balance_week_mm" in row and pd.notna(row.get("water_balance_week_mm")):
        balance = words["intel_balance"].format(
            pe=float(row.get("pe_week_mm") or 0),
            etc=float(row.get("etc_week_mm") or 0),
            bal=float(row["water_balance_week_mm"]),
            kc=float(row.get("kc_maize") or 0),
            stage=row.get("maize_stage") or "—",
        )
    return (
        f'<div class="why-box"><strong>{words["why_title"]}</strong>'
        f"{climate_html}<p>{body}</p>"
        f"{'<p>' + balance + '</p>' if balance else ''}"
        f"<p>{words['why_sources']}</p></div>"
    )


def provable_evidence_box(row, words):
    rain_diff = float(row.get("rain_difference_pct", 0))
    rain_so_far = float(row.get("rain_so_far_mm", 0))
    usual_rain = float(row.get("usual_sep_oct_mm", 1))
    irrig_pct = float(row.get("irrigated_pct", 0))
    pe = float(row.get("pe_week_mm") or 0)
    etc = float(row.get("etc_week_mm") or 0)
    bal = float(row.get("water_balance_week_mm") or 0)
    kc = float(row.get("kc_maize") or 0.94)
    stage = str(row.get("maize_stage") or "development")
    f_week = float(row.get("forecast_week_mm") or 0)
    f_days = int(row.get("forecast_days_with_rain") or 0)
    lat = float(row.get("latitude") or -1.94)
    lon = float(row.get("longitude") or 29.87)
    sample_weight = float(row.get("irrigated_weight") or 500000)
    fetched = row.get("fetched_on", "2026-10-30")

    lbl_anomaly = tr("Rain compared with normal", "Itandukaniro ry'imvura")
    lbl_balance = tr("Weekly water balance (rain − crop demand)", "Icyuho cy'amazi (imvura − ibikenewe)")
    lbl_irrig = tr("Irrigated plots in survey", "Imirima ihirwa (SAS)")
    lbl_stage = tr("Maize stage and crop factor (Kc)", "Icyiciro cy'ibigori na Kc")
    lbl_fc = tr("Forecast:", "Iteganyagihe:")
    lbl_thr = tr("above the 10% threshold", "hejuru ya 10%") if irrig_pct >= 10 else tr("below the 10% threshold", "munsi ya 10%")
    lbl_audit = tr("How we checked this", "Uko byagenzuwe")
    lbl_body = tr(
        "Ground truth from the NISR Seasonal Agriculture Survey",
        "Amakuru y'ibanze yavuye muri NISR SAS",
    )
    lbl_plots = tr("plots", "imirima")
    lbl_end = tr(
        "Weather from Open-Meteo, normal rainfall from CHIRPS 2018–2025. Data fetched on",
        "Iteganyagihe rya Open-Meteo, imvura isanzwe ya CHIRPS 2018–2025. Amakuru yakiriwe ku itariki",
    )
    c_rain = "#b42318" if rain_diff < -15 else "#9a5700" if rain_diff < 0 else "#0d4f2b"
    c_bal = "#b42318" if bal < 0 else "#0d4f2b"

    math_proof = (
        '<div class="evidence-math-grid">'
        '<div class="evidence-math-cell">'
        f'<span class="math-label">{lbl_anomaly}</span>'
        f'<strong class="math-value" style="color:{c_rain};">{rain_diff:+.1f}%</strong>'
        f'<span class="math-formula">({rain_so_far:.0f} mm / {usual_rain:.0f} mm)</span></div>'
        '<div class="evidence-math-cell">'
        f'<span class="math-label">{lbl_balance}</span>'
        f'<strong class="math-value" style="color:{c_bal};">{bal:+.1f} mm</strong>'
        f'<span class="math-formula">({pe:.1f} mm rain − {etc:.1f} mm demand)</span></div>'
        '<div class="evidence-math-cell">'
        f'<span class="math-label">{lbl_irrig}</span>'
        f'<strong class="math-value">{irrig_pct:.1f}%</strong>'
        f'<span class="math-formula">({lbl_thr})</span></div>'
        '<div class="evidence-math-cell">'
        f'<span class="math-label">{lbl_stage}</span>'
        f'<strong class="math-value">{stage.capitalize()} (Kc={kc:.2f})</strong>'
        f'<span class="math-formula">{lbl_fc} {f_week:.1f} mm / {f_days}d</span></div>'
        "</div>"
    )
    audit_footer = (
        '<div class="evidence-audit-footer"><div class="evidence-stamp">'
        '<span class="stamp-icon">🛡️</span><div>'
        f"<strong>{lbl_audit}</strong>"
        f"<p>{lbl_body} ({sample_weight:,.0f} {lbl_plots}). "
        f"{lbl_end} <strong>{fetched}</strong>. "
        f"<code>{lat:.4f}°N, {lon:.4f}°E</code></p>"
        "</div></div></div>"
    )
    return f'<div class="provable-evidence-box">{math_proof}{audit_footer}</div>'


def source_card(item, lang, words):
    copy = item[lang]
    kind_en, kind_rw = KIND_LABEL[item["kind"]]
    kind = kind_rw if lang == "rw" else kind_en
    link = ""
    if item["url"]:
        link = (
            f"<dt>{words['src_link']}</dt>"
            f"<dd><a href='{item['url']}' target='_blank' rel='noreferrer'>{words['src_open']}</a></dd>"
        )
    return (
        '<article class="source-card">'
        f'<span class="kind-pill">{kind}</span>'
        f"<h3>{copy['name']}</h3>"
        "<dl>"
        f"<dt>{words['src_publisher']}</dt><dd>{copy['publisher']}</dd>"
        f"<dt>{words['src_contains']}</dt><dd>{copy['contains']}</dd>"
        f"<dt>{words['src_vars']}</dt><dd>{copy['vars']}</dd>"
        f"<dt>{words['src_geo']}</dt><dd>{copy['geo']}</dd>"
        f"<dt>{words['src_time']}</dt><dd>{copy['time']}</dd>"
        f"<dt>{words['src_update']}</dt><dd>{copy['update']}</dd>"
        f"{link}"
        f"<dt>{words['src_accessed']}</dt><dd>{copy['accessed']}</dd>"
        f"<dt>{words['src_processing']}</dt><dd>{copy['processing']}</dd>"
        f"<dt>{words['src_modules']}</dt><dd>{copy['modules']}</dd>"
        f"<dt>{words['src_limits']}</dt><dd>{copy['limits']}</dd>"
        f"<dt>{words['src_license']}</dt><dd>{copy['license']}</dd>"
        "</dl></article>"
    )


def page_head(title, lead, words, **_extra):
    st.markdown(
        f"""
        <section class="page-band">
          <div class="inner">
            <h1>{title}</h1>
            <p class="lead">{lead}</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_footer(words):
    """Slim footer: who we are, where to go, where the data comes from.

    Freshness dates live on the Data page, the legal notice lives on the About and Data pages,
    and "what it does" lives on the home page.
    """
    lang = st.session_state.lang
    site_footer = tr("Site footer", "Hasi ku rupapuro")
    platform_label = tr("Platform", "Urubuga")
    sources_label = tr("Data sources", "Aho amakuru ava")
    sources_more = tr("All sources, dates and limits", "Amasoko yose, amatariki n'imbibi")
    built_for = tr("Built for NST2 · Season A 2026", "Byakozwe kuri NST2 · Igihembwe A 2026")
    back_top = tr("Back to top ↑", "Subira hejuru ↑")
    mission = tr(
        "A crop water early-warning desk for all 30 districts. It turns rainfall, forecast, soil and market data into one plain answer for farmers, extension agents and planners.",
        "Ikigo cy'iburira ry'amazi y'imyaka mu turere 30. Gihindura amakuru y'imvura, iteganyagihe, ubutaka n'isoko igisubizo kimwe cyoroshye.",
    )

    def nav_link(page_key, label):
        return f'<li><a href="?page={page_key}&lang={lang}" target="_self">{label}</a></li>'

    platform = "".join([
        nav_link("home", words["nav_home"]),
        nav_link("alerts", words["nav_alerts"]),
        nav_link("district", tr("My district", "Akarere kanjye")),
        nav_link("advise", "ADVICE AI"),
        nav_link("data", words["nav_data"]),
        nav_link("about", words["nav_about"]),
    ])
    sources = "".join(f"<li>{t}</li>" for t in (
        "NISR Seasonal Agriculture Survey",
        "CHIRPS rainfall, 2018–2025",
        "Open-Meteo 7-day forecast",
        "WFP VAM market prices",
        "FAO-56 crop water method",
    ))

    st.markdown(
        f"""
        <footer class="landing-footer" aria-label="{site_footer}">
          <div class="footer-inner">
            <div class="footer-main">
              <section>
                <div class="landing-brand">
                  <img src="{LOGO_URI}" alt="CropWatch" />
                  <span>CropWatch Rwanda<small>{words["brand_tag"]}</small></span>
                </div>
                <p class="footer-mission">{mission}</p>
              </section>
              <nav aria-label="{platform_label}">
                <h2>{platform_label}</h2>
                <ul>{platform}</ul>
              </nav>
              <section>
                <h2>{sources_label}</h2>
                <ul>{sources}</ul>
                <a class="footer-more" href="?page=data&lang={lang}" target="_self">{sources_more}</a>
              </section>
            </div>
            <div class="landing-copyright">
              <span>© 2026 CropWatch Rwanda · {words["footer_copy"]}</span>
              <span>{built_for}</span>
              <a href="#cw-top">{back_top}</a>
            </div>
          </div>
        </footer>""",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------------
# Map helpers
# --------------------------------------------------------------------------------------
@st.cache_data
def load_geojson(mtime):
    path = APP_TABLES / "districts.geojson"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


ALERT_COLOR = {
    "irrigate_now": "#dc2626",
    "irrigation_gap": "#ea580c",
    "soil_rain": "#ca8a04",
    "dry_watch": "#d97706",
    "soil_watch": "#ca8a04",
    "stable": "#16a34a",
}
CLIMATE_COLOR = {
    "water_stress": "#dc2626",
    "excess_rain": "#7a4e22",
    "rainfall_watch": "#d97706",
    "agronomist": "#6d28d9",
    "normal_monitoring": "#16a34a",
}


def layer_fill(row, layer):
    if layer == "alert":
        return ALERT_COLOR.get(str(row["alert"]), "#16a34a")
    if layer == "climate":
        return CLIMATE_COLOR.get(str(row.get("climate_class") or ""), "#16a34a")
    if layer == "rain":
        value = float(row["rain_difference_pct"])
        if value <= -20:
            return "#dc2626"
        if value <= -10:
            return "#ea580c"
        if value < 10:
            return "#ca8a04"
        return "#16a34a"
    if layer == "irrigation":
        value = float(row["irrigated_pct"])
        if value < 2:
            return "#dc2626"
        if value < 10:
            return "#ea580c"
        return "#16a34a"
    if layer == "soil":
        value = float(row["concern_pct"])
        if value >= 30:
            return "#dc2626"
        if value >= 20:
            return "#ea580c"
        if value >= 10:
            return "#ca8a04"
        return "#16a34a"
    value = float(row["ndre_2026"]) if "ndre_2026" in row and pd.notna(row["ndre_2026"]) else 0
    if value < 0.25:
        return "#b45309"
    if value < 0.30:
        return "#ca8a04"
    return "#16a34a"


def layer_legend(layer, words):
    if layer == "alert":
        items = [
            ("#dc2626", words["label_irrigate_now"]),
            ("#ea580c", words["label_irrigation_gap"]),
            ("#ca8a04", words["label_soil_watch"]),
            ("#16a34a", words["label_stable"]),
        ]
    elif layer == "climate":
        items = [
            ("#dc2626", words["label_water_stress"]),
            ("#d97706", words["label_rainfall_watch"]),
            ("#7a4e22", words["label_excess_rain"]),
            ("#6d28d9", words["label_agronomist"]),
            ("#16a34a", words["label_normal_monitoring"]),
        ]
    elif layer == "rain":
        items = [("#dc2626", "≤ −20%"), ("#ea580c", "−20 to −10%"), ("#ca8a04", "−10 to +10%"), ("#16a34a", "> +10%")]
    elif layer == "irrigation":
        items = [("#dc2626", "< 2%"), ("#ea580c", "2–10%"), ("#16a34a", "≥ 10%")]
    elif layer == "soil":
        items = [("#16a34a", "< 10%"), ("#ca8a04", "10–20%"), ("#ea580c", "20–30%"), ("#dc2626", "≥ 30%")]
    else:
        items = [("#b45309", "NDRE < 0.25"), ("#ca8a04", "0.25–0.30"), ("#16a34a", "≥ 0.30")]
    rows = "".join(f'<div class="legend-item"><i class="legend-swatch" style="background:{colour}"></i>{label}</div>' for colour, label in items)
    return f'<div class="legend-card"><h3>{words["legend_title"]}</h3>{rows}</div>'


def week_line(forecast, district):
    week = forecast[forecast["district"] == district].sort_values("date")
    if week.empty:
        return "—"
    parts = []
    for _, item in week.iterrows():
        parts.append(f"{pd.to_datetime(item['date']).strftime('%d %b')} {float(item['forecast_mm']):.1f} mm")
    return " · ".join(parts)


def harvest_strip(watch, district, words):
    """After-harvest: latest WFP maize if present, PICS tip, export pointer. No invented prices."""
    hit = watch[(watch["district"] == district)]
    if "season" in watch.columns:
        a = hit[hit["season"] == "A"]
        if not a.empty:
            hit = a
    row = hit.iloc[0] if not hit.empty else None
    price = None
    when = ""
    scope = ""
    if row is not None:
        if pd.notna(row.get("maize_price_rwf_per_kg")):
            price = float(row["maize_price_rwf_per_kg"])
            when = str(row.get("price_date") or "")
            scope = str(row.get("price_scope") or "district")
        elif pd.notna(row.get("national_maize_price_rwf_per_kg")):
            price = float(row["national_maize_price_rwf_per_kg"])
            when = str(row.get("national_price_date") or "")
            scope = "national mean (no district maize kg row)"
    if price is None:
        price_html = f"<strong>{words.get('harvest_no_price', 'No WFP maize kg row')}</strong><span>{words.get('harvest_no_price_note', 'Through 15 Mar 2026. Not a missing harvest.')}</span>"
    else:
        price_html = f"<strong>{price:.0f} RWF/kg</strong><span>WFP VAM · {when} · {scope}</span>"
    return (
        f'<div class="harvest-strip">'
        f'<p class="kicker-green">{words.get("harvest_title", "After harvest")}</p>'
        f'<p class="section-p">{words.get("harvest_lead", "Storage tip plus the latest WFP maize price. CropWatch does not forecast prices or send SMS.")}</p>'
        f'<div class="harvest-grid">'
        f'<div class="harvest-cell"><span>{words.get("harvest_price", "Maize price")}</span>{price_html}</div>'
        f'<div class="harvest-cell"><span>{words.get("harvest_store", "Store")}</span>'
        f"<strong>PICS</strong><span>{words.get('harvest_store_note', 'Dry to ≤13.5% moisture. Hermetic bags. Not a MINAGRI voucher.')}</span></div>"
        f'<div class="harvest-cell"><span>{words.get("harvest_export", "Formal maize exports")}</span>'
        f"<strong>HS 1005</strong><span>{words.get('harvest_export_note', 'Open Data table through 2025. No 2026 file.')}</span></div>"
        f"</div></div>"
    )


def geometry_bounds(geometry):
    """Return [[south, west], [north, east]] and [lat, lon] centroid from GeoJSON geometry."""
    lons, lats = [], []

    def walk(node):
        if not node:
            return
        if isinstance(node[0], (int, float)):
            lons.append(float(node[0]))
            lats.append(float(node[1]))
            return
        for child in node:
            walk(child)

    walk(geometry.get("coordinates") if isinstance(geometry, dict) else geometry)
    if not lons or not lats:
        return [[-2.84, 28.86], [-1.05, 30.90]], [-1.94, 29.87]
    south, north, west, east = min(lats), max(lats), min(lons), max(lons)
    return [[south, west], [north, east]], [(south + north) / 2, (west + east) / 2]


def rwanda_frame(geojson):
    lons, lats = [], []
    for feat in geojson.get("features", []):
        box, _ = geometry_bounds(feat.get("geometry") or {})
        lats.extend([box[0][0], box[1][0]])
        lons.extend([box[0][1], box[1][1]])
    if not lons:
        return [[-2.84, 28.86], [-1.05, 30.90]]
    pad = 0.04
    return [[min(lats) - pad, min(lons) - pad], [max(lats) + pad, max(lons) + pad]]


def alert_map(alerts, forecast, geojson, words, layer="alert", focus_district=None):
    lookup = alerts.set_index("district")
    features = []
    for feat in geojson["features"]:
        name = feat["properties"].get("district")
        props = dict(feat["properties"])
        if name in lookup.index:
            row = lookup.loc[name]
            props["alert_label"] = words["label_" + str(row["alert"])]
            props["rain_vs"] = f"{float(row['rain_difference_pct']):+.1f}%"
            props["irrig_share"] = f"{float(row['irrigated_pct']):.1f}%"
            props["week_mm"] = f"{float(row['forecast_week_mm']):.0f} mm"
            props["fill"] = layer_fill(row, layer)
        else:
            props["alert_label"] = "—"
            props["rain_vs"] = "—"
            props["irrig_share"] = "—"
            props["week_mm"] = "—"
            props["fill"] = "#94a3b8"
        features.append({"type": "Feature", "geometry": feat["geometry"], "properties": props})
    layered = {"type": "FeatureCollection", "features": features}
    frame = rwanda_frame(layered)

    fig = folium.Figure(width="100%", height="620px")
    rwanda = folium.Map(
        location=[-1.944, 29.874],
        zoom_start=8,
        tiles=None,
        control_scale=False,
        zoom_control=True,
        min_zoom=8,
        max_zoom=10,
        max_bounds=True,
        width="100%",
        height="620px",
        prefer_canvas=True,
    )
    fig.add_child(rwanda)
    rwanda.options["maxBounds"] = frame
    rwanda.options["maxBoundsViscosity"] = 1.0

    def style_function(feature, focus=focus_district):
        selected = feature["properties"].get("district") == focus
        return {
            "fillColor": feature["properties"].get("fill", "#16a34a"),
            "color": "#8a6d2b" if selected else "#f7fbf8",
            "weight": 2.6 if selected else 1.1,
            "fillOpacity": 0.94 if selected else 0.82,
        }

    folium.GeoJson(
        layered,
        style_function=style_function,
        highlight_function=lambda _feature: {"weight": 2.4, "fillOpacity": 0.96, "color": "#062615"},
        tooltip=folium.GeoJsonTooltip(
            fields=["district", "alert_label", "rain_vs", "irrig_share", "week_mm"],
            aliases=[
                words["district_col"],
                words["col_status"],
                words["map_rain"],
                words["stat_irrigated"],
                words["map_week"],
            ],
            sticky=True,
            labels=True,
            style=(
                "background:#fff;color:#1a1f16;font-family:Inter,system-ui,sans-serif;"
                "font-size:13px;padding:10px 12px;border-radius:10px;"
                "border:1px solid #d5ddd0;box-shadow:0 10px 24px rgba(0,25,9,.14);"
            ),
        ),
        name="districts",
    ).add_to(rwanda)

    focus_feat = next(
        (item for item in layered["features"] if item["properties"].get("district") == focus_district),
        None,
    )
    if focus_feat:
        _, center = geometry_bounds(focus_feat["geometry"])
        folium.CircleMarker(
            location=center,
            radius=6,
            color="#8a6d2b",
            weight=2,
            fill=True,
            fill_color="#c4a35a",
            fill_opacity=1,
            tooltip=focus_district,
        ).add_to(rwanda)

    rwanda.fit_bounds(frame, padding=(18, 18), max_zoom=9)
    fig.header.add_child(folium.Element(
        """
        <style>
          html, body { margin:0; height:100%; background:#e7eee4; }
          .folium-map, .leaflet-container {
            width:100% !important; height:620px !important;
            background:#e7eee4 !important; border:0;
          }
          .leaflet-control-attribution, .leaflet-control-scale { display:none !important; }
          .leaflet-tooltip-pane .leaflet-tooltip { white-space:normal; }
        </style>
        """
    ))
    return fig.render()


FORM_RW = {
    "grain": "intete",
    "dry beans": "ibishyimbo byumye",
    "fresh beans": "ibishyimbo byo kurya",
    "root": "imizi",
    "tuber": "imizi",
    "vegetable": "imboga",
    "fruit": "imbuto",
}

# Home page feature cards: (icon, destination page, (title en, rw), (body en, rw))
FEATURES = [
    ("💧", "alerts",
     ("Irrigation alerts", "Iburira ryo kuhira"),
     ("Every district gets a plain verdict each week: irrigate now, watch, or stable. Rain is compared with the 2018–2025 normal.",
      "Buri karere kabona igisubizo cyoroshye buri cyumweru: kuhira ubu, kwitegereza, cyangwa bitekanye.")),
    ("🌦️", "district",
     ("Forecast and water balance", "Iteganyagihe n'icyuho cy'amazi"),
     ("Seven-day rain, crop water demand (FAO-56) and the weekly gap for maize, by growth stage.",
      "Imvura y'iminsi 7, amazi imyaka ikenera (FAO-56) n'icyuho cy'icyumweru ku bigori.")),
    ("⛰️", "district",
     ("Soil and terraces", "Ubutaka n'amaterasi"),
     ("Where erosion worries farmers most and how many plots have terraces, from the NISR survey.",
      "Aho isuri ritera impungenge n'imirima ifite amaterasi, biturutse kuri NISR.")),
    ("📈", "district",
     ("What-if yield", "Isesengura ry'umusaruro"),
     ("See how more irrigation or better fertilizer could change yield in a district, using real 2022 plot gaps.",
      "Reba uko kuhira cyangwa ifumbire byahindura umusaruro mu karere.")),
    ("🤖", "advise",
     ("ADVICE AI", "ADVICE AI"),
     ("Ask in English or Kinyarwanda. Get a schedule, market note or 160-character SMS draft, with voice read-out.",
      "Baza mu Kinyarwanda cyangwa Icyongereza. Ubone gahunda, amakuru y'isoko cyangwa SMS.")),
    ("📱", "alerts",
     ("Works on any phone", "Ikora kuri telefone zose"),
     ("SMS and *801# menus preview how alerts reach farmers who do not use smartphones.",
      "SMS na *801# byerekana uko iburira rigera ku bahinzi badafite telefone zigezweho.")),
]
SOURCE_CHIPS = ["NISR SAS", "CHIRPS", "Open-Meteo", "WFP VAM", "FAO-56", "Meteo Rwanda"]

# --------------------------------------------------------------------------------------
# Load data
# --------------------------------------------------------------------------------------
(
    status, matches, unmatched, seasons, calendar, zones, survey_rows, rain, watch,
    soil, alerts, forecast, exports_year, exports_partners, benchmark, sim_base,
    vegetation,
) = load()
veg_now = vegetation[vegetation["year"] == 2026][["district", "vegetation_mean"]].rename(columns={"vegetation_mean": "ndre_2026"})
if "ndre_2026" not in alerts.columns:
    alerts = alerts.merge(veg_now, on="district", how="left")

matches["safe_to_join"] = matches["safe_to_join"].astype(str).str.lower().eq("true")
blank_rw = unmatched["survey_crop_rw"].isna() | unmatched["survey_crop_rw"].astype(str).str.strip().eq("")
unmatched.loc[blank_rw, "survey_crop_rw"] = unmatched.loc[blank_rw, "survey_crop"]

PILOTS = ("Bugesera", "Nyagatare", "Musanze", "Nyaruguru")

# Six pages in the header. The old Dashboard and Simulator now live in "My district".
NAV_PAGES = ("home", "alerts", "district", "advise", "data", "about")
PAGE_ALIAS = {
    "dashboard": "district",
    "simulator": "district",
    "soil": "district",
    "watch": "district",
    "pilot": "alerts",
    "method": "about",
}
ALL_PAGES = NAV_PAGES + tuple(PAGE_ALIAS)


def nav_label(key, words):
    if key == "advise":
        return "ADVICE AI"
    if key == "district":
        return tr("My district", "Akarere kanjye")
    return words["nav_" + key]


words = TEXT[st.session_state.lang]
safe = matches[matches["safe_to_join"] == True].copy()
close = matches[matches["safe_to_join"] == False].copy()

st.markdown('<div id="cw-top"></div>', unsafe_allow_html=True)
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


def apply_page(dest):
    dest = PAGE_ALIAS.get(dest, dest)
    if dest not in NAV_PAGES:
        dest = "home"
    st.session_state.current_page = dest
    st.session_state.page_nav = dest
    st.session_state.last_nav = dest


requested = st.query_params.get("page")
if isinstance(requested, list):
    requested = requested[0] if requested else None
if requested in ALL_PAGES and st.session_state.get("_qp") != requested:
    apply_page(requested)
    st.session_state._qp = requested
if st.session_state.get("page_nav") not in NAV_PAGES:
    st.session_state.page_nav = (
        st.session_state.current_page if st.session_state.current_page in NAV_PAGES else "home"
    )
if "pending_page" in st.session_state:
    apply_page(st.session_state.pop("pending_page"))
    st.session_state._qp = st.session_state.current_page
    if st.query_params.get("page") != st.session_state.current_page:
        st.query_params["page"] = st.session_state.current_page

# --------------------------------------------------------------------------------------
# Topbar: brand | page navigation | season badge | language
# (laid out as one CSS grid row, see TOPBAR in style.py)
# --------------------------------------------------------------------------------------
col_brand, col_nav, col_status, col_lang = st.columns([2.4, 5.6, 1.5, 1.0], vertical_alignment="center")
with col_brand:
    st.markdown(
        f"""
        <a class="header-brand" href="?page=home&lang={st.session_state.lang}" target="_self"
           aria-label="CropWatch Rwanda: {tr("home", "ahabanza")}">
          <span class="header-crest">
            <img src="{LOGO_URI}" alt="" />
          </span>
          <span class="header-title-box">
            <span class="header-main-title">CropWatch Rwanda</span>
            <span class="header-sub-tag">{tr("National decision desk", "Ikigo cy'icyemezo")} · NST2</span>
          </span>
        </a>
        """,
        unsafe_allow_html=True,
    )
with col_nav:
    page_nav = st.pills(
        "Page",
        options=list(NAV_PAGES),
        format_func=lambda key: nav_label(key, words),
        label_visibility="collapsed",
        key="page_nav",
    )
with col_status:
    st.markdown(
        f"""
        <div class="topbar-status-badge" role="status">
          <span class="topbar-status-dot" aria-hidden="true"></span>
          <span class="topbar-status-text"><strong>{tr("Season A 2026", "Igihembwe A 2026")}</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_lang:
    language = st.pills(
        "Language",
        options=["en", "rw"],
        format_func=lambda code: code.upper(),
        label_visibility="collapsed",
        key="lang_nav",
    )
    if language and language != st.session_state.lang:
        st.session_state.lang = language
        st.rerun()

last_nav = st.session_state.get("last_nav")
if page_nav and last_nav is not None and page_nav != last_nav:
    st.session_state.current_page = page_nav
    st.session_state._qp = page_nav
    st.session_state.last_nav = page_nav
    if st.query_params.get("page") != page_nav:
        st.query_params["page"] = page_nav
else:
    st.session_state.last_nav = page_nav if page_nav in NAV_PAGES else st.session_state.get("last_nav")
page = st.session_state.current_page or "home"

role = st.session_state.get("role", "all")

month = words["month_names"][int(status["rain_last_month"])]
rain_text = f"{month} {int(status['rain_last_year'])}"

n_gap = int(alerts["alert"].isin(["irrigation_gap", "irrigate_now"]).sum())
irrig_national = 100 * alerts["irrigated_yes_weight"].sum() / alerts["irrigated_weight"].sum()
driest = alerts.sort_values("rain_difference_pct").iloc[0]
district_names_all = sorted(alerts["district"].unique())

# ======================================================================================
# HOME: what CropWatch does, one question, one answer
# ======================================================================================
if page == "home":
    preview_rows = ""
    preview = alerts[alerts["district"].isin(PILOTS)]
    if preview.empty:
        preview = alerts.head(4)
    for _, item in preview.iterrows():
        preview_rows += (
            "<tr>"
            f"<th>{item['district']}</th>"
            f"<td class='landing-number'><strong>{item['rain_difference_pct']:.0f}%</strong>"
            f"<span>{item['rain_so_far_mm']:.0f} / {item['usual_sep_oct_mm']:.0f} mm</span></td>"
            f"<td>{pill(item['alert'], words)}</td>"
            "</tr>"
        )

    # ---- hero
    st.markdown(
        f"""
        <section class="photo-hero">
          <div class="landing-shell landing-hero-grid">
            <div>
              <p class="hero-eyebrow">{tr("Crop water early warning for Rwanda", "Iburira ry'amazi y'imyaka mu Rwanda")}</p>
              <h1>{tr("Know if your crops need water this week.", "Menya niba imyaka yawe ikeneye amazi muri iki cyumweru.")}</h1>
              <p class="lead">{tr(
                  "CropWatch compares this season's rain with what is normal, adds the 7-day forecast and farm survey data, and gives every district one clear answer: irrigate, watch, or stable.",
                  "CropWatch igereranya imvura y'iki gihembwe n'isanzwe, ikongeraho iteganyagihe ry'iminsi 7 n'amakuru y'ubuhinzi, ikaha buri karere igisubizo kimwe: kuhira, kwitegereza, cyangwa bitekanye."
              )}</p>
              <ol class="hero-steps">
                <li><b>1</b><span>{tr("Pick your district", "Hitamo akarere kawe")}</span></li>
                <li><b>2</b><span>{tr("Read the verdict and the 7-day rain", "Soma igisubizo n'imvura y'iminsi 7")}</span></li>
                <li><b>3</b><span>{tr("Act, or ask ADVICE AI what to do", "Fata icyemezo, cyangwa ubaze ADVICE AI")}</span></li>
              </ol>
              <dl class="hero-facts">
                <div><dd>30</dd><dt>{tr("districts", "uturere")}</dt></div>
                <div><dd>7</dd><dt>{tr("day forecast", "iminsi y'iteganyagihe")}</dt></div>
                <div><dd>2</dd><dt>{tr("languages", "indimi")}</dt></div>
                <div><dd>11k</dd><dt>{tr("2022 maize plots (OLS)", "imirima ya 2022 (OLS)")}</dt></div>
              </dl>
            </div>
            <aside class="landing-prices">
              <header>
                <h2>{words["preview_title"]}</h2>
                <span class="live-dot">{words["preview_live"]}</span>
              </header>
              <table>
                <thead>
                  <tr>
                    <th>{words["district_col"]}</th>
                    <th>{words["diff_col"]}</th>
                    <th>{words["col_status"]}</th>
                  </tr>
                </thead>
                <tbody>{preview_rows}</tbody>
              </table>
            </aside>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # ---- the one action: pick a district, get the verdict
    with st.container(key="home_pick"):
        st.markdown(
            f'<p class="pick-title">{tr("Check your district", "Reba akarere kawe")}</p>'
            f'<p class="pick-sub">{tr("Pick a district to see if crops there need water this week.", "Hitamo akarere urebe niba imyaka ikeneye amazi muri iki cyumweru.")}</p>',
            unsafe_allow_html=True,
        )
        chosen_home = district_select(words["pick_district"], district_names_all, "home_district")
        home_row = alerts[alerts["district"] == chosen_home].iloc[0]
        st.markdown(verdict_card(home_row, words), unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        b1.button(
            tr("See the map", "Reba ikarita"),
            width="stretch", type="primary", key="home_go_alerts", on_click=jump, args=("alerts",),
        )
        b2.button(
            tr(f"Ask ADVICE AI about {chosen_home}", f"Baza ADVICE AI kuri {chosen_home}"),
            width="stretch", key="home_ask_ai", on_click=ask_ai, args=(chosen_home, str(home_row["alert"])),
        )
        b3.button(
            tr("More about this district", "Amakuru y'akarere"),
            width="stretch", key="home_go_district", on_click=jump, args=("district",),
        )

    # ---- national snapshot, the problem it solves, section title for the feature grid
    st.markdown(
        f"""
        <section class="landing-section">
          <div class="landing-shell">
            <p class="kicker-green">{tr("Across Rwanda right now", "Mu Rwanda hose ubu")}</p>
            <div class="landing-stats">
              <dl>
                <div><dd>{n_gap}</dd><dt>{words["stat_alert_districts"]}</dt></div>
                <div><dd>{irrig_national:.1f}%</dd><dt>{words["stat_irrigated"]}</dt></div>
                <div><dd>{driest["rain_difference_pct"]:.0f}%</dd><dt>{words["stat_worst"]}</dt></div>
              </dl>
            </div>
            <div class="problem-band">
              <div>
                <p class="kicker-green">{tr("Why it matters", "Impamvu bifite akamaro")}</p>
                <h2 class="section-title">{tr("Most Rwandan farmland depends on rain alone.", "Ubuhinzi bwinshi mu Rwanda bwishingikiriza ku mvura gusa.")}</h2>
              </div>
              <p class="section-p">{tr(
                  "Only a small share of plots are irrigated, so a dry few weeks can cost a season. CropWatch turns rainfall, forecast, soil and market data into one clear answer per district, so extension agents and farmers can act early.",
                  "Imirima mike ni yo ihirwa, bityo ibyumweru bike by'izuba bishobora gutwara igihembwe. CropWatch ihindura amakuru y'imvura, iteganyagihe, ubutaka n'isoko igisubizo kimwe kuri buri karere, kugira ngo bakore hakiri kare."
              )}</p>
            </div>
          </div>
        </section>
        <section class="landing-section alt">
          <div class="landing-shell">
            <p class="kicker-green">{tr("What CropWatch does", "Ibyo CropWatch ikora")}</p>
            <h2 class="section-title">{tr("Six tools, one decision desk", "Ibikoresho bitandatu, ahantu hamwe")}</h2>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # ---- feature cards: markdown card body + a real button (keeps language and district)
    feat_lang = 1 if st.session_state.lang == "rw" else 0
    with st.container(key="feature_grid"):
        for start in (0, 3):
            cols = st.columns(3, gap="medium")
            for offset, col in enumerate(cols):
                idx = start + offset
                icon, dest, title, body = FEATURES[idx]
                with col:
                    with st.container(key=f"featcard_{idx}"):
                        st.markdown(
                            f'<div class="feature-icon">{icon}</div><h3>{title[feat_lang]}</h3><p>{body[feat_lang]}</p>',
                            unsafe_allow_html=True,
                        )
                        st.button(
                            tr("Open →", "Fungura →"),
                            key=f"featbtn_{idx}",
                            on_click=jump,
                            args=(dest,),
                        )

    # ---- how it works, who it is for, data sources, closing call to action
    chips = "".join(f"<span>{c}</span>" for c in SOURCE_CHIPS)
    st.markdown(
        f"""
        <section class="landing-section">
          <div class="landing-shell">
            <h2 class="section-title">{words["home_how_title"]}</h2>
            <div class="process-row three">
              <article><span>1</span><h3>{words["home_how_1_t"]}</h3><p>{words["home_how_1"]}</p></article>
              <article><span>2</span><h3>{words["home_how_2_t"]}</h3><p>{words["home_how_2"]}</p></article>
              <article><span>3</span><h3>{words["home_how_3_t"]}</h3><p>{words["home_how_3"]}</p></article>
            </div>
            <h2 class="section-title" style="margin-top:48px">{words["home_mod_title"]}</h2>
            <div class="decision-grid">
              <article><h3>{words["role_farmer"]}</h3><p>{words["home_who_farmer"]}</p></article>
              <article><h3>{words["role_agronomist"]}</h3><p>{words["home_who_agro"]}</p></article>
              <article><h3>{words["role_policy"]}</h3><p>{words["home_who_plan"]}</p></article>
            </div>
            <div class="trust-strip">
              <div>
                <p class="kicker-green">{tr("Built on public, checkable data", "Rishingiye ku makuru rusange agenzurwa")}</p>
                <p class="section-p" style="margin:0">{tr("Every number links back to its source, date and limits on the Data page.", "Buri mubare ugaragaza aho wavuye, itariki n'imbibi ku rupapuro rw'Amakuru.")}</p>
              </div>
              <div class="src-chips">{chips}</div>
            </div>
          </div>
        </section>
        <section class="cta-band">
          <div class="landing-shell">
            <h2>{words["home_start_title"]}</h2>
            <p class="section-p">{words["home_start_body"]}</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.button(tr("See the map", "Reba ikarita"), width="stretch", type="primary", key="cta_go_alerts", on_click=jump, args=("alerts",))
    c2.button(tr("My district", "Akarere kanjye"), width="stretch", key="cta_go_district", on_click=jump, args=("district",))
    c3.button("ADVICE AI", width="stretch", key="cta_go_advise", on_click=jump, args=("advise",))
    render_footer(words)

# ======================================================================================
# ALERTS: district answer first, then the national map
# ======================================================================================
elif page == "alerts":
    page_head(words["alerts_title"], words["alerts_lead"], words)

    with page_body():
        # Live Agrometeorological Telemetry Sync Header
        latest_fetch = alerts["fetched_on"].iloc[0] if "fetched_on" in alerts.columns else date.today().isoformat()
        is_today = (str(latest_fetch) == date.today().isoformat())
        status_color = "#0d4f2b" if is_today else "#9a5700"
        status_bg = "#eaf4ed" if is_today else "#fef9ee"
        status_border = "#b7dcbe" if is_today else "#fde68a"

        c_sync_info, c_sync_btn = st.columns([3.6, 1.4], vertical_alignment="center")
        with c_sync_info:
            d_start = pd.to_datetime(latest_fetch)
            d_end = d_start + timedelta(days=6)
            st.markdown(
                f'<div style="background:{status_bg}; border:1px solid {status_border}; border-radius:8px; padding:8px 14px; font-size:12.5px; color:{status_color}; font-weight:600; display:flex; align-items:center; gap:8px; margin-bottom:12px;">'
                f'<span>🛰️</span> <span>{words["alerts_live_sync_title"]} · '
                f'<strong>{words["alerts_today_forecast"]}</strong> '
                f'{d_start.strftime("%d %b")} – {d_end.strftime("%d %b %Y")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c_sync_btn:
            if st.button("🔄 " + words["alerts_btn_refresh"], key="btn_refresh_forecast", width="stretch", help="Fetch live 7-day numerical forecast from Open-Meteo for all 30 districts"):
                with st.spinner("Fetching live Open-Meteo telemetry..."):
                    from src.prepare_alerts import update_alerts_and_forecast
                    update_alerts_and_forecast(force=True)
                    st.rerun()

        st.markdown(
            f'<p class="kicker-green" style="margin:0">{tr("1. Check one district", "1. Reba akarere kamwe")}</p>',
            unsafe_allow_html=True,
        )
        chosen = district_select(words["pick_district"], district_names_all, "district_pick")
        row = alerts[alerts["district"] == chosen].iloc[0]
        week = forecast[forecast["district"] == chosen].sort_values("date")

        st.markdown(
            '<div class="inner-wrap">' + verdict_card(row, words) + week_panel(week, words) + "</div>",
            unsafe_allow_html=True,
        )
        col_act1, col_act2 = st.columns(2, vertical_alignment="center")
        with col_act1:
            st.download_button(
                words["export_html"],
                html_report(row, words, week).encode("utf-8"),
                f"cropwatch_{chosen.lower()}_note.html",
                "text/html",
                key="alert_html",
                width="stretch",
            )
        with col_act2:
            st.button(
                f"🤖 {words.get('btn_ask_advice_ai', 'Ask ADVICE AI about this alert')} ({chosen})",
                key="ask_ai_btn",
                type="primary",
                width="stretch",
                on_click=ask_ai,
                args=(chosen, str(row["alert"])),
            )

        with st.expander("🔬 " + tr("Show the numbers and evidence", "Erekana imibare n'ibimenyetso")):
            st.markdown(
                '<div class="kpi-row six">'
                + kpi(words["rain_now"], f"{row['rain_so_far_mm']:.0f}")
                + kpi(words["usual_col"], f"{row['usual_sep_oct_mm']:.0f}")
                + kpi(words["yield_usual"], f"{row['usual_yield_kg_ha']:.0f}")
                + opt_kpi(words["stat_water"], row, "water_balance_week_mm", "{:+.0f}")
                + opt_kpi(words["stat_etc"], row, "etc_week_mm", "{:.0f}")
                + kpi(words["stat_irrigated"], f"{row['irrigated_pct']:.1f}%")
                + "</div>"
                + why_box(row, words)
                + provable_evidence_box(row, words),
                unsafe_allow_html=True,
            )

        profile = pack(alerts, forecast, watch, soil, vegetation, chosen)
        if "ussd_step" not in st.session_state:
            st.session_state.ussd_step = "home"
        screen = {
            "home": words["ussd_home"],
            "weather": words["ussd_weather"].format(district=chosen, pct=profile["rain_pct"], week=profile["week_mm"], irrig=profile["irrigated_pct"]),
            "soil": words["ussd_soil"].format(district=chosen, concern=profile["concern_pct"], protected=profile["protected_pct"]),
            "kit": words["ussd_kit"],
        }[st.session_state.ussd_step]
        with st.expander("📱 " + tr("Phone preview: SMS and *801# menu", "Reba kuri telefone: SMS na *801#")):
            st.markdown(
                f'<p class="section-p">{words["sms_note"]}</p><div class="phone-wrap">'
                f'<div><p class="kicker-green">{words["sms_title"]}</p>'
                f'<div class="feature-phone"><div class="phone-bar">SMS · MTN</div>'
                f'<div class="phone-screen">{sms_text(profile, words)}</div></div></div>'
                f'<div><p class="kicker-green">{words["ussd_title"]}</p>'
                f'<div class="feature-phone"><div class="phone-bar">*801#</div>'
                f'<div class="phone-screen">{screen}</div></div></div></div>',
                unsafe_allow_html=True,
            )
            u1, u2, u3, u0 = st.columns(4)
            if u1.button(words["ussd_1"], key="ussd_w"):
                st.session_state.ussd_step = "weather"
                st.rerun()
            if u2.button(words["ussd_2"], key="ussd_s"):
                st.session_state.ussd_step = "soil"
                st.rerun()
            if u3.button(words["ussd_3"], key="ussd_k"):
                st.session_state.ussd_step = "kit"
                st.rerun()
            if u0.button(words["ussd_0"], key="ussd_h"):
                st.session_state.ussd_step = "home"
                st.rerun()

        # ---- national overview ---------------------------------------------------------
        n_crit = int((alerts["climate_class"] == "water_stress").sum()) if "climate_class" in alerts.columns else 0
        n_high = max(int((alerts["alert"] == "irrigation_gap").sum()) - n_crit, 0)
    n_soil = int(alerts["alert"].isin(["soil_rain", "soil_watch"]).sum())
    n_stab = int((alerts["alert"] == "stable").sum())

    st.markdown(
        f"""
            <div class="inner-wrap" style="padding-top:24px">
              <p class="kicker-green">{tr("2. See all districts", "2. Reba uturere twose")}</p>
              <p class="section-p">{words["alerts_explain"]}</p>
          <div class="alert-triage-grid">
            <div class="alert-triage-card critical">
                  <div class="triage-head"><span class="triage-title">{words.get("alerts_triage_critical", "Critical moisture stress")}</span><span class="triage-count">{n_crit}</span></div>
                  <div class="triage-desc">{words.get("alerts_triage_critical_desc", "Severe deficit and under 10% irrigation.")}</div>
            </div>
            <div class="alert-triage-card high">
                  <div class="triage-head"><span class="triage-title">{words.get("alerts_triage_high", "High irrigation gap")}</span><span class="triage-count">{n_high}</span></div>
                  <div class="triage-desc">{words.get("alerts_triage_high_desc", "Rainfall deficit. Mobilize supplementary irrigation.")}</div>
            </div>
            <div class="alert-triage-card soil">
                  <div class="triage-head"><span class="triage-title">{words.get("alerts_triage_soil", "Hillside runoff risk")}</span><span class="triage-count">{n_soil}</span></div>
                  <div class="triage-desc">{words.get("alerts_triage_soil_desc", "Sloping plots. Reinforce terraces and drainage.")}</div>
            </div>
            <div class="alert-triage-card stable">
                  <div class="triage-head"><span class="triage-title">{words.get("alerts_triage_stable", "Stable")}</span><span class="triage-count">{n_stab}</span></div>
                  <div class="triage-desc">{words.get("alerts_triage_stable_desc", "Standard seasonal monitoring.")}</div>
              </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

        view = alerts.copy()
        geo_path = APP_TABLES / "districts.geojson"
        geojson = load_geojson(geo_path.stat().st_mtime if geo_path.exists() else 0)

        with st.container(key="alert_map_board"):
            col_ctrl, col_map = st.columns([0.95, 2.05], vertical_alignment="top", gap="medium")
    with col_ctrl:
        st.markdown(
            f"""
            <div class="map-controls-deck">
              <div class="deck-header">
                        <span class="deck-icon">🇷🇼</span>
                <div>
                          <strong>{tr("Rwanda · 30 districts", "u Rwanda · uturere 30")}</strong>
                          <small>{tr(f"Selected: {chosen}", f"Byatoranijwe: {chosen}")}</small>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
                st.markdown(
                    f'<p class="map-side-label">{words["layer_title"]}</p>',
                    unsafe_allow_html=True,
                )
        layer = st.radio(
            words["layer_title"],
            ["alert", "climate", "rain", "irrigation", "soil", "vegetation"],
            format_func=lambda key: {
                "alert": "🚨 " + words["layer_alert"],
                "climate": "🌍 " + words["layer_climate"],
                "rain": "🌧️ " + words["layer_rain"],
                "irrigation": "💧 " + words["layer_irrig"],
                "soil": "⛰️ " + words["layer_soil"],
                "vegetation": "🌿 " + words["layer_veg"],
            }[key],
            index=0 if role != "agronomist" else 1,
            label_visibility="collapsed",
            key="map_layer",
        )
                st.markdown(f'<p class="map-side-label">🎯 {words["filter"]}</p>', unsafe_allow_html=True)
        shown = st.pills(
            words["filter"],
            ["all", "irrigation", "soil", "stable"],
            format_func=lambda key: {
                        "all": tr("All (30)", "Byose (30)"),
                        "irrigation": tr("Irrigation", "Kuhira"),
                        "soil": tr("Hillside", "Ubutaka"),
                        "stable": tr("Stable", "Bitekanye"),
            }[key],
            default="all" if role == "agronomist" else "irrigation",
            label_visibility="collapsed",
            key="alert_filter",
        )
        if shown is None:
            shown = "all" if role == "agronomist" else "irrigation"
        dry_cut = st.slider(words["filter_rain"], min_value=-40, max_value=10, value=10, step=5, key="dry_cut")
        st.markdown(layer_legend(layer, words), unsafe_allow_html=True)

    if shown == "irrigation":
        view = view[view["alert"].isin(["irrigation_gap", "irrigate_now", "dry_watch"])]
    elif shown == "soil":
        view = view[view["alert"].isin(["soil_rain", "soil_watch"])]
    elif shown == "stable":
        view = view[view["alert"] == "stable"]
    view = view[view["rain_difference_pct"] <= dry_cut]
    with col_map:
                st.markdown(
                    f'<p class="map-frame-title">{tr("National alert map", "Ikarita y\'iburira y\'igihugu")} · {chosen}</p>',
                    unsafe_allow_html=True,
                )
        if geojson is not None:
                    components.html(
                        alert_map(alerts, forecast, geojson, words, layer=layer, focus_district=chosen),
                        height=620,
                        scrolling=False,
                    )
        else:
            st.markdown(f'<div class="note-box">{words["map_missing"]}</div>', unsafe_allow_html=True)

        if view.empty:
            st.markdown(f'<div class="note-box">{words["empty_district"]}</div>', unsafe_allow_html=True)

        rank = national_ranking(alerts)
        st.markdown(
            f'<p class="kicker-green">{words.get("ranking_title", "District order this Season A")}</p>'
            f'<p class="section-p">{words.get("ranking_lead", "Ordered by irrigation and soil need for planners. The NISR 20-point boxes score the CropWatch project, not districts.")}</p>',
            unsafe_allow_html=True,
        )
        rank_rows = [
            (
                int(item["rank"]),
            item["district"],
                f"<strong>{item['track1_score']:.1f}</strong>",
                f"{item['rain_pts']:.1f} / 40",
                f"{item['irrig_pts']:.1f} / 30",
                f"{item['soil_pts']:.1f} / 20",
                f"{item['week_pts']:.1f} / 10",
            pill(item["alert"], words),
        )
            for _, item in rank.iterrows()
    ]
    st.markdown(
            data_table(
                [
                    words.get("rank_col", "Rank"),
                    words["district_col"],
                    words.get("score_col", "Need /100"),
                    words.get("pts_rain", "Rain /40"),
                    words.get("pts_irrig", "Irrigation /30"),
                    words.get("pts_soil", "Soil /20"),
                    words.get("pts_week", "Week water /10"),
                    words["col_status"],
                ],
                rank_rows,
            ),
        unsafe_allow_html=True,
    )
        st.download_button(
            words.get("ranking_csv", "Download district order (CSV)"),
            rank.to_csv(index=False).encode("utf-8"),
            "cropwatch_district_order.csv",
            "text/csv",
            key="national_rank_csv",
            width="stretch",
        )
        st.caption(words.get("ranking_note", "Planner order: rain, irrigation gap, soil, week water. Not a judge score of the team."))
    render_footer(words)

# ======================================================================================
# MY DISTRICT: overview, climate and markets, soil, what-if yield, irrigation kit
# ======================================================================================
elif page == "district":
    page_head(words["dash_title"], words["dash_lead"], words)

    with page_body():
        tab_matrix, tab_climate, tab_soil, tab_yield, tab_ssit = st.tabs([
            tr("Overview", "Incamake"),
            tr("Climate & markets", "Ikirere n'amasoko"),
            tr("Soil & terraces", "Ubutaka n'amaterasi"),
            tr("What-if yield", "Isesengura ry'umusaruro"),
            tr("Irrigation kit", "Ibikoresho byo kuhira"),
        ])

        # ---- Overview ------------------------------------------------------------------
    with tab_matrix:
            chosen_d = district_select(words["dash_profile_title"], district_names_all, "dash_district")
            drow = alerts[alerts["district"] == chosen_d].iloc[0]
            dweek = forecast[forecast["district"] == chosen_d].sort_values("date")
            st.markdown(
                '<div class="inner-wrap">'
                + verdict_card(drow, words)
                + '<div class="kpi-row six">'
                + kpi(words["rain_now"], f"{drow['rain_so_far_mm']:.0f}")
                + kpi(words["stat_irrigated"], f"{drow['irrigated_pct']:.1f}%")
                + kpi(words["concern_metric"], f"{drow['concern_pct']:.0f}")
                + kpi(words["yield_usual"], f"{drow['usual_yield_kg_ha']:.0f}")
                + opt_kpi(words["stat_water"], drow, "water_balance_week_mm", "{:+.0f}")
                + opt_kpi(words["stat_etc"], drow, "etc_week_mm", "{:.0f}")
                + "</div>"
                + why_box(drow, words)
                + week_panel(dweek, words)
                + harvest_strip(watch, chosen_d, words)
                + "</div>",
                unsafe_allow_html=True,
            )
            st.download_button(
                words["export_html"],
                html_report(drow, words, dweek).encode("utf-8"),
                f"cropwatch_{chosen_d.lower()}_note.html",
                "text/html",
                key="dash_html",
            )

        counts = alerts["alert"].value_counts()
        count_rows = [(words.get("label_" + name, name), int(value)) for name, value in counts.items()]
        climate_block = ""
        if "climate_class" in alerts.columns:
            climate_rows = [
                (words.get("label_" + name, name), int(value))
                for name, value in alerts["climate_class"].value_counts().items()
            ]
            climate_block = (
                f'<p class="kicker-green" style="margin-top:28px">{words["climate_kicker"]}</p>'
                f'<p class="section-p">{words["climate_lead"]}</p>'
                + data_table([words["col_status"], words["districts"]], climate_rows)
            )
        water_kpi = ""
        if "water_balance_week_mm" in driest.index and pd.notna(driest.get("water_balance_week_mm")):
            water_kpi = kpi(words["stat_water"], f"{float(driest['water_balance_week_mm']):+.0f}")
            with st.expander("📊 " + tr("National summary tables", "Incamake y'igihugu")):
        st.markdown(
                    '<div class="kpi-row">'
            + kpi(words["stat_alert_districts"], str(n_gap))
            + kpi(words["stat_irrigated"], f"{irrig_national:.1f}%")
            + kpi(words["stat_worst"], f"{driest['rain_difference_pct']:.0f}%")
            + water_kpi
            + "</div>"
                    + f'<p class="kicker-green" style="margin-top:28px">{words["dash_fresh_title"]}</p>'
            + '<div class="fresh-list">'
            + f'<article><span>{words["price_until"]}</span><strong>{status["price_last_date"]}</strong></article>'
            + f'<article><span>{words["rain_until"]}</span><strong>{rain_text}</strong></article>'
            + f'<article><span>{words["trade_until"]}</span><strong>{int(status["trade_last_year"])}</strong></article>'
            + "</div>"
            + f'<div class="note-box">{words["dash_status_ok"]}. {words["dash_status_api"]}. {words["pilot_note"]}</div>'
            + f'<p class="kicker-green">{words["dash_risk_title"]}</p>'
            + data_table([words["col_status"], words["districts"]], count_rows)
            + climate_block
                    + f'<p class="section-p">{words["export_note"]}</p>',
            unsafe_allow_html=True,
        )
        st.download_button(
            words["export_csv"],
            alerts.to_csv(index=False).encode("utf-8"),
            "cropwatch_irrigation_alerts.csv",
            "text/csv",
            key="dash_csv",
        )

        # ---- Climate and markets -------------------------------------------------------
    with tab_climate:
            st.markdown(f'<p class="section-p">{words["watch_explain"]}</p>', unsafe_allow_html=True)
        district_names_w = sorted(watch["district"].unique())
            left_w, right_w = st.columns([1.1, 2], vertical_alignment="bottom")
        with left_w:
            chosen_w = st.selectbox(
                words["pick_district"],
                district_names_w,
                index=district_names_w.index("Nyagatare") if "Nyagatare" in district_names_w else 0,
                key="watch_district",
            )
        with right_w:
            season_labels = {
                    "A": tr("Season A 2026", "Igihembwe A 2026"),
                    "B": tr("Season B 2026", "Igihembwe B 2026"),
            }
            chosen_season = st.pills(
                words["season_col"],
                ["B", "A"],
                format_func=lambda code: season_labels[code],
                default="B",
                label_visibility="collapsed",
                key="season_pick",
            )
            if chosen_season is None:
                chosen_season = "B"
        w_row = watch[(watch["district"] == chosen_w) & (watch["season"] == chosen_season)].iloc[0]
        pct_w = float(w_row["rain_difference_pct"])
        yield_kg_w = float(w_row["usual_yield_kg_ha"])
        if pct_w <= -10:
            sentence_w = words["watch_drier"]
        elif pct_w >= 10:
            sentence_w = words["watch_wetter"]
        else:
            sentence_w = words["watch_close"]
        if pd.notna(w_row["maize_price_rwf_per_kg"]):
            price_text_w = words["price_here"].format(price=w_row["maize_price_rwf_per_kg"], date=w_row["price_date"])
        else:
            price_text_w = words["price_national"].format(price=w_row["national_maize_price_rwf_per_kg"], date=w_row["national_price_date"])
        veg_text_w = words["veg_line"].format(year=2026, now=w_row["vegetation_2026"], usual=w_row["usual_vegetation"])
        export_year_rows = [(int(item["year"]), f"{item['trade_value_usd']:,.0f}", item.get("partner", "")) for _, item in exports_year.iterrows()]
        export_partner_rows = [(item["partner"], f"{item['trade_value_usd']:,.0f}", int(item["year"])) for _, item in exports_partners.iterrows()]
        st.markdown(
            '<div class="inner-wrap">'
            + board(
                season_labels[chosen_season],
                chosen_w,
                sentence_w.format(pct=abs(pct_w), yield_kg=yield_kg_w),
                "",
                [
                    kpi(words["rain_now"], f"{w_row['rain_mm']:.0f}"),
                    kpi(words["usual_col"], f"{w_row['usual_rain_mm']:.0f}"),
                    kpi(words["diff_col"], f"{w_row['rain_difference_mm']:.0f}"),
                    kpi(words["yield_usual"], f"{yield_kg_w:.0f}"),
                ],
            )
            + '<div class="split-cards">'
            + f'<article><h3>{words["price_card"]}</h3><p>{price_text_w}</p></article>'
            + f'<article><h3>{words["veg_card"]}</h3><p>{veg_text_w}</p></article>'
            + "</div>"
            + f'<p class="kicker-green">{words["ndre_title"]}</p><p class="section-p">{words["ndre_lead"]}</p>'
            + "</div>",
            unsafe_allow_html=True,
        )
        veg_d = vegetation[vegetation["district"] == chosen_w].sort_values("year")
        nat_v = vegetation.groupby("year")["vegetation_mean"].mean()
        ndre_chart = pd.DataFrame({
            words["ndre_district"]: veg_d.set_index("year")["vegetation_mean"],
            words["ndre_national"]: nat_v,
        })
        st.line_chart(ndre_chart, height=280)
            with st.expander("🌽 " + tr("Maize exports", "Ibigori byoherezwa hanze")):
                st.markdown(
                    f'<p class="kicker-green">{words["export_year"]}</p><p class="section-p">{words["export_lead"]}</p>'
                    + data_table([words["year_col"], "USD", words["note_col"]], export_year_rows)
                    + f'<p class="kicker-green">{words["export_partners"]}</p>'
                    + data_table([words["note_col"], "USD", words["year_col"]], export_partner_rows),
                    unsafe_allow_html=True,
                )

        # ---- Soil and terraces ---------------------------------------------------------
    with tab_soil:
            st.markdown(f'<p class="section-p">{words["soil_explain"]}</p>', unsafe_allow_html=True)
        view_s = soil.copy()
        view_s["concern"] = 100 * view_s["concern_yes_weight"] / view_s["concern_weight"]
        view_s["severe"] = 100 * view_s["severe_yes_weight"] / view_s["severe_weight"]
        view_s["protected"] = 100 * view_s["protected_yes_weight"] / view_s["protected_weight"]
        view_s["organic"] = 100 * view_s["organic_yes_weight"] / view_s["organic_weight"]
        view_s["inorganic"] = 100 * view_s["inorganic_yes_weight"] / view_s["inorganic_weight"]
        view_s["short"] = 100 * view_s["organic_short_yes_weight"] / view_s["organic_short_weight"]
        district_names_s = sorted(view_s["district"].unique())
        chosen_s = st.selectbox(
            words["pick_district"],
            district_names_s,
            index=district_names_s.index("Rulindo") if "Rulindo" in district_names_s else 0,
            key="soil_district",
        )
        s_row = view_s[view_s["district"] == chosen_s].iloc[0]
        rain_pct_s = float(s_row["rain_difference_pct"])
        if rain_pct_s <= -10:
            rain_sentence_s = words["soil_rain_drier"]
        elif rain_pct_s >= 10:
            rain_sentence_s = words["soil_rain_wetter"]
        else:
            rain_sentence_s = words["soil_rain_close"]
        ranked_s = view_s.sort_values("concern", ascending=False)
        ranked_rows_s = [
            (
                item["district"],
                bar_cell(item["concern"]),
                f"{item['severe']:.0f}%",
                f"{item['protected']:.0f}%",
                f"{item['organic']:.0f}%",
                f"{item['inorganic']:.0f}%",
                f"{item['rain_difference_pct']:.0f}%",
            )
            for _, item in ranked_s.iterrows()
        ]
        st.markdown(
            '<div class="inner-wrap">'
            + board(
                    tr("Soil", "Ubutaka"),
                chosen_s,
                words["soil_sentence"].format(
                    concern=s_row["concern"],
                    severe=s_row["severe"],
                    protected=s_row["protected"],
                    organic=s_row["organic"],
                    inorganic=s_row["inorganic"],
                )
                + " "
                + words["soil_short"].format(short=s_row["short"]),
                rain_sentence_s.format(
                    pct=abs(rain_pct_s),
                    rain=s_row["rain_mm"],
                    usual=s_row["usual_rain_mm"],
                    yield_kg=s_row["usual_yield_kg_ha"],
                ),
                [
                    kpi(words["concern_metric"], f"{s_row['concern']:.0f}"),
                    kpi(words["severe_metric"], f"{s_row['severe']:.0f}"),
                    kpi(words["protected_metric"], f"{s_row['protected']:.0f}"),
                    kpi(words["organic_metric"], f"{s_row['organic']:.0f}"),
                    kpi(words["inorganic_metric"], f"{s_row['inorganic']:.0f}"),
                ],
            )
            + f'<p class="kicker-green">{words["soil_table"]}</p>'
            + data_table(
                [
                    words["district_col"],
                    words["concern_metric"],
                    words["severe_metric"],
                    words["protected_metric"],
                    words["organic_metric"],
                    words["inorganic_metric"],
                    words["rain_vs"],
                ],
                ranked_rows_s,
            )
            + "</div>",
            unsafe_allow_html=True,
        )
        st.download_button(
            words["export_csv"],
            view_s[["district", "concern", "severe", "protected", "organic", "inorganic", "short", "rain_difference_pct"]].to_csv(index=False).encode("utf-8"),
            "cropwatch_soil_season_a_2022.csv",
            "text/csv",
            key="soil_csv",
        )

        # ---- What-if yield -------------------------------------------------------------
        sim_names = sorted(sim_base["district"].unique()) if not sim_base.empty else district_names_all
    with tab_yield:
            st.markdown(f'<p class="section-p">{words["sim_lead"]}</p>', unsafe_allow_html=True)
        chosen_sim = st.selectbox(
            words["pick_district"],
                sim_names,
                index=sim_names.index("Bugesera") if "Bugesera" in sim_names else 0,
            key="sim_district_select",
        )
        sim_row = sim_base[sim_base["district"] == chosen_sim].iloc[0] if not sim_base.empty else alerts[alerts["district"] == chosen_sim].iloc[0]
        effects = (benchmark or {}).get("within_district_kg_ha", {})
        left, right = st.columns(2)
        with left:
            d_irrig = st.slider(words["sim_irrig_slider"], 0, 30, 10, 5, help=words["sim_irrig_help"], key="d_irrig")
        with right:
            d_short = st.slider(words["sim_organic_slider"], 0, 50, 20, 10, help=words["sim_organic_help"], key="d_short")
        current_irrig = float(sim_row["irrigated_pct"])
        current_short = float(sim_row["organic_short_pct"]) if "organic_short_pct" in sim_row and pd.notna(sim_row["organic_short_pct"]) else 0.0
            whatif = district_share_whatif(
                sim_row["usual_yield_kg_ha"], current_irrig, current_short, d_irrig, d_short, effects
            )
            irrig_gap = whatif["irrig_gap"]
            short_gap = whatif["short_gap"]
            new_irrig = whatif["new_irrig_pct"]
            new_short = whatif["new_short_pct"]
            gain_kg = whatif["gain_kg_ha"]
            base_y = whatif["base_kg_ha"]
            proj_y = whatif["projected_kg_ha"]
            gain_pct = whatif["gain_pct"]
        sim_body = words["sim_body"].format(
            district=chosen_sim, irrig_gap=irrig_gap, short_gap=short_gap,
            d_irrig=new_irrig - current_irrig, d_short=current_short - new_short, gain=gain_kg, pct=gain_pct,
        )
        st.markdown(
            '<div class="inner-wrap">'
            + f'<div class="note-box">{words["sim_assump"]}</div>'
            + board(
                    tr("What-if yield", "Isesengura ry'umusaruro"), chosen_sim, sim_body,
                words["sim_policy_note"] + " " + words["sim_protect_note"],
                [
                    kpi(words["sim_base_yield"], f"{base_y:.0f}"),
                    kpi(words["sim_projected_yield"], f"{proj_y:.0f}"),
                    kpi(words["sim_gain"], f"{gain_kg:+.0f}"),
                    kpi(words["sim_gain_pct"], f"{gain_pct:+.1f}%"),
                    kpi(words["stat_irrigated"], f"{current_irrig:.1f}% → {new_irrig:.1f}%"),
                    kpi(words["sim_short_now"], f"{current_short:.1f}% → {new_short:.1f}%"),
                ],
            )
            + "</div>",
            unsafe_allow_html=True,
        )

        # ---- Irrigation kit ------------------------------------------------------------
    with tab_ssit:
            chosen_kit = st.selectbox(
                words["pick_district"], sim_names,
                index=sim_names.index("Bugesera") if "Bugesera" in sim_names else 0,
                key="ssit_district",
            )
        kit_row = alerts[alerts["district"] == chosen_kit].iloc[0]
        watch_hit = watch[(watch["district"] == chosen_kit) & (watch["season"] == "A")]
        watch_hit = watch_hit.iloc[0] if not watch_hit.empty else None
        hectares = st.slider(words["ssit_ha"], 0.2, 5.0, 0.5, 0.1, key="ssit_ha")
        src_col, crop_col = st.columns(2)
        with src_col:
                source = st.selectbox(
                    words["ssit_source"],
                    ["marsh", "well", "tank"],
                    format_func=lambda key: words["ssit_src_" + key],
                    key="ssit_src",
                )
        with crop_col:
            crop_choice = st.selectbox(
                words["ssit_crop"],
                ["maize", "veg", "bean", "potato"],
                format_func=lambda key: words["ssit_crop_" + key],
                key="ssit_crop",
            )
            plan = ssit_plan(hectares, source)
            kit_name = plan["name_rw"] if st.session_state.lang == "rw" else plan["name_en"]
            irrig_gap_kit = float((benchmark or {}).get("within_district_kg_ha", {}).get("irrigated", 365.3))
            protected_kg = irrig_gap_kit * hectares
        price = None
        price_date = None
        if watch_hit is not None and pd.notna(watch_hit.get("maize_price_rwf_per_kg")):
            price = float(watch_hit["maize_price_rwf_per_kg"])
            price_date = str(watch_hit["price_date"])
        elif watch_hit is not None:
            price = float(watch_hit["national_maize_price_rwf_per_kg"]) if pd.notna(watch_hit.get("national_maize_price_rwf_per_kg")) else None
            price_date = str(watch_hit.get("national_price_date") or "")
        value_rwf = protected_kg * price if price else None
        extra_note = words["ssit_badge"]
            if plan.get("warning"):
                extra_note += " " + plan["warning"]
        if crop_choice != "maize":
            extra_note += " " + words["ssit_other_crop"]
        if watch_hit is not None and pd.isna(watch_hit.get("maize_price_rwf_per_kg")):
            extra_note += " " + words["ssit_no_price"].format(date=price_date or "—")
        kpis = [
            kpi(words["ssit_kit"], kit_name),
                kpi(words.get("ssit_cost", "Indicative kit (RWF)"), f"{plan['indicative_cost_rwf']:,.0f}"),
                kpi(words.get("ssit_farmer", "Farmer 50% (RWF)"), f"{plan['farmer_rwf']:,.0f}"),
                kpi(words.get("ssit_subsidy_amt", "Subsidy 50% (RWF)"), f"{plan['subsidy_rwf']:,.0f}"),
            kpi(words["ssit_protect"], f"{protected_kg:.0f}" if crop_choice == "maize" else "—"),
            kpi(words["ssit_value"], f"{value_rwf:,.0f}" if value_rwf is not None and crop_choice == "maize" else "—"),
        ]
        st.markdown(
            '<div class="inner-wrap">'
            + f'<div class="policy-badge">{words["ssit_badge"]}</div>'
            + board(words["ssit_title"], chosen_kit, words["ssit_lead"], extra_note, kpis)
            + "</div>",
            unsafe_allow_html=True,
        )

        d1, d2, d3 = st.columns(3)
        d1.button(words["nav_alerts"], width="stretch", key="dash_to_alerts", on_click=jump, args=("alerts",))
        d2.button("ADVICE AI", width="stretch", key="dash_to_advise", on_click=jump, args=("advise",))
        d3.button(words["nav_data"], width="stretch", key="dash_to_data", on_click=jump, args=("data",))
    render_footer(words)

# ======================================================================================
# ADVICE AI
# ======================================================================================
elif page == "advise":
    page_head(
        words.get("chat_title", "ADVICE AI"),
        words.get("chat_lead", "Ask questions about irrigation, soil, markets and risk for any district."),
        words,
    )

    ORB = (
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<path d="M12 2l1.8 5.7L19.5 9.5l-5.7 1.8L12 17l-1.8-5.7L4.5 9.5l5.7-1.8z" fill="#062615"/>'
        '<path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z" fill="#062615"/></svg>'
    )
    QUICK_DEFS = [
        ("yield", "chat_btn_yield", "🧪 Yield uplift"),
        ("insurance", "chat_btn_insurance", "🛡️ Climate insurance"),
        ("market", "chat_btn_market", "💰 Market and storage"),
        ("irrigation", "chat_btn_irrigation", "💧 Smart irrigation"),
        ("soil", "chat_btn_soil", "🏔️ Terraces and soil"),
        ("pests", "chat_btn_pests", "🐛 Pests and fertilizer"),
        ("sms", "chat_btn_sms", "📱 160-character SMS"),
        ("week", "chat_pill_week", "📅 This week"),
    ]

    def quick_grid():
        picked = None
        for start in (0, 4):
            cols = st.columns(4)
            for col, (intent, key, default) in zip(cols, QUICK_DEFS[start:start + 4]):
                if col.button(words.get(key, default), key=f"btn_ai_{intent}", width="stretch"):
                    picked = intent
        return picked

    with page_body():
        # a district detected in the typed question is applied here, before the picker is drawn
        if "chat_district_next" in st.session_state:
            st.session_state.chat_district = st.session_state.pop("chat_district_next")

        district_names = district_names_all
        default_d = st.session_state.get("district") or ("Nyaruguru" if role == "farmer" else ("Bugesera" if role == "policy" else "Nyagatare"))
    if default_d not in district_names:
        default_d = district_names[0]
        current_d = st.session_state.get("chat_district", default_d)
        if current_d not in district_names:
            current_d = district_names[0]
        history_key = f"chat_{current_d}_{st.session_state.lang}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []
        profile = pack(alerts, forecast, watch, soil, vegetation, current_d)

        engine = llm_status()
        status_msg = words.get("chat_engine_llm", "Cloud LLM connected") if engine else words.get("chat_engine_fast", "Local agronomic engine")
        status_msg = status_msg.replace("⚡", "").strip()

        col_main, col_side = st.columns([2.2, 1.0], gap="large")

        # =================== conversation panel ===================
        with col_main:
            with st.container(key="ai_chat"):
                st.markdown(
                    f"""
                    <div class="ai-head">
                      <div class="ai-orb">{ORB}</div>
                      <div class="ai-head-text">
                        <h2>ADVICE AI</h2>
                        <p>{tr("Crop water assistant for", "Umufasha ku mazi y'imyaka mu")} {current_d}</p>
                      </div>
                      <span class="ai-live"><i></i>{status_msg}</span>
                    </div>
                    <div class="ai-ctx">
                      <span>🌧️ {profile['rain_pct']:+.0f}% {tr("vs usual", "ku isanzwe")}</span>
                      <span>📅 {profile['week_mm']:.0f} mm {tr("next 7 days", "mu minsi 7")}</span>
                      <span>💧 {profile['deficit_mm']:.1f} mm {tr("water gap", "icyuho")}</span>
                      <span>🌽 {f"{profile['price']:.0f} RWF/kg" if profile.get("price") is not None else "no WFP maize price"}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_d, col_exp, col_clr = st.columns([2.0, 1.2, 0.8], vertical_alignment="bottom")
    with col_d:
        chosen_chat = st.selectbox(
            words["pick_district"],
            district_names,
                        index=district_names.index(current_d),
            key="chat_district",
        )
                    st.session_state.district = chosen_chat
    with col_exp:
        if st.session_state[history_key]:
                        transcript_text = f"# CropWatch Rwanda: ADVICE AI briefing ({chosen_chat})\n\n"
            for s_role, s_msg in st.session_state[history_key]:
                            pfx = "Farmer or extension agent" if s_role == "user" else "ADVICE AI"
                transcript_text += f"### {pfx}:\n{s_msg}\n\n"
            st.download_button(
                            "📥 " + tr("Export", "Koporora"),
                transcript_text.encode("utf-8"),
                            f"cropwatch_advice_{chosen_chat.lower()}.md",
                "text/markdown",
                key=f"dl_transcript_{chosen_chat}",
                width="stretch",
            )
        else:
                        st.button("📥 " + tr("Export", "Koporora"), disabled=True, width="stretch", key="btn_exp_disabled")
    with col_clr:
                    if st.button("🔄 " + tr("Clear", "Siba"), key="btn_clear_chat", width="stretch"):
            st.session_state[history_key] = []
            st.rerun()

                quick = None
                history = st.session_state[history_key]
                last_bot = next((msg for speaker, msg in reversed(history) if speaker == "bot"), "")
                chat_ctx = {"district": current_d, "last_bot": last_bot}

                if not history:
    st.markdown(
        f"""
                        <div class="ai-welcome">
                          <div class="ai-orb big">{ORB}</div>
                          <h3>{tr(f"How can I help in {chosen_chat}?", f"Nagufasha iki muri {chosen_chat}?")}</h3>
                          <p>{tr(
                              "Ask about irrigation, soil, fertilizer, prices or risk. Answers use this week's rain, the 7-day forecast and survey data for the district.",
                              "Baza ku kuhira, ubutaka, ifumbire, ibiciro cyangwa ibyago. Ibisubizo bishingiye ku mvura, iteganyagihe n'amakuru y'ubuhinzi by'akarere."
                          )}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
                    quick = quick_grid()

        if quick:
                    label = dict((i, words.get(k, d)) for i, k, d in QUICK_DEFS)[quick]
                    with st.spinner(tr("ADVICE AI is thinking…", "ADVICE AI iratekereza…")):
                        text = answer(label, profile, words, st.session_state.lang, force_intent=quick, context=chat_ctx)
                    st.session_state[history_key].append(("user", label))
            st.session_state[history_key].append(("bot", text))
            st.rerun()

        if "pending_chat_prompt" in st.session_state:
            pending_q = st.session_state.pop("pending_chat_prompt")
                    with st.spinner(tr("ADVICE AI is thinking…", "ADVICE AI iratekereza…")):
                        ans_text = answer(pending_q, profile, words, st.session_state.lang, context=chat_ctx)
            st.session_state[history_key].append(("user", pending_q))
            st.session_state[history_key].append(("bot", ans_text))
            st.rerun()

                num_msgs = len(history)
                for idx, (speaker, text) in enumerate(history):
            if speaker == "user":
                with st.chat_message("user", avatar="👤"):
                            st.markdown('<span class="user-marker" style="display:none;"></span>', unsafe_allow_html=True)
                    st.markdown(text)
            else:
                with st.chat_message("assistant", avatar="🌾"):
                    st.markdown(
                                f'<span class="assistant-marker" style="display:none;"></span>'
                                f'<div class="ai-msg-label">ADVICE AI · {chosen_chat}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(text)
                    if idx == num_msgs - 1:
                                components.html(audio_speech_html(text, st.session_state.lang), height=46)
                                followups = get_followups(classify(text), st.session_state.lang)
                        if followups:
                                    st.markdown(f'<p class="ai-next">{tr("Try next", "Inyigo zikurikira")}</p>', unsafe_allow_html=True)
                            chip_cols = st.columns(len(followups))
                            for c_idx, chip_text in enumerate(followups):
                                if chip_cols[c_idx].button(chip_text, key=f"chip_btn_{idx}_{c_idx}", width="stretch"):
                                    st.session_state["pending_chat_prompt"] = chip_text
                                    st.rerun()

                if history:
                    with st.expander("💡 " + tr("Suggested questions", "Ibibazo byagutse")):
                        quick = quick_grid()
                    if quick:
                        label = dict((i, words.get(k, d)) for i, k, d in QUICK_DEFS)[quick]
                        with st.spinner(tr("ADVICE AI is thinking…", "ADVICE AI iratekereza…")):
                            text = answer(label, profile, words, st.session_state.lang, force_intent=quick, context=chat_ctx)
                        st.session_state[history_key].append(("user", label))
                        st.session_state[history_key].append(("bot", text))
                        st.rerun()

                chat_input_val = st.chat_input(
                    tr(
                        f"Ask about {chosen_chat}… (e.g. Should I irrigate this week?)",
                        f"Baza ikibazo kuri {chosen_chat}… (Urugero: Nkeneye kuhira iki cyumweru?)",
                    )
                )
                st.markdown(
                    f'<p class="ai-foot">{tr("ADVICE AI can make mistakes. Check with your sector agronomist before you act.", "ADVICE AI ishobora kwibeshya. Baza agronome wa santere mbere yo gukora.")}</p>',
                    unsafe_allow_html=True,
                )

                if chat_input_val:
                    detected_d = extract_district(chat_input_val)
            if detected_d and detected_d != chosen_chat:
                        # switch district on the next run: the picker is already drawn, so its state is locked now
                        st.session_state["chat_district_next"] = detected_d
                        st.session_state["pending_chat_prompt"] = chat_input_val
                        st.toast(tr(f"Switched to {detected_d}", f"Hahinduwe ujya kuri {detected_d}"), icon="🧭")
                        st.rerun()
                    with st.spinner(tr("ADVICE AI is thinking…", "ADVICE AI iratekereza…")):
                        text = answer(chat_input_val, profile, words, st.session_state.lang, context=chat_ctx)
                    st.session_state[history_key].append(("user", chat_input_val))
            st.session_state[history_key].append(("bot", text))
            st.rerun()

        # =================== context panel ===================
        with col_side:
            rain_tone = "bad" if profile["rain_pct"] < -15 else ("warn" if profile["rain_pct"] < 0 else "good")
            screen_ai = drought_screen(profile["rain_pct"], profile["water_week"], profile["irrigated_pct"], profile["week_mm"])
            lbl_flag = tr("Water flag", "Iburira ry'amazi")
            lbl_noflag = tr("No irrigation alert", "Nta iburira ryo kuhira")
            flag_html = (
                f'<span class="ai-flag warn">{lbl_flag}</span>'
                if screen_ai["cropwatch_water_flag"]
                else f'<span class="ai-flag good">{lbl_noflag}</span>'
            )
        st.markdown(
            f"""
            <div class="ai-side-card">
                  <div class="ai-side-header"><span>📍</span> <span>{tr("Live data for", "Amakuru y'ubu ya")} {current_d}</span></div>
                  <div class="ai-tiles">
                    <div class="ai-tile {rain_tone}"><span>{tr("Rain vs usual", "Imvura ku isanzwe")}</span><strong>{profile['rain_pct']:+.0f}%</strong></div>
                    <div class="ai-tile"><span>{tr("Next 7 days", "Iminsi 7")}</span><strong>{profile['week_mm']:.0f} mm</strong></div>
                    <div class="ai-tile"><span>{tr("Water gap", "Icyuho cy'amazi")}</span><strong>{profile['deficit_mm']:.1f} mm</strong></div>
                    <div class="ai-tile"><span>{tr("Maize price", "Igiciro cy'ibigori")}</span><strong>{f"{profile['price']:.0f} RWF" if profile.get("price") is not None else "—"}</strong></div>
              </div>
              </div>
                <div class="ai-side-card">
                  <div class="ai-side-header"><span>🛡️</span> <span>{tr("Risk and insurance", "Ibyago n'ubwishingizi")}</span></div>
                  <div class="ai-side-stat"><span class="ai-side-stat-lbl">{tr("Alert status", "Uko bihagaze")}</span><span class="ai-side-stat-val">{pill(profile['alert'], words)}</span></div>
                  <div class="ai-side-stat"><span class="ai-side-stat-lbl">{tr("Water screen", "Iburira ry'amazi")}</span><span class="ai-side-stat-val">{flag_html}</span></div>
                  <div class="ai-side-stat"><span class="ai-side-stat-lbl">{tr("SSIT kit (0.5 ha, marsh)", "Pompi ya SSIT (0.5 ha, igishanga)")}</span><span class="ai-side-stat-val">{ssit_plan(0.5, "marsh")["key"]}</span></div>
              </div>
            <div class="ai-side-card">
                  <div class="ai-side-header"><span>📊</span> <span>{tr("NISR survey baseline", "Amakuru ya NISR SAS")}</span></div>
                  <div class="ai-side-stat"><span class="ai-side-stat-lbl">{tr("Usual yield", "Umusaruro usanzwe")}</span><span class="ai-side-stat-val">{profile['usual_yield']:.0f} kg/ha</span></div>
                  <div class="ai-side-stat"><span class="ai-side-stat-lbl">{tr("Irrigated plots", "Imirima ihirwa")}</span><span class="ai-side-stat-val">{profile['irrigated_pct']:.1f}%</span></div>
                  <div class="ai-side-stat"><span class="ai-side-stat-lbl">{tr("Organic fertilizer", "Ifumbire y'imborera")}</span><span class="ai-side-stat-val">{profile['organic_pct']:.1f}%</span></div>
                  <div class="ai-side-stat"><span class="ai-side-stat-lbl">{tr("Inorganic (DAP/Urea)", "Ifumbire mvaruganda")}</span><span class="ai-side-stat-val">{profile['inorganic_pct']:.1f}%</span></div>
                  <div class="ai-side-stat"><span class="ai-side-stat-lbl">{tr("Protected slopes", "Imirima ifite amaterasi")}</span><span class="ai-side-stat-val">{profile['protected_pct']:.1f}%</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        sms_preview = sms_text(profile, words)
        lines_sms = [l for l in sms_preview.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("```") and not l.startswith("*")]
            clean_sms_str = lines_sms[0] if lines_sms else f"CropWatch {current_d}: Rain {profile['rain_pct']:+.0f}%. Week {profile['week_mm']:.0f}mm. SSIT {profile['deficit_mm']:.1f}mm deficit."
        clean_sms_str = clean_sms_str[:160]
        st.markdown(
            f"""
            <div class="ai-side-card">
                  <div class="ai-side-header"><span>📱</span> <span>{tr("160-character SMS", "SMS y'inyuguti 160")}</span></div>
              <div class="ai-sms-screen">{clean_sms_str}</div>
                  <div class="ai-sms-meta"><span>{len(clean_sms_str)} / 160 {tr("characters", "inyuguti")}</span><strong>{tr("Draft only", "Inyandiko gusa")}</strong></div>
              </div>
                <div class="ai-side-card soft">
                  <div class="ai-side-header"><span>🏛️</span> <span>{tr("Extension contacts", "Ubufasha bw'inzego")}</span></div>
                  <div class="ai-contacts">
                    <div>📞 <strong>MINAGRI:</strong> 1330 ({tr("toll-free", "ni ubuntu")})</div>
                    <div>🌿 <strong>RAB:</strong> {tr("Sector agronomist", "Agronome wa santere")}</div>
                    <div>🛡️ <strong>Tekana / NAIS:</strong> {tr("Ask the sector. CropWatch does not pay.", "Saba ku murenge. CropWatch ntishyura.")}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer(words)

# ======================================================================================
# DATA
# ======================================================================================
elif page == "data":
    page_head(words["src_title"], words["src_lead"], words)
    with page_body():
    t_sources, t_overview, t_crops, t_calendar, t_rain = st.tabs([
        words["tab_sources"],
        words["tab_overview"],
        words["tab_crops"],
        words["tab_calendar"],
        words["tab_rain"],
    ])
    with t_sources:
        cards = "".join(source_card(item, st.session_state.lang, words) for item in SOURCES)
            st.markdown(
                f'<div class="inner-wrap">{cards}'
                f'<div class="note-box"><strong>{words["footer_legal"]}</strong><br>{words["footer_disclaimer"]}<br>{words["footer_ack"]}</div>'
                "</div>",
                unsafe_allow_html=True,
            )

    with t_overview:
        wide = survey_rows.pivot(index="year", columns="season", values="crop_rows").sort_index().reset_index()
        record_headers = [words["year_col"]] + [str(col) for col in wide.columns if col != "year"]
        record_rows = []
        for _, item in wide.iterrows():
            record_rows.append([int(item["year"])] + [f"{int(item[col]):,}" if pd.notna(item[col]) else "—" for col in wide.columns if col != "year"])
        st.markdown(
            '<div class="inner-wrap">'
                + '<div class="kpi-row">'
            + kpi(words["survey_rows"], f"{int(status['survey_crop_rows']):,}")
            + kpi(words["safe"], str(int(status["safe_matches"])))
            + kpi(words["separate"], str(int(status["similar_kept_separate"])))
            + kpi(words["districts"], str(int(status["districts"])))
            + "</div>"
                + f'<p class="kicker-green" style="margin-top:32px">{words["fresh_files"]}</p>'
            + '<div class="fresh-list">'
            + f'<article><span>{words["price_until"]}</span><strong>{status["price_last_date"]}</strong></article>'
            + f'<article><span>{words["rain_until"]}</span><strong>{rain_text}</strong></article>'
            + f'<article><span>{words["trade_until"]}</span><strong>{int(status["trade_last_year"])}</strong></article>'
            + "</div>"
            + f'<div class="note-box">{words["not_all"]}</div>'
            + f'<p class="kicker-green">{words["records_title"]}</p><p class="section-p">{words["records_note"]}</p>'
            + data_table(record_headers, record_rows)
            + "</div>",
            unsafe_allow_html=True,
        )

    with t_crops:
            st.markdown(f'<p class="section-p">{words["safe_lead"]}</p>', unsafe_allow_html=True)
        if st.session_state.lang == "rw":
            safe_rw = safe.copy()
            safe_rw["product_form"] = safe_rw["product_form"].map(FORM_RW)
            show_table(
                safe_rw.rename(
                    columns={
                        "survey_crop_rw": words["survey_col"],
                        "price_name_rw": words["price_col"],
                        "product_form": words["form_col"],
                        "hs_heading": words["hs_col"],
                        "note_rw": words["note_col"],
                    }
                )[[words["survey_col"], words["price_col"], words["form_col"], words["hs_col"], words["note_col"]]]
            )
        else:
            show_table(
                safe.rename(
                    columns={
                        "survey_crop": words["survey_col"],
                        "price_name": words["price_col"],
                        "product_form": words["form_col"],
                        "hs_heading": words["hs_col"],
                        "note_en": words["note_col"],
                    }
                )[[words["survey_col"], words["price_col"], words["form_col"], words["hs_col"], words["note_col"]]]
            )

            st.markdown(f'<p class="kicker-green" style="margin-top:12px">{words["separate"]}</p><p class="section-p">{words["close_lead"]}</p>', unsafe_allow_html=True)
        if st.session_state.lang == "rw":
            show_table(
                close.rename(
                    columns={
                        "survey_crop_rw": words["survey_col"],
                        "price_name_rw": words["price_col"],
                        "note_rw": words["note_col"],
                    }
                )[[words["survey_col"], words["price_col"], words["note_col"]]]
            )
        else:
            show_table(
                close.rename(
                    columns={
                        "survey_crop": words["survey_col"],
                        "price_name": words["price_col"],
                        "note_en": words["note_col"],
                    }
                )[[words["survey_col"], words["price_col"], words["note_col"]]]
            )

            st.markdown(f'<p class="kicker-green" style="margin-top:12px">{words["no_price"]}</p><p class="section-p">{words["unmatched_lead"]}</p>', unsafe_allow_html=True)
        name_col = "survey_crop_rw" if st.session_state.lang == "rw" else "survey_crop"
        why_col = "why_rw" if st.session_state.lang == "rw" else "why_en"
        show_table(
            unmatched.rename(columns={name_col: words["crop_col"], why_col: words["note_col"]})[
                [words["crop_col"], words["note_col"]]
            ]
        )

    with t_calendar:
            st.markdown(f'<p class="section-p">{words["season_lead"]}</p>', unsafe_allow_html=True)
        if st.session_state.lang == "rw":
            show_table(
                seasons.rename(
                    columns={
                        "season_rw": words["season_col"],
                        "months_rw": words["months_col"],
                        "about_rw": words["about_col"],
                    }
                )[[words["season_col"], words["months_col"], words["about_col"]]]
            )
        else:
            show_table(
                seasons.rename(
                    columns={
                        "season_en": words["season_col"],
                        "months_en": words["months_col"],
                        "about_en": words["about_col"],
                    }
                )[[words["season_col"], words["months_col"], words["about_col"]]]
            )

            maize_title = tr("Maize and sorghum", "Ibigori n'amasaka")
            st.markdown(f'<p class="kicker-green" style="margin-top:12px">{maize_title}</p><p class="section-p">{words["calendar_lead"]}</p>', unsafe_allow_html=True)
        if st.session_state.lang == "rw":
            show_table(
                calendar.rename(
                    columns={
                        "crop_rw": words["crop_col"],
                        "season": words["season_col"],
                        "plant_rw": words["plant_col"],
                        "harvest_rw": words["harvest_col"],
                        "source": words["source_col"],
                    }
                )[[words["crop_col"], words["season_col"], words["plant_col"], words["harvest_col"], words["source_col"]]]
            )
        else:
            show_table(
                calendar.rename(
                    columns={
                        "crop_en": words["crop_col"],
                        "season": words["season_col"],
                        "plant_en": words["plant_col"],
                        "harvest_en": words["harvest_col"],
                        "source": words["source_col"],
                    }
                )[[words["crop_col"], words["season_col"], words["plant_col"], words["harvest_col"], words["source_col"]]]
            )

            st.markdown(f'<p class="kicker-green" style="margin-top:12px">{words["zone_col"]}</p><p class="section-p">{words["zone_lead"]}</p>', unsafe_allow_html=True)
        crop_key = 1 if st.session_state.lang == "rw" else 0
        crop_labels = {name: FAO_CROP[name][crop_key] for name in FAO_CROP}
        picked = st.selectbox(words["crop_col"], list(crop_labels), format_func=lambda name: crop_labels[name], key="hub_crop_zone")
        zone_view = zones[zones["fao_crop"] == picked].copy()
        month_names = words["month_names"]

        def span(day_start, month_start, day_end, month_end):
            if pd.isna(month_start) or pd.isna(month_end):
                return ""
            return f"{int(day_start)} {month_names[int(month_start)]} – {int(day_end)} {month_names[int(month_end)]}"

        zone_view[words["plant_col"]] = [
            span(a, b, c, d)
            for a, b, c, d in zip(
                zone_view["early_sowing_day"],
                zone_view["early_sowing_month"],
                zone_view["late_sowing_day"],
                zone_view["late_sowing_month"],
            )
        ]
        zone_view[words["harvest_col"]] = [
            span(a, b, c, d)
            for a, b, c, d in zip(
                zone_view["early_harvest_day"],
                zone_view["early_harvest_month"],
                zone_view["late_harvest_day"],
                zone_view["late_harvest_month"],
            )
        ]
        show_table(
            zone_view.rename(columns={"zone": words["zone_col"]})[
                [words["zone_col"], words["plant_col"], words["harvest_col"]]
            ]
        )

    with t_rain:
            st.markdown(f'<p class="section-p">{words["rain_lead"]}</p>', unsafe_allow_html=True)
            rain_districts = sorted(rain["district"].unique())
            rd_col, ry_col = st.columns(2)
            with rd_col:
                chosen_rd = st.selectbox(words["district_col"], rain_districts, index=rain_districts.index("Nyagatare") if "Nyagatare" in rain_districts else 0, key="hub_rain_district")
        years = sorted(rain["year"].unique())
            with ry_col:
        chosen_year = st.selectbox(words["year_col"], years, index=len(years) - 1, key="hub_rain_year")
            view_rain = rain[(rain["district"] == chosen_rd) & (rain["year"] == chosen_year)].sort_values("month").copy()
        view_rain[words["month_col"]] = view_rain["month"].map(words["month_names"])
        view_rain[words["rain_col"]] = view_rain["rainfall_mm"].round(1)
        view_rain[words["usual_col"]] = view_rain["usual_mm"].round(1)
        view_rain[words["diff_col"]] = view_rain["difference_mm"].round(1)
        show_table(view_rain[[words["month_col"], words["rain_col"], words["usual_col"], words["diff_col"]]])

    render_footer(words)

# ======================================================================================
# ABOUT
# ======================================================================================
elif page == "about":
    page_head(words["about_title"], words["about_lead"], words)
    with page_body():
    st.markdown(
        '<div class="inner-wrap">'
        f'<p class="section-p">{words["about_body"]}</p>'
        f'<p class="kicker-green">{words["about_obj"]}</p>'
        f'<p class="section-p">{words["about_obj_body"]}</p>'
        f'<p class="kicker-green">{words["about_who"]}</p>'
        '<div class="decision-grid">'
        f'<article><h3>{words["role_farmer"]}</h3><p>{words["about_farmer"]}</p></article>'
        f'<article><h3>{words["role_agronomist"]}</h3><p>{words["about_agro"]}</p></article>'
        f'<article><h3>{words["role_policy"]}</h3><p>{words["about_policy"]}</p></article>'
        "</div>"
        f'<p class="kicker-green" style="margin-top:36px">{words["more_tools"]}</p>'
        f'<p class="section-p">{words["about_ai"]}</p>'
        f'<p class="kicker-green" style="margin-top:36px">{words["about_team_title"]}</p>'
            f'<div style="display:inline-block; padding:5px 14px; background:rgba(196,163,90,0.15); border:1px solid var(--accent); border-radius:16px; font-size:14px; font-weight:600; color:var(--gold-soft); margin-bottom:16px;">🏆 {words["hackathon_badge"]}</div>'
            '<div class="decision-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:16px;">'
            f'<article style="border-top:3px solid var(--accent); border-left:0; padding:16px 0 0;">'
        f'<h3 style="margin-bottom:2px;">{words["team_murenzi_name"]}</h3>'
            f'<p style="color:var(--gold-soft); font-weight:600; font-size:14px; margin-bottom:6px;">{words["team_murenzi_role"]}</p>'
            f'<p style="font-size:15px; line-height:1.55; color:var(--text);">{words["team_murenzi_desc"]}</p>'
            '</article>'
            f'<article style="border-top:3px solid var(--accent); border-left:0; padding:16px 0 0;">'
        f'<h3 style="margin-bottom:2px;">{words["team_bahire_name"]}</h3>'
            f'<p style="color:var(--gold-soft); font-weight:600; font-size:14px; margin-bottom:6px;">{words["team_bahire_role"]}</p>'
            f'<p style="font-size:15px; line-height:1.55; color:var(--text);">{words["team_bahire_desc"]}</p>'
            '</article>'
        '</div>'
            f'<div class="note-box" style="margin-top:28px"><strong>{words["footer_legal"]}</strong><br>{words["footer_disclaimer"]}</div>'
        f'<p class="section-p">{words["footer_ack"]}</p>'
        "</div>",
        unsafe_allow_html=True,
    )
        with st.expander(words.get("about_method_title", "How the numbers are made"), expanded=True):
        steps = "".join(
            f'<article><span class="step">{i:02d}</span><p>{words[key]}</p></article>'
            for i, key in enumerate(("how_1", "how_2", "how_3", "how_4", "how_5", "how_6", "how_7", "how_8", "how_9", "how_10"), start=1)
        )
        glossary = "".join(
            f"<p>{words[key]}</p>"
            for key in ("gl_irrigation", "gl_rain", "gl_erosion", "gl_prod", "gl_yield", "gl_fert", "gl_terrace", "gl_forecast", "gl_warn", "gl_ndre", "gl_et0", "gl_etc")
        )
        benchmark_html = model_tables(benchmark, words)
        if benchmark and "models" in benchmark:
            benchmark_rows = [
                [m["name"], f"{m['mae_kg_ha']:.1f}", f"{m['rmse_kg_ha']:.1f}", f"{m['r2']:.3f}", m["verdict"]]
                for m in benchmark["models"]
            ]
            feat_keys = [
                ("inorganic", "feat_inorganic"),
                ("rain_diff_pct", "feat_rain"),
                ("vegetation_mean", "feat_veg"),
                ("organic_short", "feat_organic_short"),
                ("organic", "feat_organic"),
                ("protected", "feat_protected"),
                ("erosion_moderate", "feat_erosion_moderate"),
                ("irrigated", "feat_irrigated"),
                ("erosion_severe", "feat_erosion_severe"),
            ]
            importances = (benchmark.get("pooled") or {}).get("feature_importances") or benchmark.get("feature_importances", {})
            feat_rows = [
                [words[label_key], f"{importances.get(name, 0) * 100:.1f}%"]
                for name, label_key in feat_keys
                if name in importances
            ]
            benchmark_html += (
                f'<p class="kicker-green" style="margin-top:36px">{words["benchmark_title"]}</p>'
                f'<p class="section-p">{words["benchmark_lead"]}</p>'
                + data_table(
                    [words["model_col"], words["mae_col"], words["rmse_col"], words["r2_col"], words["note_col"]],
                    benchmark_rows,
                )
                + f'<p class="kicker-green" style="margin-top:28px">{words["feat_title"]}</p>'
                + data_table([words["note_col"], words["share_col"]], feat_rows)
            )
        st.markdown(
            f'<div class="method-list">{steps}</div>{benchmark_html}'
            f'<p class="kicker-green" style="margin-top:36px">{words["method_glossary"]}</p>'
            f'<div class="glossary">{glossary}</div>',
            unsafe_allow_html=True,
        )

    render_footer(words)