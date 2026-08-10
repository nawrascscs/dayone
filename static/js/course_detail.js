document.addEventListener('DOMContentLoaded', () => {
    const courseId = window.location.pathname.split('/').pop();
    const titleNode = document.getElementById('course-title');
    const instructorNode = document.getElementById('course-instructor');
    const descriptionNode = document.getElementById('course-description');
    const sidebarInstructor = document.getElementById('sidebar-instructor');
    const sidebarSkills = document.getElementById('sidebar-skills');
    const relatedCourses = document.getElementById('related-courses');
    const enrollButton = document.getElementById('enroll-button');

    async function fetchCourse() {
        const response = await fetch(`/api/courses/${courseId}`);
        const data = await response.json();
        if (!response.ok) {
            titleNode.textContent = 'Course not found';
            descriptionNode.textContent = data.error || 'Unable to load course details.';
            return;
        }

        const course = data.course;
        titleNode.textContent = course.title;
        instructorNode.textContent = `Instructor: ${course.instructor || 'TBD'}`;
        sidebarInstructor.textContent = course.instructor || 'Instructor information is not available yet.';
        descriptionNode.innerHTML = course.description ? `<p>${course.description}</p>` : '<p>No description available.</p>';
        sidebarSkills.innerHTML = course.skill_requirements.length
            ? course.skill_requirements.map((skill) => `<span class="badge">${skill}</span>`).join('')
            : '<span class="badge">No requirements listed</span>';

        if (data.course.related_courses && data.course.related_courses.length) {
            relatedCourses.innerHTML = data.course.related_courses.map((related) => `
                <article class="related-card">
                    <h3>${related.title}</h3>
                    <p>${related.description ? related.description.slice(0, 100) + '...' : 'No description available.'}</p>
                    <a class="button ghost" href="/courses/${related.id}">View course</a>
                </article>
            `).join('');
        } else {
            relatedCourses.innerHTML = '<p class="page-note">No related courses found.</p>';
        }
    }

    enrollButton.addEventListener('click', () => {
        window.location.href = '/courses';
    });

    fetchCourse();
});
