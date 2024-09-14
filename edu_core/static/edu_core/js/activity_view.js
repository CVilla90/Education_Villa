// Portfolio\Education_Villa\edu_core\static\edu_core\js\activity_view.js

document.addEventListener('DOMContentLoaded', function () {
    console.log('Page loaded, initializing script...');

    const questionsContainer = document.getElementById('questions-container');

    if (questionsContainer) {
        console.log('Questions container found:', questionsContainer);

        // Retrieve the JSON data safely
        const answersData = document.getElementById('answers-data');
        if (answersData) {
            try {
                let answersText = answersData.textContent;
                
                // Clean up the JSON string by removing special characters
                answersText = answersText.replace(/\\n/g, "\\n")
                                         .replace(/\\'/g, "\\'")
                                         .replace(/\\"/g, '\\"')
                                         .replace(/\\&/g, "\\&")
                                         .replace(/\\r/g, "\\r")
                                         .replace(/\\t/g, "\\t")
                                         .replace(/\\b/g, "\\b")
                                         .replace(/\\f/g, "\\f");
                answersText = answersText.replace(/[\u0000-\u001F]+/g,""); // Remove non-printable characters
                
                const answers = JSON.parse(answersText);
                console.log('Retrieved answers from session:', answers);

                // Iterate through each question and set the checked state based on session data
                Object.entries(answers).forEach(([questionId, optionId]) => {
                    console.log(`Setting checked state for question ID: ${questionId}, option ID: ${optionId}`);
                    const radioInput = document.querySelector(`input[name="question_${questionId}"][value="${optionId}"]`);
                    if (radioInput) {
                        radioInput.checked = true;
                        console.log(`Checked input found and marked for question ID: ${questionId}, option ID: ${optionId}`);
                    } else {
                        console.warn(`Input not found for question ID: ${questionId}, option ID: ${optionId}`);
                    }
                });
            } catch (error) {
                console.error('Error parsing answers JSON:', error);
            }
        } else {
            console.warn('Answers data element not found.');
        }
    } else {
        console.warn('Questions container not found on the page.');
    }

    const activityForm = document.getElementById('activity-form');
    if (activityForm) {
        activityForm.addEventListener('submit', function (event) {
            console.log('Form submitted, processing current answers...');
            const formData = new FormData(activityForm);
            formData.forEach((value, key) => {
                console.log(`Storing in sessionStorage: ${key} = ${value}`);
                sessionStorage.setItem(key, value);
            });
            console.log('Answers stored in sessionStorage.');
        });
    } else {
        console.warn('Activity form not found on the page.');
    }

    document.querySelectorAll('input[type="radio"]').forEach(input => {
        const storedValue = sessionStorage.getItem(input.name);
        if (storedValue) {
            console.log(`Checking stored input for ${input.name} with value ${storedValue}`);
        }
        if (storedValue && input.value === storedValue) {
            input.checked = true;
            console.log(`Checked input restored for ${input.name} with value ${storedValue}`);
        }
    });

    const retryButton = document.getElementById('retry-button');
    if (retryButton) {
        retryButton.addEventListener('click', function () {
            console.log('Retry button clicked, clearing sessionStorage...');
            sessionStorage.clear();  // Clear all stored answers
            console.log('Session storage cleared.');
        });
    } else {
        console.warn('Retry button not found on the page.');
    }
});
