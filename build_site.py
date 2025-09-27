import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def generate_weekly_preview_html(data, output_filename="weekly_preview.html"):
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
        .streak-holder {{ font-weight: bold; color: #afa; }}
        .playoff-details {{ font-size: 0.85em; color: #aaa; }}
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
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    logging.info(f"✅ Successfully generated HTML preview: {output_filename}")

def generate_weekly_report_html(data, output_filename="weekly_report.html"):
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
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    logging.info(f"✅ Successfully generated HTML report: {output_filename}")

def main():
    """
    Main orchestrator for building the static site from data files.
    """
    logging.info("--- Building Static Site ---")

    try:
        with open("preview_data.json", "r") as f:
            preview_data = json.load(f)
        generate_weekly_preview_html(preview_data)
    except FileNotFoundError:
        logging.warning("preview_data.json not found. Skipping weekly preview generation.")
    except Exception as e:
        logging.error(f"Error generating weekly preview: {e}")

    try:
        with open("report_card_data.json", "r") as f:
            report_data = json.load(f)
        generate_weekly_report_html(report_data)
    except FileNotFoundError:
        logging.warning("report_card_data.json not found. Skipping weekly report generation.")
    except Exception as e:
        logging.error(f"Error generating weekly report: {e}")

    logging.info("--- Static Site Build Complete ---")

if __name__ == "__main__":
    main()