import { createBarChart, createLineChart, createPieChart } from './charts.js';

/**
 * Initialize vote analysis charts
 * @param {object} data - The data for the charts
 */
export function initVoteAnalysisCharts(data) {
    // Overall vote distribution chart
    createPieChart('overallVoteChart', {
        labels: data.vote_types.labels,
        datasets: [{
            label: 'Vote Distribution',
            data: data.vote_types.counts,
            backgroundColor: [
                'rgba(255, 99, 132, 0.7)',  // Red for corrupt
                'rgba(75, 192, 192, 0.7)', // Green for not corrupt
                'rgba(255, 205, 86, 0.7)'  // Yellow for undecided
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(255, 205, 86, 1)'
            ],
            borderWidth: 1
        }]
    }, {
        plugins: {
            legend: {
                position: 'right',
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.raw || 0;
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = Math.round((value / total) * 100);
                        return `${label}: ${value} (${percentage}%)`;
                    }
                }
            }
        }
    });
    
    // Vote trends chart
    createLineChart('voteTrendsChart', {
        labels: data.vote_trends.dates,
        datasets: [
            {
                label: 'Corrupt',
                data: data.vote_trends.corrupt,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            },
            {
                label: 'Not Corrupt',
                data: data.vote_trends.not_corrupt,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            },
            {
                label: 'Undecided',
                data: data.vote_trends.undecided,
                borderColor: 'rgba(255, 205, 86, 1)',
                backgroundColor: 'rgba(255, 205, 86, 0.2)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }
        ]
    }, {
        yAxisTitle: 'Number of Votes',
        xAxisTitle: 'Date'
    });
    
    // Top judges chart
    createBarChart('topJudgesChart', {
        labels: data.top_judges.names,
        datasets: [{
            label: 'Vote Count',
            data: data.top_judges.counts,
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    }, {
        indexAxis: 'y',  // Horizontal bar chart
        scales: {
            x: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Number of Votes'
                }
            }
        }
    });
    
    // Judge vote distribution chart
    const judgeDistributionData = data.judge_vote_distribution;
    const judgeNames = Object.keys(judgeDistributionData);
    const corruptVotes = [];
    const notCorruptVotes = [];
    const undecidedVotes = [];
    
    judgeNames.forEach(name => {
        corruptVotes.push(judgeDistributionData[name].corrupt || 0);
        notCorruptVotes.push(judgeDistributionData[name].not_corrupt || 0);
        undecidedVotes.push(judgeDistributionData[name].undecided || 0);
    });
    
    createBarChart('judgeDistributionChart', {
        labels: judgeNames,
        datasets: [
            {
                label: 'Corrupt',
                data: corruptVotes,
                backgroundColor: 'rgba(255, 99, 132, 0.7)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            },
            {
                label: 'Not Corrupt',
                data: notCorruptVotes,
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            },
            {
                label: 'Undecided',
                data: undecidedVotes,
                backgroundColor: 'rgba(255, 205, 86, 0.7)',
                borderColor: 'rgba(255, 205, 86, 1)',
                borderWidth: 1
            }
        ]
    }, {
        scales: {
            x: {
                stacked: true,
                title: {
                    display: true,
                    text: 'Judge Name'
                }
            },
            y: {
                stacked: true,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Number of Votes'
                }
            }
        }
    });
}
