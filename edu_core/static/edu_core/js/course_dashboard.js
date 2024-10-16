// Portfolio\Education_Villa\edu_core\static\edu_core\js\course_dashboard.js

document.addEventListener('DOMContentLoaded', function () {
    // Ensure that the CSRF token is accessible
    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        console.error("CSRF token not found. Ensure the CSRF token is present on the page.");
    }
});

// Open Tab Functionality
function openTab(event, tabName) {
    // Hide all tab contents
    const tabContents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove("active");
    }

    // Remove 'active' class from all tabs
    const tabs = document.getElementsByClassName("tab");
    for (let i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove("active");
    }

    // Show the current tab content and highlight the tab
    document.getElementById(tabName).classList.add("active");
    event.currentTarget.classList.add("active");
}

// Toggle Course Status (Pause/Resume)
function toggleCourseStatus(courseId, pause) {
    const csrfToken = getCSRFToken();

    if (!csrfToken) {
        console.error("CSRF token is not available.");
        return;
    }

    // Send the request to toggle the course status
    fetch(`/courses/${courseId}/toggle_pause/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ pause: pause })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload to reflect changes
            location.reload();
        } else {
            alert('Failed to update course status.');
        }
    })
    .catch(error => {
        console.error("Error updating course status:", error);
        alert('An error occurred while updating the course status.');
    });
}

// Utility Function to Get CSRF Token
function getCSRFToken() {
    const form = document.getElementById('pause-course-form');
    return form ? form.querySelector('[name=csrfmiddlewaretoken]').value : null;
}

// Ban or Unban Function
function toggleBan(registrationId, currentBanStatus) {
    const csrfToken = getCSRFToken();

    if (!csrfToken) {
        console.error("CSRF token is not available.");
        return;
    }

    // Toggle the ban status
    const newBanStatus = !currentBanStatus;

    console.log("Sending request to toggle ban status for registration ID:", registrationId);
    console.log("New Ban Status:", newBanStatus);

    fetch(`/registrations/${registrationId}/toggle_ban/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ is_banned: newBanStatus })
    })
    .then(response => {
        console.log("Response received with status:", response.status);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log("Ban status updated successfully.");
            location.reload();  // Refresh to update button labels and states
        } else {
            console.error('Failed to update ban status:', data.error);
            alert('Failed to update ban status.');
        }
    })
    .catch(error => {
        console.error("Error updating ban status:", error);
        alert('An error occurred while updating the ban status.');
    });
}

// Unregister Studen Function
function removeStudent(registrationId) {
    if (!confirm("Are you sure you want to remove this student from the course?")) {
        return;
    }

    fetch(`/registrations/${registrationId}/remove/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();  // Refresh to remove the student from the list
        } else {
            alert('Failed to remove student.');
        }
    });
}