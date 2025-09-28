import json
import logging
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

# Import the core logic from our tool scripts
from tools.generate_preview import run_preview_process
from tools.dashboard_weekly_report import run_report_process
from tools.init_history import run_full_historical_build

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

# --- Directory Setup ---
DATA_DIR = Path("data")
CACHE_DIR = Path("cache")
SITE_DIR = Path("site")
TEMPLATES_DIR = Path("templates")

DATA_DIR.mkdir(exist_ok=True)
SITE_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True) # yfpy will use this
STATE_FILE = DATA_DIR / "state.json"

# --- Yahoo API Credentials ---
YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

# --- Pickle Compatibility Fix ---
# This function is added here to allow unpickling of old cache files that
# were created when this function was defined in a different module.
# Once all cache files are regenerated, this can be removed.
def default_alt_standing():
    return {'wins': 0, 'losses': 0, 'pf': 0.0}

def get_current_state():
    if not STATE_FILE.exists():
        return {"last_processed_week": 0}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def generate_weekly_preview_html(data):
    """
    Generates the weekly_preview.html file from a data object.
    """
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
        .commissioner-note h4 {{ margin: 0 0 5px 0; color: #fff; font-size: 1em; }}
        .social-section {{ margin-top: 20px; border-top: 1px solid #050; padding-top: 15px; }}
        .reactions button {{ background: #020; border: 1px solid #070; color: #0f0; padding: 5px 10px; margin-right: 5px; cursor: pointer; }}
        .reactions button:hover {{ background: #040; color: #fff; }}
        .comments {{ margin-top: 15px; }}
        .comment {{ margin-bottom: 10px; font-size: 0.9em; }}
        .comment-author {{ font-weight: bold; color: #fff; }}
        .comment-reply {{ margin-left: 20px; border-left: 1px solid #050; padding-left: 10px; }}
        .comment-form textarea {{ background: #010; color: #0f0; border: 1px solid #070; width: 100%; padding: 8px; font-family: 'Courier New', Courier, monospace; margin-bottom: 5px; }}
        .comment-form button {{ background: #030; border: 1px solid #090; color: #fff; padding: 8px 15px; cursor: pointer; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-bar"><a href="index.html">« System.Index</a></div>
        <h1>{season} Y2K: Week {preview_week} Preview</h1>
    """]

    for matchup in data['matchups']:
        team1_data = matchup['team1']
        team2_data = matchup['team2']
        h2h = matchup['h2h']

        html_parts.append('<div class="matchup">')
        html_parts.append(f"""
            <div class="matchup-header">
                {team1_data['rank']}. <span class="team-name">{team1_data['name']}</span> <span class="record">{team1_data['record']}</span>
                vs 
                {team2_data['rank']}. <span class="team-name">{team2_data['name']}</span> <span class="record">{team2_data['record']}</span>
            </div>
            <div class="h2h-stats">
        """)

        if h2h:
            html_parts.append(f"<p><strong>Season H2H:</strong> {h2h['reg_h2h']}</p>")
            html_parts.append(f"<p><strong>Streak:</strong> {h2h['streak_info']}</p>")
            html_parts.append(f"<p>{h2h['playoff_h2h_display']}</p>")
        else:
            html_parts.append("<p><strong>Season H2H:</strong> 0-0</p>")
            html_parts.append("<p><strong>Streak:</strong> First Meeting</p>")
            html_parts.append("<p><strong>Playoffs H2H:</strong> 0-0</p>")

        html_parts.append('</div>') # End h2h-stats

        # --- Commissioner's Note & Social Section ---
        html_parts.append("""
            <div class="commissioner-note">
                <h4>Commissioner's Note</h4>
                <p>This is where the commissioner's analysis of the matchup will go, providing expert insight and witty commentary.</p>
            </div>
            <div class="social-section">
                <div class="reactions">
                    <button>👍</button> <button>🔥</button> <button>🤣</button> <button>🗑️</button>
                </div>
                <div class="comments">
                    <div class="comment"><span class="comment-author">Boaz:</span> This is a certified lock of the week.</div>
                    <div class="comment comment-reply"><span class="comment-author">Dylan:</span> You wish. Prepare to get wrecked. <button class="reactions" style="padding: 2px 5px; font-size: 0.8em;">Reply</button></div>
                    <form class="comment-form" style="margin-top: 15px;"><textarea rows="2" placeholder="> Add a comment..."></textarea><button type="submit">Submit</button></form>
                </div>
            </div>
        """)
        html_parts.append('</div>') # End matchup

    html_parts.append("</div></body></html>")
    
    final_html = "\n".join(html_parts)
    output_filename = SITE_DIR / "weekly_preview.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    logging.info(f"✅ Successfully generated HTML preview: {output_filename.name}")

def generate_weekly_report_html(data):
    """
    Generates the weekly_report.html file from a data object.
    """
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
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; border: 1px solid #050; }}
        th, td {{ padding: 4px 6px; text-align: left; border: 1px solid #050; }}
        thead th {{ background-color: #030; font-weight: bold; color: #fff; }}
        tbody tr:nth-child(even) {{ background-color: #010; }}
        .delta-pos {{ color: #3f3; }}
        .delta-neg {{ color: #f33; }}
        .accolades {{ margin-top: 20px; padding: 0; list-style: none; }}
        .accolades li {{ background: #010; border: 1px solid #050; padding: 15px; margin-bottom: 15px; }}
        .accolades strong {{ color: #fff; }}
        .accolades .count {{ color: #aaa; font-size: 0.9em; }}
        .social-section {{ margin-top: 15px; border-top: 1px solid #050; padding-top: 10px; }}
        .reactions button {{ background: #020; border: 1px solid #070; color: #0f0; padding: 5px 10px; margin-right: 5px; cursor: pointer; }}
        .reactions button:hover {{ background: #040; color: #fff; }}
        .comments {{ margin-top: 10px; }}
        .comment {{ margin-bottom: 8px; font-size: 0.9em; }}
        .comment-author {{ font-weight: bold; color: #fff; }}
        .comment-form textarea {{ background: #010; color: #0f0; border: 1px solid #070; width: 100%; padding: 8px; font-family: 'Courier New', Courier, monospace; margin-bottom: 5px; font-size: 0.9em; }}
        .comment-form button {{ background: #030; border: 1px solid #090; color: #fff; padding: 5px 10px; cursor: pointer; font-weight: bold; font-size: 0.9em; }}
    </style>
</head>
<body>
<div class="container">
    <div class="nav-bar"><a href="index.html">« System.Index</a></div>
    <h1>{data['season']} Y2K: Week {report_week} Report Card</h1>
    """]

    html_parts.append("<h2>🌌 Alternative Universe Standings 🌌</h2>")
    html_parts.append("<table><thead><tr><th>Alt</th><th>ΔA</th><th>W?</th><th>Real</th><th>ΔR</th><th>W?</th><th>Name</th><th>Wk Score</th><th>Total PF</th><th>Alt Rec</th><th>Real Rec</th></tr></thead><tbody>")

    for row in data['alt_standings_rows']:
        html_parts.append(f"""
            <tr>
                <td>{row['alt_rank']}</td>
                <td class='{row['alt_delta_class']}'>{row['alt_delta_str']}</td>
                <td>{row['alt_win_marker']}</td>
                <td>{row['current_real_rank']}</td>
                <td class='{row['real_delta_class']}'>{row['real_delta_str']}</td>
                <td>{row['real_win_marker']}</td>
                <td>{row['manager']}</td>
                <td>{row['weekly_score']:.2f}</td>
                <td>{row['total_pf']:.2f}</td>
                <td>{row['alt_record']}</td>
                <td>{row['real_record']}</td>
            </tr>
        """)

    html_parts.append("</tbody></table>")

    html_parts.append("<h2>🏆 Weekly Accolades 🏆</h2><ul class='accolades'>")
    for accolade in data['accolades']:
        html_parts.append(f"""
        <li>
            <p>{accolade}</p>
            <div class="social-section">
                <div class="reactions">
                    <button>👍</button> <button>😢</button> <button>🤣</button>
                </div>
                <form class="comment-form" style="margin-top: 10px;"><textarea rows="1" placeholder="> React..."></textarea><button type="submit">Submit</button></form>
            </div>
        </li>
        """)
    html_parts.append("</ul></div></body></html>")

    final_html = "\n".join(html_parts)
    output_filename = SITE_DIR / "weekly_report.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    logging.info(f"✅ Successfully generated HTML report: {output_filename.name}")

def generate_index_html():
    """
    Generates the main index.html landing page.
    """
    try:
        with open(TEMPLATES_DIR / "index.html", "r", encoding="utf-8") as f:
            template_html = f.read()
    except FileNotFoundError:
        logging.error("Could not find templates/index.html. Cannot build index page.")
        return

    # Conditionally create the links
    preview_link_html = '<a href="weekly_preview.html">» Weekly Matchup Preview</a>' if (DATA_DIR / "preview_data.json").exists() else ''
    report_link_html = '<a href="weekly_report.html">» Weekly Report Card</a>' if (DATA_DIR / "report_card_data.json").exists() else ''

    # Replace placeholders
    html = template_html.replace("{PREVIEW_LINK}", preview_link_html)
    html = html.replace("{REPORT_LINK}", report_link_html)

    with open(SITE_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)
    logging.info("✅ Successfully generated HTML index: index.html")

def build_html_from_data():
    """Generates all HTML pages from their respective JSON data files."""
    logging.info("\n--- Building HTML from data files ---")
    # Clear the site directory first to ensure no old files remain
    for item in SITE_DIR.glob('*'):
        if item.is_file():
            item.unlink()

    try:
        with open(DATA_DIR / "preview_data.json", "r", encoding="utf-8") as f:
            preview_data = json.load(f)
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
    
    # Always generate the index page
    generate_index_html()
    logging.info("--- HTML build complete ---")

def main():
    """
    Main orchestrator. Checks for new data, refreshes if necessary, and builds the site.
    """
    parser = argparse.ArgumentParser(description="Build the Y2K Statsbook website.")
    parser.add_argument('--force-refresh', action='store_true', help="Force a refresh of all data from the API.")
    args = parser.parse_args()

    # --- ONE-TIME SETUP CHECK ---
    # If the core historical data file is missing, run the full one-time build process.
    if not (DATA_DIR / "h2h_records.json").exists():
        logging.warning("Core historical data not found. Running one-time setup...")
        run_full_historical_build()

    # --- CONFIGURATION ---
    TARGET_SEASON = "2025"

    # --- LOAD STATE & CONFIG ---
    state = get_current_state()
    with open("leagues.json", "r") as f:
        config = json.load(f)[TARGET_SEASON]

    # --- CHECK IF DATA REFRESH IS NEEDED ---
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
    # Add a check to see if data files are missing, which happens on a cold start.
    elif not (DATA_DIR / "preview_data.json").exists() or not (DATA_DIR / "report_card_data.json").exists():
        logging.info("Data files are missing. Triggering a data generation process.")
        needs_refresh = True
    else:
        logging.info("No new weekly data found. Building site with existing data.")

    if needs_refresh:
        logging.info("\n--- Running Data Generation Processes ---")
        # Run the report process for the last completed week
        run_report_process(TARGET_SEASON, last_completed_week)
        # Run the preview process for the current week
        run_preview_process(TARGET_SEASON, current_league_week)
        
        # Update state file
        state['last_processed_week'] = last_completed_week
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        logging.info(f"State updated. Last processed week is now {last_completed_week}.")

    # --- BUILD THE HTML SITE ---
    build_html_from_data()
    logging.info("\n✅ Y2K Statsbook build complete!")

if __name__ == "__main__":
    main()