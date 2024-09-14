// Portfolio\Education_Villa\edu_core\static\edu_core\js\cb_creator.js

document.addEventListener('DOMContentLoaded', function () {
    console.log('Quill editor initialization...');

    // Initialize Quill editor
    var quill = new Quill('#editor', {
        theme: 'snow',
        modules: {
            toolbar: {
                container: [
                    ['bold', 'italic', 'underline'],
                    ['link', 'image', 'video'],
                    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                    [{ 'header': [1, 2, 3, false] }],
                    ['clean']
                ],
                handlers: {
                    image: imageHandler
                }
            }
        }
    });

    // Custom image handler for Quill
    function imageHandler() {
        const input = document.createElement('input');
        input.setAttribute('type', 'file');
        input.setAttribute('accept', 'image/*');
        input.click();

        input.onchange = () => {
            const file = input.files[0];
            if (!file) {
                return;
            }

            const formData = new FormData();
            formData.append('image', file);

            fetch('/upload_image/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')  // Make sure to replace with your CSRF token handling
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.url) {
                    const range = quill.getSelection();
                    quill.insertEmbed(range.index, 'image', data.url);
                    console.log(`Image inserted at index ${range.index}: ${data.url}`);
                } else {
                    console.error('Failed to upload image:', data.error);
                }
            })
            .catch(error => console.error('Error uploading image:', error));
        };
    }

    // Helper function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Select the form correctly to prevent 'form is not defined' error
    const form = document.querySelector('.cb-form');
    if (!form) {
        console.error('Form element not found');
        return;
    }

    form.addEventListener('submit', function (event) {
        event.preventDefault();  // Prevent default form submission

        // Get JSON content from Quill editor
        const quillContent = quill.getContents();  // Fetches the Delta format
        const jsonContent = JSON.stringify(quillContent);  // Convert Delta to JSON string
        console.log('Quill content to submit:', jsonContent);

        // Set the content into the hidden textarea for form submission
        const textField = document.querySelector('input[name="text"]');
        if (textField) {
            textField.value = jsonContent;  // Set JSON string as the value
            console.log('Updated hidden input content:', textField.value);
        } else {
            console.error('Hidden input for "text" not found.');
            return;
        }

        // Submit the form using Fetch API
        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-CSRFToken': getCookie('csrftoken')  // Include CSRF token
            }
        })
        .then(response => {
            if (!response.ok) {
                console.error('Server responded with an error:', response.status, response.statusText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();  // Parse JSON from the response
        })
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                alert(`Error: ${data.error}`);  // Display the error to the user
            } else {
                // Handle success and redirect if needed
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    console.log('Form submitted successfully:', data);
                    alert('Content block added successfully!');
                    // Optionally refresh the page or update the UI dynamically here
                }
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            alert('An error occurred while submitting the form. Please try again.');
        });
    });
});
