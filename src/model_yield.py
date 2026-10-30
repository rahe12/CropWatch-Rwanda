"""Maize yield models on every SAS season that can actually be joined.

Plot-level kg/ha needs production and harvested area (or a native yield) and
plot_weight. That rules out 2018–2019 (no plot_weight on the crop file), 2024
(no harvested area), and 2026 (published tables, not plots).

Native yield exists in 2022, 2023, and 2025. 2020–2021 use production / area.
Season rain is CHIRPS: A = Sep–Dec of the previous year + Jan–Feb; B = Mar–Jun.
NDRE is one district-year number, not a season.

s4q8/s4q11 are machines, not fertilizer. Fertilizer is s3q*.

Shuffled plot CV can leak place. The pooled model also reports a district-grouped
fold. Neither score is this season's harvest.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import shapefile
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GroupKFold, KFold

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
APP = PROCESSED / "app"
SOURCE = ROOT / "data" / "source"
SHAPE_ZIP = SOURCE / "rwa_adm_2006_nisr_wgs1984_20181002_shp.zip"
SHAPE_NAME = "rwa_adm2_2006_NISR_WGS1984_20181002"

KEYS = ["year", "season", "district", "segment_id", "s1q6", "plot_id"]
PLOT_FEATURES = [
    "irrigated",
    "organic",
    "organic_short",
    "inorganic",
    "protected",
    "erosion_moderate",
    "erosion_severe",
]
CONTEXT_FEATURES = ["rain_diff_pct", "vegetation_mean"]
ALL_FEATURES = PLOT_FEATURES + CONTEXT_FEATURES
SIM_YEAR = 2022
SIM_SEASON = "A"


def as_key(series):
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def plot_yes(frame, this_col, any_col):
    this_word = frame[this_col].astype("string").str.strip().str.lower()
    any_plot = frame[any_col].astype("string").str.strip().str.lower()
    yes = this_word.eq("yes").fillna(False)
    no = this_word.eq("no").fillna(False) | (this_word.isna() & any_plot.eq("no").fillna(False))
    result = pd.Series(pd.NA, index=frame.index, dtype="boolean")
    result[no.to_numpy()] = False
    result[yes.to_numpy()] = True
    return result


def scores(y_true, y_pred):
    return {
        "mae_kg_ha": round(float(mean_absolute_error(y_true, y_pred)), 1),
        "rmse_kg_ha": round(float(root_mean_squared_error(y_true, y_pred)), 1),
        "r2": round(float(r2_score(y_true, y_pred)), 3),
    }


def season_rain_table(rain, year, season):
    if season == "A":
        part = rain[
            ((rain["year"] == year - 1) & rain["month"].between(9, 12))
            | ((rain["year"] == year) & rain["month"].between(1, 2))
        ]
    else:
        part = rain[(rain["year"] == year) & rain["month"].between(3, 6)]
    out = part.groupby("district", as_index=False).agg(
        rain_mm=("rainfall_mm", "sum"),
        usual_rain_mm=("usual_mm", "sum"),
    )
    out["rain_diff_pct"] = 100 * (out["rain_mm"] - out["usual_rain_mm"]) / out["usual_rain_mm"]
    out["year"] = year
    out["season"] = season
    return out


def maize_yield(crop):
    crop = crop.copy()
    for column in ("production_kg", "harvested_area_ha", "yield_kg_per_ha", "plot_weight"):
        crop[column] = pd.to_numeric(crop[column], errors="coerce")
    native = crop["yield_kg_per_ha"].notna() & (crop["yield_kg_per_ha"] >= 0)
    computed = crop["production_kg"].notna() & crop["harvested_area_ha"].notna() & (crop["harvested_area_ha"] > 0)
    crop["yield_kg_ha"] = np.where(
        native,
        crop["yield_kg_per_ha"],
        np.where(computed, crop["production_kg"] / crop["harvested_area_ha"], np.nan),
    )
    crop["yield_source"] = np.where(native, "native", np.where(computed, "production_over_area", "none"))
    return crop


def load_joined_plots():
    crop = pd.read_csv(
        PROCESSED / "sas" / "crop_production.csv",
        usecols=KEYS + ["plot_weight", "crop_name", "production_kg", "harvested_area_ha", "yield_kg_per_ha"],
        low_memory=False,
    )
    crop = crop[(crop["crop_name"] == "Maize") & crop["season"].isin(["A", "B"])].copy()
    crop = maize_yield(crop)
    crop = crop.dropna(subset=["yield_kg_ha", "plot_weight", "district"])
    crop = crop[(crop["plot_weight"] > 0) & (crop["yield_kg_ha"] >= 0)]

    practice = pd.read_csv(
        PROCESSED / "sas" / "agricultural_practice.csv",
        usecols=KEYS + ["s4q1", "s4q2", "s4q3", "s4q14", "s4q15"],
        low_memory=False,
    )
    practice = practice[practice["season"].isin(["A", "B"])].copy()
    degree = practice["s4q1"].astype("string")
    practice["erosion_moderate"] = degree.str.contains("Moderate", case=False, na=False).astype(int)
    practice["erosion_severe"] = degree.str.contains("Severe", case=False, na=False).astype(int)
    practice["protected"] = plot_yes(practice, "s4q3", "s4q2").astype("boolean")
    practice["irrigated"] = plot_yes(practice, "s4q15", "s4q14").astype("boolean")

    fertilizer = pd.read_csv(
        PROCESSED / "sas" / "fertilizer.csv",
        usecols=KEYS + ["s3q1", "s3q3", "s3q5", "s3q7", "s3q9"],
        low_memory=False,
    )
    fertilizer = fertilizer[fertilizer["season"].isin(["A", "B"])].copy()
    fertilizer["organic"] = plot_yes(fertilizer, "s3q3", "s3q1").astype("boolean")
    fertilizer["inorganic"] = plot_yes(fertilizer, "s3q9", "s3q7").astype("boolean")
    enough = fertilizer["s3q5"].astype("string").str.strip().str.lower()
    fertilizer["organic_short"] = pd.Series(pd.NA, index=fertilizer.index, dtype="boolean")
    fertilizer.loc[enough.eq("no"), "organic_short"] = True
    fertilizer.loc[enough.eq("yes"), "organic_short"] = False
    fertilizer.loc[fertilizer["organic"].eq(False), "organic_short"] = False

    for frame in (crop, practice, fertilizer):
        for column in KEYS:
            frame[column] = as_key(frame[column])

    plots = crop.merge(
        practice[KEYS + ["irrigated", "protected", "erosion_moderate", "erosion_severe"]],
        on=KEYS,
        how="inner",
    ).merge(
        fertilizer[KEYS + ["organic", "organic_short", "inorganic"]],
        on=KEYS,
        how="inner",
    )
    for column in PLOT_FEATURES:
        plots = plots[plots[column].notna()].copy()
        plots[column] = plots[column].astype(int)

    rain = pd.read_csv(PROCESSED / "rainfall" / "district_month_anomaly.csv")
    veg = pd.read_csv(PROCESSED / "vegetation" / "district_year.csv")
    rain_parts = []
    for year, season in plots[["year", "season"]].drop_duplicates().itertuples(index=False):
        rain_parts.append(season_rain_table(rain, int(year), season))
    rain_season = pd.concat(rain_parts, ignore_index=True)
    plots["year"] = plots["year"].astype(int)
    plots = plots.merge(rain_season[["year", "season", "district", "rain_diff_pct"]], on=["year", "season", "district"], how="left")
    plots = plots.merge(veg.rename(columns={"vegetation_mean": "vegetation_mean"}), on=["district", "year"], how="left")
    plots = plots.dropna(subset=["yield_kg_ha", "rain_diff_pct", "vegetation_mean"])
    return plots


def trim_yield(plots):
    low, high = plots["yield_kg_ha"].quantile([0.01, 0.99])
    kept = plots[(plots["yield_kg_ha"] >= low) & (plots["yield_kg_ha"] <= high)].copy()
    return kept, float(low), float(high)


def cross_validate(plots, folds=5, grouped=False, forest_trees=160, use_boost=True):
    y = plots["yield_kg_ha"].to_numpy()
    weights = plots["plot_weight"].to_numpy()
    X = plots[ALL_FEATURES]
    X_rain = plots[["rain_diff_pct"]]
    districts = plots["district"].to_numpy()
    rain_hat = np.zeros(len(plots))
    dist_hat = np.zeros(len(plots))
    rf_hat = np.zeros(len(plots))
    gb_hat = np.zeros(len(plots)) if use_boost else None

    if grouped:
        splitter = GroupKFold(n_splits=min(folds, plots["district"].nunique()))
        split_iter = splitter.split(X, y, groups=districts)
    else:
        splitter = KFold(n_splits=folds, shuffle=True, random_state=42)
        split_iter = splitter.split(X)

    for train_idx, test_idx in split_iter:
        y_train = y[train_idx]
        w_train = weights[train_idx]
        rain_model = LinearRegression()
        rain_model.fit(X_rain.iloc[train_idx], y_train, sample_weight=w_train)
        rain_hat[test_idx] = rain_model.predict(X_rain.iloc[test_idx])

        train_districts = pd.DataFrame({"district": districts[train_idx], "yield_kg_ha": y_train, "w": w_train})
        dist_means = train_districts.groupby("district").apply(
            lambda part: np.average(part["yield_kg_ha"], weights=part["w"]),
            include_groups=False,
        )
        global_mean = float(np.average(y_train, weights=w_train))
        dist_hat[test_idx] = pd.Series(districts[test_idx]).map(dist_means).fillna(global_mean).to_numpy()

        forest = RandomForestRegressor(
            n_estimators=forest_trees,
            max_depth=6,
            min_samples_leaf=40,
            random_state=42,
            n_jobs=-1,
        )
        forest.fit(X.iloc[train_idx], y_train, sample_weight=w_train)
        rf_hat[test_idx] = forest.predict(X.iloc[test_idx])

        if use_boost:
            boost = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.05,
                random_state=42,
            )
            boost.fit(X.iloc[train_idx], y_train, sample_weight=w_train)
            gb_hat[test_idx] = boost.predict(X.iloc[test_idx])

    out = {"rain": scores(y, rain_hat), "district": scores(y, dist_hat), "forest": scores(y, rf_hat)}
    if use_boost:
        out["boost"] = scores(y, gb_hat)
    return out


def fit_effects(plots):
    demeaned = plots.copy()
    for column in PLOT_FEATURES + ["yield_kg_ha"]:
        demeaned[column] = plots[column] - plots.groupby("district")[column].transform("mean")
    model = LinearRegression()
    model.fit(demeaned[PLOT_FEATURES], demeaned["yield_kg_ha"], sample_weight=plots["plot_weight"])
    return {name: float(coef) for name, coef in zip(PLOT_FEATURES, model.coef_)}


def district_panel(crop, rain, veg):
    maize = maize_yield(crop)
    maize = maize[maize["season"].isin(["A", "B"])].copy()
    maize = maize.dropna(subset=["yield_kg_ha", "plot_weight", "district"])
    maize = maize[(maize["plot_weight"] > 0) & (maize["harvested_area_ha"].fillna(0) > 0)]
    maize["year"] = maize["year"].astype(int)
    maize["weighted"] = maize["yield_kg_ha"] * maize["plot_weight"]
    by = maize.groupby(["year", "season", "district"], as_index=False).agg(
        weighted=("weighted", "sum"),
        weight=("plot_weight", "sum"),
        n=("yield_kg_ha", "size"),
    )
    by["yield_kg_ha"] = by["weighted"] / by["weight"]
    rain_parts = [season_rain_table(rain, int(year), season) for year, season in by[["year", "season"]].drop_duplicates().itertuples(index=False)]
    rain_season = pd.concat(rain_parts, ignore_index=True)
    panel = by.merge(rain_season, on=["year", "season", "district"], how="left")
    panel = panel.merge(veg, on=["district", "year"], how="left")
    panel = panel.dropna(subset=["yield_kg_ha", "rain_diff_pct", "vegetation_mean"])
    years = sorted(panel["year"].unique())
    y = panel["yield_kg_ha"].to_numpy()
    rain_hat = np.full(len(panel), np.nan)
    rf_hat = np.full(len(panel), np.nan)
    X = panel[["rain_diff_pct", "vegetation_mean"]]
    for held in years:
        train = panel["year"] != held
        test = panel["year"] == held
        if train.sum() < 30 or test.sum() < 5:
            continue
        lin = LinearRegression()
        lin.fit(panel.loc[train, ["rain_diff_pct"]], panel.loc[train, "yield_kg_ha"])
        rain_hat[test.to_numpy()] = lin.predict(panel.loc[test, ["rain_diff_pct"]])
        forest = RandomForestRegressor(n_estimators=120, max_depth=4, min_samples_leaf=8, random_state=42, n_jobs=-1)
        forest.fit(X.loc[train], panel.loc[train, "yield_kg_ha"])
        rf_hat[test.to_numpy()] = forest.predict(X.loc[test])
    mask = np.isfinite(rain_hat) & np.isfinite(rf_hat)
    return panel, {
        "n_district_seasons": int(len(panel)),
        "years": [int(v) for v in years],
        "validation": "Leave-one-year-out at district-season level. Rain and NDRE only. No plot practices.",
        "rain": scores(y[mask], rain_hat[mask]) if mask.any() else {},
        "forest": scores(y[mask], rf_hat[mask]) if mask.any() else {},
        "note": "This is a district-year panel, not a plot model. It tests whether rain and NDRE travel to a year the model did not train on.",
    }


def coverage_table():
    return [
        {"year": 2018, "season": "A/B", "status": "skip", "reason": "Crop file has no plot_weight. 2018 area is m2 converted to ha in preparation. Practice file is not in 2018."},
        {"year": 2019, "season": "A/B", "status": "skip", "reason": "Crop file has no plot_weight. Practice and fertilizer lack s1q6, so the plot join key is incomplete."},
        {"year": 2020, "season": "A/B", "status": "district-panel", "reason": "Yield = production / harvested area and plot_weight exists, but s4q15 is empty in 2020 so the irrigation flag is missing and the plot join drops. District maize means still enter the leave-one-year-out rain+NDRE panel."},
        {"year": 2021, "season": "A/B", "status": "district-panel", "reason": "Yield = production / harvested area and plot_weight exists, but the practice/fertilizer join does not keep complete irrigation flags. District maize means still enter the leave-one-year-out rain+NDRE panel."},
        {"year": 2022, "season": "A/B", "status": "plot", "reason": "Native yield on the crop file. Season A is the questionnaire year used for the what-if sliders."},
        {"year": 2023, "season": "A/B", "status": "plot", "reason": "Native yield on the crop file."},
        {"year": 2024, "season": "A/B", "status": "skip", "reason": "No harvested area and no native yield, so kg/ha cannot be formed."},
        {"year": 2025, "season": "A/B", "status": "plot", "reason": "Native yield on the crop file."},
        {"year": 2026, "season": "A/B", "status": "skip", "reason": "SAS 2026 arrived as published tables, not plot files."},
    ]


def thin_ring(coords, step=8):
    if len(coords) <= 40:
        return coords
    out = coords[::step]
    if out[-1] != coords[-1]:
        out.append(coords[-1])
    return out


def thin_geometry(geom):
    kind = geom.get("type")
    if kind == "Polygon":
        return {"type": "Polygon", "coordinates": [thin_ring(ring) for ring in geom["coordinates"]]}
    if kind == "MultiPolygon":
        return {
            "type": "MultiPolygon",
            "coordinates": [[thin_ring(ring) for ring in poly] for poly in geom["coordinates"]],
        }
    return geom


def export_geojson():
    with zipfile.ZipFile(SHAPE_ZIP) as zipped:
        reader = shapefile.Reader(
            shp=io.BytesIO(zipped.read(f"{SHAPE_NAME}.shp")),
            shx=io.BytesIO(zipped.read(f"{SHAPE_NAME}.shx")),
            dbf=io.BytesIO(zipped.read(f"{SHAPE_NAME}.dbf")),
        )
        fields = [field[0] for field in reader.fields[1:]]
        features = []
        for shape_record in reader.shapeRecords():
            record = dict(zip(fields, shape_record.record))
            features.append(
                {
                    "type": "Feature",
                    "properties": {"district": record["ADM2_EN"], "district_pcode": record["ADM2_PCODE"]},
                    "geometry": thin_geometry(shape_record.shape.__geo_interface__),
                }
            )
    collection = {"type": "FeatureCollection", "features": features}
    path = APP / "districts.geojson"
    path.write_text(json.dumps(collection), encoding="utf-8")
    print("GeoJSON districts", len(features), "bytes", path.stat().st_size)
    return path


def verdict(name, result, district):
    if name == "district":
        return "Training-fold district mean. Strong because soils and rain cluster by place."
    if result["rmse_kg_ha"] >= district["rmse_kg_ha"]:
        return "Does not beat the district mean on held-out plots. Not used as a harvest forecast."
    return "Beats the district mean on held-out plots. Still an association, not this season's harvest."


def main():
    APP.mkdir(parents=True, exist_ok=True)
    plots = load_joined_plots()
    print("Joined maize plots", len(plots), "year-seasons", plots.groupby(["year", "season"]).size().to_dict())

    slices = []
    for (year, season), part in plots.groupby(["year", "season"]):
        raw_n = int(len(part))
        kept, low, high = trim_yield(part)
        if len(kept) < 400:
            slices.append({
                "year": int(year),
                "season": season,
                "n_joined": raw_n,
                "n_model": int(len(kept)),
                "skipped": "Fewer than 400 plots after the 1–99 yield window.",
            })
            continue
        print("CV", year, season, "n", len(kept))
        cv = cross_validate(kept, folds=3, forest_trees=120, use_boost=False)
        effects = fit_effects(kept)
        slices.append({
            "year": int(year),
            "season": season,
            "n_joined": raw_n,
            "n_model": int(len(kept)),
            "n_districts": int(kept["district"].nunique()),
            "yield_source": str(kept["yield_source"].mode().iloc[0]),
            "mean_yield_kg_ha": round(float(np.average(kept["yield_kg_ha"], weights=kept["plot_weight"])), 1),
            "rain": cv["rain"],
            "district": cv["district"],
            "forest": cv["forest"],
            "forest_beats_district": cv["forest"]["rmse_kg_ha"] < cv["district"]["rmse_kg_ha"],
            "within_district_kg_ha": {name: round(value, 1) for name, value in effects.items()},
            "yield_window_kg_ha": [round(low, 1), round(high, 1)],
        })

    pooled, plow, phigh = trim_yield(plots)
    print("Pooled n", len(pooled))
    cv_pool = cross_validate(pooled, folds=5, grouped=False, forest_trees=160, use_boost=True)
    cv_group = cross_validate(pooled, folds=5, grouped=True, forest_trees=120, use_boost=False)
    forest = RandomForestRegressor(n_estimators=200, max_depth=6, min_samples_leaf=40, random_state=42, n_jobs=-1)
    forest.fit(pooled[ALL_FEATURES], pooled["yield_kg_ha"], sample_weight=pooled["plot_weight"])
    importances = {
        name: round(float(value), 4)
        for name, value in sorted(zip(ALL_FEATURES, forest.feature_importances_), key=lambda item: -item[1])
    }

    sim_part = plots[(plots["year"] == SIM_YEAR) & (plots["season"] == SIM_SEASON)]
    sim_kept, slow, shigh = trim_yield(sim_part)
    cv_sim = cross_validate(sim_kept, folds=5, forest_trees=200, use_boost=True)
    effects = fit_effects(sim_kept)
    print("Simulator year-season", SIM_YEAR, SIM_SEASON, "n", len(sim_kept))
    for name, value in effects.items():
        print(f"  {name:20s} {value:8.1f}")

    crop_all = pd.read_csv(
        PROCESSED / "sas" / "crop_production.csv",
        usecols=["year", "season", "district", "plot_weight", "crop_name", "production_kg", "harvested_area_ha", "yield_kg_per_ha"],
        low_memory=False,
    )
    crop_all = crop_all[crop_all["crop_name"] == "Maize"]
    rain = pd.read_csv(PROCESSED / "rainfall" / "district_month_anomaly.csv")
    veg = pd.read_csv(PROCESSED / "vegetation" / "district_year.csv")
    _panel, panel_scores = district_panel(crop_all, rain, veg)
    print("District panel", panel_scores)

    district = cv_sim["district"]
    benchmark = {
        "level": "plot",
        "crop": "Maize",
        "year": SIM_YEAR,
        "season": SIM_SEASON,
        "n_plots_joined": int(len(sim_part)),
        "n_plots_model": int(len(sim_kept)),
        "n_districts": int(sim_kept["district"].nunique()),
        "yield_window_kg_ha": [round(slow, 1), round(shigh, 1)],
        "validation": "5-fold shuffled plots on Season A 2022. District mean uses only the training fold. Sample weight is plot_weight.",
        "columns": {
            "erosion_irrigation": "agricultural_practice s4q1 s4q2 s4q3 s4q14 s4q15",
            "fertilizer": "fertilizer s3q1 s3q3 s3q5 s3q7 s3q9 (not s4q8/s4q11; those are machines)",
            "rain": "CHIRPS Season A = Sep–Dec previous year + Jan–Feb; Season B = Mar–Jun; usual is 2018–2025",
            "vegetation": "Sentinel NDRE district mean for the interview year",
        },
        "models": [
            {"name": "Naive rain-only linear", "key": "rain", **cv_sim["rain"], "verdict": verdict("rain", cv_sim["rain"], district)},
            {"name": "Historical district mean", "key": "district", **cv_sim["district"], "verdict": verdict("district", cv_sim["district"], district)},
            {"name": "Multi-factor random forest", "key": "forest", **cv_sim["forest"], "verdict": verdict("forest", cv_sim["forest"], district)},
            {"name": "Multi-factor gradient boosting", "key": "boost", **cv_sim["boost"], "verdict": verdict("boost", cv_sim["boost"], district)},
        ],
        "feature_importances": importances,
        "within_district_kg_ha": {name: round(value, 1) for name, value in effects.items()},
        "note": "What-if kg/ha come from Season A 2022 within-district OLS. Other years are scored in slices and in the pooled table. None of these is a 2026 harvest.",
        "coverage": coverage_table(),
        "slices": slices,
        "pooled": {
            "n_plots_model": int(len(pooled)),
            "years": sorted(int(v) for v in pooled["year"].unique()),
            "seasons": sorted(pooled["season"].unique()),
            "yield_window_kg_ha": [round(plow, 1), round(phigh, 1)],
            "shuffled": cv_pool,
            "grouped_by_district": cv_group,
            "feature_importances": importances,
            "note": "Grouped CV holds out whole districts. If the forest loses here, plot practices are not travelling cleanly to new places.",
        },
        "district_panel": panel_scores,
    }
    (APP / "model_benchmark.json").write_text(json.dumps(benchmark, indent=2), encoding="utf-8")
    pd.DataFrame(slices).to_csv(APP / "model_slices.csv", index=False)

    alerts = pd.read_csv(APP / "irrigation_alerts.csv")
    sim = alerts[
        [
            "district",
            "irrigated_pct",
            "organic_pct",
            "inorganic_pct",
            "protected_pct",
            "concern_pct",
            "usual_yield_kg_ha",
            "rain_so_far_mm",
            "rain_difference_pct",
            "forecast_week_mm",
            "alert",
        ]
    ].copy()
    soil = pd.read_csv(APP / "soil_season_a_2022.csv")
    soil["organic_short_pct"] = 100 * soil["organic_short_yes_weight"] / soil["organic_short_weight"]
    sim = sim.merge(soil[["district", "organic_short_pct"]], on="district", how="left")
    sim["effect_irrigated_kg_ha"] = effects["irrigated"]
    sim["effect_organic_kg_ha"] = effects["organic"]
    sim["effect_organic_short_kg_ha"] = effects["organic_short"]
    sim["effect_protected_kg_ha"] = effects["protected"]
    sim.to_csv(APP / "district_simulation_base.csv", index=False)
    export_geojson()
    print("Saved", APP / "model_benchmark.json")
    print(json.dumps(benchmark["models"], indent=2))


if __name__ == "__main__":
    main()
