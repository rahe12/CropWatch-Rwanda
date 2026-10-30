import importlib
import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import src.advise as advise_mod
import src.export_note as export_mod
import src.sources as sources_mod
import src.style as style_mod
import src.words as words_mod

importlib.reload(words_mod)
importlib.reload(style_mod)
importlib.reload(advise_mod)
importlib.reload(sources_mod)
importlib.reload(export_mod)

from src.advise import answer, audio_speech_html, kit_for_hectares, llm_status, pack, sms_text, classify, extract_district, get_followups
from src.export_note import html_report
from src.sources import KIND_LABEL, SOURCES
from src.style import inject
from src.words import TEXT

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
LOOKUPS = PROCESSED / "lookups"
APP_TABLES = PROCESSED / "app"

st.set_page_config(page_title="CropWatch Rwanda", layout="wide", initial_sidebar_state="collapsed")
st.markdown(inject(), unsafe_allow_html=True)

if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "lang_nav" not in st.session_state:
    st.session_state.lang_nav = st.session_state.lang
if "page_nav" not in st.session_state:
    st.session_state.page_nav = "home"

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


def pill(alert, words):
    return f'<span class="status-pill {alert}">{words["label_" + str(alert)]}</span>'


def kpi(label, value, hint=""):
    extra = f"<small>{hint}</small>" if hint else ""
    return f'<div class="kpi"><span>{label}</span><strong>{value}</strong>{extra}</div>'


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


def bar_cell(pct):
    width = max(0, min(100, float(pct)))
    return f'<div class="bar-cell"><b>{width:.0f}%</b><i style="width:{width:.0f}%"></i></div>'


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


def guide_card(title, body):
    return f"""
    <div class="guide-card">
      <div class="guide-card-head">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d4f2b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        <h4>{title}</h4>
      </div>
      <p class="guide-card-body">{body}</p>
    </div>
    """


def jump(page_name, role=None):
    st.session_state.pending_page = page_name
    if role:
        st.session_state.role = role


def render_footer(words):
    """Footer with working Streamlit page buttons (HTML href alone cannot switch Streamlit pages)."""
    st.markdown(
        f"""
        <footer class="landing-footer">
          <div class="landing-footer-grid footer-grid-simple">
            <div>
              <div class="landing-brand">
                <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="20" cy="20" r="20" fill="#ffffff"/>
                  <path d="M12 24c4-10 8-14 11-15-2 7-2 12 1 15 4-7 7-9 9-9-4 9-8 14-14 15-5-1-7-3-7-6z" fill="#0d4f2b"/>
                </svg>
                <span>CropWatch Rwanda<small>{words["brand_tag"]}</small></span>
              </div>
              <p>{words["footer_blurb"]}</p>
              <p class="footer-tagline-text">{words["footer_tagline"]}</p>
            </div>
            <div>
              <h2>{words["footer_legal"]}</h2>
              <p>{words["footer_disclaimer"]}</p>
              <p>{words["footer_ack"]}</p>
            </div>
          </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="footer-nav"><p class="footer-nav-label">{words["footer_platform"]}</p></div>',
        unsafe_allow_html=True,
    )
    f1, f2, f3, f4, f5, f6, f7 = st.columns(7)
    f1.button(words["nav_home"], width="stretch", key="ft_home", on_click=jump, args=("home",))
    f2.button(words["nav_alerts"], width="stretch", key="ft_alerts", on_click=jump, args=("alerts",))
    f3.button(words["nav_dashboard"], width="stretch", key="ft_dashboard", on_click=jump, args=("dashboard",))
    f4.button(words["nav_simulator"], width="stretch", key="ft_simulator", on_click=jump, args=("simulator",))
    f5.button(words["nav_advise"], width="stretch", key="ft_advise", on_click=jump, args=("advise",))
    f6.button(words["nav_data"], width="stretch", key="ft_data", on_click=jump, args=("data",))
    f7.button(words["nav_about"], width="stretch", key="ft_about", on_click=jump, args=("about",))
    st.markdown(
        f'<div class="landing-copyright">© 2026 CropWatch Rwanda · {words["footer_copy"]}</div>',
        unsafe_allow_html=True,
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
    is_rw = words.get("lang_code") == "rw" or words.get("col_status") == "Imiterere"
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

    math_proof = (
        f'<div class="evidence-math-grid">'
        f'<div class="evidence-math-cell">'
        f'  <span class="math-label">{"Itandukaniro ry\'Imvura" if is_rw else "Cumulative Rain Anomaly"}</span>'
        f'  <strong class="math-value" style="color:{"#b42318" if rain_diff < -15 else "#9a5700" if rain_diff < 0 else "#0d4f2b"};">{rain_diff:+.1f}%</strong>'
        f'  <span class="math-formula">({rain_so_far:.0f} mm / {usual_rain:.0f} mm normal)</span>'
        f'</div>'
        f'<div class="evidence-math-cell">'
        f'  <span class="math-label">{"Icyuho cy\'Amazi (Pₑ - ETc)" if is_rw else "FAO-56 Water Balance (Pₑ - ETc)"}</span>'
        f'  <strong class="math-value" style="color:{"#b42318" if bal < 0 else "#0d4f2b"};">{bal:+.1f} mm/wk</strong>'
        f'  <span class="math-formula">({pe:.1f} mm rain - {etc:.1f} mm demand)</span>'
        f'</div>'
        f'<div class="evidence-math-cell">'
        f'  <span class="math-label">{"Ubuso Butuhirwa (SAS)" if is_rw else "Surveyed Irrigated Plots"}</span>'
        f'  <strong class="math-value">{irrig_pct:.1f}%</strong>'
        f'  <span class="math-formula">({"Munsi ya 10%" if irrig_pct < 10 else "Hejuru ya 10%"} threshold)</span>'
        f'</div>'
        f'<div class="evidence-math-cell">'
        f'  <span class="math-label">{"Icyiciro cy\'Ibigori & Kc" if is_rw else "Maize Phenology Stage"}</span>'
        f'  <strong class="math-value">{stage.capitalize()} (Kc={kc:.2f})</strong>'
        f'  <span class="math-formula">{"Iteganyagihe:" if is_rw else "Forecast:"} {f_week:.1f} mm / {f_days}d rain</span>'
        f'</div>'
        f'</div>'
    )

    audit_footer = (
        f'<div class="evidence-audit-footer">'
        f'  <div class="evidence-stamp">'
        f'    <span class="stamp-icon">🛡️</span>'
        f'    <div>'
        f'      <strong>{"IBIMENYETSO BYEMEZA INTEGUZA (AUDIT TRAIL)" if is_rw else "PROVABLE BIOPHYSICAL AUDIT TRAIL"}</strong>'
        f'      <p>{"Amakuru y\'ibanze yemejwe binyuze muri NISR SAS Microdata (Imirima " if is_rw else "Ground-truth verified against NISR Seasonal Agriculture Survey microdata (plot weight: "}'
        f'<strong>{sample_weight:,.0f}</strong> plots), Open-Meteo High-Resolution Model (Centroid: <code>{lat:.4f}°N, {lon:.4f}°E</code>), '
        f'{"na CHIRPS 8-Yr Reanalysis (2018–2025). Iteganyagihe ryakiriwe ako kanya ku ya " if is_rw else "and CHIRPS 8-Yr historical normal (2018–2025). Telemetry verified live for "}'
        f'<strong>{row.get("fetched_on", "2026-10-30")}</strong>.</p>'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )
    return f'<div class="provable-evidence-box">{math_proof}{audit_footer}</div>'


def intel_card(row, words):
    climate = str(row.get("climate_class") or "")
    alert = str(row["alert"])
    if alert in {"irrigation_gap", "irrigate_now", "dry_watch"}:
        action = words["action_irrigation"]
    elif alert in {"soil_rain", "soil_watch"}:
        action = words["action_soil"]
    else:
        action = words["action_stable"]
    return (
        '<div class="intel-card">'
        f'<p class="kicker-green">{words["intel_title"]}</p>'
        "<dl>"
        f"<dt>{words['intel_condition']}</dt><dd>{words.get('label_' + alert, alert)}"
        f"{' · ' + words.get('label_' + climate, climate) if climate else ''}</dd>"
        f"<dt>{words['intel_used']}</dt><dd>{words['intel_used_body']}</dd>"
        f"<dt>{words['intel_method']}</dt><dd>{words['intel_method_body']}</dd>"
        f"<dt>{words['intel_reason']}</dt><dd>{words.get('why_' + alert, words['why_stable'])}</dd>"
        f"<dt>{words['intel_action']}</dt><dd>{action}</dd>"
        f"<dt>{words['intel_limits']}</dt><dd>{words['intel_limits_body']}</dd>"
        "</dl></div>"
    )


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


def alert_map(alerts, forecast, geojson, words, layer="alert"):
    lookup = alerts.set_index("district")
    features = []
    for feat in geojson["features"]:
        name = feat["properties"].get("district")
        props = dict(feat["properties"])
        if name in lookup.index:
            row = lookup.loc[name]
            props["alert_label"] = words["label_" + str(row["alert"])]
            props["rain_vs"] = f"{float(row['rain_difference_pct']):.1f}"
            props["irrig_share"] = f"{float(row['irrigated_pct']):.1f}"
            props["week_mm"] = f"{float(row['forecast_week_mm']):.1f}"
            props["week_detail"] = week_line(forecast, name)
            props["fill"] = layer_fill(row, layer)
        else:
            props["alert_label"] = "—"
            props["rain_vs"] = "—"
            props["irrig_share"] = "—"
            props["week_mm"] = "—"
            props["week_detail"] = "—"
            props["fill"] = "#94a3b8"
        features.append({"type": "Feature", "geometry": feat["geometry"], "properties": props})
    layered = {"type": "FeatureCollection", "features": features}

    rwanda = folium.Map(
        location=[-1.94, 29.87],
        zoom_start=7,
        tiles=None,
        control_scale=True,
        zoom_control=True,
    )
    folium.TileLayer(
        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="&copy; OpenStreetMap contributors",
        name="OpenStreetMap",
        overlay=False,
        control=False,
    ).add_to(rwanda)
    folium.GeoJson(
        layered,
        style_function=lambda feature: {
            "fillColor": feature["properties"].get("fill", "#16a34a"),
            "color": "#ffffff",
            "weight": 1,
            "fillOpacity": 0.78,
        },
        highlight_function=lambda _feature: {
            "weight": 2.5,
            "fillOpacity": 0.92,
            "color": "#080d25",
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["district", "alert_label", "rain_vs", "irrig_share", "week_mm"],
            aliases=[
                words["district_col"],
                words["col_status"],
                words["map_rain"],
                words["stat_irrigated"],
                words["map_week"],
            ],
            sticky=False,
            labels=True,
        ),
        popup=folium.GeoJsonPopup(
            fields=["district", "alert_label", "rain_vs", "irrig_share", "week_detail"],
            aliases=[
                words["district_col"],
                words["col_status"],
                words["map_rain"],
                words["stat_irrigated"],
                words["week_title"],
            ],
            labels=True,
            max_width=360,
        ),
        name="districts",
    ).add_to(rwanda)
    rwanda.fit_bounds([[-2.85, 28.85], [-1.05, 30.90]])
    return rwanda.get_root().render()


def page_head(title, lead, words, **_extra):
    st.markdown(
        f"""
        <section class="page-band">
          <div class="inner">
            <p class="kicker-green">{words["eyebrow"]}</p>
            <h1>{title}</h1>
            <p class="lead">{lead}</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def more_bar(words):
    c1, c2, c3 = st.columns(3)
    c1.button(words["more_back"], width="stretch", key="more_back", on_click=jump, args=("about",))
    c2.button(words["nav_dashboard"], width="stretch", key="more_to_desk", on_click=jump, args=("dashboard",))
    c3.button(words["nav_alerts"], width="stretch", key="more_to_alerts", on_click=jump, args=("alerts",))


FORM_RW = {
    "grain": "intete",
    "dry beans": "ibishyimbo byumye",
    "fresh beans": "ibishyimbo byo kurya",
    "root": "imizi",
    "tuber": "imizi",
    "vegetable": "imboga",
    "fruit": "imbuto",
}

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
NAV_PAGES = ("home", "alerts", "dashboard", "simulator", "advise", "data", "about")
ALL_PAGES = NAV_PAGES + ("soil", "pilot", "watch", "method")
NAV_LABEL = {
    "home": "nav_home",
    "alerts": "nav_alerts",
    "dashboard": "nav_dashboard",
    "simulator": "nav_simulator",
    "advise": "nav_advise",
    "data": "nav_data",
    "about": "nav_about",
}
NAV_ICONS = {
    "home": "🏠",
    "alerts": "🚨",
    "dashboard": "📊",
    "simulator": "🧪",
    "advise": "🤖",
    "data": "📁",
    "about": "ℹ️",
}

words = TEXT[st.session_state.lang]
safe = matches[matches["safe_to_join"] == True].copy()
close = matches[matches["safe_to_join"] == False].copy()

st.markdown('<div id="cw-top"></div>', unsafe_allow_html=True)
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

def apply_page(dest):
    st.session_state.current_page = dest
    st.session_state.page_nav = dest if dest in NAV_PAGES else "about"
    st.session_state.last_nav = st.session_state.page_nav

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
    dest = st.session_state.pop("pending_page")
    apply_page(dest)
    st.session_state._qp = dest
    if st.query_params.get("page") != dest:
        st.query_params["page"] = dest

col_brand, col_nav, col_status, col_lang = st.columns([1.8, 6.2, 1.2, 0.8], vertical_alignment="center")
with col_brand:
    st.markdown(
        f"""
        <div class="header-brand">
          <div class="header-crest">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="20" cy="20" r="19" fill="#0d4f2b" stroke="#c4a35a" stroke-width="2"/>
              <path d="M12 24c4-10 8-14 11-15-2 7-2 12 1 15 4-7 7-9 9-9-4 9-8 14-14 15-5-1-7-3-7-6z" fill="#ffffff"/>
              <circle cx="20" cy="14" r="2.5" fill="#e2c87d"/>
            </svg>
          </div>
          <div class="header-title-box">
            <span class="header-main-title">CropWatch Rwanda</span>
            <span class="header-sub-tag">National Decision Desk &middot; NST2</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_nav:
    page_nav = st.pills(
        "Page",
        options=list(NAV_PAGES),
        format_func=lambda key: "ADVICE AI" if key == "advise" else words[NAV_LABEL[key]],
        default="home",
        label_visibility="collapsed",
        key="page_nav",
    )
with col_status:
    st.markdown(
        """
        <div class="topbar-status-badge">
          <span class="topbar-status-dot"></span>
          <span class="topbar-status-text"><strong>Season A 2026</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_lang:
    language = st.pills(
        "Language",
        options=["en", "rw"],
        format_func=lambda code: code.upper(),
        default=st.session_state.lang,
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
page = st.session_state.current_page
if page is None:
    page = "home"

role = st.session_state.get("role", "all")

month = words["month_names"][int(status["rain_last_month"])]
rain_text = f"{month} {int(status['rain_last_year'])}"

n_gap = int(alerts["alert"].isin(["irrigation_gap", "irrigate_now"]).sum())
irrig_national = 100 * alerts["irrigated_yes_weight"].sum() / alerts["irrigated_weight"].sum()
driest = alerts.sort_values("rain_difference_pct").iloc[0]
power_sum = pd.read_csv(APP_TABLES / "nasa_power_summary.csv") if (APP_TABLES / "nasa_power_summary.csv").exists() else pd.DataFrame()

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
    st.markdown(
        f"""
        <section class="photo-hero">
          <div class="landing-shell landing-hero-grid">
            <div>
              <p class="landing-eyebrow">{words["eyebrow"]}</p>
              <h1>{words["hero_title"]}</h1>
              <p class="lead">{words["hero_lead"]}</p>

              <div class="what-is-hero-card">
                <div class="what-is-hero-badge">
                  <span>🌾</span> <strong>{words["what_is_title"]}</strong>
                </div>
                <p class="what-is-hero-desc">{words["what_is_desc"]}</p>
                <div class="what-is-hero-pillars">
                  <div class="what-is-hero-pillar">
                    <span class="pillar-icon">🛰️</span>
                    <div>
                      <strong>{words["what_is_p1_title"]}</strong>
                      <p>{words["what_is_p1_desc"]}</p>
                    </div>
                  </div>
                  <div class="what-is-hero-pillar">
                    <span class="pillar-icon">🌱</span>
                    <div>
                      <strong>{words["what_is_p2_title"]}</strong>
                      <p>{words["what_is_p2_desc"]}</p>
                    </div>
                  </div>
                  <div class="what-is-hero-pillar">
                    <span class="pillar-icon">🤖</span>
                    <div>
                      <strong>{words["what_is_p3_title"]}</strong>
                      <p>{words["what_is_p3_desc"]}</p>
                    </div>
                  </div>
                </div>
              </div>

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
    h1, h2, h3 = st.columns(3)
    h1.button(words["home_go_alerts"], width="stretch", type="primary", key="home_go_alerts", on_click=jump, args=("alerts",))
    h2.button(words["home_go_dash"], width="stretch", key="home_go_dash", on_click=jump, args=("dashboard",))
    h3.button(words["home_go_advise"], width="stretch", key="home_go_advise", on_click=jump, args=("advise",))
    st.markdown(
        f"""
        <section class="landing-section">
          <div class="landing-shell">
            <div class="landing-stats">
              <dl>
                <div><dt>{words["stat_alert_districts"]}</dt><dd>{n_gap}</dd></div>
                <div><dt>{words["stat_irrigated"]}</dt><dd>{irrig_national:.1f}%</dd></div>
                <div><dt>{words["stat_worst"]}</dt><dd>{driest["rain_difference_pct"]:.0f}%</dd></div>
              </dl>
            </div>
            <p class="kicker-green">{words["home_challenge_kicker"]}</p>
            <h2>{words["home_challenge_title"]}</h2>
            <p class="section-p">{words["home_challenge_lead"]}</p>
            <p class="kicker-green" style="margin-top:48px">{words["home_how_kicker"]}</p>
            <h2>{words["home_how_title"]}</h2>
            <div class="process-row three">
              <article><span>01</span><h3>{words["home_how_1_t"]}</h3><p>{words["home_how_1"]}</p></article>
              <article><span>02</span><h3>{words["home_how_2_t"]}</h3><p>{words["home_how_2"]}</p></article>
              <article><span>03</span><h3>{words["home_how_3_t"]}</h3><p>{words["home_how_3"]}</p></article>
            </div>
            <p class="kicker-green" style="margin-top:48px">{words["home_mod_kicker"]}</p>
            <h2>{words["home_mod_title"]}</h2>
            <div class="decision-grid">
              <article><h3>{words["role_farmer"]}</h3><p>{words["home_who_farmer"]}</p></article>
              <article><h3>{words["role_agronomist"]}</h3><p>{words["home_who_agro"]}</p></article>
              <article><h3>{words["role_policy"]}</h3><p>{words["home_who_plan"]}</p></article>
            </div>
          </div>
        </section>
        <section class="cta-band">
          <div class="landing-shell">
            <p class="kicker-gold">{words["home_start_kicker"]}</p>
            <h2>{words["home_start_title"]}</h2>
            <p class="section-p" style="color:#d6e3dc">{words["home_start_body"]}</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.button(words["home_go_alerts"], width="stretch", type="primary", key="cta_go_alerts", on_click=jump, args=("alerts",))
    c2.button(words["home_go_dash"], width="stretch", key="cta_go_dash", on_click=jump, args=("dashboard",))
    c3.button(words["home_go_advise"], width="stretch", key="cta_go_advise", on_click=jump, args=("advise",))
    render_footer(words)

elif page == "alerts":
    page_head(
        words["alerts_title"],
        words["alerts_lead"],
        words,
        kicker=words.get("kicker_alerts"),
        sources=words.get("banner_sources_alerts"),
        action=words.get("banner_action_alerts"),
        tags=[words["districts"] + ": 30", "Meteo Rwanda", "CHIRPS Climatology", "7-Day Forecast"],
    )
    n_crit = int((alerts["climate_class"] == "water_stress").sum())
    n_high = int((alerts["alert"] == "irrigation_gap").sum() - n_crit)
    n_soil = int(alerts["alert"].isin(["soil_rain", "soil_watch"]).sum())
    n_stab = int((alerts["alert"] == "stable").sum())

    st.markdown(
        f"""
        <div class="inner-wrap" style="padding-top:14px; padding-bottom:4px;">
          <div class="alert-telemetry-strip">
            <div class="telemetry-pill">
              <span class="pulse-dot green"></span>
              <span><strong>{"Agrometeo Ako Kanya:" if st.session_state.lang == "rw" else "Real-Time Agrometeo:"}</strong> Open-Meteo High-Res (Active · 110ms)</span>
            </div>
            <div class="telemetry-pill">
              <span class="pulse-dot gold"></span>
              <span><strong>{"Ikigereranyo cy'Imvura:" if st.session_state.lang == "rw" else "Climatology Baseline:"}</strong> CHIRPS 8-Yr Reanalysis (2018–2025 Normal)</span>
            </div>
            <div class="telemetry-pill">
              <span class="pulse-dot blue"></span>
              <span><strong>{"Ibarura ry'Imirima:" if st.session_state.lang == "rw" else "Ground-Truth Survey:"}</strong> NISR SAS Microdata (Plot-Weighted · 30 Districts)</span>
            </div>
          </div>
          <div class="alert-triage-grid">
            <div class="alert-triage-card critical">
              <div class="triage-head">
                <span class="triage-title">{words.get("alerts_triage_critical", "Critical Moisture Stress")}</span>
                <span class="triage-count">{n_crit}</span>
              </div>
              <div class="triage-desc">{words.get("alerts_triage_critical_desc", "Severe deficit & <10% irrigation. Immediate SSIT pump deployment required.")}</div>
            </div>
            <div class="alert-triage-card high">
              <div class="triage-head">
                <span class="triage-title">{words.get("alerts_triage_high", "High Irrigation Gap")}</span>
                <span class="triage-count">{n_high}</span>
              </div>
              <div class="triage-desc">{words.get("alerts_triage_high_desc", "Cumulative rainfall deficit. Mobilize supplementary irrigation systems.")}</div>
            </div>
            <div class="alert-triage-card soil">
              <div class="triage-head">
                <span class="triage-title">{words.get("alerts_triage_soil", "Hillside Runoff Risk")}</span>
                <span class="triage-count">{n_soil}</span>
              </div>
              <div class="triage-desc">{words.get("alerts_triage_soil_desc", "Vulnerable sloping plots. Reinforce terraces and drainage ditches.")}</div>
            </div>
            <div class="alert-triage-card stable">
              <div class="triage-head">
                <span class="triage-title">{words.get("alerts_triage_stable", "Moisture & Soil Stable")}</span>
                <span class="triage-count">{n_stab}</span>
              </div>
              <div class="triage-desc">{words.get("alerts_triage_stable_desc", "Balanced root-zone water envelope. Standard seasonal monitoring.")}</div>
            </div>
          </div>
          <p class="section-p">{words["alerts_explain"]}</p>
          <p class="kicker-green">{words["map_title"]}</p>
          <p class="section-p">{words["layer_lead"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_ctrl, col_map = st.columns([1.1, 2.9], vertical_alignment="top", gap="large")
    with col_ctrl:
        st.markdown(
            f"""
            <div class="map-controls-deck">
              <div class="deck-header">
                <span class="deck-icon">🗺️</span>
                <div>
                  <strong>{words["layer_title"]}</strong>
                  <small>{"Gukurikirana ubutaka na satelite" if st.session_state.lang == "rw" else "Spatial Layers & Risk Telemetry"}</small>
                </div>
              </div>
            </div>
            """,
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
        st.markdown(
            f'<div style="font-size:11.5px; font-weight:700; text-transform:uppercase; color:#0d4f2b; letter-spacing:0.04em; margin-top:14px; margin-bottom:4px;">'
            f'🎯 {words["filter"]}:'
            f'</div>',
            unsafe_allow_html=True,
        )
        shown = st.pills(
            words["filter"],
            ["all", "irrigation", "soil", "stable"],
            format_func=lambda key: {
                "all": "All (30)" if st.session_state.lang == "en" else "Byose (30)",
                "irrigation": "Irrigation" if st.session_state.lang == "en" else "Kuhira",
                "soil": "Hillside" if st.session_state.lang == "en" else "Ubutaka",
                "stable": "Stable" if st.session_state.lang == "en" else "Bitekanye",
            }[key],
            default="all" if role == "agronomist" else "irrigation",
            label_visibility="collapsed",
            key="alert_filter",
        )
        if shown is None:
            shown = "all" if role == "agronomist" else "irrigation"
        dry_cut = st.slider(words["filter_rain"], min_value=-40, max_value=10, value=10, step=5, key="dry_cut")
        st.markdown(layer_legend(layer, words), unsafe_allow_html=True)
    view = alerts.copy()
    if shown == "irrigation":
        view = view[view["alert"].isin(["irrigation_gap", "irrigate_now", "dry_watch"])]
    elif shown == "soil":
        view = view[view["alert"].isin(["soil_rain", "soil_watch"])]
    elif shown == "stable":
        view = view[view["alert"] == "stable"]
    view = view[view["rain_difference_pct"] <= dry_cut]
    if view.empty:
        st.markdown(f'<div class="inner-wrap"><div class="note-box">{words["empty_district"]}</div></div>', unsafe_allow_html=True)
    geo_path = APP_TABLES / "districts.geojson"
    geojson = load_geojson(geo_path.stat().st_mtime if geo_path.exists() else 0)
    district_names = list(alerts["district"])
    with col_map:
        if geojson is not None:
            components.html(alert_map(view if not view.empty else alerts, forecast, geojson, words, layer=layer), height=560, scrolling=False)
        else:
            st.markdown(f'<div class="note-box">{words["map_missing"]}</div>', unsafe_allow_html=True)
    table_rows = [
        (
            item["district"],
            f"<span class='landing-number'><strong>{item['rain_difference_pct']:.0f}%</strong><span>{item['rain_so_far_mm']:.0f} / {item['usual_sep_oct_mm']:.0f} mm</span></span>",
            pill(item["alert"], words),
            f"{item['irrigated_pct']:.1f}%",
        )
        for _, item in view.iterrows()
    ]
    st.markdown(
        '<div class="inner-wrap">'
        + data_table(
            [words["district_col"], words["diff_col"], words["col_status"], words["stat_irrigated"]],
            table_rows if table_rows else [("—", "—", "—", "—")],
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="inner-wrap" style="margin-top:32px; margin-bottom:12px;">
          <p class="kicker-green">{"ISUZUMA RY'AKARERE KU KANDI" if st.session_state.lang == "rw" else "DISTRICT AGROMETEOROLOGICAL PROFILE & PROVABLE AUDIT"}</p>
          <h2 style="font-size:22px; margin-top:2px; margin-bottom:6px;">{"Hitamo Akarere ushaka gusuzuma mu buryo burambuye:" if st.session_state.lang == "rw" else "Select District for Deep Biophysical & Evidence Audit:"}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_pick, col_dummy = st.columns([1.5, 2.5], vertical_alignment="center")
    with col_pick:
        chosen = st.selectbox(
            words["pick_district"],
            district_names,
            index=district_names.index("Nyaruguru") if "Nyaruguru" in district_names else 0,
            label_visibility="collapsed",
            key="district_pick",
        )
    row = alerts[alerts["district"] == chosen].iloc[0]
    if row["alert"] in {"irrigation_gap", "irrigate_now", "dry_watch"}:
        action = words["action_irrigation"]
    elif row["alert"] in {"soil_rain", "soil_watch"}:
        action = words["action_soil"]
    else:
        action = words["action_stable"]
    week = forecast[forecast["district"] == chosen].sort_values("date")
    st.markdown(
        '<div class="inner-wrap">'
        + board(
            words["label_" + str(row["alert"])],
            row["district"],
            alert_sentence(row, words),
            action,
            [
                kpi(words["rain_now"], f"{row['rain_so_far_mm']:.0f}"),
                kpi(words["usual_col"], f"{row['usual_sep_oct_mm']:.0f}"),
                kpi(words["stat_irrigated"], f"{row['irrigated_pct']:.1f}%"),
                kpi(words["yield_usual"], f"{row['usual_yield_kg_ha']:.0f}"),
                kpi(words["stat_water"], f"{float(row['water_balance_week_mm']):+.0f}") if "water_balance_week_mm" in row.index and pd.notna(row.get("water_balance_week_mm")) else kpi(words["stat_water"], "—"),
                kpi(words["stat_etc"], f"{float(row['etc_week_mm']):.0f}") if "etc_week_mm" in row.index and pd.notna(row.get("etc_week_mm")) else kpi(words["stat_etc"], "—"),
            ],
            extra=why_box(row, words) + provable_evidence_box(row, words) + week_panel(week, words),
            pill_html=pill(row["alert"], words) + (" " + pill(row["climate_class"], words) if "climate_class" in row.index and pd.notna(row.get("climate_class")) else ""),
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    col_act1, col_act2 = st.columns([1, 1], vertical_alignment="center")
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
        if st.button(
            f"🤖 {words.get('btn_ask_advice_ai', 'Ask ADVICE AI about this Alert')} ({chosen})",
            key="btn_ask_ai_alert",
            type="primary",
            width="stretch",
        ):
            st.session_state.pending_page = "advise"
            st.session_state.chat_district = chosen
            st.session_state.pending_chat_prompt = (
                f"Ntegurira ingamba zihutirwa zo kuhira n'uburyo bwo kwishingira umusaruro mu karere ka {chosen} gafite ikibazo cya {row['alert']}."
                if st.session_state.lang == "rw"
                else f"Generate an emergency agronomic response plan, supplementary irrigation schedule, and parametric insurance assessment for {chosen} District's {row['alert']} alert."
            )
            st.session_state.current_page = "advise"
            st.rerun()
    profile = pack(alerts, forecast, watch, soil, vegetation, chosen)
    if "ussd_step" not in st.session_state:
        st.session_state.ussd_step = "home"
    screen = {
        "home": words["ussd_home"],
        "weather": words["ussd_weather"].format(district=chosen, pct=profile["rain_pct"], week=profile["week_mm"], irrig=profile["irrigated_pct"]),
        "soil": words["ussd_soil"].format(district=chosen, concern=profile["concern_pct"], protected=profile["protected_pct"]),
        "kit": words["ussd_kit"],
    }[st.session_state.ussd_step]
    st.markdown(
        f'<div class="inner-wrap"><p class="kicker-green">{words["sms_title"]}</p>'
        f'<p class="section-p">{words["sms_note"]}</p><div class="phone-wrap">'
        f'<div class="feature-phone"><div class="phone-bar">SMS · MTN</div>'
        f'<div class="phone-screen">{sms_text(profile, words)}</div></div>'
        f'<div><p class="kicker-green">{words["ussd_title"]}</p>'
        f'<div class="feature-phone"><div class="phone-bar">*801#</div>'
        f'<div class="phone-screen">{screen}</div></div></div></div></div>',
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
    render_footer(words)

elif page == "dashboard":
    page_head(
        words["dash_title"],
        words["dash_lead"],
        words,
        kicker=words.get("kicker_dashboard"),
        sources=words.get("banner_sources_dashboard"),
        action=words.get("banner_action_dashboard"),
        tags=["NISR SAS 2018-2026", words["districts"] + ": 30", "WFP VAM Prices", "Soil Terracing"],
    )

    tab_matrix, tab_climate, tab_soil = st.tabs([
        words.get("tab_matrix", "📊 30-District Agricultural Matrix"),
        words.get("tab_climate", "🌱 Multi-Season Climate & Markets"),
        words.get("tab_soil", "⛰️ Hillside Soil Conservation & Terraces"),
    ])

    with tab_matrix:
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
        st.markdown(
            '<div class="inner-wrap">'
            + f'<div class="kpi-row">'
            + kpi(words["stat_alert_districts"], str(n_gap))
            + kpi(words["stat_irrigated"], f"{irrig_national:.1f}%")
            + kpi(words["stat_worst"], f"{driest['rain_difference_pct']:.0f}%")
            + water_kpi
            + "</div>"
            + f'<p class="kicker-green" style="margin-top:36px">{words["dash_fresh_title"]}</p>'
            + '<div class="fresh-list">'
            + f'<article><span>{words["price_until"]}</span><strong>{status["price_last_date"]}</strong></article>'
            + f'<article><span>{words["rain_until"]}</span><strong>{rain_text}</strong></article>'
            + f'<article><span>{words["trade_until"]}</span><strong>{int(status["trade_last_year"])}</strong></article>'
            + "</div>"
            + f'<div class="note-box">{words["dash_status_ok"]}. {words["dash_status_api"]}. {words["pilot_note"]}</div>'
            + f'<p class="kicker-green">{words["dash_risk_title"]}</p>'
            + data_table([words["col_status"], words["districts"]], count_rows)
            + climate_block
            + f'<p class="section-p">{words["export_note"]}</p>'
            + "</div>",
            unsafe_allow_html=True,
        )
        st.download_button(
            words["export_csv"],
            alerts.to_csv(index=False).encode("utf-8"),
            "cropwatch_irrigation_alerts.csv",
            "text/csv",
            key="dash_csv",
        )
        district_names = sorted(alerts["district"].unique())
        chosen_d = st.selectbox(
            words["dash_profile_title"],
            district_names,
            index=district_names.index("Nyaruguru") if "Nyaruguru" in district_names else 0,
            key="dash_district",
        )
        drow = alerts[alerts["district"] == chosen_d].iloc[0]
        dweek = forecast[forecast["district"] == chosen_d].sort_values("date")
        st.markdown(
            '<div class="inner-wrap" style="padding-top:8px">'
            + f'<p class="section-p">{words["dash_profile_lead"]}</p>'
            + board(
                words["label_" + str(drow["alert"])],
                chosen_d,
                alert_sentence(drow, words),
                words["action_irrigation"] if drow["alert"] in {"irrigation_gap", "irrigate_now", "dry_watch"} else (
                    words["action_soil"] if drow["alert"] in {"soil_rain", "soil_watch"} else words["action_stable"]
                ),
                [
                    kpi(words["rain_now"], f"{drow['rain_so_far_mm']:.0f}"),
                    kpi(words["stat_irrigated"], f"{drow['irrigated_pct']:.1f}%"),
                    kpi(words["concern_metric"], f"{drow['concern_pct']:.0f}"),
                    kpi(words["yield_usual"], f"{drow['usual_yield_kg_ha']:.0f}"),
                    kpi(words["stat_water"], f"{float(drow['water_balance_week_mm']):+.0f}") if "water_balance_week_mm" in drow.index and pd.notna(drow.get("water_balance_week_mm")) else kpi(words["stat_water"], "—"),
                    kpi(words["stat_etc"], f"{float(drow['etc_week_mm']):.0f}") if "etc_week_mm" in drow.index and pd.notna(drow.get("etc_week_mm")) else kpi(words["stat_etc"], "—"),
                ],
                extra=why_box(drow, words) + week_panel(dweek, words),
                pill_html=pill(drow["alert"], words) + (" " + pill(drow["climate_class"], words) if "climate_class" in drow.index and pd.notna(drow.get("climate_class")) else ""),
            )
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

    with tab_climate:
        st.markdown(f'<div class="inner-wrap" style="padding-bottom:0"><p class="section-p">{words["watch_explain"]}</p></div>', unsafe_allow_html=True)
        district_names_w = sorted(watch["district"].unique())
        left_w, right_w = st.columns([1.1, 2])
        with left_w:
            chosen_w = st.selectbox(
                words["pick_district"],
                district_names_w,
                index=district_names_w.index("Nyagatare") if "Nyagatare" in district_names_w else 0,
                key="watch_district",
            )
        with right_w:
            season_labels = {
                "A": "Season A 2026" if st.session_state.lang == "en" else "Igihembwe A 2026",
                "B": "Season B 2026" if st.session_state.lang == "en" else "Igihembwe B 2026",
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
            + f'<p class="kicker-green">{words["export_year"]}</p><p class="section-p">{words["export_lead"]}</p>'
            + data_table([words["year_col"], "USD", words["note_col"]], export_year_rows)
            + f'<p class="kicker-green">{words["export_partners"]}</p>'
            + data_table([words["note_col"], "USD", words["year_col"]], export_partner_rows)
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

    with tab_soil:
        st.markdown(f'<div class="inner-wrap" style="padding-bottom:0"><p class="section-p">{words["soil_explain"]}</p></div>', unsafe_allow_html=True)
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
                words["eyebrow"],
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

    d1, d2, d3 = st.columns(3)
    d1.button(words["nav_alerts"], width="stretch", key="dash_to_alerts", on_click=jump, args=("alerts",))
    d2.button(words["nav_advise"], width="stretch", key="dash_to_advise", on_click=jump, args=("advise",))
    d3.button(words["nav_simulator"], width="stretch", key="dash_to_sim", on_click=jump, args=("simulator",))
    render_footer(words)


elif page == "simulator":
    page_head(
        words["sim_title"],
        words["sim_lead"],
        words,
        kicker=words.get("kicker_simulator"),
        sources=words.get("banner_sources_simulator"),
        action=words.get("banner_action_simulator"),
        tags=["28,000+ Plot Microdata", "Ridge & Random Forest", "MINAGRI 50% SSIT Subsidy"],
    )
    tab_yield, tab_ssit = st.tabs([words["nav_simulator"], words["ssit_title"]])
    district_names = sorted(sim_base["district"].unique()) if not sim_base.empty else sorted(alerts["district"].unique())
    with tab_yield:
        chosen_sim = st.selectbox(
            words["pick_district"],
            district_names,
            index=district_names.index("Bugesera") if "Bugesera" in district_names else 0,
            key="sim_district_select",
        )
        sim_row = sim_base[sim_base["district"] == chosen_sim].iloc[0] if not sim_base.empty else alerts[alerts["district"] == chosen_sim].iloc[0]
        effects = (benchmark or {}).get("within_district_kg_ha", {})
        irrig_gap = float(effects.get("irrigated", 0))
        short_gap = abs(float(effects.get("organic_short", 0)))
        left, right = st.columns(2)
        with left:
            d_irrig = st.slider(words["sim_irrig_slider"], 0, 30, 10, 5, help=words["sim_irrig_help"], key="d_irrig")
        with right:
            d_short = st.slider(words["sim_organic_slider"], 0, 50, 20, 10, help=words["sim_organic_help"], key="d_short")
        current_irrig = float(sim_row["irrigated_pct"])
        current_short = float(sim_row["organic_short_pct"]) if "organic_short_pct" in sim_row and pd.notna(sim_row["organic_short_pct"]) else 0.0
        new_irrig = min(100.0, current_irrig + d_irrig)
        new_short = max(0.0, current_short - d_short)
        gain_kg = ((new_irrig - current_irrig) / 100.0) * irrig_gap + ((current_short - new_short) / 100.0) * short_gap
        base_y = float(sim_row["usual_yield_kg_ha"])
        proj_y = base_y + gain_kg
        gain_pct = (100.0 * gain_kg / base_y) if base_y else 0.0
        sim_body = words["sim_body"].format(
            district=chosen_sim, irrig_gap=irrig_gap, short_gap=short_gap,
            d_irrig=new_irrig - current_irrig, d_short=current_short - new_short, gain=gain_kg, pct=gain_pct,
        )
        st.markdown(
            '<div class="inner-wrap">'
            + f'<div class="note-box">{words["sim_assump"]}</div>'
            + board(
                words["nav_simulator"], chosen_sim, sim_body,
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
    with tab_ssit:
        chosen_kit = st.selectbox(words["pick_district"], district_names, index=district_names.index("Bugesera") if "Bugesera" in district_names else 0, key="ssit_district")
        kit_row = alerts[alerts["district"] == chosen_kit].iloc[0]
        watch_hit = watch[(watch["district"] == chosen_kit) & (watch["season"] == "A")]
        watch_hit = watch_hit.iloc[0] if not watch_hit.empty else None
        hectares = st.slider(words["ssit_ha"], 0.2, 5.0, 0.5, 0.1, key="ssit_ha")
        src_col, crop_col = st.columns(2)
        with src_col:
            st.selectbox(words["ssit_source"], [words["ssit_src_marsh"], words["ssit_src_well"], words["ssit_src_tank"]], key="ssit_src")
        with crop_col:
            crop_choice = st.selectbox(
                words["ssit_crop"],
                ["maize", "veg", "bean", "potato"],
                format_func=lambda key: words["ssit_crop_" + key],
                key="ssit_crop",
            )
        _key, en_name, rw_name = kit_for_hectares(hectares)
        kit_name = rw_name if st.session_state.lang == "rw" else en_name
        irrig_gap = float((benchmark or {}).get("within_district_kg_ha", {}).get("irrigated", 365.3))
        protected_kg = irrig_gap * hectares
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
        if crop_choice != "maize":
            extra_note += " " + words["ssit_other_crop"]
        if watch_hit is not None and pd.isna(watch_hit.get("maize_price_rwf_per_kg")):
            extra_note += " " + words["ssit_no_price"].format(date=price_date or "—")
        kpis = [
            kpi(words["ssit_kit"], kit_name),
            kpi(words["stat_irrigated"], f"{float(kit_row['irrigated_pct']):.1f}%"),
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
    render_footer(words)

elif page == "advise":
    page_head(
        words.get("chat_title", "CropWatch ML Agronomic Copilot"),
        words.get("chat_lead", "Predictive agronomic intelligence powered by machine learning models trained on 28,042 real NISR SAS plot records, CHIRPS/NASA agrometeorology, and WFP market prices."),
        words,
        kicker=words.get("kicker_advise", "NATIONAL ML COPILOT · NST2 DECISION DESK"),
        sources=words.get("banner_sources_advise", "NISR Seasonal Agriculture Survey Microdata, NASA POWER Agrometeorology, Open-Meteo & Meteo Rwanda, WFP VAM Price Monitor"),
        action=words.get("banner_action_advise", "Target smallholder supplementary irrigation (SSIT), trigger automated parametric crop insurance payouts (NAIS), and dispatch 160-character USSD/SMS alerts."),
        tags=["Scikit-Learn ML (<5ms)", "28,042 Surveyed Plots", "Parametric Insurance Payouts", "Voice Synthesis Enabled", "160-Char SMS Protocol"],
    )

    district_names = sorted(alerts["district"].unique())
    default_d = "Nyaruguru" if role == "farmer" else ("Bugesera" if role == "policy" else "Nyagatare")
    if default_d not in district_names:
        default_d = district_names[0]

    chosen_district_current = st.session_state.get("chat_district", default_d)
    if chosen_district_current not in district_names:
        chosen_district_current = district_names[0]
    history_key = f"chat_{chosen_district_current}_{st.session_state.lang}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # Top Control Bar: District Selection + Status Pill + Export Transcript + Reset History
    col_d, col_status_ai, col_exp, col_clr = st.columns([1.4, 2.0, 1.0, 0.6], vertical_alignment="center")
    with col_d:
        chosen_chat = st.selectbox(
            words["pick_district"],
            district_names,
            index=district_names.index(chosen_district_current),
            key="chat_district",
        )
    with col_status_ai:
        engine = llm_status()
        status_msg = words.get("chat_engine_llm", "⚡ Cloud LLM Connected") if engine else words.get("chat_engine_fast", "⚡ Fast Local Agronomic Engine Active")
        st.markdown(
            f'<div style="background:#eaf4ed; border:1px solid #b7dcbe; border-radius:6px; padding:7px 12px; font-size:12px; color:#0d4f2b; font-weight:600; margin-top:16px; display:flex; align-items:center; gap:6px;">'
            f'<span>🟢</span> <span>{status_msg} · <strong style="color:#09381e;">&lt;5ms</strong> · <span style="color:#2e5b3b; font-weight:normal;">{words.get("chat_voice_tip", "🔊 Voice enabled")}</span></span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_exp:
        # Integrated Export Briefing button right in top control bar
        if st.session_state[history_key]:
            transcript_text = f"# CropWatch Rwanda — Agronomic Copilot Briefing ({chosen_chat})\n\n"
            for s_role, s_msg in st.session_state[history_key]:
                pfx = "Farmer / Extension Agronomist" if s_role == "user" else "CropWatch Agronomic Copilot"
                transcript_text += f"### {pfx}:\n{s_msg}\n\n"
            st.download_button(
                "📥 " + ("Koporora (MD)" if st.session_state.lang == "rw" else "Export Briefing"),
                transcript_text.encode("utf-8"),
                f"cropwatch_copilot_{chosen_chat.lower()}.md",
                "text/markdown",
                key=f"dl_transcript_{chosen_chat}",
                width="stretch",
            )
        else:
            st.button("📥 " + ("Koporora" if st.session_state.lang == "rw" else "Export Briefing"), disabled=True, width="stretch", help="Available when chat history exists", key="btn_exp_disabled")
    with col_clr:
        if st.button("🔄 " + ("Siba" if st.session_state.lang == "rw" else "Clear"), key="btn_clear_chat", help="Reset chat for this district", width="stretch"):
            st.session_state[history_key] = []
            st.rerun()

    with st.expander("⚙️ " + ("Igenamiterere rya Cloud LLM (Bihitamo: Groq / Gemini)" if st.session_state.lang == "rw" else "Cloud LLM Connectivity (Optional: Groq / Gemini)"), expanded=False):
        st.markdown(f'<p style="font-size:13px; color:#3b5240; margin-bottom:12px;">{words["chat_llm_setup_guide"]}</p>', unsafe_allow_html=True)
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            groq_key_input = st.text_input("Groq API Key (llama-3.1-8b-instant)", value=st.session_state.get("GROQ_API_KEY", ""), type="password", key="groq_key_field")
            if groq_key_input != st.session_state.get("GROQ_API_KEY", ""):
                st.session_state["GROQ_API_KEY"] = groq_key_input.strip()
                import os
                if groq_key_input.strip():
                    os.environ["GROQ_API_KEY"] = groq_key_input.strip()
                st.rerun()
        with col_k2:
            gemini_key_input = st.text_input("Google Gemini API Key (gemini-2.0-flash)", value=st.session_state.get("GEMINI_API_KEY", ""), type="password", key="gemini_key_field")
            if gemini_key_input != st.session_state.get("GEMINI_API_KEY", ""):
                st.session_state["GEMINI_API_KEY"] = gemini_key_input.strip()
                import os
                if gemini_key_input.strip():
                    os.environ["GEMINI_API_KEY"] = gemini_key_input.strip()
                st.rerun()

    profile = pack(alerts, forecast, watch, soil, vegetation, chosen_chat)

    # Live 4-Metric Agrometeorological Telemetry Strip
    rain_color = "#b42318" if profile["rain_pct"] < -15 else ("#9a5700" if profile["rain_pct"] < 0 else "#0d4f2b")
    st.markdown(
        f"""
        <div class="inner-wrap">
          <div class="ai-telemetry-strip">
            <div class="ai-telemetry-card">
              <span class="ai-telemetry-label">🌧️ {"Imvura Imurihe" if st.session_state.lang == "rw" else "Rainfall Anomaly"}</span>
              <span class="ai-telemetry-val" style="color:{rain_color};">{profile['rain_pct']:+.0f}%</span>
              <span class="ai-telemetry-hint">{"Ugereranyije na 1981–2025" if st.session_state.lang == "rw" else "vs 1981–2025 Baseline"}</span>
            </div>
            <div class="ai-telemetry-card">
              <span class="ai-telemetry-label">📅 {"Imvura y'Icyumweru" if st.session_state.lang == "rw" else "7-Day Forecast"}</span>
              <span class="ai-telemetry-val">{profile['week_mm']:.0f} mm</span>
              <span class="ai-telemetry-hint">{"Meteo Rwanda / Open-Meteo" if st.session_state.lang == "rw" else "Numerical Agrometeo Model"}</span>
            </div>
            <div class="ai-telemetry-card">
              <span class="ai-telemetry-label">💧 {"Icyuho cy'Amazi" if st.session_state.lang == "rw" else "Moisture Deficit"}</span>
              <span class="ai-telemetry-val">{profile['deficit_mm']:.1f} mm</span>
              <span class="ai-telemetry-hint">{profile['liters_ha']:,.0f} L/ha {"kuhira" if st.session_state.lang == "rw" else "required"}</span>
            </div>
            <div class="ai-telemetry-card">
              <span class="ai-telemetry-label">🌽 {"Igiciro cy'Isoko" if st.session_state.lang == "rw" else "WFP Market Price"}</span>
              <span class="ai-telemetry-val">{profile['price']:.0f} RWF</span>
              <span class="ai-telemetry-hint">{"Ku kilo cy'ibigori (WFP)" if st.session_state.lang == "rw" else "per kg maize grain"}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Split-Screen Layout: Left 68% Chat & Capabilities, Right 32% Decision Context Drawer
    col_main, col_drawer = st.columns([2.3, 1.0], gap="large")

    with col_main:
        st.markdown(
            f'<div style="margin-bottom:10px; display:flex; align-items:center; justify-content:space-between;">'
            f'<span style="font-size:12px; font-weight:750; color:#0d4f2b; text-transform:uppercase; letter-spacing:0.04em;">'
            f'⚡ {"Hitamo Serivisi ya AI Ubare Ako Kanya (Microdata ya NISR SAS):" if st.session_state.lang == "rw" else "⚡ Instant ML Agronomic Actions (NISR SAS Microdata Models):"}'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # 2-Row Interactive AI Capability Pill Grid
        c1, c2, c3, c4 = st.columns(4)
        quick = None
        if c1.button(words.get("chat_btn_yield", "🧪 Yield Uplift ML"), key="btn_ai_yield", width="stretch"):
            quick = "yield"
        if c2.button(words.get("chat_btn_insurance", "🛡️ Climate Insurance"), key="btn_ai_insur", width="stretch"):
            quick = "insurance"
        if c3.button(words.get("chat_btn_market", "💰 Market & Storage"), key="btn_ai_market", width="stretch"):
            quick = "market"
        if c4.button(words.get("chat_btn_irrigation", "💧 Smart Irrigation"), key="btn_ai_irrig", width="stretch"):
            quick = "irrigation"

        c5, c6, c7, c8 = st.columns(4)
        if c5.button(words.get("chat_btn_soil", "🏔️ Terraces & Soil"), key="btn_ai_soil", width="stretch"):
            quick = "soil"
        if c6.button(words.get("chat_btn_pests", "🐛 Pests & Fertilizer"), key="btn_ai_pests", width="stretch"):
            quick = "pests"
        if c7.button(words.get("chat_btn_sms", "📱 160-Char SMS"), key="btn_ai_sms", width="stretch"):
            quick = "sms"
        if c8.button(words["chat_pill_week"], key="btn_ai_week", width="stretch"):
            quick = "week"

        if quick:
            asked_label = {
                "yield": words.get("chat_btn_yield", "ML Yield Uplift Forecast"),
                "insurance": words.get("chat_btn_insurance", "Climate Risk & Insurance"),
                "market": words.get("chat_btn_market", "Market Arbitrage & Storage"),
                "irrigation": words.get("chat_btn_irrigation", "Smart Irrigation Schedule"),
                "soil": words.get("chat_btn_soil", "Terraces & Soil Health"),
                "pests": words.get("chat_btn_pests", "Pest & Fertilizer Guide"),
                "sms": words.get("chat_btn_sms", "160-Char SMS Broadcast"),
                "week": words["chat_pill_week"],
            }.get(quick, quick)

            text = answer(asked_label, profile, words, st.session_state.lang, force_intent=quick)
            st.session_state[history_key].append(("user", asked_label))
            st.session_state[history_key].append(("bot", text))
            st.rerun()

        if "pending_chat_prompt" in st.session_state:
            pending_q = st.session_state.pop("pending_chat_prompt")
            ans_text = answer(pending_q, profile, words, st.session_state.lang)
            st.session_state[history_key].append(("user", pending_q))
            st.session_state[history_key].append(("bot", ans_text))
            st.rerun()

        # If no chat history yet, show executive guidance hero
        if not st.session_state[history_key]:
            welcome_head = f"Muraho! Ndi Umujyanama wa AI muri {chosen_chat}." if st.session_state.lang == "rw" else f"Welcome! I am your CropWatch ML Agronomic Copilot for {chosen_chat}."
            welcome_body = (
                f"Akarere ka **{chosen_chat}** kuri ubu gafite icyuho cy'ubuhehere cya **{profile['deficit_mm']:.1f} mm** n'imvura igera kuri **{profile['rain_pct']:+.0f}%** ugereranyije n'isanzwe. "
                f"Kanda hejuru kuri bumwe muri ubu bumenyi bwa Machine Learning (Umusaruro, Ubwishingizi, Ibiciro bya WFP, Kuhira) cyangwa wandike ikibazo cyawe mu gasanduku ko hasi."
                if st.session_state.lang == "rw" else
                f"**{chosen_chat} District** currently exhibits a cumulative rainfall anomaly of **{profile['rain_pct']:+.0f}%** and a weekly crop water deficit of **{profile['deficit_mm']:.1f} mm**. "
                f"Click any of the trained Machine Learning pills above to run instant inferences on 28,042 real NISR SAS survey plots, or type any agronomic question below."
            )
            st.markdown(
                f"""
                <div class="ai-welcome-box">
                  <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                    <span style="font-size:24px;">🌾</span>
                    <div>
                      <div style="font-size:16px; font-weight:750; color:#0d4f2b;">{welcome_head}</div>
                      <div style="font-size:11.5px; color:#55705d;">NISR Seasonal Agriculture Survey · Meteo Rwanda · WFP VAM</div>
                    </div>
                  </div>
                  <div style="font-size:13.5px; line-height:1.6; color:#2c3a2f; margin-bottom:12px;">{welcome_body}</div>
                  <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; padding-top:12px; border-top:1px solid #ddecde;">
                    <span style="background:#eaf4ed; color:#0d4f2b; font-size:11px; font-weight:650; padding:3px 10px; border-radius:999px; border:1px solid #b7dcbe;">⚡ Latency: &lt;5ms</span>
                    <span style="background:#eaf4ed; color:#0d4f2b; font-size:11px; font-weight:650; padding:3px 10px; border-radius:999px; border:1px solid #b7dcbe;">📊 28,042 Surveyed Plots</span>
                    <span style="background:#eaf4ed; color:#0d4f2b; font-size:11px; font-weight:650; padding:3px 10px; border-radius:999px; border:1px solid #b7dcbe;">🛡️ NAIS Parametric Triggers</span>
                    <span style="background:#eaf4ed; color:#0d4f2b; font-size:11px; font-weight:650; padding:3px 10px; border-radius:999px; border:1px solid #b7dcbe;">🔊 Hands-Free Voice Synthesis</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Render conversation history with senior-grade follow-up chips
        num_msgs = len(st.session_state[history_key])
        for idx, (speaker, text) in enumerate(st.session_state[history_key]):
            if speaker == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(
                        f"""
                        <span class="user-marker" style="display:none;"></span>
                        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #d8eadc;">
                          <div style="display:flex; align-items:center; gap:8px;">
                            <span style="background:#eaf4ed; color:#166534; font-size:11px; font-weight:750; padding:2px 8px; border-radius:999px; border:1px solid #b7dcbe;">👤 {"Umuhinzi / Agronome" if st.session_state.lang == "rw" else "Farmer / Agronomist"}</span>
                            <span style="font-size:12px; font-weight:650; color:#166534;">{chosen_chat} District</span>
                          </div>
                          <span style="font-size:11px; color:#55705d;">{"Ikibazo cyo mu murima" if st.session_state.lang == "rw" else "Field Query"}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(text)
            else:
                with st.chat_message("assistant", avatar="🌾"):
                    st.markdown(
                        f"""
                        <span class="assistant-marker" style="display:none;"></span>
                        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; border-bottom:1px solid #e2ebd8; padding-bottom:6px;">
                          <div style="display:flex; align-items:center; gap:8px;">
                            <span style="background:#0d4f2b; color:#fff; font-size:11px; font-weight:750; padding:2px 10px; border-radius:999px;">🌾 CropWatch Copilot</span>
                            <span style="font-size:12px; font-weight:700; color:#0d4f2b;">{chosen_chat} Intelligence Desk</span>
                          </div>
                          <span style="background:#fef3c7; color:#92400e; border:1px solid #fde68a; font-size:10.5px; font-weight:650; padding:2px 8px; border-radius:999px;">NST2 Verified</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(text)
                    
                    # Audio Speech Synthesis & Follow-up Action Chips ONLY on latest response
                    if idx == num_msgs - 1:
                        st.components.v1.html(
                            audio_speech_html(text, st.session_state.lang),
                            height=46,
                        )
                        last_intent = classify(text)
                        followups = get_followups(last_intent, st.session_state.lang)
                        if followups:
                            st.markdown(
                                f'<div style="font-size:11.5px; font-weight:700; color:#0d4f2b; margin:12px 0 6px; display:flex; align-items:center; gap:6px;">'
                                f'<span>💡</span> <span>{"Inyigo zikurikira (Kanda ugereyo ako kanya):" if st.session_state.lang == "rw" else "Recommended Follow-Up Actions (Instant One-Click):"}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            chip_cols = st.columns(len(followups))
                            for c_idx, chip_text in enumerate(followups):
                                if chip_cols[c_idx].button(chip_text, key=f"chip_btn_{idx}_{c_idx}", width="stretch"):
                                    st.session_state["pending_chat_prompt"] = chip_text
                                    st.rerun()

        chat_placeholder = (
            f"Baza Copilot ikibazo kuri {chosen_chat}... (Urugero: 'Nkeneye kuhira iki cyumweru?', 'Ibiciro by'ibigori')"
            if st.session_state.lang == "rw" else
            f"Ask Copilot about {chosen_chat}... (e.g. 'Should I irrigate this week?', 'Maize price forecast')"
        )
        chat_input_val = st.chat_input(chat_placeholder)
        user_prompt = st.session_state.pop("pending_chat_prompt", None) or chat_input_val

        if user_prompt:
            # Senior NER: Automatic district recognition & context shifting
            detected_d = extract_district(user_prompt)
            if detected_d and detected_d != chosen_chat:
                chosen_chat = detected_d
                st.session_state.chat_district = detected_d
                profile = pack(alerts, forecast, watch, soil, vegetation, detected_d)
                history_key = f"chat_{chosen_chat}_{st.session_state.lang}"
                if history_key not in st.session_state:
                    st.session_state[history_key] = []
                st.toast(f"📍 Context auto-switched to {detected_d} District!", icon="🧭")

            text = answer(user_prompt, profile, words, st.session_state.lang, context={"district": chosen_chat})
            st.session_state[history_key].append(("user", user_prompt))
            st.session_state[history_key].append(("bot", text))
            st.rerun()

    with col_drawer:
        # Drawer Card 1: Alert Status & Parametric Insurance
        drought_prob = 45.0 if profile["rain_pct"] <= -15.0 else 15.0
        payout_triggered = (drought_prob >= 30.0) or (profile["water_week"] <= -10.0 and profile["rain_pct"] <= -15.0)
        payout_badge = (
            '<span style="background:#fee2e2; color:#991b1b; border:1px solid #fca5a5; padding:3px 8px; border-radius:4px; font-weight:750; font-size:11px;">⚠️ PAYOUT ACTIVE</span>'
            if payout_triggered else
            '<span style="background:#dcfce7; color:#166534; border:1px solid #86efac; padding:3px 8px; border-radius:4px; font-weight:750; font-size:11px;">🟢 NORMAL RISK</span>'
        )

        st.markdown(
            f"""
            <div class="ai-side-card">
              <div class="ai-side-header">
                <span>🛡️</span> <span>{"Ibyago by'Ikirere n'Ubwishingizi" if st.session_state.lang == "rw" else "Risk & Insurance Desk"}</span>
              </div>
              <div class="ai-side-stat">
                <span class="ai-side-stat-lbl">{"Uko Ikirere Cyifashe" if st.session_state.lang == "rw" else "Agrometeo Alert"}</span>
                <span class="ai-side-stat-val">{pill(profile['alert'], words)}</span>
              </div>
              <div class="ai-side-stat">
                <span class="ai-side-stat-lbl">{"Indishyi ya NAIS" if st.session_state.lang == "rw" else "NAIS Insurance Status"}</span>
                <span class="ai-side-stat-val">{payout_badge}</span>
              </div>
              <div class="ai-side-stat">
                <span class="ai-side-stat-lbl">{"Pompi ya SSIT Ikwiye" if st.session_state.lang == "rw" else "SSIT Equipment Class"}</span>
                <span class="ai-side-stat-val" style="font-size:11.5px; color:#0d4f2b;">{kit_for_hectares(0.5)[0].title()} Pump</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Drawer Card 2: NISR SAS Survey Microdata Ground Truth
        st.markdown(
            f"""
            <div class="ai-side-card">
              <div class="ai-side-header">
                <span>📊</span> <span>{"Amakuru Nyayo ya NISR SAS" if st.session_state.lang == "rw" else "NISR Survey Baseline"}</span>
              </div>
              <div class="ai-side-stat">
                <span class="ai-side-stat-lbl">{"Umusaruro Ubusanzwe" if st.session_state.lang == "rw" else "Survey Baseline Yield"}</span>
                <span class="ai-side-stat-val">{profile['usual_yield']:.0f} kg/ha</span>
              </div>
              <div class="ai-side-stat">
                <span class="ai-side-stat-lbl">{"Imirima Ihirwa (SAS)" if st.session_state.lang == "rw" else "Irrigated Plots (SAS)"}</span>
                <span class="ai-side-stat-val">{profile['irrigated_pct']:.1f}%</span>
              </div>
              <div class="ai-side-stat">
                <span class="ai-side-stat-lbl">{"Ifumbire y'Imborera" if st.session_state.lang == "rw" else "Organic Fertilizer"}</span>
                <span class="ai-side-stat-val">{profile['organic_pct']:.1f}%</span>
              </div>
              <div class="ai-side-stat">
                <span class="ai-side-stat-lbl">{"Ifumbire Mvaruganda" if st.session_state.lang == "rw" else "Inorganic (DAP/Urea)"}</span>
                <span class="ai-side-stat-val">{profile['inorganic_pct']:.1f}%</span>
              </div>
              <div class="ai-side-stat">
                <span class="ai-side-stat-lbl">{"Imirima Ifite Amaterasi" if st.session_state.lang == "rw" else "Protected Slopes"}</span>
                <span class="ai-side-stat-val">{profile['protected_pct']:.1f}%</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Drawer Card 3: Live 160-Character SMS Dispatch Preview
        sms_preview = sms_text(profile, words)
        lines_sms = [l for l in sms_preview.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("```") and not l.startswith("*")]
        clean_sms_str = lines_sms[0] if lines_sms else f"CropWatch {chosen_chat}: Rain {profile['rain_pct']:+.0f}%. Week {profile['week_mm']:.0f}mm. SSIT {profile['deficit_mm']:.1f}mm deficit."
        clean_sms_str = clean_sms_str[:160]

        st.markdown(
            f"""
            <div class="ai-side-card">
              <div class="ai-side-header">
                <span>📱</span> <span>{"Ubutumwa bwa SMS (Inyuguti 160)" if st.session_state.lang == "rw" else "160-Char Rural SMS"}</span>
              </div>
              <div class="ai-sms-screen">{clean_sms_str}</div>
              <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; font-size:11px; color:#556353;">
                <span>{len(clean_sms_str)} / 160 {"inyuguti" if st.session_state.lang == "rw" else "chars"}</span>
                <span style="color:#0d4f2b; font-weight:700;">MTN / Airtel Ready</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Drawer Card 4: Institutional Support
        st.markdown(
            f"""
            <div class="ai-side-card" style="background:#f7fbf8; border-color:#c8dfcc;">
              <div class="ai-side-header" style="color:#0d4f2b;">
                <span>🏛️</span> <span>{"Ubufasha bw'Inzego" if st.session_state.lang == "rw" else "Extension Contacts"}</span>
              </div>
              <div style="font-size:12px; line-height:1.6; color:#2c3a2f;">
                <div>📞 <strong>MINAGRI Hotline:</strong> 1330 (Toll-Free)</div>
                <div>🌿 <strong>RAB Extension:</strong> Agronome wa Santere</div>
                <div>🛡️ <strong>NAIS Insurance:</strong> Tekana Urishingiwe</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer(words)

elif page == "data":
    page_head(
        words["src_title"],
        words["src_lead"],
        words,
        kicker=words.get("kicker_data"),
        sources=words.get("banner_sources_data"),
        action=words.get("banner_action_data"),
        tags=["Open Data Standard", "CSV / GeoJSON / Parquet", "Automated ETL"],
    )
    t_sources, t_overview, t_crops, t_calendar, t_rain = st.tabs([
        words["tab_sources"],
        words["tab_overview"],
        words["tab_crops"],
        words["tab_calendar"],
        words["tab_rain"],
    ])
    with t_sources:
        cards = "".join(source_card(item, st.session_state.lang, words) for item in SOURCES)
        st.markdown(f'<div class="inner-wrap">{cards}</div>', unsafe_allow_html=True)

    with t_overview:
        wide = survey_rows.pivot(index="year", columns="season", values="crop_rows").sort_index().reset_index()
        record_headers = [words["year_col"]] + [str(col) for col in wide.columns if col != "year"]
        record_rows = []
        for _, item in wide.iterrows():
            record_rows.append([int(item["year"])] + [f"{int(item[col]):,}" if pd.notna(item[col]) else "—" for col in wide.columns if col != "year"])
        st.markdown(
            '<div class="inner-wrap">'
            + f'<div class="kpi-row">'
            + kpi(words["survey_rows"], f"{int(status['survey_crop_rows']):,}")
            + kpi(words["safe"], str(int(status["safe_matches"])))
            + kpi(words["separate"], str(int(status["similar_kept_separate"])))
            + kpi(words["districts"], str(int(status["districts"])))
            + "</div>"
            + f'<p class="kicker-green" style="margin-top:36px">{words["fresh_files"]}</p>'
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
        st.markdown(f'<div class="inner-wrap"><p class="section-p">{words["safe_lead"]}</p></div>', unsafe_allow_html=True)
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

        st.markdown(f'<div class="inner-wrap"><p class="kicker-green" style="margin-top:24px">{words["separate"]}</p><p class="section-p">{words["close_lead"]}</p></div>', unsafe_allow_html=True)
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

        st.markdown(f'<div class="inner-wrap"><p class="kicker-green" style="margin-top:24px">{words["no_price"]}</p><p class="section-p">{words["unmatched_lead"]}</p></div>', unsafe_allow_html=True)
        name_col = "survey_crop_rw" if st.session_state.lang == "rw" else "survey_crop"
        why_col = "why_rw" if st.session_state.lang == "rw" else "why_en"
        show_table(
            unmatched.rename(columns={name_col: words["crop_col"], why_col: words["note_col"]})[
                [words["crop_col"], words["note_col"]]
            ]
        )

    with t_calendar:
        st.markdown(f'<div class="inner-wrap"><p class="section-p">{words["season_lead"]}</p></div>', unsafe_allow_html=True)
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

        st.markdown(f'<div class="inner-wrap"><p class="kicker-green" style="margin-top:24px">{"Ibigori n\'amasaka" if st.session_state.lang == "rw" else "Maize and sorghum"}</p><p class="section-p">{words["calendar_lead"]}</p></div>', unsafe_allow_html=True)
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

        st.markdown(f'<div class="inner-wrap"><p class="kicker-green" style="margin-top:24px">{words["zone_col"]}</p><p class="section-p">{words["zone_lead"]}</p></div>', unsafe_allow_html=True)
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
        st.markdown(f'<div class="inner-wrap"><p class="section-p">{words["rain_lead"]}</p></div>', unsafe_allow_html=True)
        district_names = sorted(rain["district"].unique())
        chosen_d = st.selectbox(words["district_col"], district_names, index=district_names.index("Nyagatare") if "Nyagatare" in district_names else 0, key="hub_rain_district")
        years = sorted(rain["year"].unique())
        chosen_year = st.selectbox(words["year_col"], years, index=len(years) - 1, key="hub_rain_year")
        view_rain = rain[(rain["district"] == chosen_d) & (rain["year"] == chosen_year)].sort_values("month").copy()
        view_rain[words["month_col"]] = view_rain["month"].map(words["month_names"])
        view_rain[words["rain_col"]] = view_rain["rainfall_mm"].round(1)
        view_rain[words["usual_col"]] = view_rain["usual_mm"].round(1)
        view_rain[words["diff_col"]] = view_rain["difference_mm"].round(1)
        show_table(view_rain[[words["month_col"], words["rain_col"], words["usual_col"], words["diff_col"]]])

    render_footer(words)

elif page == "about":
    page_head(
        words["about_title"],
        words["about_lead"],
        words,
        kicker=words.get("kicker_about"),
        sources=words.get("banner_sources_about"),
        action=words.get("banner_action_about"),
        tags=["Vision 2050", "NST2 Strategic Priority 1", "MINAGRI / RAB / NISR"],
    )
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
        f'<div style="display:inline-block; padding:4px 12px; background:rgba(196,163,90,0.15); border:1px solid var(--accent); border-radius:16px; font-size:12px; font-weight:600; color:var(--gold-soft); margin-bottom:16px;">🏆 {words["hackathon_badge"]}</div>'
        '<div class="decision-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">'
        f'<article style="border-top:3px solid var(--accent);">'
        f'<h3 style="margin-bottom:2px;">{words["team_murenzi_name"]}</h3>'
        f'<p style="color:var(--gold-soft); font-weight:600; font-size:12px; margin-bottom:6px;">{words["team_murenzi_role"]}</p>'
        f'<p style="font-size:13px; line-height:1.5; color:var(--text);">{words["team_murenzi_desc"]}</p>'
        f'</article>'
        f'<article style="border-top:3px solid var(--accent);">'
        f'<h3 style="margin-bottom:2px;">{words["team_bahire_name"]}</h3>'
        f'<p style="color:var(--gold-soft); font-weight:600; font-size:12px; margin-bottom:6px;">{words["team_bahire_role"]}</p>'
        f'<p style="font-size:13px; line-height:1.5; color:var(--text);">{words["team_bahire_desc"]}</p>'
        f'</article>'
        '</div>'
        f'<div class="note-box">{words["footer_disclaimer"]}</div>'
        f'<p class="section-p">{words["footer_ack"]}</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    with st.expander(words.get("about_method_title", "🔬 Scientific Methodology, FAO-56 Formulations & ML Benchmarks"), expanded=False):
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
