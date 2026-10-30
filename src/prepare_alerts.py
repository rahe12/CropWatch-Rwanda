"""Irrigation shares, district points, live rain, and the alert table.

Season A 2022 is the last year the irrigation question is written in
words and the plot weight is on the file. A skipped follow-up after
'no irrigation on any plot' counts as no.

Usual September–October rain is CHIRPS 2018–2025. Rain since
1 September 2026, and the next seven days, come from Open-Meteo at
the district midpoint. Those are two rain products, so the gap is a
signal, not a millimetre-perfect difference.
"""

from __future__ import annotations

import io
import json
import time
import zipfile
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import shapefile

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SOURCE = ROOT / "data" / "source"
APP = PROCESSED / "app"
SHAPE_ZIP = SOURCE / "rwa_adm_2006_nisr_wgs1984_20181002_shp.zip"
SHAPE_NAME = "rwa_adm2_2006_NISR_WGS1984_20181002"
YEAR = 2022
SEASON = "A"
USUAL_YEARS = list(range(2018, 2026))
SEASON_START = date(2026, 9, 1)
TODAY = date(2026, 10, 30)
ARCHIVE_END = TODAY - timedelta(days=1)
# FAO GIEWS Season A maize window is September–October. Mid-window is an
# assumed plant date, not a field visit. Kc from FAO-56 Table 12 (maize grain)
# and tropical stage lengths from Table 11.
PLANT_DATE = date(2026, 9, 15)
LINI, LDEV, LMID, LLATE = 20, 35, 40, 30
KC_INI, KC_MID, KC_END = 0.30, 1.20, 0.60


def plot_yes(frame, this_col, any_col):
    this_word = frame[this_col].astype("string").str.strip().str.lower()
    any_plot = frame[any_col].astype("string").str.strip().str.lower()
    yes = this_word.eq("yes").fillna(False)
    no = this_word.eq("no").fillna(False) | (this_word.isna() & any_plot.eq("no").fillna(False))
    result = pd.Series(pd.NA, index=frame.index, dtype="boolean")
    result[no.to_numpy()] = False
    result[yes.to_numpy()] = True
    return result


def weighted_share(frame, yes, name):
    rows = []
    for district, part in frame.groupby("district"):
        flag = yes.loc[part.index]
        weight = pd.to_numeric(part["plot_weight"], errors="coerce")
        keep = flag.notna() & weight.notna() & (weight > 0)
        total = float(weight[keep].sum())
        used = float(weight[keep & flag.fillna(False)].sum())
        rows.append({"district": district, f"{name}_yes_weight": used, f"{name}_weight": total})
    return pd.DataFrame(rows)


def irrigation():
    practice = pd.read_csv(
        PROCESSED / "sas" / "agricultural_practice.csv",
        usecols=["year", "season", "district", "district_pcode", "province", "plot_weight", "s4q14", "s4q15"],
        low_memory=False,
    )
    practice = practice[(practice["year"] == YEAR) & (practice["season"] == SEASON)].copy()
    practice["irrigated"] = plot_yes(practice, "s4q15", "s4q14")
    print("Irrigation plots", len(practice))
    print(pd.crosstab(practice["s4q14"].fillna("blank"), practice["s4q15"].fillna("blank")))
    place = practice.groupby("district", as_index=False).agg(
        district_pcode=("district_pcode", "first"),
        province=("province", "first"),
    )
    shares = weighted_share(practice, practice["irrigated"], "irrigated")
    return place.merge(shares, on="district")


def usual_sep_oct():
    rain = pd.read_csv(PROCESSED / "rainfall" / "district_month_anomaly.csv")
    window = rain[(rain["year"].isin(USUAL_YEARS)) & (rain["month"].isin([9, 10]))]
    usual = window.groupby("district", as_index=False).agg(usual_sep_oct_mm=("rainfall_mm", "mean"))
    # mean of monthly values would be too small; sum September and October, then average across years
    by_year = window.groupby(["district", "year"], as_index=False)["rainfall_mm"].sum()
    usual = by_year.groupby("district", as_index=False).agg(usual_sep_oct_mm=("rainfall_mm", "mean"))
    usual["usual_months"] = "September–October 2018–2025"
    return usual


def centroids():
    with zipfile.ZipFile(SHAPE_ZIP) as zipped:
        reader = shapefile.Reader(
            shp=io.BytesIO(zipped.read(f"{SHAPE_NAME}.shp")),
            shx=io.BytesIO(zipped.read(f"{SHAPE_NAME}.shx")),
            dbf=io.BytesIO(zipped.read(f"{SHAPE_NAME}.dbf")),
        )
        fields = [field[0] for field in reader.fields[1:]]
        rows = []
        for shape_record in reader.shapeRecords():
            record = dict(zip(fields, shape_record.record))
            bbox = shape_record.shape.bbox
            rows.append(
                {
                    "district": record["ADM2_EN"],
                    "district_pcode": record["ADM2_PCODE"],
                    "longitude": (bbox[0] + bbox[2]) / 2,
                    "latitude": (bbox[1] + bbox[3]) / 2,
                }
            )
    points = pd.DataFrame(rows)
    print("District points", len(points))
    return points


def kc_maize(day):
    if not isinstance(day, date):
        day = pd.to_datetime(day).date()
    elapsed = (day - PLANT_DATE).days
    if elapsed < 0:
        return 0.0, "pre_plant"
    if elapsed < LINI:
        return KC_INI, "initial"
    if elapsed < LINI + LDEV:
        share = (elapsed - LINI) / LDEV
        return KC_INI + (KC_MID - KC_INI) * share, "development"
    if elapsed < LINI + LDEV + LMID:
        return KC_MID, "mid"
    if elapsed < LINI + LDEV + LMID + LLATE:
        share = (elapsed - LINI - LDEV - LMID) / LLATE
        return KC_MID + (KC_END - KC_MID) * share, "late"
    return KC_END, "late"


def effective_rain(mm):
    if mm is None or (isinstance(mm, float) and pd.isna(mm)):
        return 0.0
    rain = max(0.0, float(mm))
    if rain <= 5:
        return 0.6 * rain
    return 0.8 * rain


def http_json(url, tries=3):
    request = Request(url, headers={"User-Agent": "CropWatchRwanda/1.0"})
    last_error = None
    for attempt in range(tries):
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:
            last_error = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Open-Meteo failed: {last_error}")


def open_meteo(points):
    lats = ",".join(f"{lat:.4f}" for lat in points["latitude"])
    lons = ",".join(f"{lon:.4f}" for lon in points["longitude"])
    archive_query = urlencode(
        {
            "latitude": lats,
            "longitude": lons,
            "start_date": SEASON_START.isoformat(),
            "end_date": ARCHIVE_END.isoformat(),
            "daily": "precipitation_sum,et0_fao_evapotranspiration,temperature_2m_max,temperature_2m_min",
            "timezone": "Africa/Kigali",
        }
    )
    forecast_query = urlencode(
        {
            "latitude": lats,
            "longitude": lons,
            "daily": "precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration,temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
            "forecast_days": 7,
            "timezone": "Africa/Kigali",
        }
    )
    archive = http_json(f"https://archive-api.open-meteo.com/v1/archive?{archive_query}")
    forecast = http_json(f"https://api.open-meteo.com/v1/forecast?{forecast_query}")
    if isinstance(archive, dict):
        archive = [archive]
    if isinstance(forecast, dict):
        forecast = [forecast]

    season_rows = []
    day_rows = []
    for index, point in points.iterrows():
        past = archive[index]["daily"]
        rain_list = past.get("precipitation_sum") or []
        et0_list = past.get("et0_fao_evapotranspiration") or [0] * len(past["time"])
        rain_so_far = float(pd.Series(rain_list, dtype="float").sum())
        pe_season = 0.0
        etc_season = 0.0
        et0_season = 0.0
        kc_today, stage_today = kc_maize(TODAY)
        for day, rain, et0 in zip(past["time"], rain_list, et0_list):
            kc, _stage = kc_maize(day)
            rain_v = 0.0 if pd.isna(rain) else float(rain)
            et0_v = 0.0 if pd.isna(et0) else float(et0)
            pe_season += effective_rain(rain_v)
            etc_season += et0_v * kc
            et0_season += et0_v
        season_rows.append(
            {
                "district": point["district"],
                "rain_so_far_mm": rain_so_far,
                "et0_season_mm": round(et0_season, 1),
                "etc_season_mm": round(etc_season, 1),
                "pe_season_mm": round(pe_season, 1),
                "water_balance_season_mm": round(pe_season - etc_season, 1),
                "kc_maize": round(kc_today, 2),
                "maize_stage": stage_today,
                "plant_date_assumed": PLANT_DATE.isoformat(),
                "season_start": SEASON_START.isoformat(),
                "season_until": ARCHIVE_END.isoformat(),
                "rain_source": "Open-Meteo archive",
                "et0_source": "Open-Meteo FAO-56 ET0",
            }
        )
        future = forecast[index]["daily"]
        n_days = len(future["time"])
        def col(name):
            values = future.get(name) or [None] * n_days
            if len(values) < n_days:
                values = list(values) + [None] * (n_days - len(values))
            return values
        for day, amount, chance, et0, tmax, tmin, wind in zip(
            future["time"],
            col("precipitation_sum"),
            col("precipitation_probability_max"),
            col("et0_fao_evapotranspiration"),
            col("temperature_2m_max"),
            col("temperature_2m_min"),
            col("wind_speed_10m_max"),
        ):
            rain_v = 0.0 if amount is None or pd.isna(amount) else float(amount)
            et0_v = 0.0 if et0 is None or pd.isna(et0) else float(et0)
            kc, stage = kc_maize(day)
            pe = effective_rain(rain_v)
            etc = et0_v * kc
            day_rows.append(
                {
                    "district": point["district"],
                    "date": day,
                    "forecast_mm": rain_v,
                    "rain_chance_pct": chance,
                    "et0_mm": round(et0_v, 2),
                    "etc_mm": round(etc, 2),
                    "pe_mm": round(pe, 2),
                    "water_balance_mm": round(pe - etc, 2),
                    "kc_maize": round(kc, 2),
                    "maize_stage": stage,
                    "temp_max_c": tmax,
                    "temp_min_c": tmin,
                    "wind_max_kmh": wind,
                }
            )
    return pd.DataFrame(season_rows), pd.DataFrame(day_rows)


def classify(row):
    dry = row["rain_difference_pct"] <= -10
    wet_week = row["forecast_max_mm"] >= 15
    dry_week = row["forecast_week_mm"] < 10
    low_irrigation = row["irrigated_pct"] < 10
    soil_open = (row["concern_pct"] >= 20) and (row["protected_pct"] < 80)
    week_deficit = row.get("water_balance_week_mm", 0) < -10
    season_deficit = row.get("water_balance_season_mm", 0) < -30

    if dry and low_irrigation and dry_week:
        action, priority = "irrigate_now", 1
    elif dry and low_irrigation:
        action, priority = "irrigation_gap", 2
    elif wet_week and soil_open:
        action, priority = "soil_rain", 3
    elif dry:
        action, priority = "dry_watch", 4
    elif soil_open:
        action, priority = "soil_watch", 5
    else:
        action, priority = "stable", 6

    if dry and wet_week:
        climate = "agronomist"
    elif wet_week and soil_open:
        climate = "excess_rain"
    elif (week_deficit or season_deficit) and dry and low_irrigation:
        climate = "water_stress"
    elif dry or week_deficit:
        climate = "rainfall_watch"
    else:
        climate = "normal_monitoring"
    return action, priority, climate


def main():
    APP.mkdir(parents=True, exist_ok=True)
    water = irrigation()
    water["irrigated_pct"] = 100 * water["irrigated_yes_weight"] / water["irrigated_weight"]
    print("National irrigation", round(100 * water["irrigated_yes_weight"].sum() / water["irrigated_weight"].sum(), 1))
    print(water.sort_values("irrigated_pct")[["district", "irrigated_pct"]].head(8).to_string(index=False))

    soil = pd.read_csv(APP / "soil_season_a_2022.csv")
    soil["concern_pct"] = 100 * soil["concern_yes_weight"] / soil["concern_weight"]
    soil["severe_pct"] = 100 * soil["severe_yes_weight"] / soil["severe_weight"]
    soil["protected_pct"] = 100 * soil["protected_yes_weight"] / soil["protected_weight"]
    soil["organic_pct"] = 100 * soil["organic_yes_weight"] / soil["organic_weight"]
    soil["inorganic_pct"] = 100 * soil["inorganic_yes_weight"] / soil["inorganic_weight"]

    usual = usual_sep_oct()
    points = centroids()
    missing = sorted(set(water["district"]) - set(points["district"]))
    extra = sorted(set(points["district"]) - set(water["district"]))
    if missing or extra:
        raise SystemExit(f"District names do not match. Missing {missing} extra {extra}")

    season_rain, forecast_days = open_meteo(points)
    week = forecast_days.groupby("district", as_index=False).agg(
        forecast_week_mm=("forecast_mm", "sum"),
        forecast_max_mm=("forecast_mm", "max"),
        forecast_days_with_rain=("forecast_mm", lambda values: int((values >= 1).sum())),
        et0_week_mm=("et0_mm", "sum"),
        etc_week_mm=("etc_mm", "sum"),
        pe_week_mm=("pe_mm", "sum"),
        water_balance_week_mm=("water_balance_mm", "sum"),
        temp_max_c=("temp_max_c", "max"),
        temp_min_c=("temp_min_c", "min"),
    )

    alerts = (
        water.merge(soil[["district", "concern_pct", "severe_pct", "protected_pct", "organic_pct", "inorganic_pct", "usual_yield_kg_ha"]], on="district")
        .merge(usual, on="district")
        .merge(season_rain, on="district")
        .merge(week, on="district")
        .merge(points[["district", "latitude", "longitude"]], on="district")
    )
    alerts["rain_difference_mm"] = alerts["rain_so_far_mm"] - alerts["usual_sep_oct_mm"]
    alerts["rain_difference_pct"] = 100 * alerts["rain_difference_mm"] / alerts["usual_sep_oct_mm"]
    ranked = alerts.apply(classify, axis=1, result_type="expand")
    ranked.columns = ["alert", "priority", "climate_class"]
    alerts = pd.concat([alerts, ranked], axis=1)
    alerts["year"] = YEAR
    alerts["season"] = SEASON
    alerts["fetched_on"] = TODAY.isoformat()

    alerts = alerts.sort_values(["priority", "rain_difference_pct"])
    alerts.to_csv(APP / "irrigation_alerts.csv", index=False)
    forecast_days.to_csv(APP / "forecast_7day.csv", index=False)
    print(alerts["alert"].value_counts().to_string())
    print(alerts["climate_class"].value_counts().to_string())
    print(
        alerts[
            [
                "district", "alert", "climate_class", "irrigated_pct", "rain_so_far_mm",
                "rain_difference_pct", "forecast_week_mm", "etc_week_mm", "water_balance_week_mm",
            ]
        ].round(1).to_string(index=False)
    )


if __name__ == "__main__":
    main()
