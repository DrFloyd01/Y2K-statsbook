"""
Formats and displays league data, including leaderboards, H2H records, and accolades.
"""
from typing import List, Dict
from v2.models.league import H2HRecord, Accolade

def display_h2h_records(h2h_records: List[H2HRecord]):
    """Formats and prints H2H records."""
    print("--- Head-to-Head Records ---")
    for record in sorted(h2h_records, key=lambda r: (r.manager_name, r.opponent_name)):
        total_wins = record.season_wins + record.playoff_wins
        total_losses = record.season_losses + record.playoff_losses
        print(f"{record.manager_name} vs. {record.opponent_name}: {total_wins}-{total_losses}")
        print(f"  - Regular Season: {record.season_wins}-{record.season_losses}")
        print(f"  - Playoffs: {record.playoff_wins}-{record.playoff_losses}")
    print("\n")

def display_top_5_accolades(accolades: List[Accolade]):
    """Formats and prints the top 5 of each accolade by magnitude."""
    print("--- Top 5 Accolade Results ---")
    accolade_groups: Dict[str, List[Accolade]] = {}
    for accolade in accolades:
        if accolade.name not in accolade_groups:
            accolade_groups[accolade.name] = []
        accolade_groups[accolade.name].append(accolade)

    for name, group in accolade_groups.items():
        # Sort by magnitude, ascending for specific accolades
        reverse_sort = name not in ["Lowest Scoring Win", "Smallest Margin Defeat"]
        sorted_group = sorted(group, key=lambda a: a.magnitude, reverse=reverse_sort)
        print(f"--- {name} ---")
        for i, accolade in enumerate(sorted_group[:5]):
            print(f"  {i+1}. {accolade.manager_name} ({accolade.season}, Week {accolade.week})")
            print(f"      Magnitude: {accolade.magnitude:.2f}")
            if accolade.opponent_manager_name:
                print(f"      vs. {accolade.opponent_manager_name}")
    print("\n")

def display_total_accolades(accolades: List[Accolade], num_seasons: int):
    """Formats and prints a normalized leaderboard of total accolades."""
    print("--- Total Accolades (Normalized by Season) ---")

    # First, get a unique list of all manager names from the accolades
    all_managers = sorted(list(set(a.manager_name for a in accolades)))

    # Then, get a unique list of all accolade names
    accolade_names = sorted(list(set(a.name for a in accolades)))

    # Create a dictionary to hold the counts for each manager
    manager_counts: Dict[str, Dict[str, int]] = {
        manager: {name: 0 for name in accolade_names} for manager in all_managers
    }

    for accolade in accolades:
        manager_counts[accolade.manager_name][accolade.name] += 1

    # --- Print the Header ---
    header = f"{'Manager':<20}" + "".join([f"{name:<25}" for name in accolade_names])
    print(header)
    print("-" * len(header))

    # --- Print Each Manager's Stats ---
    for manager in all_managers:
        row = f"{manager:<20}"
        for name in accolade_names:
            normalized_val = manager_counts[manager][name] / num_seasons
            row += f"{normalized_val:<25.2f}"
        print(row)
    print("\n")

def display_doh_leaderboards(doh_accolades: List[Dict]):
    """Formats and prints the 'D'OH' leaderboards."""
    print("--- D'OH! Scenarios ---")
    if not doh_accolades:
        print("No D'OH! scenarios found.")
        return

    # --- D'OH! Counts ---
    print("\n--- D'OH! Counts ---")
    doh_counts = {}
    for accolade in doh_accolades:
        manager = accolade["losing_team"]
        doh_counts[manager] = doh_counts.get(manager, 0) + 1

    sorted_counts = sorted(doh_counts.items(), key=lambda item: item[1], reverse=True)
    for manager, count in sorted_counts:
        print(f"{manager}: {count}")

    # --- Top 20 D'OH! Scenarios by Point Swing ---
    print("\n--- Top 20 D'OH! Scenarios by Point Swing ---")
    for i, accolade in enumerate(doh_accolades[:20]):
        print(f"  {i+1}. Week {accolade['week']}: {accolade['losing_team']} "
              f"lost to {accolade['winning_team']} "
              f"({accolade['losing_score']:.2f} - {accolade['winning_score']:.2f})")
        print(f"      - Margin: {accolade['margin']:.2f}")
        print(f"      - Bench Player: {accolade['bench_player']} ({accolade['bench_player_score']:.2f})")
        print(f"      - Starter: {accolade['starting_player']} ({accolade['starting_player_score']:.2f})")
        print(f"      - Point Swing: {accolade['point_swing']:.2f}")
        print(f"      - New Score: {accolade['new_score']:.2f}")
    print("\n")


def display_leaderboard(leaderboard_data: Dict):
    """
    Displays the full suite of league statistics.
    """
    display_h2h_records(leaderboard_data["h2h_records"])
    display_top_5_accolades(leaderboard_data["accolades"])
    # Note: We are hardcoding num_seasons to 1 for now, as we only have 2025 data.
    # This will be updated once historical data is pulled.
    display_total_accolades(leaderboard_data["accolades"], num_seasons=1)
    display_doh_leaderboards(leaderboard_data["doh_accolades"])
