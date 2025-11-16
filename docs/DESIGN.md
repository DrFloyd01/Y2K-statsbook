# Y2K Statsbook Design Document

## 1. Project Vision

The goal of the Y2K Statsbook is to create a dynamic, engaging, and data-rich web application for a fantasy football league. It will serve as a central hub for league members to view current and historical data in an intuitive and visually appealing way. The application will move beyond simple standings and provide deep insights into matchups, historical performance, and league accolades, fostering a more immersive and competitive league experience.

## 2. Core Features

### 2.1. Homepage: The Weekly Hub
- **Primary View:** Displays all matchups for the current week.
- **Game of the Week:** A prominently featured matchup, possibly determined by rivalry, standings, or playoff implications.
- **Matchup Cards:** Each matchup will display:
    - Team names and logos.
    - Current season W/L record.
    - Current W/L streak (e.g., W3, L1).
    - Projected scores (if available).
    - A direct link to the "Matchup Deep Dive" view.
- **Commissioner's Notes:** A dedicated section for the commissioner to post weekly notes, commentary, or announcements.

### 2.2. Matchup Deep Dive
- **View:** Accessible by clicking on a matchup card from the homepage.
- **Content:**
    - **All-Time Head-to-Head Record:** Displays the lifetime W/L record between the two managers.
    - **Historical Game Log:** A table or list of all previous matchups, including the week, year, final score, and outcome.
    - **Scoring Summary:** Key statistics from their history, such as average score, highest score, lowest score, and largest margin of victory.

### 2.3. Weekly Report Card
- **View:** A dedicated page to showcase the results and accolades from the *previous* week.
- **Accolades Section:** A list of weekly awards (e.g., "Top Scorer," "Biggest Blowout," "Closest Match").
    - Each accolade will show the winner, their metric (e.g., score, margin of victory), and a link to the accolade's history page.
- **Power Rankings:** A section for the league's weekly power rankings.

### 2.4. Accolade History
- **View:** A page dedicated to a single accolade (e.g., "Top Scorer").
- **Content:** A historical log of all winners of that award, showing the week, year, winner, and the associated metric.

### 2.5. The Alternate Universe
- **Concept:** A creative space for "what if" scenarios.
- **Potential Features:**
    - **All-Play Record:** Show what a team's record would be if they played every other team every week.
    - **Draft Rewind:** Re-ranking draft picks based on end-of-season performance.
    - **Strength of Schedule Analysis.**

### 2.6. Historical Archive
- **View:** A catalog of all historical data.
- **Content:**
    - **Past Weekly Previews:** A searchable/filterable archive of all previous commissioner's notes and weekly previews.
    - **Past Report Cards:** An archive of all previous weekly report cards.
    - **All-Time Accolades:** A summary of all-time accolade winners.

## 3. Proposed Tech Stack & Architecture

- **Backend:** **Flask**. It is a lightweight Python framework that is well-suited for building a JSON API to serve data to the frontend. It integrates well with the existing Python scripts in the project.
- **Frontend:** **Vanilla JavaScript with Web Components**. To keep the frontend simple, performant, and free of complex build steps, we will use modern vanilla JavaScript. We can structure the UI into reusable Web Components for things like `matchup-card`, `accolade-item`, etc.
- **Styling:** **Pico.css**. A lightweight, class-less CSS framework for a clean, modern look out of the box with minimal effort.

This approach avoids the overhead of larger frameworks like React or Vue, which are unnecessary for this project's scope.

## 4. API Design (Data Contracts)

The Flask backend will expose the following JSON endpoints:

- `GET /api/week/{year}/{week}`: Get all data for a specific week's homepage.
- `GET /api/matchup/{manager1_id}/{manager2_id}`: Get the complete head-to-head history for two managers.
- `GET /api/report_card/{year}/{week}`: Get the report card data for a specific week.
- `GET /api/accolade/{accolade_id}`: Get the historical data for a specific accolade.
- `GET /api/archive/{type}`: Get historical data for `previews` or `report_cards`.

## 5. Project Structure

```
/
├── app.py                  # Flask backend server
├── build_site.py
├── leagues.json
├── Pipfile
├── docs/
│   └── DESIGN.md           # This document
├── data/                     # Raw data
├── static/                   # Frontend assets
│   ├── css/
│   │   └── style.css       # Custom styles
│   ├── js/
│   │   ├── main.js         # Main application logic
│   │   └── components/     # Reusable web components
│   │       ├── MatchupCard.js
│   │       └── AccoladeItem.js
│   └── images/
│       └── logos/          # Team logos
└── templates/
    └── index.html          # Main HTML shell
```

## 6. Next Steps
1. Clean up the previously generated files that don't align with this design.
2. Set up the basic Flask `app.py` with a single API endpoint to test the data pipeline.
3. Develop the `index.html` shell and link the necessary CSS and JS files.
4. Implement the first feature: The Homepage.
