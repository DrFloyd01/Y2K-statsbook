import json
import logging
import argparse
import re
import os
from pathlib import Path
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

# Import the core logic from our tool scripts
from tools.generate_preview import run_preview_process
from tools.dashboard_weekly_report import run_report_process
from tools.init_history import run_full_historical_build
from tools.generate_accolades import generate_accolades_data
from tools.build_raw_data_cache import update_raw_data_cache
from tools.build_raw_data_cache import cache_all_raw_data

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

# --- Directory Setup ---
DATA_DIR = Path("data")
CACHE_DIR = Path("cache")
SITE_DIR = Path("site")
NOTES_DIR = Path("notes")
TEMPLATES_DIR = Path("templates")

DATA_DIR.mkdir(exist_ok=True)
SITE_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True) # yfpy will use this
STATE_FILE = DATA_DIR / "state.json"

# --- Yahoo API Credentials ---
YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

# --- Pickle Compatibility Fix ---
def get_current_state():
    if not STATE_FILE.exists():
        return {"last_processed_week": 0}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def parse_notes_file(notes_file_path):
    """Parses a markdown notes file and returns a dictionary of notes keyed by matchup."""
    notes = {}
    if not notes_file_path.exists():
        return notes

    try:
        with open(notes_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        matchup_sections = content.split('---')

        for section in matchup_sections:
            if not section.strip():
                continue

            header_match = re.search(r"##\s*Matchup:\s*(.+?)\s*vs\s*(.+)", section)
            if header_match:
                team1_name = header_match.group(1).strip()
                team2_name = header_match.group(2).strip()
                note_match = re.search(r">\s*(.*)", section, re.DOTALL)
                note_content = note_match.group(1).strip() if note_match else ""
                matchup_key = tuple(sorted((team1_name, team2_name)))
                notes[matchup_key] = note_content
    except Exception as e:
        logging.error(f"Error parsing notes file {notes_file_path}: {e}")
    return notes

def generate_weekly_preview_html(data):
    """Generates the weekly_preview.html file from a data object."""
    season = data['season']
    preview_week = data['preview_week']

    html_parts = [f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>:: Y2K CPU Machinations :: Week {preview_week} Preview ::</title>
    <style>
        body {{ font-family: 'Courier New', Courier, monospace; margin: 0; padding: 20px; background-color: #000; color: #0f0; font-size: 0.9em; }}
        .container {{ max-width: 800px; margin: 20px auto; background: #000; padding: 20px; border: 1px solid #0f0; }}
        .nav-bar {{ background-color: #010; padding: 5px; border: 1px solid #0f0; margin-bottom: 20px; text-align: center; }}
        .nav-bar a {{ color: #0f0; text-decoration: none; font-weight: bold; }}
        .nav-bar a:hover {{ color: #fff; }}
        h1 {{ font-size: 1.8em; color: #0f0; text-align: center; border-bottom: 1px solid #0f0; padding-bottom: 10px; letter-spacing: 2px; }}
        .matchup {{ border: 1px solid #050; padding: 15px; margin-bottom: 20px; }}
        .matchup:nth-child(odd) {{ background-color: #010; }}
        .matchup-header {{ font-size: 1.1em; font-weight: bold; color: #fff; margin-bottom: 10px; }}
        .team-name {{ color: #0f0; }}
        .record {{ font-style: normal; color: #aaa; font-weight: normal; }}
        .h2h-stats p {{ margin: 5px 0; font-size: 0.9em; }}
        .h2h-stats strong {{ color: #cfc; }}
        .commissioner-note {{ background: #020; border: 1px dashed #070; padding: 10px 15px; margin-top: 15px; color: #afc; }}
        .commissioner-note p {{ margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-bar"><a href="index.html">« System.Index</a></div>
        <h1>{season} Y2K: Week {preview_week} Preview</h1>
    """]

    notes_file = NOTES_DIR / f"week_{preview_week}_notes.md"
    commissioner_notes = parse_notes_file(notes_file)
    if not commissioner_notes:
        logging.warning(f"Could not find or parse notes file: {notes_file.name}. Using placeholder text.")

    for matchup in data['matchups']:
        team1_data = matchup['team1']; team2_data = matchup['team2']; h2h = matchup['h2h']
        matchup_key = tuple(sorted((team1_data['name'], team2_data['name'])))

        html_parts.append('<div class="matchup">')
        html_parts.append(f'''
            <div class="matchup-header">
                {team1_data["rank"]}. <span class="team-name">{team1_data['name']}</span> <span class="record">{team1_data['record']}</span>
                vs 
                {team2_data["rank"]}. <span class="team-name">{team2_data['name']}</span> <span class="record">{team2_data['record']}</span>
            </div>
            <div class="h2h-stats">
        ''')

        if h2h:
            html_parts.append(f"<p><strong>Season H2H:</strong> {h2h['reg_h2h']}</p>")
            html_parts.append(f"<p><strong>Streak:</strong> {h2h['streak_info']}</p>")
            html_parts.append(f"<p>{h2h['playoff_h2h_display']}</p>")
        else:
            html_parts.append("<p><strong>Season H2H:</strong> 0-0</p>")
            html_parts.append("<p><strong>Streak:</strong> First Meeting</p>")
            html_parts.append("<p><strong>Playoffs H2H:</strong> 0-0</p>")

        html_parts.append('</div>')
        note_text = commissioner_notes.get(matchup_key, "This is where the commissioner's analysis of the matchup will go, providing expert insight and witty commentary.")
        html_parts.append(f'''
            <div class="commissioner-note">
                <p>{note_text}</p>
            </div>
        ''')
        html_parts.append('</div>')

    html_parts.append("</div></body></html>")
    
    final_html = "\n".join(html_parts)
    output_filename = SITE_DIR / "weekly_preview.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    logging.info(f"✅ Successfully generated HTML preview: {output_filename.name}")

def generate_weekly_report_html(data):
    report_week = data['report_week']

    html_parts = [f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>:: Y2K CPU Machinations :: Week {report_week} Report Card ::</title>
    <style>
        body {{ font-family: 'Courier New', Courier, monospace; margin: 0; padding: 20px; background-color: #000; color: #0f0; font-size: 0.9em; }}
        .container {{ max-width: 950px; margin: 20px auto; background: #000; padding: 20px; border: 1px solid #0f0; }}
        .nav-bar {{ background-color: #010; padding: 5px; border: 1px solid #0f0; margin-bottom: 20px; text-align: center; }}
        .nav-bar a {{ color: #0f0; text-decoration: none; font-weight: bold; }}
        .nav-bar a:hover {{ color: #fff; }}
        h1, h2 {{ color: #0f0; text-align: center; border-bottom: 1px solid #0f0; padding-bottom: 10px; margin-top: 25px; letter-spacing: 2px; }}
        h1 {{ font-size: 1.8em; }}
        h2 {{ font-size: 1.4em; }}
        .delta-pos {{ color: #3f3; }}
        .delta-neg {{ color: #f33; }}
        
        /* New Standings Layout */
        .standings-container {{ display: flex; flex-direction: column; gap: 5px; }}
        .manager-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px; border: 1px solid #050; }}
        .manager-row:nth-child(odd) {{ background-color: #010; }}
        .alt-stats, .real-stats {{ flex: 1; font-size: 0.9em; }}
        .real-stats {{ text-align: right; }}
        .manager-delta {{ flex: 0 0 200px; text-align: center; }}
        .manager-delta .name {{ font-size: 1.1em; color: #cfc; font-weight: bold; }}
        .manager-delta .delta-line {{ border-bottom: 1px dashed #070; margin: 3px 0; }}

        /* Accolades */
        .accolades-grid {{ display: flex; flex-wrap: wrap; gap: 15px; margin-top: 20px; }}
        .accolade-card {{ background: #010; border: 1px solid #050; padding: 15px; box-sizing: border-box; flex: 1 1 30%; min-width: 250px; text-align: center; }}
        .accolade-card h3 {{ margin: 0 0 10px 0; font-size: 1.1em; color: #fff; }}
        .accolade-card .manager {{ font-size: 1.2em; font-weight: bold; color: #cfc; margin-bottom: 5px; }}
        .accolade-card .details {{ font-size: 0.9em; color: #aaa; margin-bottom: 10px; }}
        .accolade-summary {{ font-size: 0.8em; color: #888; margin-top: 10px; border-top: 1px dashed #050; padding-top: 10px; }}
        .record-status {{ margin-top: 10px; padding: 5px; background: #310; border: 1px dashed #a30; color: #fd7; font-weight: bold; }}
        .record-status.all-time {{ background: #500; border-color: #f00; color: #f77; }}
    </style>
</head>
<body>
<div class="container">
    <div class="nav-bar"><a href="index.html">« System.Index</a></div>
    <h1>{data['season']} Y2K: Week {report_week} Report Card</h1>
    
    <h2>🏆 Weekly Accolades 🏆</h2><div class='accolades-grid'>
    """]

    for accolade in data['accolades']:
        record_html = ""
        if accolade.get('record_status'):
            record_status = accolade['record_status']
            status_class = "all-time" if "All-Time" in record_status else ""
            record_html = f"<div class='record-status {status_class}'>{record_status}</div>"
        
        summary_html = ""
        if accolade.get('summary'):
            summary_html = f"<div class='accolade-summary'>{accolade['summary']}</div>"

        html_parts.append(f"""
        <div class="accolade-card">
            <h3>{accolade['title']}</h3>
            <div class="manager">{accolade['manager']}</div>
            <div class="details">{accolade['details']}</div>
            {record_html}
            {summary_html}
        </div>
        """)
    html_parts.append("</div>")

    html_parts.append("""
    <h2>🌌 Universe Comparison 🌌</h2>
    <div class="standings-container">
        <div class="manager-row" style="font-weight: bold; background: #030; font-size: 0.8em;">
            <div class="alt-stats">Alt. Universe (Rank, Rec, PF)</div>
            <div class="manager-delta">Manager (Real - Alt)</div>
            <div class="real-stats">(Rec, PF/PA, Rank) Real Universe</div>
        </div>
    """)

    for row in data['alt_standings_rows']:
        delta = row['current_real_rank'] - row['alt_rank']
        delta_str = f"({delta:+})"
        delta_class = "delta-pos" if delta < 0 else "delta-neg" if delta > 0 else ""

        html_parts.append('<div class="manager-row">')
        html_parts.append(f'''
            <div class="alt-stats">
                {row["alt_rank"]} {row['alt_record']} ({row['alt_pf']:.2f} <span style="color: #aaa;">{row['stdev']}</span>)
            </div>
            <div class="manager-delta">
                <div class="name">{row['manager']}</div>
                <div class="delta-line"></div>
                <div class="{delta_class}">{delta_str}</div>
            </div>
            <div class="real-stats">
                {row['real_record']} ({row['real_pf']:.2f}/{row['real_pa']:.2f}) {row["current_real_rank"]}
            </div>
        ''')
        html_parts.append('</div>')

    html_parts.append("</div></div></body></html>")

    final_html = "\n".join(html_parts)
    output_filename = SITE_DIR / "weekly_report.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    logging.info(f"✅ Successfully generated HTML report: {output_filename.name}")

def generate_accolades_html(data):
    """Generates the all_time_accolades.html file."""
    all_time_stats = data['all_time_stats']
    all_time_records = data['all_time_records']
    
    MANAGERS_TO_HIDE = ["cooper", "nick", "Torin", "--hidden--"]
    hidden_lower = [h.lower() for h in MANAGERS_TO_HIDE]
    
    def get_filtered_managers(stats_dict):
        return [m for m in stats_dict if m.lower() not in hidden_lower]

    def _format_record_string(record):
        manager = record.get('manager', 'N/A'); opponent = record.get('opponent', 'N/A')
        season_str = str(record.get('season', ''))[-2:]; week_str = record.get('week', '')
        if 'score' in record:
            return f"{record['score']:.2f} pts (by {manager} vs {opponent}, Wk {week_str}'{season_str})"
        elif 'margin' in record:
            return f"{record['margin']:.2f} pts (by {manager} vs {opponent}, Wk {week_str}'{season_str})"
        return "N/A"

    html_parts = [f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>:: Y2K CPU Machinations :: All-Time Accolades ::</title>
    <style>
        body {{ font-family: 'Courier New', Courier, monospace; margin: 0; padding: 20px; background-color: #000; color: #0f0; font-size: 0.9em; }}
        .container {{ max-width: 950px; margin: 20px auto; background: #000; padding: 20px; border: 1px solid #0f0; }}
        .nav-bar {{ background-color: #010; padding: 5px; border: 1px solid #0f0; margin-bottom: 20px; text-align: center; }}
        .nav-bar a {{ color: #0f0; text-decoration: none; font-weight: bold; }}
        .nav-bar a:hover {{ color: #fff; }}
        h1, h2 {{ color: #0f0; text-align: center; border-bottom: 1px solid #0f0; padding-bottom: 10px; margin-top: 25px; letter-spacing: 2px; }}
        h1 {{ font-size: 1.8em; }}; h2 {{ font-size: 1.4em; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; border: 1px solid #050; }}
        th, td {{ padding: 4px 6px; text-align: left; border: 1px solid #050; }}
        thead th {{ background-color: #030; font-weight: bold; color: #fff; }}
        tbody tr:nth-child(even) {{ background-color: #010; }}
        .podium {{ display: flex; justify-content: space-around; text-align: center; margin-top: 20px; }}
        .podium-item {{ background: #010; border: 1px solid #050; padding: 15px; width: 48%; box-sizing: border-box; }}
        .podium-item h3 {{ margin: 0 0 10px 0; color: #fff; }}
        .podium-item p {{ margin: 8px 0; }}
        .podium-rank-1 {{ font-size: 1.0em; color: #cfc; }}
        .podium-rank-2, .podium-rank-3 {{ font-size: 0.9em; color: #afc; }}
    </style>
</head>
<body>
<div class="container">
    <div class="nav-bar"><a href="index.html">« System.Index</a></div>
    <h1>👑 All-Time Accolade Leaderboard 👑</h1>
    """]

    html_parts.append("<h2>🏆 All-Time Records Podium 🏆</h2><div class='podium'>")
    podium_accolades = {
        'top_points': "🌋 Highest Scores",
        'highest_scoring_loss': "💔 Toughest Losses",
        'blowout_win': "💥 Biggest Blowouts",
        'lowest_scoring_win': "🍀 Luckiest Wins",
        'smallest_margin_defeat': "🤏 Heartbreak Losses"
    }
    for key, title in podium_accolades.items():
        records = all_time_records.get(key, [])
        html_parts.append(f"<div class='podium-item'><h3>{title}</h3>")
        if records:
            for i, record in enumerate(records):
                rank = i + 1
                html_parts.append(f"<p class='podium-rank-{rank}'>{rank}. {_format_record_string(record)}</p>")
        else:
            html_parts.append("<p>No records found.</p>")
        html_parts.append("</div>")
    html_parts.append("</div>")

    html_parts.append("<h2>📊 All-Time Leaderboards 📊</h2>")
    accolade_map = {
        'top_points': "🌋 Top Point Weeks", 'highest_scoring_loss': "💔 Tough Luck Losses",
        'lowest_scoring_win': "🍀 Luckiest Wins", 'smallest_margin_defeat': "🤏 Heartbreak Losses",
        'blowout_win': "💥 Biggest Blowouts"
    }
    all_time_managers = get_filtered_managers(all_time_stats)
    for key, title in accolade_map.items():
        board = sorted(all_time_managers, key=lambda m: all_time_stats[m].get(key, 0), reverse=True)
        html_parts.append(f"<h3>{title}</h3><table><thead><tr><th>Rank</th><th>Manager</th><th>Count</th></tr></thead><tbody>")
        for i, manager in enumerate(board):
            count = all_time_stats.get(manager, {}).get(key, 0)
            if count == 0: continue
            html_parts.append(f"<tr><td>{i+1}</td><td>{manager}</td><td>{count}</td></tr>")
        html_parts.append("</tbody></table>")

    html_parts.append("</div></body></html>")
    
    final_html = "\n".join(html_parts)
    output_filename = SITE_DIR / "all_time_accolades.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    logging.info(f"✅ Successfully generated HTML accolades page: {output_filename.name}")

def generate_index_html():
    """Generates the main index.html landing page."""
    try:
        with open(TEMPLATES_DIR / "index.html", "r", encoding="utf-8") as f:
            template_html = f.read()
    except FileNotFoundError:
        logging.error("Could not find templates/index.html. Cannot build index page.")
        return

    preview_link_html = '<a href="weekly_preview.html">» Weekly Matchup Preview</a>' if (DATA_DIR / "preview_data.json").exists() else ''
    report_link_html = '<a href="weekly_report.html">» Weekly Report Card</a>' if (DATA_DIR / "report_card_data.json").exists() else ''
    accolades_link_html = '<a href="all_time_accolades.html">» All-Time Accolades</a>' if (DATA_DIR / "accolades_data.json").exists() else ''

    html = template_html.replace("{PREVIEW_LINK}", preview_link_html)
    html = html.replace("{REPORT_LINK}", report_link_html)
    html = html.replace("{ACCOLADES_LINK}", accolades_link_html)

    with open(SITE_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)
    logging.info("✅ Successfully generated HTML index: index.html")

def generate_notes_template_if_needed(preview_data):
    """Creates a markdown template for commissioner notes if it doesn't exist."""
    preview_week = preview_data['preview_week']
    notes_file = NOTES_DIR / f"week_{preview_week}_notes.md"

    if notes_file.exists():
        return

    logging.info(f"Generating new notes template: {notes_file.name}")
    template_parts = [f"# Week {preview_week} Preview Notes\n"]

    for matchup in preview_data['matchups']:
        team1_name = matchup['team1']['name']
        team2_name = matchup['team2']['name']
        template_parts.append(f"## Matchup: {team1_name} vs {team2_name}\n\n> Add your commissioner's note for this matchup here.\n\n---\n")

    with open(notes_file, "w", encoding="utf-8") as f:
        f.write("".join(template_parts))

def build_html_from_data():
    """
    Generates all HTML pages from their respective JSON data files.
    Also generates a notes template if one doesn't exist for the current preview week.
    """
    logging.info("\n--- Building HTML from data files ---")
    for item in SITE_DIR.glob('*'):
        if item.is_file():
            item.unlink()

    try:
        with open(DATA_DIR / "preview_data.json", "r", encoding="utf-8") as f:
            preview_data = json.load(f)
        generate_notes_template_if_needed(preview_data)
        generate_weekly_preview_html(preview_data)
    except FileNotFoundError:
        logging.warning("preview_data.json not found. Skipping weekly preview generation.")
    except Exception as e:
        logging.error(f"Error generating weekly preview: {e}")
    
    try:
        with open(DATA_DIR / "report_card_data.json", "r", encoding="utf-8") as f:
            report_data = json.load(f)
        generate_weekly_report_html(report_data)
    except FileNotFoundError:
        logging.warning("report_card_data.json not found. Skipping weekly report generation.")
    except Exception as e:
        logging.error(f"Error generating weekly report: {e}")
    
    try:
        with open(DATA_DIR / "accolades_data.json", "r", encoding="utf-8") as f:
            accolades_data = json.load(f)
        generate_accolades_html(accolades_data)
    except FileNotFoundError:
        logging.warning("accolades_data.json not found. Skipping all-time accolades generation.")
    except Exception as e:
        logging.error(f"Error generating all-time accolades: {e}")

    generate_index_html()
    logging.info("--- HTML build complete ---")

def main():
    """
    Main orchestrator. Checks for new data, refreshes if necessary, and builds the site.
    """
    parser = argparse.ArgumentParser(description="Build the Y2K Statsbook website.")
    parser.add_argument('--force-refresh', action='store_true', help="Force a refresh of all data from the API.")
    args = parser.parse_args()

    if not (DATA_DIR / "h2h_records.json").exists():
        logging.warning("Core historical data not found. Running one-time setup...")
        run_full_historical_build()

    TARGET_SEASON = "2025"

    state = get_current_state()
    with open("leagues.json", "r") as f:
        config = json.load(f)[TARGET_SEASON]

    logging.info("--- Checking for new weekly data ---")
    query = YahooFantasySportsQuery(
        league_id=config["league_id"], game_code="nfl", game_id=config["game_id"],
        yahoo_consumer_key=YAHOO_CONSUMER_KEY, yahoo_consumer_secret=YAHOO_CONSUMER_SECRET,
        env_file_location=Path("."), save_token_data_to_env_file=True
    )
    current_league_week = query.get_league_info().current_week
    last_completed_week = current_league_week - 1

    needs_refresh = False
    if args.force_refresh:
        logging.info("Force refresh flag detected. Regenerating all data.")
        needs_refresh = True
    elif last_completed_week > state['last_processed_week']:
        logging.info(f"New completed week detected (Week {last_completed_week}). Regenerating data.")
        needs_refresh = True
    elif not (DATA_DIR / "preview_data.json").exists() or not (DATA_DIR / "report_card_data.json").exists():
        logging.info("Data files are missing. Triggering a data generation process.")
        needs_refresh = True
    else:
        logging.info("No new weekly data found. Building site with existing data.")

    if needs_refresh:
        logging.info("Clearing weekly cache files...")
        # Preserve the main historical data cache, but clear out any weekly
        # or other temporary cache files.
        preserved_cache_file = "raw_api_cache.pkl"
        for item in CACHE_DIR.glob('*'):
            if item.is_file() and item.name != preserved_cache_file:
                try:
                    item.unlink()
                    logging.info(f"  - Removed {item.name}")
                except OSError as e:
                    logging.error(f"Error removing cache file {item}: {e}")

        logging.info("\n--- Running Data Generation Processes ---")
        # Run data generation processes in the correct order
        # 1. Update the raw data cache with the new week's data.
        update_raw_data_cache(TARGET_SEASON, last_completed_week)
        # 2. Rebuild historical data (this is a prerequisite for accolades).
        run_full_historical_build()
        # 3. Generate the preview for the current week.
        run_preview_process(TARGET_SEASON, current_league_week)
        # 4. Generate all-time accolades from the fully updated historical data.
        generate_accolades_data()
        # 5. Process last week's results, which can now compare against fresh accolades.
        run_report_process(TARGET_SEASON, last_completed_week)

        state['last_processed_week'] = last_completed_week
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        logging.info(f"State updated. Last processed week is now {last_completed_week}.")

    build_html_from_data()
    logging.info("\n✅ Y2K Statsbook build complete!")

if __name__ == "__main__":
    main()