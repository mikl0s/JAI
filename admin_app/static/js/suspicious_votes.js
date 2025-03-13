import { createBarChart } from './charts.js';

/**
 * Initialize suspicious votes charts
 * @param {Array} hourlyVotes - Hourly vote data
 */
export function initSuspiciousVotesCharts(hourlyVotes) {
    // Hourly vote chart
    const hourlyLabels = Array.from({length: 24}, (_, i) => i.toString().padStart(2, '0') + ':00');
    
    createBarChart('hourlyVoteChart', {
        labels: hourlyLabels,
        datasets: [{
            label: 'Votes per Hour',
            data: hourlyVotes,
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    }, {
        yAxisTitle: 'Number of Votes',
        xAxisTitle: 'Hour of Day (24h format)'
    });
}
