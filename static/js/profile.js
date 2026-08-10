document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname !== '/profile') return;

    const profileContent = document.getElementById('profile-content');
    const token = localStorage.getItem('authToken');

    if (!token) {
        profileContent.innerHTML = '<p>Please login to access your profile.</p>';
        return;
    }

    function buildSkillList(skills) {
        if (!skills.length) {
            return '<li>No skills added yet.</li>';
        }

        return skills.map((skill) => `<li>${skill.skill.name} - ${skill.proficiency_level}</li>`).join('');
    }

    function renderProfile(user) {
        profileContent.innerHTML = `
            <div class="user-info-card">
                <h2>${user.username}</h2>
                <p><strong>Email:</strong> ${user.email}</p>
                <p><strong>Phone:</strong> ${user.phone || 'Not provided'}</p>
                <p><strong>Age:</strong> ${user.age || 'Not provided'}</p>
                <p><strong>Major:</strong> ${user.major || 'Not provided'}</p>
            </div>
            <div class="stats-grid">
                <div class="stats-card"><strong>${user.skills.length}</strong><span>Skills added</span></div>
                <div class="stats-card"><strong>${user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</strong><span>Member since</span></div>
                <div class="stats-card"><strong>${user.skills.filter((item) => item.proficiency_level === 'advanced').length}</strong><span>Advanced skills</span></div>
            </div>
            <section class="recommendation-panel">
                <div class="recommendation-header">
                    <div>
                        <h2>About you</h2>
                        <p class="info-note">Update your profile fields below for a more personalized experience.</p>
                    </div>
                </div>
                <div class="profile-card">
                    <label for="profile-major">Major</label>
                    <input id="profile-major" type="text" value="${user.major || ''}" />
                    <label for="profile-phone">Phone</label>
                    <input id="profile-phone" type="text" value="${user.phone || ''}" />
                    <label for="profile-age">Age</label>
                    <input id="profile-age" type="number" min="10" max="110" value="${user.age || ''}" />
                    <button id="save-profile" class="button primary" type="button">Save changes</button>
                </div>
            </section>
            <section class="recommendation-panel">
                <h2>Your skills</h2>
                <ul>${buildSkillList(user.skills)}</ul>
            </section>
        `;

        const saveButton = document.getElementById('save-profile');
        saveButton.addEventListener('click', async () => {
            const updated = {
                major: document.getElementById('profile-major').value.trim(),
                phone: document.getElementById('profile-phone').value.trim(),
                age: Number(document.getElementById('profile-age').value) || null
            };
            const response = await fetch('/api/users/me', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updated)
            });
            const data = await response.json();
            if (response.ok) {
                renderProfile(data.user);
                alert('Profile updated successfully.');
            } else {
                alert(data.error || 'Unable to update profile.');
            }
        });
    }

    fetch('/api/users/me', {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    }).then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
            profileContent.innerHTML = `<p>${data.error || 'Unable to load profile.'}</p>`;
            return;
        }
        renderProfile(data.user);
    });
});
