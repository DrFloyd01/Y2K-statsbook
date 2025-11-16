
document.addEventListener('DOMContentLoaded', () => {
    const homepage = document.getElementById('homepage');

    // Fetch data for a specific week (e.g., 2024, Week 8)
    fetch('/api/week/2024/8')
        .then(response => response.json())
        .then(data => {
            renderHomepage(data);
        })
        .catch(error => {
            console.error('Error fetching weekly data:', error);
            homepage.innerHTML = '<p>Error loading data. Please try again later.</p>';
        });
});

function renderHomepage(data) {
    const homepage = document.getElementById('homepage');

    // Clear existing content
    homepage.innerHTML = '';

    // Render Game of the Week
    const gotw = data.game_of_the_week;
    const gameOfTheWeekHTML = `
        <article>
            <header>
                <h2>Game of the Week</h2>
            </header>
            <h3>${gotw.manager1} (${gotw.streak1}) vs. ${gotw.manager2} (${gotw.streak2})</h3>
            <p>Projection: ${gotw.projection}</p>
        </article>
    `;

    // Render Other Matchups
    const matchupsHTML = data.matchups.map(matchup => `
        <li>
            <strong>${matchup.manager1} (${matchup.streak1})</strong> vs. <strong>${matchup.manager2} (${matchup.streak2})</strong>
            <br>
            <small>Projection: ${matchup.projection}</small>
        </li>
    `).join('');

    // Render Commissioner Notes
    const commissionerNotesHTML = `
        <article>
            <header>
                <h3>Commissioner's Notes</h3>
            </header>
            <p>${data.commissioner_notes}</p>
        </article>
    `;

    homepage.innerHTML = `
        ${gameOfTheWeekHTML}
        <section>
            <h2>Matchups</h2>
            <ul>
                ${matchupsHTML}
            </ul>
        </section>
        ${commissionerNotesHTML}
    `;
}
