import json
from pathlib import Path
import pydeck as pdk
import pandas as pd
import streamlit as st

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

    return (
        status, matches, unmatched, seasons, calendar, zones, rows, rain, watch,
        soil, alerts, forecast, exports_year, exports_partners, benchmark, sim_base
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
            f'<span>{float(item["rain_chance_pct"]):.0f}%</span></div>'
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
        f'<div class="kpi-row{" five" if len(kpis) == 5 else ""}">{"".join(kpis)}</div>'
        f"{extra}</section>"
    )


def site_footer(words):
    return f"""
    <footer class="landing-footer">
      <div class="landing-footer-grid">
        <div>
          <div class="landing-brand">CropWatch</div>
          <p>{words["footer_blurb"]}</p>
        </div>
        <div>
          <h2>{words["alerts"]}</h2>
          <p>{words["soil"]}</p>
          <p>{words["watch"]}</p>
        </div>
        <div>
          <h2>{words["how"]}</h2>
          <p>NISR · CHIRPS · Open-Meteo · Scikit-Learn</p>
        </div>
        <div>
          <h2>{words["nav_about"]}</h2>
          <p>{words["footer_copy"]}</p>
        </div>
      </div>
      <div class="landing-copyright">{words["footer_copy"]}</div>
    </footer>
    """


def page_head(title, lead, words):
    st.markdown(
        f'<section class="page-band"><div class="inner">'
        f'<p class="kicker-green">{words["eyebrow"]}</p>'
        f"<h1>{title}</h1><p class='lead'>{lead}</p></div></section>",
        unsafe_allow_html=True,
    )


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
    soil, alerts, forecast, exports_year, exports_partners, benchmark, sim_base
) = load()

matches["safe_to_join"] = matches["safe_to_join"].astype(str).str.lower().eq("true")
blank_rw = unmatched["survey_crop_rw"].isna() | unmatched["survey_crop_rw"].astype(str).str.strip().eq("")
unmatched.loc[blank_rw, "survey_crop_rw"] = unmatched.loc[blank_rw, "survey_crop"]

PAGES = ("alerts", "soil", "watch", "simulator", "home", "how")
NAV_LABEL = {
    "alerts": "nav_alerts",
    "soil": "nav_soil",
    "watch": "nav_season",
    "simulator": "nav_simulator",
    "home": "nav_data",
    "how": "nav_method",
}

words = TEXT[st.session_state.lang]
safe = matches[matches["safe_to_join"] == True].copy()
close = matches[matches["safe_to_join"] == False].copy()

st.markdown('<div id="cw-top"></div>', unsafe_allow_html=True)
brand, nav_col, lang_col = st.columns([1.2, 5.1, 0.95], vertical_alignment="center")
with brand:
    st.markdown(
        """
        <div class="landing-brand">
          <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="20" fill="#008a28"/>
            <path d="M12 24c4-10 8-14 11-15-2 7-2 12 1 15 4-7 7-9 9-9-4 9-8 14-14 15-5-1-7-3-7-6z" fill="#fff"/>
          </svg>
          CropWatch
        </div>
        """,
        unsafe_allow_html=True,
    )
with nav_col:
    page = st.pills(
        "Page",
        options=list(PAGES),
        format_func=lambda key: words[NAV_LABEL[key]],
        default="alerts",
        label_visibility="collapsed",
        key="page_nav",
    )
    if page is None:
        page = "alerts"
with lang_col:
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

month = words["month_names"][int(status["rain_last_month"])]
rain_text = f"{month} {int(status['rain_last_year'])}"

if page == "alerts":
    n_gap = int(alerts["alert"].isin(["irrigation_gap", "irrigate_now"]).sum())
    irrig_national = 100 * alerts["irrigated_yes_weight"].sum() / alerts["irrigated_weight"].sum()
    driest = alerts.sort_values("rain_difference_pct").iloc[0]
    preview_rows = ""
    for _, item in alerts.head(4).iterrows():
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
              <div class="landing-actions">
                <span class="landing-button hero-primary">{words["hero_cta"]} →</span>
                <span class="landing-button hero-secondary">{words["hero_cta2"]}</span>
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
              <footer>{words["view_all"]}</footer>
            </aside>
          </div>
        </section>
        <section class="landing-section">
          <div class="landing-shell">
            <div class="landing-stats">
              <dl>
                <div><dt>{words["stat_alert_districts"]}</dt><dd>{n_gap}</dd></div>
                <div><dt>{words["stat_irrigated"]}</dt><dd>{irrig_national:.1f}%</dd></div>
                <div><dt>{words["stat_worst"]}</dt><dd>{driest["rain_difference_pct"]:.0f}%</dd></div>
              </dl>
            </div>
            <div class="decision-heading">
              <div>
                <p class="kicker-green">{words["kicker_decisions"]}</p>
                <h2>{words["what_today"]}</h2>
                <p>{words["what_lead"]}</p>
              </div>
            </div>
            <div class="decision-grid">
              <article><span class="decision-number">01</span><h3>{words["card_fresh"]}</h3><p>{words["card_fresh_body"]}</p></article>
              <article><span class="decision-number">02</span><h3>{words["card_rule"]}</h3><p>{words["card_rule_body"]}</p></article>
              <article><span class="decision-number">03</span><h3>{words["card_action"]}</h3><p>{words["card_action_body"]}</p></article>
            </div>
            <div class="logic-box">
              <strong>{words["logic_title"]}</strong>
              <ol>
                <li>{words["logic_1"]}</li>
                <li>{words["logic_2"]}</li>
                <li>{words["logic_3"]}</li>
                <li>{words["logic_4"]}</li>
              </ol>
            </div>
          </div>
        </section>
        <section class="landing-section">
          <div class="landing-shell">
            <p class="kicker-green">04 / {words["alerts"]}</p>
            <h2>{words["alerts_title"]}</h2>
            <p class="section-p">{words["alerts_lead"]}</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    shown = st.pills(
        words["filter"],
        ["irrigation", "soil", "stable", "all"],
        format_func=lambda key: {
            "all": words["filter_all"],
            "irrigation": words["filter_irrigation"],
            "soil": words["filter_soil"],
            "stable": words["filter_stable"],
        }[key],
        default="irrigation",
        label_visibility="collapsed",
        key="alert_filter",
    )
    if shown is None:
        shown = "irrigation"
    view = alerts.copy()
    if shown == "irrigation":
        view = view[view["alert"].isin(["irrigation_gap", "irrigate_now", "dry_watch"])]
    elif shown == "soil":
        view = view[view["alert"].isin(["soil_rain", "soil_watch"])]
    elif shown == "stable":
        view = view[view["alert"] == "stable"]
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
            table_rows,
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    # Interactive Pydeck Alert Map
    color_map = {
        "irrigate_now": [220, 38, 38, 210],
        "irrigation_gap": [234, 88, 12, 210],
        "soil_rain": [202, 138, 4, 210],
        "dry_watch": [217, 119, 6, 190],
        "soil_watch": [180, 83, 9, 190],
        "stable": [22, 163, 74, 210],
    }
    map_df = alerts.copy()
    map_df["color"] = map_df["alert"].map(color_map)
    map_df["alert_label"] = map_df["alert"].apply(lambda a: words.get("label_" + str(a), a))
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["longitude", "latitude"],
        get_color="color",
        get_radius=8500,
        pickable=True,
    )
    view_state = pdk.ViewState(latitude=-1.94, longitude=29.87, zoom=7.6, pitch=0)
    tooltip = {
        "html": "<b>{district}</b><br/>"
                "Status: <b>{alert_label}</b><br/>"
                "Rain vs Usual: <b>{rain_difference_pct:.0f}%</b><br/>"
                "Plots Irrigated: <b>{irrigated_pct:.1f}%</b><br/>"
                "7-Day Forecast: <b>{forecast_week_mm:.0f} mm</b>",
        "style": {"backgroundColor": "#080d25", "color": "#ffffff", "fontSize": "13px", "padding": "10px", "borderRadius": "8px"}
    }
    st.markdown(
        f'<div class="inner-wrap" style="margin-top:24px;">'
        f'<p class="kicker-green">{words["map_title"]}</p>'
        f'<p class="section-p">{words["map_lead"]}</p>'
        f'<div style="font-size:12px; color:var(--lp-muted); margin-bottom:12px;">{words["map_legend"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip), height=380)

    district_names = list(alerts["district"])
    chosen = st.selectbox(
        words["pick_district"],
        district_names,
        index=district_names.index("Nyaruguru") if "Nyaruguru" in district_names else 0,
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
            ],
            extra=week_panel(week, words),
            pill_html=pill(row["alert"], words),
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(site_footer(words), unsafe_allow_html=True)

elif page == "soil":
    page_head(words["nav_soil"], words["soil_lead"], words)
    view = soil.copy()
    view["concern"] = 100 * view["concern_yes_weight"] / view["concern_weight"]
    view["severe"] = 100 * view["severe_yes_weight"] / view["severe_weight"]
    view["protected"] = 100 * view["protected_yes_weight"] / view["protected_weight"]
    view["organic"] = 100 * view["organic_yes_weight"] / view["organic_weight"]
    view["inorganic"] = 100 * view["inorganic_yes_weight"] / view["inorganic_weight"]
    view["short"] = 100 * view["organic_short_yes_weight"] / view["organic_short_weight"]
    district_names = sorted(view["district"].unique())
    chosen = st.selectbox(
        words["pick_district"],
        district_names,
        index=district_names.index("Rulindo") if "Rulindo" in district_names else 0,
        key="soil_district",
    )
    row = view[view["district"] == chosen].iloc[0]
    rain_pct = float(row["rain_difference_pct"])
    if rain_pct <= -10:
        rain_sentence = words["soil_rain_drier"]
    elif rain_pct >= 10:
        rain_sentence = words["soil_rain_wetter"]
    else:
        rain_sentence = words["soil_rain_close"]
    ranked = view.sort_values("concern", ascending=False)
    ranked_rows = [
        (
            item["district"],
            bar_cell(item["concern"]),
            f"{item['severe']:.0f}%",
            f"{item['protected']:.0f}%",
            f"{item['organic']:.0f}%",
            f"{item['inorganic']:.0f}%",
            f"{item['rain_difference_pct']:.0f}%",
        )
        for _, item in ranked.iterrows()
    ]
    st.markdown(
        '<div class="inner-wrap">'
        + board(
            words["eyebrow"],
            chosen,
            words["soil_sentence"].format(
                concern=row["concern"],
                severe=row["severe"],
                protected=row["protected"],
                organic=row["organic"],
                inorganic=row["inorganic"],
            )
            + " "
            + words["soil_short"].format(short=row["short"]),
            rain_sentence.format(
                pct=abs(rain_pct),
                rain=row["rain_mm"],
                usual=row["usual_rain_mm"],
                yield_kg=row["usual_yield_kg_ha"],
            ),
            [
                kpi(words["concern_metric"], f"{row['concern']:.0f}"),
                kpi(words["severe_metric"], f"{row['severe']:.0f}"),
                kpi(words["protected_metric"], f"{row['protected']:.0f}"),
                kpi(words["organic_metric"], f"{row['organic']:.0f}"),
                kpi(words["inorganic_metric"], f"{row['inorganic']:.0f}"),
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
            ranked_rows,
        )
        + "</div>"
        + site_footer(words),
        unsafe_allow_html=True,
    )

elif page == "watch":
    page_head(words["watch"], words["watch_lead"], words)
    district_names = sorted(watch["district"].unique())
    left, right = st.columns([1.1, 2])
    with left:
        chosen = st.selectbox(
            words["pick_district"],
            district_names,
            index=district_names.index("Nyagatare") if "Nyagatare" in district_names else 0,
            key="watch_district",
        )
    with right:
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
    row = watch[(watch["district"] == chosen) & (watch["season"] == chosen_season)].iloc[0]
    pct = float(row["rain_difference_pct"])
    yield_kg = float(row["usual_yield_kg_ha"])
    if pct <= -10:
        sentence = words["watch_drier"]
    elif pct >= 10:
        sentence = words["watch_wetter"]
    else:
        sentence = words["watch_close"]
    if pd.notna(row["maize_price_rwf_per_kg"]):
        price_text = words["price_here"].format(price=row["maize_price_rwf_per_kg"], date=row["price_date"])
    else:
        price_text = words["price_national"].format(price=row["national_maize_price_rwf_per_kg"], date=row["national_price_date"])
    veg_text = words["veg_line"].format(year=2026, now=row["vegetation_2026"], usual=row["usual_vegetation"])
    export_year_rows = [(int(item["year"]), f"{item['trade_value_usd']:,.0f}", item.get("partner", "")) for _, item in exports_year.iterrows()]
    export_partner_rows = [(item["partner"], f"{item['trade_value_usd']:,.0f}", int(item["year"])) for _, item in exports_partners.iterrows()]
    st.markdown(
        '<div class="inner-wrap">'
        + board(
            season_labels[chosen_season],
            chosen,
            sentence.format(pct=abs(pct), yield_kg=yield_kg),
            "",
            [
                kpi(words["rain_now"], f"{row['rain_mm']:.0f}"),
                kpi(words["usual_col"], f"{row['usual_rain_mm']:.0f}"),
                kpi(words["diff_col"], f"{row['rain_difference_mm']:.0f}"),
                kpi(words["yield_usual"], f"{yield_kg:.0f}"),
            ],
        )
        + '<div class="split-cards">'
        + f'<article><h3>{words["price_card"]}</h3><p>{price_text}</p></article>'
        + f'<article><h3>{words["veg_card"]}</h3><p>{veg_text}</p></article>'
        + "</div>"
        + f'<p class="kicker-green">{words["export_year"]}</p><p class="section-p">{words["export_lead"]}</p>'
        + data_table([words["year_col"], "USD", words["note_col"]], export_year_rows)
        + f'<p class="kicker-green">{words["export_partners"]}</p>'
        + data_table([words["note_col"], "USD", words["year_col"]], export_partner_rows)
        + "</div>"
        + site_footer(words),
        unsafe_allow_html=True,
    )

elif page == "simulator":
    page_head(words["sim_title"], words["sim_lead"], words)
    district_names = sorted(sim_base["district"].unique()) if not sim_base.empty else sorted(alerts["district"].unique())
    chosen_sim = st.selectbox(
        words["pick_district"],
        district_names,
        index=district_names.index("Bugesera") if "Bugesera" in district_names else 0,
        key="sim_district_select",
    )
    sim_row = sim_base[sim_base["district"] == chosen_sim].iloc[0] if not sim_base.empty else alerts[alerts["district"] == chosen_sim].iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        d_irrig = st.slider(words["sim_irrig_slider"], 0, 30, 15, 5, key="d_irrig")
    with c2:
        d_organic = st.slider(words["sim_organic_slider"], 0, 40, 20, 5, key="d_organic")
    with c3:
        d_protect = st.slider(words["sim_protect_slider"], 0, 30, 10, 5, key="d_protect")

    base_y = float(sim_row["usual_yield_kg_ha"])
    pct_uplift = (0.30 * (d_irrig / 100.0) + 0.20 * (d_organic / 100.0) + 0.15 * (d_protect / 100.0)) * 100.0
    proj_y = base_y * (1.0 + pct_uplift / 100.0)
    gain_kg = proj_y - base_y

    sim_body = (
        f"Simulating policy interventions for {chosen_sim}: expanding small-scale irrigation by +{d_irrig}%, "
        f"closing the organic fertilizer shortage by +{d_organic}%, and improving anti-erosion protection by +{d_protect}%."
        if st.session_state.lang == "en"
        else f"Igereranya ry'ishoramari muri {chosen_sim}: kongera kuhira ku buso buciriritse ho +{d_irrig}%, "
        f"gukemura ibura ry'imborera ho +{d_organic}%, no gushimangira amaterasi n'imiringoti yo kurwanya isuri ho +{d_protect}%."
    )

    st.markdown(
        '<div class="inner-wrap">'
        + board(
            "What-If Policy Simulation",
            f"{chosen_sim} · Maize Yield Optimization",
            sim_body,
            words["sim_policy_note"],
            [
                kpi(words["sim_base_yield"], f"{base_y:.0f}"),
                kpi(words["sim_projected_yield"], f"{proj_y:.0f}"),
                kpi(words["sim_gain"], f"+{gain_kg:.0f} kg/ha", hint=f"+{pct_uplift:.1f}%"),
                kpi(words["stat_irrigated"], f"{sim_row['irrigated_pct']:.1f}%", hint=f"Simulated: {min(100, sim_row['irrigated_pct'] + d_irrig):.1f}%"),
            ],
        )
        + "</div>"
        + site_footer(words),
        unsafe_allow_html=True,
    )

elif page == "home":
    page_head(words["nav_data"], words["home_lead"], words)
    t_overview, t_crops, t_calendar, t_rain = st.tabs([
        words["tab_overview"],
        words["tab_crops"],
        words["tab_calendar"],
        words["tab_rain"],
    ])

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

    st.markdown(site_footer(words), unsafe_allow_html=True)

else:
    page_head(words["how"], words["subtitle"], words)
    steps = "".join(
        f'<article><span class="step">0{i}</span><p>{words[key]}</p></article>'
        for i, key in enumerate(("how_1", "how_2", "how_3", "how_4", "how_5", "how_6", "how_7", "how_8"), start=1)
    )
    benchmark_html = ""
    if benchmark and "models" in benchmark:
        benchmark_rows = [
            [m["name"], f"{m['mae_kg_ha']:.1f}", f"{m['rmse_kg_ha']:.1f}", f"{m['r2']:.3f}", m["verdict"]]
            for m in benchmark["models"]
        ]
        feat_rows = [
            ["Seasonal Rain (mm)", f"{benchmark['feature_importances'].get('rain_mm', 0)*100:.1f}%", "Growing season water volume"],
            ["Rain Anomaly (% vs normal)", f"{benchmark['feature_importances'].get('rain_diff_pct', 0)*100:.1f}%", "Deficit/surplus vs district climatology"],
            ["Sentinel NDRE Vegetation", f"{benchmark['feature_importances'].get('vegetation_mean', 0)*100:.1f}%", "Canopy chlorophyll & vegetative vigor"],
            ["Organic Fertilizer Share", f"{benchmark['feature_importances'].get('organic_pct', 0)*100:.1f}%", "Manure application for soil organic carbon"],
            ["Inorganic Fertilizer Share", f"{benchmark['feature_importances'].get('inorganic_pct', 0)*100:.1f}%", "Commercial NPK / DAP utilization"],
            ["Small-Scale Irrigation Share", f"{benchmark['feature_importances'].get('irrigated_pct', 0)*100:.1f}%", "Mitigates dry spells at flowering"],
            ["Soil Protection / Terracing", f"{benchmark['feature_importances'].get('protected_pct', 0)*100:.1f}%", "Prevents nutrient runoff on steep hills"],
            ["Severe Erosion Concern", f"{benchmark['feature_importances'].get('concern_pct', 0)*100:.1f}%", "Vulnerability to rills, gullies, landslides"],
        ]
        benchmark_html = (
            f'<div style="margin-top:40px;">'
            f'<p class="kicker-green">{words["benchmark_title"]}</p>'
            f'<p class="section-p">{words["benchmark_lead"]}</p>'
            + data_table(["Model Architecture", "MAE (kg/ha)", "RMSE (kg/ha)", "R² Score", "Evaluation Verdict"], benchmark_rows)
            + f'<p class="kicker-green" style="margin-top:28px">Multi-Factor Feature Importances (Random Forest)</p>'
            + data_table(["Predictor Variable", "Importance (%)", "Agronomic Role"], feat_rows)
            + f'</div>'
        )

    st.markdown(
        f'<div class="inner-wrap"><div class="method-list">{steps}</div>{benchmark_html}</div>' + site_footer(words),
        unsafe_allow_html=True,
    )
