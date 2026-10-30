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
            "daily": "precipitation_sum",
            "timezone": "Africa/Kigali",
        }
    )
    forecast_query = urlencode(
        {
            "latitude": lats,
            "longitude": lons,
            "daily": "precipitation_sum,precipitation_probability_max",
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
        rain_so_far = float(pd.Series(past["precipitation_sum"], dtype="float").sum())
        season_rows.append(
            {
                "district": point["district"],
                "rain_so_far_mm": rain_so_far,
                "season_start": SEASON_START.isoformat(),
                "season_until": ARCHIVE_END.isoformat(),
                "rain_source": "Open-Meteo archive",
            }
        )
        future = forecast[index]["daily"]
        for day, amount, chance in zip(
            future["time"],
            future["precipitation_sum"],
            future["precipitation_probability_max"],
        ):
            day_rows.append(
                {
                    "district": point["district"],
                    "date": day,
                    "forecast_mm": amount,
                    "rain_chance_pct": chance,
                }
            )
    return pd.DataFrame(season_rows), pd.DataFrame(day_rows)


def classify(row):
    dry = row["rain_difference_pct"] <= -10
    wet_week = row["forecast_max_mm"] >= 15
    dry_week = row["forecast_week_mm"] < 10
    low_irrigation = row["irrigated_pct"] < 10
    soil_open = (row["concern_pct"] >= 20) and (row["protected_pct"] < 80)

    if dry and low_irrigation and dry_week:
        return "irrigate_now", 1
    if dry and low_irrigation:
        return "irrigation_gap", 2
    if wet_week and soil_open:
        return "soil_rain", 3
    if dry:
        return "dry_watch", 4
    if soil_open:
        return "soil_watch", 5
    return "stable", 6


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
    ranked.columns = ["alert", "priority"]
    alerts = pd.concat([alerts, ranked], axis=1)
    alerts["year"] = YEAR
    alerts["season"] = SEASON
    alerts["fetched_on"] = TODAY.isoformat()

    alerts = alerts.sort_values(["priority", "rain_difference_pct"])
    alerts.to_csv(APP / "irrigation_alerts.csv", index=False)
    forecast_days.to_csv(APP / "forecast_7day.csv", index=False)
    print(alerts["alert"].value_counts().to_string())
    print(alerts[["district", "alert", "irrigated_pct", "rain_so_far_mm", "usual_sep_oct_mm", "rain_difference_pct", "forecast_week_mm"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
