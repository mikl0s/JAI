import { fetchAndDisplayJudges } from './judges.js';
import { initializeModals } from './modals.js';
import { initializeForm } from './form.js';

document.addEventListener('DOMContentLoaded', () => {
    // USA Only Toggle
    const usaOnlyToggle = document.getElementById('usa-only-toggle');

    // Initial fetch
    fetchAndDisplayJudges();

    // Add event listener for the toggle
    usaOnlyToggle.addEventListener('change', () => {
        fetchAndDisplayJudges(usaOnlyToggle.checked);
    });

    // Initialize modals
    const { modal, form } = initializeModals();

    // Initialize form
    initializeForm(modal, form);
});
