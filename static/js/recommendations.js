document.addEventListener('DOMContentLoaded', () => {
    const recommendationsGrid = document.getElementById('recommendations-grid');
    const refreshButton = document.getElementById('refresh-recommendations');
    const emptyNotice = document.getElementById('recommendations-empty');
    const token = localStorage.getItem('authToken');

    async function loadRecommendations() {
        recommendationsGrid.innerHTML = '<p class="page-note">Loading recommendations...</p>';
        emptyNotice.textContent = '';

        if (!token) {
            recommendationsGrid.innerHTML = '';
            emptyNotice.textContent = 'Login to see your personalized recommendations.';
            return;
        }

        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ skills: [] })
        });
        const data = await response.json();
        if (!response.ok) {
            recommendationsGrid.innerHTML = '';
            emptyNotice.textContent = data.error || 'Unable to fetch recommendations.';
            return;
        }

        if (!data.recommendations.length) {
            recommendationsGrid.innerHTML = '';
            emptyNotice.textContent = 'No recommendations available yet.';
            return;
        }

        recommendationsGrid.innerHTML = data.recommendations.map((course) => `
            <article class="course-card">
                <h3>${course.title}</h3>
                <p>${course.description ? course.description.slice(0, 120) + '...' : 'No description available.'}</p>
                <div class="badge-row">
                    <span class="badge primary">Match ${course.match_score}%</span>
                    <span class="badge explanation">${course.explanation}</span>
                </div>
                <div class="card-footer">
                    <a class="button secondary" href="/courses/${course.id}">View details</a>
                </div>
            </article>
        `).join('');
    }

    refreshButton.addEventListener('click', loadRecommendations);
    loadRecommendations();
});
