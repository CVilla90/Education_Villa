// Portfolio\Education_Villa\edu_core\static\edu_core\js\drag_and_drop.js

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('questions-container');
    let draggedItem = null;

    container.addEventListener('dragstart', function(e) {
        if (e.target.classList.contains('question-card')) {
            draggedItem = e.target;
            setTimeout(function() {
                e.target.style.display = 'none';
            }, 0);
        }
    });

    container.addEventListener('dragend', function(e) {
        if (draggedItem) {
            setTimeout(function() {
                draggedItem.style.display = 'block';
                draggedItem = null;
            }, 0);
        }
    });

    container.addEventListener('dragover', function(e) {
        e.preventDefault();
    });

    container.addEventListener('dragenter', function(e) {
        e.preventDefault();
        if (e.target.classList.contains('question-card')) {
            e.target.style.border = '1px dashed #ccc';
        }
    });

    container.addEventListener('dragleave', function(e) {
        if (e.target.classList.contains('question-card')) {
            e.target.style.border = 'none';
        }
    });

    container.addEventListener('drop', function(e) {
        if (e.target.classList.contains('question-card')) {
            e.target.style.border = 'none';
            container.insertBefore(draggedItem, e.target);
            saveOrder(); // Automatically save order on drop
        }
    });

    function saveOrder() {
        const questionOrder = [];
        const questions = document.querySelectorAll('.question-card');
        questions.forEach((question, index) => {
            questionOrder.push({
                id: question.getAttribute('data-id'),
                order: index + 1
            });
        });

        const activityId = container.getAttribute('data-activity-id');  // Ensure the activity ID is correctly set
        const saveOrderUrl = `/activities/${activityId}/save_question_order/`;  // Updated the endpoint to match urls.py

        fetch(saveOrderUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ order: questionOrder })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                alert('Failed to save order.');
            }
        })
        .catch(error => {
            console.error('Error saving order:', error);
            alert('Failed to save order.');
        });
    }
});
