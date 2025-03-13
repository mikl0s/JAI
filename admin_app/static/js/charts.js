/**
 * Charts module for the admin app
 * Handles creation and configuration of all charts
 */

/**
 * Creates a bar chart
 * @param {string} elementId - The ID of the canvas element
 * @param {object} chartData - The data for the chart
 * @param {object} options - Chart options
 */
export function createBarChart(elementId, chartData, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: options.yAxisTitle || 'Value'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: options.xAxisTitle || 'Category'
                    },
                    stacked: options.stacked || false
                }
            },
            ...options
        }
    });
}

/**
 * Creates a line chart
 * @param {string} elementId - The ID of the canvas element
 * @param {object} chartData - The data for the chart
 * @param {object} options - Chart options
 */
export function createLineChart(elementId, chartData, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: options.yAxisTitle || 'Value'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: options.xAxisTitle || 'Category'
                    }
                }
            },
            ...options
        }
    });
}

/**
 * Creates a pie chart
 * @param {string} elementId - The ID of the canvas element
 * @param {object} chartData - The data for the chart
 * @param {object} options - Chart options
 */
export function createPieChart(elementId, chartData, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    return new Chart(ctx, {
        type: 'pie',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...options
        }
    });
}
