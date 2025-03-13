import { createBarChart, createPieChart, createLineChart } from './charts.js';

/**
 * Initialize submission analysis charts
 * @param {object} data - The data for the charts
 */
export function initSubmissionAnalysisCharts(data) {
    const pageData = document.getElementById('page-data');
    if (!pageData) return;
    
    try {
        // Parse the data from the hidden element
        const chartData = JSON.parse(pageData.dataset.pageData);
        
        // Create status distribution chart
        if (document.getElementById('submissionChart')) {
            createPieChart('submissionChart', {
                labels: chartData.status.labels,
                datasets: [{
                    data: chartData.status.counts,
                    backgroundColor: [
                        'rgba(255, 205, 86, 0.7)', // Yellow for pending
                        'rgba(75, 192, 192, 0.7)', // Green for approved
                        'rgba(255, 99, 132, 0.7)'  // Red for rejected
                    ],
                    borderColor: [
                        'rgba(255, 205, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 1
                }]
            }, {
                title: 'Submission Status Distribution',
                legend: true
            });
        }
        
        // Create submissions over time chart
        if (document.getElementById('submissionStatusChart') && chartData.dates) {
            createLineChart('submissionStatusChart', {
                labels: chartData.dates.labels,
                datasets: [{
                    label: 'Submissions Over Time',
                    data: chartData.dates.counts,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.1,
                    fill: true
                }]
            }, {
                yAxisTitle: 'Number of Submissions',
                xAxisTitle: 'Date'
            });
        }
    } catch (error) {
        console.error('Error initializing submission analysis charts:', error);
    }
}
