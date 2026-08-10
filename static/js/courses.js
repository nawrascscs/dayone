document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('course-search');
    const searchButton = document.getElementById('course-search-button');
    const filterSelect = document.getElementById('course-skill-filter');
    const coursesGrid = document.getElementById('courses-grid');
    const pagination = document.getElementById('courses-pagination');

    const queryState = {
        q: '',
        skill: '',
        page: 1,
        per_page: 9
    };

    const defaultSkills = ['Python', 'JavaScript', 'Java', 'CSS', 'HTML', 'C++', 'Machine Learning', 'Data Analysis'];

    function renderFilterOptions() {
        if (!filterSelect) return;
        defaultSkills.forEach((skill) => {
            const option = document.createElement('option');
            option.value = skill;
            option.textContent = skill;
            filterSelect.appendChild(option);
        });
    }

    function renderCourses(data) {
        coursesGrid.innerHTML = '';
        if (!data.courses.length) {
            coursesGrid.innerHTML = '<p class="page-note">No courses match your search. Try a broader query.</p>';
            pagination.innerHTML = '';
            return;
        }

        data.courses.forEach((course) => {
            const card = document.createElement('article');
            card.className = 'course-card';
            card.innerHTML = `
                <h3>${course.title}</h3>
                <p>${course.description ? course.description.slice(0, 140) + '...' : 'No description available.'}</p>
                <div class="course-meta">
                    <span class="badge primary">${course.instructor || 'Instructor TBD'}</span>
                    ${course.match_score !== undefined ? `<span class="badge">Match: ${course.match_score}%</span>` : ''}
                </div>
                <div class="badge-row">
                    ${course.skill_requirements.map((skill) => `<span class="badge">${skill}</span>`).join('')}
                </div>
                <div class="card-footer">
                    <a class="button secondary" href="/courses/${course.id}">View details</a>
                </div>
            `;
            coursesGrid.appendChild(card);
        });

        const pages = Math.ceil(data.total / data.per_page);
        pagination.innerHTML = '';
        for (let index = 1; index <= pages; index += 1) {
            const pageButton = document.createElement('button');
            pageButton.type = 'button';
            pageButton.className = 'button ghost';
            pageButton.textContent = index;
            if (index === data.page) {
                pageButton.classList.add('primary');
            }
            pageButton.addEventListener('click', () => {
                queryState.page = index;
                fetchCourses();
            });
            pagination.appendChild(pageButton);
        }
    }

    async function fetchCourses() {
        const params = new URLSearchParams({
            q: queryState.q,
            skill: queryState.skill,
            page: queryState.page,
            per_page: queryState.per_page
        });
        const response = await fetch(`/api/courses?${params.toString()}`);
        const data = await response.json();
        if (response.ok) {
            renderCourses(data);
        } else {
            coursesGrid.innerHTML = `<p class="error-message">${data.error || 'Unable to load courses.'}</p>`;
            pagination.innerHTML = '';
        }
    }

    if (searchButton) {
        searchButton.addEventListener('click', () => {
            queryState.q = searchInput.value.trim();
            queryState.skill = filterSelect.value;
            queryState.page = 1;
            fetchCourses();
        });
    }

    if (filterSelect) {
        filterSelect.addEventListener('change', () => {
            queryState.skill = filterSelect.value;
            queryState.page = 1;
            fetchCourses();
        });
    }

    if (searchInput) {
        searchInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                searchButton.click();
            }
        });
    }

    renderFilterOptions();
    fetchCourses();
});
