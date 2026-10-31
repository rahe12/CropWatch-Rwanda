"""Second preparation step.

The survey files are already cleaned. This step keeps the new files that arrived
after that, drops the heavy map shapes we do not need, and compares each month's
rain with the usual rain for that month.
"""

import csv
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source"
PROCESSED = ROOT / "data" / "processed"
LOOKUPS = PROCESSED / "lookups"
csv.field_size_limit(50_000_000)

TRADE_COLUMNS = {
    "refYear": "year",
    "reporterISO": "reporter_iso",
    "reporterDesc": "reporter",
    "flowDesc": "flow",
    "partnerISO": "partner_iso",
    "partnerDesc": "partner",
    "cmdCode": "commodity_code",
    "cmdDesc": "commodity",
    "qtyUnitAbbr": "quantity_unit",
    "qty": "quantity",
    "netWgt": "net_weight_kg",
    "primaryValue": "trade_value_usd",
}


def slim_vegetation():
    path = SOURCE / "rwanda_ndre_30_districts_2018_2026.csv"
    out_dir = PROCESSED / "vegetation"
    saved = out_dir / "district_year.csv"
    if not path.exists():
        if saved.exists():
            print(f"Vegetation is already saved in {saved.name}. The large download was removed.")
            return
        raise SystemExit("The district vegetation file is not in data/source, and no saved table was found.")
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "province": row["ADM1_NAME"],
                    "district": row["ADM2_NAME"],
                    "district_code": row["ADM2_CODE"],
                    "year": int(row["Year"]),
                    "vegetation_mean": float(row["mean"]),
                }
            )
    table = pd.DataFrame(rows).drop(columns=["province"])
    districts = pd.read_csv(LOOKUPS / "districts.csv")
    known = set(districts["district"])
    missing = sorted(set(table["district"]) - known)
    if missing or table["district"].nunique() != 30:
        raise SystemExit(f"Vegetation districts do not match the 30 districts: {missing}")
    out = PROCESSED / "vegetation"
    out.mkdir(parents=True, exist_ok=True)
    table = table.merge(districts[["district", "district_pcode", "province"]], on="district", how="left")
    table.to_csv(out / "district_year.csv", index=False)
    # The source file is large because each row carries a map shape. The numbers are kept above.
    path.unlink()
    province_file = SOURCE / "rwanda_ndre_2018_2025.csv"
    if province_file.exists():
        province_file.unlink()
    print(f"Vegetation: {len(table)} district-years, {table['year'].min()}-{table['year'].max()}")


def clean_calendar():
    book = openpyxl.load_workbook(SOURCE / "Crop_Calendar_Data_All.xlsx", read_only=True, data_only=True)
    sheet = book.active
    lines = sheet.iter_rows(values_only=True)
    next(lines)
    next(lines)
    rows = []
    for row in lines:
        if not row or row[0] != "Rwanda":
            continue
        rows.append(
            {
                "fao_crop": row[1],
                "zone": row[2],
                "early_sowing_day": row[4],
                "early_sowing_month": row[5],
                "late_sowing_day": row[6],
                "late_sowing_month": row[7],
                "all_year": row[8],
                "sowing_rate": row[9],
                "sowing_rate_unit": row[10],
                "growing_period": row[11],
                "growing_period_unit": row[12],
                "early_harvest_day": row[13],
                "early_harvest_month": row[14],
                "late_harvest_day": row[15],
                "late_harvest_month": row[16],
                "source": "FAO crop calendar, Rwanda agroecological zones",
            }
        )
    table = pd.DataFrame(rows)
    if table.empty:
        raise SystemExit("The crop calendar has no Rwanda rows.")
    table.to_csv(LOOKUPS / "crop_calendar_zones.csv", index=False)
    print(f"Calendar: {len(table)} rows, {table['fao_crop'].nunique()} crops, {table['zone'].nunique()} zones")


def stack_trade():
    frames = []
    for path in sorted(SOURCE.glob("TradeData_*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            frame = pd.DataFrame(list(reader))
        keep = frame.rename(columns=TRADE_COLUMNS)[list(TRADE_COLUMNS.values())]
        frames.append(keep)
        print(path.name, "rows", len(keep), "year", sorted(keep["year"].unique()))
    fresh = pd.concat(frames, ignore_index=True)
    old_path = PROCESSED / "trade" / "exports_by_partner.csv"
    old = pd.read_csv(old_path, dtype=str)
    year_2023 = old[old["year"] == "2023"].copy()
    if year_2023.empty:
        raise SystemExit("2023 exports are missing from the earlier trade file.")
    if "2023" in set(fresh["year"].astype(str)):
        raise SystemExit("2023 is in a new trade file and in the old file.")
    combined = pd.concat([fresh, year_2023[list(TRADE_COLUMNS.values())]], ignore_index=True)
    combined["year"] = combined["year"].astype(int)
    counts = combined.groupby("year").size()
    print(counts.to_string())
    combined.to_csv(old_path, index=False)
    print(f"Trade rows: {len(combined)}")


def rain_anomaly():
    rain = pd.read_csv(PROCESSED / "rainfall" / "district_month.csv")
    usual_years = rain[rain["year"].between(2018, 2025)]
    usual = (
        usual_years.groupby(["district", "month"], as_index=False)["rainfall_mm"]
        .mean()
        .rename(columns={"rainfall_mm": "usual_mm"})
    )
    out = rain.merge(usual, on=["district", "month"], how="left")
    out["difference_mm"] = out["rainfall_mm"] - out["usual_mm"]
    out["difference_pct"] = (out["difference_mm"] / out["usual_mm"] * 100).where(out["usual_mm"] > 0)
    out["usual_years"] = "2018-2025"
    keep = [
        "district",
        "district_pcode",
        "province",
        "year",
        "month",
        "rainfall_mm",
        "usual_mm",
        "difference_mm",
        "difference_pct",
        "usual_years",
    ]
    table = out[keep].sort_values(["district", "year", "month"])
    table.to_csv(PROCESSED / "rainfall" / "district_month_anomaly.csv", index=False)
    print(f"Rain rows: {len(table)}. Usual month is the average of 2018 to 2025.")


def main():
    slim_vegetation()
    clean_calendar()
    stack_trade()
    rain_anomaly()


if __name__ == "__main__":
    main()
