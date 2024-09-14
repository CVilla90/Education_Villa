// Portfolio\Education_Villa\edu_core\static\edu_core\js\activity_edit.js

document.addEventListener('DOMContentLoaded', function() {
    // Function to send AJAX requests
    function sendAjaxRequest(url, data, method='POST') {
        return fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // Function to get CSRF token
            },
            body: JSON.stringify(data),
        }).then(response => response.json());
    }

    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                // Does this cookie string begin with the name we want?
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Attach event listeners to move up buttons
    document.querySelectorAll('.move-up-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const questionId = this.dataset.questionId;
            const url = this.dataset.url;

            sendAjaxRequest(url, { 'question_id': questionId })
                .then(data => {
                    if (data.success) {
                        // Update the DOM accordingly
                        // You can re-render the questions list or swap the elements
                        location.reload(); // Simple way to refresh the page content
                    } else {
                        alert('Error moving question up.');
                    }
                });
        });
    });

    // Attach event listeners to move down buttons
    document.querySelectorAll('.move-down-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const questionId = this.dataset.questionId;
            const url = this.dataset.url;

            sendAjaxRequest(url, { 'question_id': questionId })
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error moving question down.');
                    }
                });
        });
    });

    // Attach event listeners to remove question buttons
    document.querySelectorAll('.remove-question-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            if (!confirm('Are you sure you want to remove this question?')) {
                return;
            }
            const questionId = this.dataset.questionId;
            const url = this.dataset.url;

            sendAjaxRequest(url, { 'question_id': questionId })
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error removing question.');
                    }
                });
        });
    });

    // Attach event listeners to remove page buttons
    document.querySelectorAll('.remove-page-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            if (!confirm('Are you sure you want to remove this page?')) {
                return;
            }
            const pageNumber = this.dataset.pageNumber;
            const url = this.dataset.url;

            sendAjaxRequest(url, { 'page_number': pageNumber })
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error removing page.');
                    }
                });
        });
    });
});
