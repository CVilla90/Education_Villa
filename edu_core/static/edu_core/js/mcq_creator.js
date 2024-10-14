// Portfolio\Education_Villa\edu_core\static\edu_core\js\mcq_creator.js

document.addEventListener('DOMContentLoaded', function () {
    const addOptionButton = document.getElementById('add-option');
    const optionFormsContainer = document.getElementById('option-forms');
    const totalFormsInput = document.querySelector('input[name="form-TOTAL_FORMS"]');

    if (!addOptionButton || !optionFormsContainer || !totalFormsInput) {
        console.error("Missing form elements. Please ensure all elements are present in the form.");
        return;
    }

    let optionCount = parseInt(totalFormsInput.value); // Current number of options

    addOptionButton.addEventListener('click', function () {
        // Create a new option form
        const newOptionForm = document.createElement('div');
        newOptionForm.classList.add('option-form');

        // Set placeholders dynamically
        newOptionForm.innerHTML = `
            <div id="form-${optionCount}">
                <input type="hidden" name="form-${optionCount}-id" id="id_form-${optionCount}-id">
                <input type="hidden" name="form-${optionCount}-DELETE" id="id_form-${optionCount}-DELETE">
                <label for="id_form-${optionCount}-text">Text:</label>
                <input type="text" name="form-${optionCount}-text" maxlength="255" required id="id_form-${optionCount}-text" placeholder="Option ${optionCount + 1}">
                <label for="correct_option_${optionCount}">Is correct:</label>
                <input type="radio" name="correct_option" value="${optionCount}" id="correct_option_${optionCount}">
                <button type="button" class="remove-option btn btn-danger">Remove Option</button>
            </div>
        `;

        // Append the new form to the container
        optionFormsContainer.appendChild(newOptionForm);

        // Update the management form count
        optionCount++;
        totalFormsInput.value = optionCount;

        // Add remove button functionality
        addRemoveOptionListener(newOptionForm.querySelector('.remove-option'));

        // Ensure only one correct answer is selectable
        updateCorrectOptionSelection();
    });

    // Function to add remove button functionality
    function addRemoveOptionListener(removeButton) {
        removeButton.addEventListener('click', function () {
            const parentForm = removeButton.closest('.option-form');
            if (parentForm) {
                // Instead of removing the form from the DOM, mark it as deleted and hide it
                const deleteField = parentForm.querySelector('input[name$="-DELETE"]');
                const textField = parentForm.querySelector('input[type="text"]');
                if (deleteField) {
                    deleteField.value = 'on';
                    parentForm.style.display = 'none';

                    // Remove the required attribute so it doesn't block form submission
                    if (textField) {
                        textField.removeAttribute('required');
                    }
                } else {
                    console.error("DELETE field not found in the option form.");
                }
            } else {
                console.error("Option form not found for the remove button.");
            }
        });
    }

    // Add the remove functionality to all existing remove buttons
    document.querySelectorAll('.remove-option').forEach(button => {
        addRemoveOptionListener(button);
    });

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
