// frontend/app.js - Fixed Version

const API_BASE = '';

async function getWeather() {
    const cityInput = document.getElementById('cityInput');
    const city = cityInput.value.trim();
    
    if (!city) {
        showError("Please enter a city name");
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/weather?city=${encodeURIComponent(city)}`);
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        displayWeather(data);

    } catch (error) {
        console.error(error);
        showError("Could not connect to server. Make sure backend is running on port 8000.");
    } finally {
        showLoading(false);
    }
}

function displayWeather(data) {
    document.getElementById('weatherContainer').classList.remove('hidden');
    document.getElementById('error').classList.add('hidden');

    // Current Weather
    document.getElementById('locationName').textContent = data.location.name;
    document.getElementById('temperature').textContent = `${Math.round(data.current.data.temperature_c)}°C`;
    document.getElementById('condition').textContent = data.current.data.condition.replace('_', ' ').toUpperCase();
    document.getElementById('feelsLike').textContent = `Feels like ${Math.round(data.current.data.feels_like_c || data.current.data.temperature_c)}°C`;

    // Summary & Recommendation
    document.getElementById('summary').textContent = data.summary || "No summary available.";
    document.getElementById('recommendation').textContent = data.recommendation || "Enjoy your day!";

    // Details
    const currentData = data.current.data;
    document.getElementById('humidity').textContent = `${currentData.humidity_percent || 'N/A'}%`;
    document.getElementById('windSpeed').textContent = `${Math.round(currentData.wind_speed_kmh || 0)} km/h`;
    document.getElementById('visibility').textContent = `${currentData.visibility_km ? currentData.visibility_km.toFixed(1) : 'N/A'} km`;
    document.getElementById('uvIndex').textContent = currentData.uv_index ? currentData.uv_index.toFixed(1) : 'N/A';

    // Alerts
    const alertsSection = document.getElementById('alertsSection');
    const alertsContainer = document.getElementById('alerts');
    alertsContainer.innerHTML = '';

    if (data.alerts && data.alerts.length > 0) {
        alertsSection.classList.remove('hidden');
        data.alerts.forEach(alert => {
            const alertEl = document.createElement('div');
            alertEl.className = 'alert-item';
            alertEl.innerHTML = `
                <strong>${alert.title}</strong>
                <p>${alert.description}</p>
                <small>Severity: ${alert.severity.toUpperCase()}</small>
            `;
            alertsContainer.appendChild(alertEl);
        });
    } else {
        alertsSection.classList.add('hidden');
    }

    // Render Forecasts - This was causing the error
    renderHourlyForecast(data.hourly_forecast);
    renderDailyForecast(data.daily_forecast);
}

// Hourly Forecast
function renderHourlyForecast(forecast) {
    const container = document.getElementById('hourlyForecast');
    if (!container) return;
    container.innerHTML = '';

    if (!forecast || !forecast.data_points || forecast.data_points.length === 0) {
        container.innerHTML = '<p style="color:#888; text-align:center; grid-column:1/-1;">No hourly forecast available</p>';
        return;
    }

    forecast.data_points.slice(0, 12).forEach(point => {
        const time = new Date(point.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
        const card = document.createElement('div');
        card.className = 'forecast-card';
        card.innerHTML = `
            <div class="forecast-time">${time}</div>
            <div class="forecast-temp">${Math.round(point.temperature_c)}°C</div>
            <div class="forecast-condition">${point.condition.replace('_', ' ')}</div>
        `;
        container.appendChild(card);
    });
}

// Daily Forecast
function renderDailyForecast(forecast) {
    const container = document.getElementById('dailyForecast');
    if (!container) return;
    container.innerHTML = '';

    if (!forecast || !forecast.data_points || forecast.data_points.length === 0) {
        container.innerHTML = '<p style="color:#888; text-align:center; grid-column:1/-1;">No daily forecast available</p>';
        return;
    }

    forecast.data_points.forEach(point => {
        const date = new Date(point.timestamp).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
        const card = document.createElement('div');
        card.className = 'forecast-card';
        card.innerHTML = `
            <div class="forecast-time">${date}</div>
            <div class="forecast-temp">${Math.round(point.temperature_c)}°C</div>
            <div class="forecast-condition">${point.condition.replace('_', ' ')}</div>
        `;
        container.appendChild(card);
    });
}

function showError(message) {
    const errorEl = document.getElementById('error');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
    document.getElementById('weatherContainer').classList.add('hidden');
}

function showLoading(isLoading) {
    document.getElementById('loading').classList.toggle('hidden', !isLoading);
    document.getElementById('weatherContainer').classList.toggle('hidden', isLoading);
}

// Enter key support
document.getElementById('cityInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') getWeather();
});

// Load on start
window.onload = () => getWeather();