// Portfolio\Education_Villa\edu_core\static\edu_core\js\home.js

// Add interactivity, like animating the search bar focus
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-container input[type="search"]');
    const searchForm = document.querySelector('.search-container form');
    const courseCardsContainer = document.querySelector('.course-cards');

    searchInput.addEventListener('focus', function() {
        this.parentNode.classList.add('focused');
    });

    searchInput.addEventListener('blur', function() {
        this.parentNode.classList.remove('focused');
    });

    // Handle AJAX search
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent the default form submission

        const formData = new FormData(searchForm);
        const searchQuery = formData.get('q');

        // Perform an AJAX request to search courses
        fetch(`${searchForm.action}?q=${encodeURIComponent(searchQuery)}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest', // Important for Django to identify it as an AJAX request
            },
        })
        .then(response => response.json())
        .then(data => {
            courseCardsContainer.innerHTML = ''; // Clear existing course cards

            if (data.courses.length > 0) {
                data.courses.forEach(course => {
                    const courseCard = document.createElement('div');
                    courseCard.classList.add('course-card');

                    let imageHtml = '';
                    if (course.image_url) {
                        imageHtml = `<img src="${course.image_url}" alt="${course.name}" class="course-image">`;
                    }

                    courseCard.innerHTML = `
                        ${imageHtml}
                        <a href="/courses/${course.id}/"><h3>${course.name}</h3></a>
                        <p>${course.description}</p>
                    `;

                    // Append the course card first
                    courseCardsContainer.appendChild(courseCard);

                    // Add the fade-in class after a slight delay to trigger the animation
                    requestAnimationFrame(() => {
                        courseCard.classList.add('fade-in');
                    });
                });
            } else {
                // If no courses are found, show a message
                courseCardsContainer.innerHTML = '<p>No courses found.</p>';
            }
        })
        .catch(error => console.error('Error fetching courses:', error));
    });
});

// JavaScript to create the wave effect:
document.querySelector('.hero').addEventListener('mousemove', function (e) {
    const wave = document.createElement('div');
    wave.classList.add('wave');
    wave.style.left = `${e.clientX - 20}px`; // Smaller offset for smoother waves
    wave.style.top = `${e.clientY - 70}px`;
    this.appendChild(wave);

    // Remove the wave after the animation ends
    wave.addEventListener('animationend', () => {
        wave.remove();
    });
});
