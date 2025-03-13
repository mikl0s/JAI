import { createBarChart, createLineChart } from './charts.js';

/**
 * Initialize geo votes charts
 * @param {object} data - The data for the charts
 */
export function initGeoVotesCharts(data) {
    // Country chart
    const countryData = data.countries;
    const topCountries = countryData.slice(0, 10); // Show top 10 countries
    
    createBarChart('countryChart', {
        labels: topCountries.map(item => item.country_name),
        datasets: [{
            label: 'Votes by Country',
            data: topCountries.map(item => item.vote_count),
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    }, {
        yAxisTitle: 'Number of Votes',
        xAxisTitle: 'Country'
    });
    
    // Region chart - group by country
    const regionData = data.regions;
    const regionDatasets = [];
    
    // Group by country
    const countriesWithRegions = [...new Set(regionData.map(item => item.country_name))];
    const colorPalette = [
        'rgba(54, 162, 235, 0.5)', // blue
        'rgba(255, 99, 132, 0.5)', // red
        'rgba(75, 192, 192, 0.5)', // green
        'rgba(255, 205, 86, 0.5)', // yellow
        'rgba(153, 102, 255, 0.5)' // purple
    ];
    
    countriesWithRegions.forEach((country, index) => {
        const countryRegions = regionData.filter(item => item.country_name === country);
        regionDatasets.push({
            label: country,
            data: countryRegions.map(item => item.vote_count),
            backgroundColor: colorPalette[index % colorPalette.length],
            borderColor: colorPalette[index % colorPalette.length].replace('0.5', '1'),
            borderWidth: 1
        });
    });
    
    // Get all unique regions across all countries
    const allRegions = [];
    regionData.forEach(item => {
        if (!allRegions.includes(item.region)) {
            allRegions.push(item.region);
        }
    });
    
    createBarChart('regionChart', {
        labels: allRegions,
        datasets: regionDatasets
    }, {
        yAxisTitle: 'Number of Votes',
        xAxisTitle: 'Region',
        stacked: true,
        scales: {
            y: {
                stacked: true
            }
        }
    });
    
    // Hourly chart
    const hourlyLabels = Array.from({length: 24}, (_, i) => i.toString().padStart(2, '0') + ':00');
    
    createLineChart('hourlyChart', {
        labels: hourlyLabels,
        datasets: [{
            label: 'Votes by Hour',
            data: data.hourly,
            backgroundColor: 'rgba(75, 192, 192, 0.5)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
        }]
    }, {
        yAxisTitle: 'Number of Votes',
        xAxisTitle: 'Hour of Day (24h format)'
    });
    
    // Daily chart
    const dayLabels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    createBarChart('dailyChart', {
        labels: dayLabels,
        datasets: [{
            label: 'Votes by Day of Week',
            data: data.daily,
            backgroundColor: 'rgba(153, 102, 255, 0.5)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 1
        }]
    }, {
        yAxisTitle: 'Number of Votes',
        xAxisTitle: 'Day of Week'
    });
}
