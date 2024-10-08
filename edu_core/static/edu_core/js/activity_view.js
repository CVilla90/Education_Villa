// Portfolio\Education_Villa\edu_core\static\edu_core\js\activity_view.js

document.addEventListener('DOMContentLoaded', function () {
    console.log('Page loaded, initializing script...');

    const questionsContainer = document.getElementById('questions-container');

    if (questionsContainer) {
        console.log('Questions container found:', questionsContainer);

        // Retrieve answers from sessionStorage if available and restore checked state
        const answers = JSON.parse(sessionStorage.getItem('answers') || '{}');
        Object.keys(answers).forEach(questionId => {
            const selectedOptionId = answers[questionId];
            const radioInput = document.querySelector(`input[name="question_${questionId}"][value="${selectedOptionId}"]`);
            if (radioInput) {
                radioInput.checked = true;
                console.log(`Restored answer for question ${questionId} with option ${selectedOptionId}`);
            }
        });

        // Store the answers in sessionStorage upon selection
        document.querySelectorAll('input[type="radio"]').forEach(input => {
            input.addEventListener('change', function () {
                const questionId = this.name.split('_')[1];
                answers[questionId] = this.value;
                sessionStorage.setItem('answers', JSON.stringify(answers));
                console.log(`Stored answer for question ${questionId} with option ${this.value}`);
            });
        });
    }

    // Restore feedback state from sessionStorage if available
    document.querySelectorAll('.feedback-toggle button').forEach(button => {
        const questionId = button.getAttribute('onclick').match(/toggleFeedback\('(\d+)'\)/)[1];
        const storedFeedbackState = sessionStorage.getItem(`feedback_${questionId}`);
        const feedbackContent = document.getElementById(`feedback-${questionId}`);
        if (storedFeedbackState === 'expanded' && feedbackContent) {
            feedbackContent.style.display = 'block';
            button.querySelector('.arrow').textContent = '▲';
            button.querySelector('.feedback-expand').textContent = 'Hide Feedback';
        }
        button.addEventListener('click', function () {
            if (feedbackContent.style.display === 'block') {
                sessionStorage.setItem(`feedback_${questionId}`, 'collapsed');
            } else {
                sessionStorage.setItem(`feedback_${questionId}`, 'expanded');
            }
        });
    });

    const retryButton = document.getElementById('retry-button');
    if (retryButton) {
        retryButton.addEventListener('click', function () {
            console.log('Retry button clicked, clearing sessionStorage...');
            sessionStorage.clear();  // Clear all stored feedback states and answers
            console.log('Session storage cleared.');
        });
    } else {
        console.warn('Retry button not found on the page.');
    }
});
