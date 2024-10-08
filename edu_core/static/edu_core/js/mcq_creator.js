// Portfolio\Education_Villa\edu_core\static\edu_core\js\mcq_creator.js

// Ensure that when a radio button is selected, the "correct_option" is updated properly
document.addEventListener('DOMContentLoaded', function () {
    const addOptionButton = document.getElementById('add-option');
    const optionFormsContainer = document.getElementById('option-forms');
    const totalFormsInput = document.querySelector('input[name="form-TOTAL_FORMS"]');
    
    let optionCount = parseInt(totalFormsInput.value); // Current number of options

    addOptionButton.addEventListener('click', function () {
        optionCount++;

        // Create a new option form
        const newOptionForm = document.createElement('div');
        newOptionForm.classList.add('option-form');

        // Set placeholders dynamically
        newOptionForm.innerHTML = `
            <label for="id_form-${optionCount}-text">Text:</label>
            <input type="text" name="form-${optionCount}-text" maxlength="255" required id="id_form-${optionCount}-text" placeholder="Option ${optionCount + 1}">
            <label for="id_form-${optionCount}-is_correct">Is correct:</label>
            <input type="radio" name="correct_option" value="${optionCount}" id="id_form-${optionCount}-is_correct">
            <button type="button" class="remove-option btn btn-danger">Remove Option</button>
        `;

        // Append the new form to the container
        optionFormsContainer.appendChild(newOptionForm);

        // Update the management form count
        totalFormsInput.value = optionCount + 1;

        // Add remove button functionality
        newOptionForm.querySelector('.remove-option').addEventListener('click', function () {
            newOptionForm.remove();
            optionCount--;
            updateTotalForms();
        });

        // Ensure only one correct answer is selectable
        updateCorrectOptionSelection();
    });

    // Function to update total forms count
    function updateTotalForms() {
        totalFormsInput.value = document.querySelectorAll('.option-form').length;
    }

    // Function to ensure only one correct answer is selectable
    function updateCorrectOptionSelection() {
        const correctOptionInputs = document.querySelectorAll('input[type="radio"][name="correct_option"]');
        correctOptionInputs.forEach(input => {
            input.addEventListener('change', () => {
                correctOptionInputs.forEach(otherInput => {
                    if (otherInput !== input) {
                        otherInput.checked = false;
                    }
                });
            });
        });
    }

    // Initial setup for radio buttons to ensure only one can be selected
    updateCorrectOptionSelection();
});
