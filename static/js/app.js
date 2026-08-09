document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');

    if (registerForm) {
        const skillCheckboxes = Array.from(document.querySelectorAll('.skill-checkbox'));
        const skillLevelSelectors = Array.from(document.querySelectorAll('.skill-level'));

        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const selectedSkills = skillCheckboxes
                .filter((checkbox) => checkbox.checked)
                .map((checkbox) => {
                    const skillName = checkbox.value;
                    const levelSelect = skillLevelSelectors.find((select) => select.dataset.skill === skillName);
                    return {
                        name: skillName,
                        proficiency_level: levelSelect ? levelSelect.value : 'beginner'
                    };
                });

            document.getElementById('skills-input').value = JSON.stringify(selectedSkills);

            const payload = {
                username: event.target.username.value.trim(),
                email: event.target.email.value.trim(),
                password: event.target.password.value,
                phone: event.target.phone.value.trim(),
                age: event.target.age.value ? Number(event.target.age.value) : null,
                major: event.target.major.value.trim(),
                skills: selectedSkills
            };

            const emailRegex = /^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$/;
            const phoneRegex = /^\d{10}$/;

            if (!emailRegex.test(payload.email)) {
                alert('Please enter a valid email address with @ and a domain suffix like .com or .net.');
                return;
            }

            if (payload.phone && !phoneRegex.test(payload.phone)) {
                alert('Phone number must contain exactly 10 digits.');
                return;
            }

            if (payload.age !== null && (payload.age < 10 || payload.age > 110)) {
                alert('Age must be between 10 and 110.');
                return;
            }

            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('authToken', data.token);
                window.location.href = '/profile';
            } else {
                alert(data.error || 'Registration failed.');
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const payload = {
                email: event.target.email.value,
                password: event.target.password.value
            };

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('authToken', data.token);
                window.location.href = '/profile';
            } else {
                alert(data.error || 'Login failed.');
            }
        });
    }

    const authToken = localStorage.getItem('authToken');
    const navRegister = document.getElementById('nav-register');
    const navLogin = document.getElementById('nav-login');
    const navLogout = document.getElementById('nav-logout');

    const homeCtaButtons = document.getElementById('home-cta-buttons');

    if (authToken) {
        if (navRegister) navRegister.style.display = 'none';
        if (navLogin) navLogin.style.display = 'none';
        if (navLogout) navLogout.style.display = 'inline-block';
        if (homeCtaButtons) homeCtaButtons.style.display = 'none';
    } else {
        if (navLogout) navLogout.style.display = 'none';
        if (homeCtaButtons) homeCtaButtons.style.display = 'flex';
    }

    if (navLogout) {
        navLogout.addEventListener('click', () => {
            localStorage.removeItem('authToken');
            window.location.href = '/';
        });
    }

    if (window.location.pathname === '/profile') {
        const token = localStorage.getItem('authToken');
        const profileContent = document.getElementById('profile-content');
        if (!token) {
            profileContent.innerHTML = '<p>Please login to access your profile.</p>';
            return;
        }

        fetch('/api/users/me', {
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }
        }).then(async (response) => {
            const data = await response.json();
            if (!response.ok) {
                profileContent.innerHTML = `<p>${data.error || 'Unable to load profile.'}</p>`;
                return;
            }
            const user = data.user;
            const skills = user.skills.map((skillItem) => `<li>${skillItem.skill.name} - ${skillItem.proficiency_level}</li>`).join('');
            profileContent.innerHTML = `
                <p><strong>Username:</strong> ${user.username}</p>
                <p><strong>Email:</strong> ${user.email}</p>
                <p><strong>Phone:</strong> ${user.phone || 'Not provided'}</p>
                <p><strong>Age:</strong> ${user.age || 'Not provided'}</p>
                <p><strong>Major:</strong> ${user.major || 'Not provided'}</p>
                <div>
                    <h2>Skills</h2>
                    <ul>${skills || '<li>No skills added yet.</li>'}</ul>
                </div>
            `;
        });
    }
});
