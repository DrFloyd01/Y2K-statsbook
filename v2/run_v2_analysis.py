"""
Main entry point for running the v2 analysis and displaying the results.
"""
import sys
from pathlib import Path
sys.path.append(".")

from v2.parsers.main_parser import load_league_from_cache
from v2.leaderboard import calculate_leaderboards
from v2.display import display_leaderboard

# --- Constants ---
CACHE_DIR = Path("v2/api_cache")
TARGET_SEASON = 2025

def main():
    """
    Loads a league from cached API data, runs the analysis, and displays the results.
    """
    print("--- Initializing v2 League Analysis ---")

    # 1. Load a complete league object from the cached API data
    print(f"Loading league data for season: {TARGET_SEASON}")
    league = load_league_from_cache(CACHE_DIR, TARGET_SEASON)

    if not league or not any(league.schedule.regular_season.values()):
        print("\nERROR: No matchup data found in the cache for the target season.")
        print("Please run `v2/api_explorer.py` to fetch the latest data from the API.")
        print("--- v2 League Analysis Aborted ---")
        return

    # 2. Calculate leaderboards, H2H records, and accolades
    print("Calculating leaderboards and accolades...")
    from v2.accolades import calculate_doh_accolades
    doh_accolades = calculate_doh_accolades(league)
    leaderboard_data = calculate_leaderboards(league, doh_accolades)

    # 3. Display the results
    print("Displaying results...\n")
    display_leaderboard(leaderboard_data)

    # 4. Save D'OH log to JSON file
    import json
    with open("doh_log.json", "w") as f:
        json.dump(doh_accolades, f, indent=2)
    print("D'OH log saved to doh_log.json")

    print("--- v2 League Analysis Complete ---")

if __name__ == "__main__":
    main()
