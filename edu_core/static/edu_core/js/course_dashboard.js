// Portfolio\Education_Villa\edu_core\static\edu_core\js\course_dashboard.js

function openTab(event, tabName) {
    // Hide all tab contents
    var tabContents = document.getElementsByClassName("tab-content");
    for (var i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove("active");
    }

    // Remove 'active' class from all tabs
    var tabs = document.getElementsByClassName("tab");
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove("active");
    }

    // Show the current tab content and highlight the tab
    document.getElementById(tabName).classList.add("active");
    event.currentTarget.classList.add("active");
}
