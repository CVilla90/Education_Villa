// Portfolio\Education_Villa\edu_core\static\edu_core\js\home.js

// Add interactivity, like animating the search bar focus
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-container input[type="search"]');
    
    searchInput.addEventListener('focus', function() {
        this.parentNode.classList.add('focused');
    });

    searchInput.addEventListener('blur', function() {
        this.parentNode.classList.remove('focused');
    });
});
