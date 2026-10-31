"""Match survey crop names to market price names.

We only mark a pair as safe when it is the same product.
Flour, fresh food, and shelled nuts stay on their own rows.
Kinyarwanda names are the everyday farming names, written next to the English survey name.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
LOOKUPS = PROCESSED / "lookups"
APP_TABLES = PROCESSED / "app"

# survey name, Kinyarwanda, price name, price id, product form, HS heading
# These pairs are the same product. The price id comes from the price file.
SAFE = [
    ("Maize", "Ibigori", "Maize", 51, "grain", "1005"),
    ("Bush bean", "Ibishyimbo byo hasi", "Beans (dry)", 262, "dry beans", "0713"),
    ("Climbing bean", "Ibishyimbo byo kuzamuka", "Beans (dry)", 262, "dry beans", "0713"),
    ("French bean", "Ibishyimbo byo kurya", "Beans (green, fresh)", 458, "fresh beans", "0708"),
    ("French beans", "Ibishyimbo byo kurya", "Beans (green, fresh)", 458, "fresh beans", "0708"),
    ("Soybean", "Soya", "Soybeans", 248, "grain", "1201"),
    ("Sorghum", "Amasaka", "Sorghum", 65, "grain", "1007"),
    ("Wheat", "Ingano", "Wheat", 84, "grain", "1001"),
    ("Cassava", "Imyumbati", "Cassava", 68, "root", "0714"),
    ("Sweet potato", "Ibijumba", "Sweet potatoes", 87, "root", "0714"),
    ("Irish potato", "Ibirayi", "Potatoes (Irish)", 148, "tuber", "0701"),
    ("Tomato", "Inyanya", "Tomatoes", 114, "vegetable", "0702"),
    ("Cabbage", "Amashu", "Cabbage", 181, "vegetable", "0704"),
    ("Eggplant", "Intoryi", "Eggplants", 434, "vegetable", "0709"),
    ("Carrot", "Karoti", "Carrots", 166, "vegetable", "0706"),
    ("Avocado", "Avoka", "Avocados", 454, "fruit", "0804"),
    ("Mango", "Imyembe", "Mangoes", 411, "fruit", "0804"),
    ("Garlic", "Tungurusumu", "Garlic", 105, "vegetable", "0703"),
    ("Spinach", "Epinari", "Spinach", 404, "vegetable", "0709"),
    ("Cauliflower", "Kolifure", "Cauliflower", 231, "vegetable", "0704"),
    ("Papaya", "Ipapayi", "Papaya", 408, "fruit", "0807"),
    ("Passion fruit", "Maracuja", "Passion fruit", 447, "fruit", "0810"),
    ("Passion fruits", "Maracuja", "Passion fruit", 447, "fruit", "0810"),
    ("Guava", "Amapera", "Guava", 407, "fruit", "0804"),
]

# Similar names that must not be added together.
# survey, kinyarwanda, price, price id, form, hs, note in English, note in Kinyarwanda
CLOSE = [
    (
        "Small red bean",
        "Ibishyimbo bitukura",
        "Beans (dry)",
        262,
        "dry beans",
        "0713",
        "Small red bean is one kind of dry bean. The price is for dry beans in general.",
        "Ibishyimbo bitukura ni ubwoko bumwe bw'ibishyimbo byumye. Igiciro ni icy'ibishyimbo byumye muri rusange.",
    ),
    (
        "Groundnut",
        "Ubunyobwa",
        "Groundnuts (shelled)",
        119,
        "shelled nuts",
        "1202",
        "The price is for groundnuts with the shell removed. The survey does not say if the shell was removed.",
        "Igiciro ni icy'ubunyobwa bwakuweho ikibaba. Ubushakashatsi ntibuvuga niba ikibaba cyakuweho.",
    ),
    (
        "Paddy rice",
        "Umuceri w'umutobo",
        "Rice (local)",
        71,
        "milled rice",
        "1006",
        "Paddy rice is rice before it is milled. The price is for rice you buy to cook.",
        "Umuceri w'umutobo ntarasya. Igiciro ni icy'umuceri uteka.",
    ),
    (
        "Cooking banana",
        "Ibitoke",
        "Bananas",
        254,
        "fruit",
        "0803",
        "The price list has one banana price. The survey separates cooking banana and dessert banana.",
        "Urutonde rw'ibiciro rufite igiciro kimwe. Ubushakashatsi bugabanya ibitoke n'imineke.",
    ),
    (
        "Dessert banana",
        "Imineke",
        "Bananas",
        254,
        "fruit",
        "0803",
        "The price list has one banana price. The survey separates cooking banana and dessert banana.",
        "Urutonde rw'ibiciro rufite igiciro kimwe. Ubushakashatsi bugabanya ibitoke n'imineke.",
    ),
    (
        "Onion",
        "Ibitunguru",
        "Onions (red)",
        110,
        "vegetable",
        "0703",
        "The survey says onion. The price list splits red onion and white onion.",
        "Ubushakashatsi buvuga igitunguru. Urutonde rw'ibiciro rugabanya ibitunguru bitukura n'umweru.",
    ),
    (
        "Onion",
        "Ibitunguru",
        "Onions (white)",
        111,
        "vegetable",
        "0703",
        "The survey says onion. The price list splits red onion and white onion.",
        "Ubushakashatsi buvuga igitunguru. Urutonde rw'ibiciro rugabanya ibitunguru bitukura n'umweru.",
    ),
    (
        "Pepper",
        "Urusenda",
        "Chili (red)",
        91,
        "vegetable",
        "0709",
        "The survey says pepper. The price list splits green pepper and red chili.",
        "Ubushakashatsi buvuga urusenda. Urutonde rw'ibiciro rugabanya urusenda rw'icyatsi n'urutukura.",
    ),
    (
        "Sweet pepper",
        "Puwavuro",
        "Peppers (green)",
        292,
        "vegetable",
        "0709",
        "Sweet pepper is close to green pepper, but the names are not the same.",
        "Puwavuro irasa urusenda rw'icyatsi, ariko amazina ntabwo ari amwe.",
    ),
    (
        "Pea",
        "Amashaza",
        "Peas (dry)",
        457,
        "dry peas",
        "0713",
        "The survey does not say if the peas were dry or fresh.",
        "Ubushakashatsi ntibuvuga niba amashaza yari yumye cyangwa mabisi.",
    ),
    (
        "Pea",
        "Amashaza",
        "Peas (fresh)",
        456,
        "fresh peas",
        "0708",
        "The survey does not say if the peas were dry or fresh.",
        "Ubushakashatsi ntibuvuga niba amashaza yari yumye cyangwa mabisi.",
    ),
    (
        "Black eggplant",
        "Intoryi y'irabura",
        "Eggplants",
        434,
        "vegetable",
        "0709",
        "Black eggplant is one kind of eggplant. The price is for eggplant in general.",
        "Intoryi y'irabura ni ubwoko bumwe bw'intoryi. Igiciro ni icy'intoryi muri rusange.",
    ),
    (
        "Apple",
        "Pome",
        "Apples (red)",
        229,
        "fruit",
        "0808",
        "The price is for red apples only.",
        "Igiciro ni icy'pome itukura gusa.",
    ),
    (
        "Orange",
        "Amacunga",
        "Oranges (big size)",
        241,
        "fruit",
        "0805",
        "The price is for big oranges only.",
        "Igiciro ni icy'amacunga manini gusa.",
    ),
    (
        "Maize",
        "Ibigori",
        "Maize flour",
        76,
        "flour",
        "1102",
        "This is flour, not the grain harvest. Do not join it to maize production.",
        "Iyi ni ifu, si ibigori byasaruye. Ntibihuzwa n'umusaruro w'ibigori.",
    ),
    (
        "Cassava",
        "Imyumbati",
        "Cassava flour",
        74,
        "flour",
        "1106",
        "This is flour, not the root harvest. Do not join it to cassava production.",
        "Iyi ni ifu, si imyumbati yasaruwe. Ntibihuzwa n'umusaruro w'imyumbati.",
    ),
    (
        "Sorghum",
        "Amasaka",
        "Sorghum flour",
        253,
        "flour",
        "1102",
        "This is flour, not the grain harvest. Do not join it to sorghum production.",
        "Iyi ni ifu, si amasaka yasaruwe. Ntibihuzwa n'umusaruro w'amasaka.",
    ),
    (
        "Wheat",
        "Ingano",
        "Wheat flour",
        58,
        "flour",
        "1101",
        "This is flour, not the grain harvest. Do not join it to wheat production.",
        "Iyi ni ifu, si ingano yasaruwe. Ntibihuzwa n'umusaruro w'ingano.",
    ),
]

# Crops with no price row. Kinyarwanda is filled only where the farming name is clear.
UNMATCHED_RW = {
    "Banana for beer": "Ibitoke by'urwagwa",
    "Coffee": "Ikawa",
    "Tea": "Icyayi",
    "Millet": "Uburo",
    "Taro": "Amateke",
    "Pineapple": "Inanasi",
    "Yam": "Ibinyamesa",
    "Yams": "Ibinyamesa",
    "Amaranth": "Dodo",
    "Tree tomato": "Ibinyomoro",
    "Sun flower": "Tournesol",
    "Pumpkin": "Igihaza",
    "Sugar cane": "Igisheke",
    "Wheat": "Ingano",
}

PROVINCE_RW = {
    "Eastern Province": "Iburasirazuba",
    "Western Province": "Iburengerazuba",
    "Northern Province": "Amajyaruguru",
    "Southern Province": "Amajyepfo",
    "Kigali City": "Umujyi wa Kigali",
}


def safe_table():
    rows = []
    for survey, rw, price, price_id, form, hs in SAFE:
        rows.append(
            {
                "survey_crop": survey,
                "survey_crop_rw": rw,
                "price_name": price,
                "price_name_rw": rw if survey.split()[0].lower() in price.lower() or price.split()[0].lower() in survey.lower() else price,
                "commodity_id": price_id,
                "product_form": form,
                "hs_heading": hs,
                "match": "same product",
                "safe_to_join": True,
                "note_en": "The survey name and the price name are the same product.",
                "note_rw": "Izina ry'ubushakashatsi n'izina ry'igiciro ni igicuruzwa kimwe.",
            }
        )
    # Set Kinyarwanda price names explicitly for the few that differ in English plural.
    price_rw = {
        "Maize": "Ibigori",
        "Beans (dry)": "Ibishyimbo byumye",
        "Beans (green, fresh)": "Ibishyimbo byo kurya",
        "Soybeans": "Soya",
        "Sorghum": "Amasaka",
        "Wheat": "Ingano",
        "Cassava": "Imyumbati",
        "Sweet potatoes": "Ibijumba",
        "Potatoes (Irish)": "Ibirayi",
        "Tomatoes": "Inyanya",
        "Cabbage": "Amashu",
        "Eggplants": "Intoryi",
        "Carrots": "Karoti",
        "Avocados": "Avoka",
        "Mangoes": "Imyembe",
        "Garlic": "Tungurusumu",
        "Spinach": "Epinari",
        "Cauliflower": "Kolifure",
        "Papaya": "Ipapayi",
        "Passion fruit": "Maracuja",
        "Guava": "Amapera",
    }
    for row in rows:
        row["price_name_rw"] = price_rw[row["price_name"]]
    return pd.DataFrame(rows)


def close_table():
    price_rw = {
        "Beans (dry)": "Ibishyimbo byumye",
        "Groundnuts (shelled)": "Ubunyobwa bwakuweho ikibaba",
        "Rice (local)": "Umuceri wo mu Rwanda",
        "Bananas": "Ibitoke n'imineke",
        "Onions (red)": "Ibitunguru bitukura",
        "Onions (white)": "Ibitunguru umweru",
        "Chili (red)": "Urusenda rutukura",
        "Peppers (green)": "Urusenda rw'icyatsi",
        "Peas (dry)": "Amashaza yumye",
        "Peas (fresh)": "Amashaza mabisi",
        "Eggplants": "Intoryi",
        "Apples (red)": "Pome itukura",
        "Oranges (big size)": "Amacunga manini",
        "Maize flour": "Ifu y'ibigori",
        "Cassava flour": "Ifu y'imyumbati",
        "Sorghum flour": "Ifu y'amasaka",
        "Wheat flour": "Ifu y'ingano",
    }
    rows = []
    for survey, rw, price, price_id, form, hs, note_en, note_rw in CLOSE:
        rows.append(
            {
                "survey_crop": survey,
                "survey_crop_rw": rw,
                "price_name": price,
                "price_name_rw": price_rw[price],
                "commodity_id": price_id,
                "product_form": form,
                "hs_heading": hs,
                "match": "similar, keep separate",
                "safe_to_join": False,
                "note_en": note_en,
                "note_rw": note_rw,
            }
        )
    return pd.DataFrame(rows)


def check_names(table, survey_names, price_names):
    missing_survey = sorted(set(table["survey_crop"]) - survey_names)
    missing_price = sorted(set(table["price_name"]) - price_names)
    if missing_survey or missing_price:
        raise SystemExit(
            "A match uses a name that is not in the files.\n"
            f"Missing survey names: {missing_survey}\n"
            f"Missing price names: {missing_price}"
        )


def season_calendar():
    seasons = pd.DataFrame(
        [
            {
                "season": "A",
                "season_en": "Season A",
                "season_rw": "Igihembwe A",
                "months_en": "September to February",
                "months_rw": "Nzeri kugeza Gashyantare",
                "about_en": "The main farming season.",
                "about_rw": "Igihembwe kinini cy'ubuhinzi.",
                "source": "NISR Seasonal Agricultural Survey",
            },
            {
                "season": "B",
                "season_en": "Season B",
                "season_rw": "Igihembwe B",
                "months_en": "March to June",
                "months_rw": "Werurwe kugeza Kamena",
                "about_en": "The second farming season.",
                "about_rw": "Igihembwe cya kabiri cy'ubuhinzi.",
                "source": "NISR Seasonal Agricultural Survey",
            },
            {
                "season": "C",
                "season_en": "Season C",
                "season_rw": "Igihembwe C",
                "months_en": "July to September",
                "months_rw": "Nyakanga kugeza Nzeri",
                "about_en": "A short season, mostly vegetables and sweet potato in marshes, and Irish potato in the volcanic north.",
                "about_rw": "Igihembwe kigufi, cyane cyane imboga n'ibijumba mu bishanga, n'ibirayi mu majyaruguru y'ibirunga.",
                "source": "NISR Seasonal Agricultural Survey",
            },
        ]
    )
    stages = pd.DataFrame(
        [
            {
                "crop_en": "Maize",
                "crop_rw": "Ibigori",
                "season": "A",
                "plant_en": "September to October",
                "plant_rw": "Nzeri kugeza Ukwakira",
                "harvest_en": "January to February",
                "harvest_rw": "Mutarama kugeza Gashyantare",
                "drying_days": "",
                "source": "FAO GIEWS national crop calendar, 2015",
            },
            {
                "crop_en": "Maize",
                "crop_rw": "Ibigori",
                "season": "B",
                "plant_en": "February to March",
                "plant_rw": "Gashyantare kugeza Werurwe",
                "harvest_en": "June to July",
                "harvest_rw": "Kamena kugeza Nyakanga",
                "drying_days": "",
                "source": "FAO GIEWS national crop calendar, 2015",
            },
            {
                "crop_en": "Sorghum",
                "crop_rw": "Amasaka",
                "season": "A",
                "plant_en": "September to October",
                "plant_rw": "Nzeri kugeza Ukwakira",
                "harvest_en": "January to February",
                "harvest_rw": "Mutarama kugeza Gashyantare",
                "drying_days": "",
                "source": "FAO GIEWS national crop calendar, 2015. FAO used this same calendar for maize and sorghum.",
            },
            {
                "crop_en": "Sorghum",
                "crop_rw": "Amasaka",
                "season": "B",
                "plant_en": "February to March",
                "plant_rw": "Gashyantare kugeza Werurwe",
                "harvest_en": "June to July",
                "harvest_rw": "Kamena kugeza Nyakanga",
                "drying_days": "",
                "source": "FAO GIEWS national crop calendar, 2015. FAO used this same calendar for maize and sorghum.",
            },
        ]
    )
    return seasons, stages


def main():
    LOOKUPS.mkdir(parents=True, exist_ok=True)
    APP_TABLES.mkdir(parents=True, exist_ok=True)

    survey = pd.read_csv(
        PROCESSED / "sas" / "crop_production.csv",
        usecols=["year", "season", "crop_name"],
        dtype="string",
    )
    survey_names = set(survey["crop_name"].dropna().unique())

    prices = pd.read_parquet(
        ROOT / "data" / "source" / "train-00000-of-00001.parquet",
        columns=["commodity", "commodity_id", "date"],
    )
    prices_test = pd.read_parquet(
        ROOT / "data" / "source" / "test-00000-of-00001.parquet",
        columns=["commodity", "commodity_id", "date"],
    )
    prices = pd.concat([prices, prices_test], ignore_index=True)
    price_names = set(prices["commodity"].dropna().unique())
    id_check = prices.groupby("commodity")["commodity_id"].nunique()
    if (id_check > 1).any():
        raise SystemExit("One price name has more than one id.")

    safe = safe_table()
    close = close_table()
    check_names(safe, survey_names, price_names)
    check_names(close, survey_names, price_names)

    # The id in our table must be the id stored in the price file.
    file_ids = prices.groupby("commodity")["commodity_id"].first()
    for table in (safe, close):
        for _, row in table.iterrows():
            found = int(file_ids.loc[row["price_name"]])
            if found != int(row["commodity_id"]):
                raise SystemExit(
                    f"{row['price_name']} is id {found} in the price file, not {row['commodity_id']}."
                )

    matches = pd.concat([safe, close], ignore_index=True)
    matches.to_csv(LOOKUPS / "crop_price_match.csv", index=False)

    matched_survey = set(matches["survey_crop"])
    unmatched_names = sorted(survey_names - matched_survey)
    unmatched = pd.DataFrame(
        {
            "survey_crop": unmatched_names,
            "survey_crop_rw": [UNMATCHED_RW.get(name, "") for name in unmatched_names],
            "why_en": "This crop has no safe price match.",
            "why_rw": "Iki gihingwa nta giciro gihuye neza na cyo.",
        }
    )
    unmatched.to_csv(LOOKUPS / "crops_without_a_price.csv", index=False)

    seasons, stages = season_calendar()
    seasons.to_csv(LOOKUPS / "seasons.csv", index=False)
    stages.to_csv(LOOKUPS / "maize_sorghum_calendar.csv", index=False)

    districts = pd.read_csv(PROCESSED / "district_lookup.csv")
    districts["province_rw"] = districts["province"].map(PROVINCE_RW)
    if districts["province_rw"].isna().any():
        raise SystemExit("A province has no Kinyarwanda name.")
    districts["district_rw"] = districts["district"]
    districts.to_csv(LOOKUPS / "districts.csv", index=False)

    by_season = (
        survey.dropna(subset=["year", "season"])
        .groupby(["year", "season"], as_index=False)
        .size()
        .rename(columns={"size": "crop_rows"})
    )
    by_season.to_csv(APP_TABLES / "survey_rows_by_season.csv", index=False)

    rain = pd.read_csv(PROCESSED / "rainfall" / "district_month.csv", usecols=["year", "month"])
    trade = pd.read_csv(PROCESSED / "trade" / "exports_by_partner.csv", usecols=["year"])
    status = pd.DataFrame(
        [
            {
                "survey_crop_rows": int(len(survey)),
                "survey_crop_names": int(survey["crop_name"].nunique(dropna=True)),
                "safe_matches": int(len(safe)),
                "similar_kept_separate": int(len(close)),
                "crops_without_a_price": int(len(unmatched)),
                "price_rows": int(len(prices)),
                "price_names": int(prices["commodity"].nunique()),
                "price_last_date": str(pd.to_datetime(prices["date"]).max().date()),
                "rain_last_year": int(rain["year"].max()),
                "rain_last_month": int(rain.loc[rain["year"] == rain["year"].max(), "month"].max()),
                "districts": int(districts["district"].nunique()),
                "trade_rows": int(len(trade)),
                "trade_last_year": int(trade["year"].max()),
            }
        ]
    )
    status.to_csv(APP_TABLES / "status.csv", index=False)
    print(status.to_string(index=False))
    print(f"Safe matches: {len(safe)}. Similar, kept separate: {len(close)}. Crops with no price: {len(unmatched)}.")


if __name__ == "__main__":
    main()
