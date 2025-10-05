# Changelog

## [Unreleased] - 2025-10-05

### Features

- **All-Time Accolades Page**: A new, dedicated "All-Time Accolades" page (`all_time_accolades.html`) has been created to track and display historical records and leaderboards for various accolades.
- **Weekly Accolade Summary**: The weekly report now includes a summary of who has won each accolade in the current season, making it easier to track seasonal trends.
- **Record-Breaking Notifications**: The weekly report now highlights when a new season or all-time record is set for an accolade.

### Refactoring

- **Accolade Generation**: The logic for calculating accolades has been extracted from the dashboard scripts and centralized into a new `tools/generate_accolades.py` module. This improves modularity and makes the codebase easier to maintain.
- **Weekly Report Generation**: The weekly report generation logic has been moved from `dashboards/dashboard_weekly_report.py` to `tools/dashboard_weekly_report.py` and significantly refactored for clarity and to support the new features.
- **Data Flow**: The main `build_site.py` script now orchestrates the generation of all data, including the new accolade data, and then builds the corresponding HTML pages.

### Styling

- **Weekly Report Redesign**: The weekly report card has been redesigned with a new layout for standings and a card-based design for accolades, improving readability and visual appeal.
- **Weekly Preview Cleanup**: The weekly preview page has been streamlined, removing social media-style buttons and comments to focus on the matchup analysis.
- **Consistent Styling**: The styling across all generated pages has been updated and harmonized for a more consistent user experience.
