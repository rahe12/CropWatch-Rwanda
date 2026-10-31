"""District soil table for Season A 2022.

That is the last year where the questionnaire text still names these
questions, the answers are words, and the plot weight is on the file.
Season B is not added to Season A. A blank follow-up means the farmer
said the practice was not used on any plot, so this plot counts as no.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
APP = PROCESSED / "app"
YEAR = 2022
SEASON = "A"


def plot_answer(frame, this_col, any_col):
    """Yes or no on this plot. A skipped follow-up after 'no on any plot' is no."""
    this_word = frame[this_col].astype("string").str.strip().str.lower()
    any_plot = frame[any_col].astype("string").str.strip().str.lower()
    yes = this_word.eq("yes").fillna(False)
    no = this_word.eq("no").fillna(False) | (this_word.isna() & any_plot.eq("no").fillna(False))
    result = pd.Series(pd.NA, index=frame.index, dtype="boolean")
    result[no.to_numpy()] = False
    result[yes.to_numpy()] = True
    return result


def share(yes, weight):
    keep = yes.notna() & weight.notna() & (weight > 0)
    used = weight[keep]
    if used.sum() == 0:
        return 0.0, 0.0
    return float(weight[keep & yes.fillna(False)].sum()), float(used.sum())


def by_district(frame, yes, weight_name):
    rows = []
    for district, part in frame.groupby("district"):
        yes_weight, total_weight = share(yes.loc[part.index], part["plot_weight"])
        rows.append(
            {
                "district": district,
                f"{weight_name}_yes_weight": yes_weight,
                f"{weight_name}_weight": total_weight,
            }
        )
    return pd.DataFrame(rows)


def main():
    practice = pd.read_csv(
        PROCESSED / "sas" / "agricultural_practice.csv",
        usecols=["year", "season", "district", "district_pcode", "province", "plot_weight", "s4q1", "s4q2", "s4q3"],
        low_memory=False,
    )
    practice = practice[(practice["year"] == YEAR) & (practice["season"] == SEASON)].copy()
    practice["plot_weight"] = pd.to_numeric(practice["plot_weight"], errors="coerce")
    degree = practice["s4q1"].astype("string")
    known = degree.str.contains("Low|Moderate|Severe", case=False, na=False)
    if not known.all():
        raise SystemExit(f"Unexpected erosion labels: {degree[~known].unique()[:10]}")
    practice["concern"] = degree.str.contains("Moderate|Severe", case=False, na=False)
    practice["severe"] = degree.str.contains("Severe", case=False, na=False)
    practice["protected"] = plot_answer(practice, "s4q3", "s4q2")
    unanswered = practice["protected"].isna()
    print("Protection left blank", int(unanswered.sum()), "weight", float(practice.loc[unanswered, "plot_weight"].sum()))
    print("Season A 2022 plots", len(practice), "districts", practice["district"].nunique())
    print(practice["s4q1"].value_counts().to_string())
    print(pd.crosstab(practice["s4q2"].fillna("blank"), practice["s4q3"].fillna("blank")))

    fertilizer = pd.read_csv(
        PROCESSED / "sas" / "fertilizer.csv",
        usecols=["year", "season", "district", "plot_weight", "s3q1", "s3q3", "s3q5", "s3q7", "s3q9"],
        low_memory=False,
    )
    fertilizer = fertilizer[(fertilizer["year"] == YEAR) & (fertilizer["season"] == SEASON)].copy()
    fertilizer["plot_weight"] = pd.to_numeric(fertilizer["plot_weight"], errors="coerce")
    fertilizer["organic"] = plot_answer(fertilizer, "s3q3", "s3q1")
    fertilizer["inorganic"] = plot_answer(fertilizer, "s3q9", "s3q7")
    used_organic = fertilizer["organic"].fillna(False)
    enough_word = fertilizer["s3q5"].astype("string").str.strip().str.lower()
    fertilizer["organic_short"] = enough_word.eq("no").where(used_organic & enough_word.isin(["yes", "no"]))
    print("Fertilizer plots", len(fertilizer))
    print(pd.crosstab(fertilizer["s3q1"].fillna("blank"), fertilizer["s3q3"].fillna("blank")))

    place = (
        practice.groupby("district", as_index=False)
        .agg(district_pcode=("district_pcode", "first"), province=("province", "first"))
    )
    concern = by_district(practice, practice["concern"], "concern")
    severe = by_district(practice, practice["severe"], "severe")
    protected = by_district(practice, practice["protected"], "protected")
    organic = by_district(fertilizer, fertilizer["organic"], "organic")
    inorganic = by_district(fertilizer, fertilizer["inorganic"], "inorganic")
    short = by_district(fertilizer, fertilizer["organic_short"], "organic_short")
    soil = place.merge(concern, on="district").merge(severe, on="district").merge(protected, on="district")
    soil = soil.merge(organic, on="district").merge(inorganic, on="district").merge(short, on="district")
    soil["year"] = YEAR
    soil["season"] = SEASON

    watch = pd.read_csv(APP / "season_watch.csv")
    rain = watch[watch["season"] == "B"][
        ["district", "rain_mm", "usual_rain_mm", "rain_difference_pct", "usual_yield_kg_ha"]
    ]
    soil = soil.merge(rain, on="district", how="left")
    soil = soil.sort_values("district")
    if soil["district"].nunique() != 30:
        raise SystemExit(f"Expected 30 districts, got {soil['district'].nunique()}")
    if soil["rain_difference_pct"].isna().any():
        missing = soil.loc[soil["rain_difference_pct"].isna(), "district"].tolist()
        raise SystemExit(f"Rain is missing for {missing}")

    APP.mkdir(parents=True, exist_ok=True)
    soil.to_csv(APP / "soil_season_a_2022.csv", index=False)
    nyagatare = soil[soil["district"] == "Nyagatare"].iloc[0]
    print(
        "Nyagatare concern {:.1f}% severe {:.1f}% protected {:.1f}% organic {:.1f}% inorganic {:.1f}%".format(
            100 * nyagatare["concern_yes_weight"] / nyagatare["concern_weight"],
            100 * nyagatare["severe_yes_weight"] / nyagatare["severe_weight"],
            100 * nyagatare["protected_yes_weight"] / nyagatare["protected_weight"],
            100 * nyagatare["organic_yes_weight"] / nyagatare["organic_weight"],
            100 * nyagatare["inorganic_yes_weight"] / nyagatare["inorganic_weight"],
        )
    )
    print("Saved", len(soil), "districts")


if __name__ == "__main__":
    main()
