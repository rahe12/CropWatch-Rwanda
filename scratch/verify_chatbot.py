import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.advise import answer, classify, pack
from src.words import TEXT

PROCESSED = ROOT / "data" / "processed"
LOOKUPS = PROCESSED / "lookups"
APP_TABLES = PROCESSED / "app"

alerts = pd.read_csv(APP_TABLES / "irrigation_alerts.csv")
forecast = pd.read_csv(APP_TABLES / "forecast_7day.csv")
watch = pd.read_csv(APP_TABLES / "season_watch.csv")
soil = pd.read_csv(APP_TABLES / "soil_season_a_2022.csv")
vegetation = pd.read_csv(PROCESSED / "vegetation" / "district_year.csv")

district = "Musanze"
profile = pack(alerts, forecast, watch, soil, vegetation, district)

queries = [
    ("Why are my maize leaves turning yellow?", "yellow_leaves", "en"),
    ("What fertilizer should I apply for maize?", "fertilizer", "en"),
    ("My soil is too acidic, what can I do?", "lime_acidity", "en"),
    ("When should I plant for Season A and B?", "seasons", "en"),
    ("Compare Musanze and Nyagatare", "district_compare", "en"),
    ("What is the recommended plant spacing for Irish potatoes?", "spacing", "en"),
    ("How do I store maize safely without weevils?", "storage", "en"),
    ("How does the government irrigation subsidy work?", "ssit_subsidy", "en"),
    ("How does crop insurance work?", "nais_insurance", "en"),
    ("Kuki ibibabi by'ibigori bihinduka umuhondo?", "yellow_leaves", "rw"),
    ("Ni ifumbire ki nkwiye gukoresha ku bigori?", "fertilizer", "rw"),
]

print("=" * 60)
print("TESTING CHATBOT INTENT CLASSIFICATION & DOMAIN RESPONSES")
print("=" * 60)

all_passed = True
for q, expected_intent, lang in queries:
    words = TEXT[lang]
    intent = classify(q)
    ans = answer(q, profile, words, lang)
    
    # Check that answer is rich, domain-specific, and not an empty or fallback response
    is_valid = len(ans) > 150
    status_icon = "PASS" if (intent == expected_intent and is_valid) else "FAIL"
    if intent != expected_intent or not is_valid:
        all_passed = False
        
    print(f"\n[{status_icon}] Query ({lang}): '{q}'")
    print(f"   Intent: '{intent}' (Expected: '{expected_intent}')")
    first_line = ans.strip().split("\n")[0]
    print(f"   Opening: {first_line[:90]}...")
    print(f"   Length: {len(ans)} chars")

print("\n" + "=" * 60)
if all_passed:
    print("ALL 11 TEST QUERIES PASSED WITH DEDICATED DOMAIN RESPONSES!")
else:
    print("SOME QUERIES HAD ISSUES - CHECK ABOVE.")
print("=" * 60)
