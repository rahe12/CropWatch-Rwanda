"""Small tables for the season watch page.

Usual maize yield is the survey average for a district and a season.
Rain for a season is the sum of the growing months.
The maize price is the latest retail price in kilograms.
Exports are maize grain lines, and the World total is left out.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
APP = PROCESSED / "app"

YIELD_YEARS = [2020, 2021, 2022, 2023, 2025]


def usual_maize():
    columns = ["year", "season", "district", "district_pcode", "province", "crop_name", "production_kg", "harvested_area_ha", "plot_weight"]
    crop = pd.read_csv(PROCESSED / "sas" / "crop_production.csv", usecols=columns)
    maize = crop[(crop["crop_name"] == "Maize") & (crop["season"].isin(["A", "B"]))].copy()
    for column in ("production_kg", "harvested_area_ha", "plot_weight"):
        maize[column] = pd.to_numeric(maize[column], errors="coerce")
    maize = maize[maize["year"].isin(YIELD_YEARS)]
    maize = maize.dropna(subset=["production_kg", "harvested_area_ha", "plot_weight", "district"])
    maize = maize[(maize["harvested_area_ha"] > 0) & (maize["plot_weight"] > 0) & (maize["production_kg"] >= 0)]
    maize["yield_kg_ha"] = maize["production_kg"] / maize["harvested_area_ha"]
    maize["weighted_yield"] = maize["yield_kg_ha"] * maize["plot_weight"]
    by_year = maize.groupby(["year", "season", "district", "district_pcode", "province"], as_index=False).agg(
        weighted_yield=("weighted_yield", "sum"),
        weight=("plot_weight", "sum"),
    )
    by_year["yield_kg_ha"] = by_year["weighted_yield"] / by_year["weight"]
    usual = by_year.groupby(["season", "district", "district_pcode", "province"], as_index=False).agg(
        usual_yield_kg_ha=("yield_kg_ha", "mean"),
        years=("year", "nunique"),
    )
    usual["yield_years"] = "2020, 2021, 2022, 2023, 2025"
    usual["crop"] = "Maize"
    print("Usual maize rows", len(usual))
    print(by_year.groupby("year")["yield_kg_ha"].median().round(0).to_string())
    return usual


def season_rain(rain, season, year):
    if season == "A":
        months = rain[
            ((rain["year"] == year - 1) & (rain["month"].between(9, 12)))
            | ((rain["year"] == year) & (rain["month"].between(1, 2)))
        ]
        needed = 6
    else:
        months = rain[(rain["year"] == year) & (rain["month"].between(3, 6))]
        needed = 4
    grouped = months.groupby(["district", "district_pcode", "province"], as_index=False).agg(
        rain_mm=("rainfall_mm", "sum"),
        usual_rain_mm=("usual_mm", "sum"),
        months=("month", "nunique"),
    )
    grouped = grouped[grouped["months"] == needed].drop(columns=["months"])
    grouped["season"] = season
    grouped["season_year"] = year
    grouped["rain_difference_mm"] = grouped["rain_mm"] - grouped["usual_rain_mm"]
    grouped["rain_difference_pct"] = grouped["rain_difference_mm"] / grouped["usual_rain_mm"] * 100
    return grouped


def maize_prices():
    prices = pd.read_csv(
        PROCESSED / "prices" / "market_prices.csv",
        usecols=["date", "commodity", "unit", "pricetype", "price", "district", "market"],
    )
    maize = prices[(prices["commodity"] == "Maize") & (prices["unit"] == "KG") & (prices["pricetype"] == "Retail")].copy()
    maize["date"] = pd.to_datetime(maize["date"])
    maize["price"] = pd.to_numeric(maize["price"], errors="coerce")
    maize = maize.dropna(subset=["price", "district"])
    latest_date = maize.groupby("district")["date"].transform("max")
    recent = maize[maize["date"] == latest_date]
    by_district = recent.groupby(["district", "date"], as_index=False).agg(
        maize_price_rwf_per_kg=("price", "median"),
        markets=("market", "nunique"),
    )
    by_district["price_date"] = by_district["date"].dt.date.astype(str)
    by_district = by_district.drop(columns=["date"])
    print("Maize prices in", len(by_district), "districts. Newest date", by_district["price_date"].max())
    return by_district


def maize_exports():
    trade = pd.read_csv(
        PROCESSED / "trade" / "exports_by_partner.csv",
        usecols=["year", "partner", "commodity_code", "trade_value_usd"],
        dtype={"commodity_code": str},
    )
    maize = trade[trade["commodity_code"].str.startswith("1005")].copy()
    maize = maize[~maize["partner"].str.lower().isin(["world"])]
    maize["trade_value_usd"] = pd.to_numeric(maize["trade_value_usd"], errors="coerce")
    maize["year"] = pd.to_numeric(maize["year"], errors="coerce")
    by_year = maize.groupby("year", as_index=False)["trade_value_usd"].sum()
    by_year["partner"] = "All partners except World"
    latest_year = int(maize["year"].max())
    partners = (
        maize[maize["year"] == latest_year]
        .groupby("partner", as_index=False)["trade_value_usd"]
        .sum()
        .sort_values("trade_value_usd", ascending=False)
    )
    partners["year"] = latest_year
    print("Maize export years", sorted(by_year["year"].astype(int)))
    print(partners.head(5).to_string(index=False))
    return by_year, partners


def main():
    APP.mkdir(parents=True, exist_ok=True)
    usual = usual_maize()
    rain = pd.read_csv(PROCESSED / "rainfall" / "district_month_anomaly.csv")
    seasons = pd.concat(
        [season_rain(rain, "A", 2026), season_rain(rain, "B", 2026)],
        ignore_index=True,
    )
    watch = seasons.merge(usual, on=["district", "district_pcode", "province", "season"], how="left")
    prices = maize_prices()
    watch = watch.merge(prices, on="district", how="left")
    vegetation = pd.read_csv(PROCESSED / "vegetation" / "district_year.csv")
    past = vegetation[vegetation["year"].between(2018, 2025)].groupby("district", as_index=False)["vegetation_mean"].mean()
    past = past.rename(columns={"vegetation_mean": "usual_vegetation"})
    this_year = vegetation[vegetation["year"] == 2026][["district", "vegetation_mean"]].rename(
        columns={"vegetation_mean": "vegetation_2026"}
    )
    watch = watch.merge(past, on="district", how="left").merge(this_year, on="district", how="left")
    watch.to_csv(APP / "season_watch.csv", index=False)
    year_exports, partner_exports = maize_exports()
    year_exports.to_csv(APP / "maize_exports_by_year.csv", index=False)
    partner_exports.to_csv(APP / "maize_exports_partners.csv", index=False)
    print("Watch rows", len(watch), "districts", watch["district"].nunique())


if __name__ == "__main__":
    main()
