"""Plain-language district notes for CSV/HTML download. Not a harvest certificate."""


def _has(row, key):
    try:
        value = row[key]
    except Exception:
        return False
    if value is None:
        return False
    try:
        return value == value
    except Exception:
        return True


def district_note(row, words, week=None):
    lines = [
        "CropWatch Rwanda — district note",
        "NISR 2026 Big Data Hackathon · Track 1. Student project, not a NISR publication.",
        "",
        f"District: {row['district']}",
        f"Alert: {row['alert']}",
        f"Rain so far (mm): {float(row['rain_so_far_mm']):.1f}",
        f"Usual Sep–Oct (mm, CHIRPS 2018–2025): {float(row['usual_sep_oct_mm']):.1f}",
        f"Rain vs usual (%): {float(row['rain_difference_pct']):.1f}",
        f"Next 7 days (mm, Open-Meteo): {float(row['forecast_week_mm']):.1f}",
        f"Climate class: {row['climate_class']}" if _has(row, "climate_class") else None,
        f"FAO-56 maize ETc week (mm): {float(row['etc_week_mm']):.1f}" if _has(row, "etc_week_mm") else None,
        f"Week water balance Pe−ETc (mm): {float(row['water_balance_week_mm']):.1f}" if _has(row, "water_balance_week_mm") else None,
        f"Season A 2022 plots irrigated (%): {float(row['irrigated_pct']):.1f}",
        f"Moderate/severe erosion Season A 2022 (%): {float(row['concern_pct']):.1f}",
        f"Erosion protection Season A 2022 (%): {float(row['protected_pct']):.1f}",
        f"Usual maize yield kg/ha (past average): {float(row['usual_yield_kg_ha']):.0f}",
        "",
        "Why this alert:",
        words.get("why_" + str(row["alert"]), words.get("why_stable", "")),
        "",
        "Sources: NISR SAS Season A 2022 (plot-weighted); CHIRPS usual Sep–Oct 2018–2025;",
        "Open-Meteo rain since 1 September 2026 and 7-day forecast at the district midpoint.",
        "Decision-support only. Not a guaranteed agricultural outcome.",
    ]
    lines = [line for line in lines if line is not None]
    if week is not None and not week.empty:
        lines.append("")
        lines.append("Open-Meteo week:")
        for _, item in week.iterrows():
            lines.append(f"  {item['date']}: {float(item['forecast_mm']):.1f} mm")
    return "\n".join(lines)


def html_report(row, words, week=None):
    body = district_note(row, words, week).replace("\n", "<br>\n")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>CropWatch district note</title>"
        "<style>body{font-family:Georgia,serif;max-width:720px;margin:40px auto;color:#1a1f16;line-height:1.5}</style>"
        f"</head><body>{body}</body></html>"
    )
