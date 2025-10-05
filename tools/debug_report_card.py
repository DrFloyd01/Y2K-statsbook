import json
from pathlib import Path

DATA_DIR = Path("data")
REPORT_DATA_FILE = DATA_DIR / "report_card_data.json"

def test_report_card_data():
    """
    This test loads the generated report card data and inspects the 'accolades'
    list to ensure every item is a dictionary, not a string. This is the root
    cause of the "'str' object has no attribute 'get'" error.
    """
    print(f"--- Running Test: Inspecting {REPORT_DATA_FILE} ---")

    if not REPORT_DATA_FILE.exists():
        print(f"❌ FAILURE: Data file not found at {REPORT_DATA_FILE}")
        return

    with open(REPORT_DATA_FILE, "r") as f:
        data = json.load(f)

    accolades = data.get("accolades")
    if not isinstance(accolades, list):
        print(f"❌ FAILURE: 'accolades' key is not a list. Found type: {type(accolades)}")
        return

    for i, accolade in enumerate(accolades):
        if not isinstance(accolade, dict):
            print(f"\n❌ FAILURE: Found a non-dictionary item in the 'accolades' list at index {i}.")
            print(f"   - Type: {type(accolade)}")
            print(f"   - Value: \"{accolade}\"")
            if i > 0:
                print("\n   Context: The previous valid accolade was:")
                print(f"   {json.dumps(accolades[i-1], indent=4)}")
            print("\n   Suggestion: The error originates in 'tools/dashboard_weekly_report.py'. Check how the accolades list is being appended. It seems a raw string is being added instead of a dictionary object for one of the accolade types.")
            return

    print("✅ SUCCESS: All items in the 'accolades' list are valid dictionaries.")

if __name__ == "__main__":
    test_report_card_data()