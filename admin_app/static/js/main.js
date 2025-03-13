import { showNotification, formatDate } from './utils.js';
import { initGeoVotesCharts } from './geo_votes.js';
import { initSuspiciousVotesCharts } from './suspicious_votes.js';
import { initVoteAnalysisCharts } from './vote_analysis.js';
import { initSubmissionAnalysisCharts } from './submission_analysis.js';

/**
 * Initialize the admin app
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize page-specific functionality based on the current page
    initCurrentPage();
});

/**
 * Initialize the current page based on its content
 */
function initCurrentPage() {
    // Geo Votes page
    if (document.getElementById('countryChart')) {
        try {
            const data = JSON.parse(document.getElementById('page-data').dataset.pageData || '{}');
            initGeoVotesCharts(data);
        } catch (error) {
            console.error('Error initializing geo votes charts:', error);
        }
    }
    
    // Suspicious Votes page
    if (document.getElementById('hourlyVoteChart')) {
        try {
            const hourlyVotes = JSON.parse(document.getElementById('page-data').dataset.hourlyVotes || '[]');
            initSuspiciousVotesCharts(hourlyVotes);
        } catch (error) {
            console.error('Error initializing suspicious votes charts:', error);
        }
    }
    
    // Vote Analysis page
    if (document.getElementById('overallVoteChart')) {
        try {
            const data = JSON.parse(document.getElementById('page-data').dataset.pageData || '{}');
            initVoteAnalysisCharts(data);
        } catch (error) {
            console.error('Error initializing vote analysis charts:', error);
        }
    }
    
    // Submission Analysis page
    if (document.getElementById('submissionChart')) {
        try {
            const data = JSON.parse(document.getElementById('page-data').dataset.pageData || '{}');
            initSubmissionAnalysisCharts(data);
        } catch (error) {
            console.error('Error initializing submission analysis charts:', error);
        }
    }
    
    // Initialize common functionality
    initCommonFunctionality();
}

/**
 * Initialize functionality common to all admin pages
 */
function initCommonFunctionality() {
    // Handle form submissions with AJAX
    document.querySelectorAll('form[data-ajax="true"]').forEach(form => {
        form.addEventListener('submit', handleAjaxFormSubmit);
    });
    
    // Initialize any notification messages
    const notificationElement = document.getElementById('notification-message');
    if (notificationElement && notificationElement.textContent.trim()) {
        showNotification(notificationElement.textContent, 5000);
    }
}

/**
 * Handle AJAX form submissions
 * @param {Event} event - The form submit event
 */
function handleAjaxFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const url = form.action;
    const method = form.method || 'POST';
    
    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'Operation successful', 3000);
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            } else if (form.dataset.reload === 'true') {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showNotification(data.error || 'Operation failed', 5000, 'error');
        }
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        showNotification('An error occurred. Please try again.', 5000, 'error');
    });
}
