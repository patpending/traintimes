/**
 * UK Train Departure Board - Client-side JavaScript
 *
 * Handles real-time updates, animations, and interactivity
 * for the departure board display.
 */

class DepartureBoard {
  constructor(options = {}) {
    this.stationCrs = options.stationCrs || 'PAD';
    this.refreshInterval = options.refreshInterval || 30000; // 30 seconds
    this.numDepartures = options.numDepartures || 6;
    this.container = document.getElementById('departures-container');
    this.clockElement = document.getElementById('clock');
    this.dateElement = document.getElementById('date');
    this.lastUpdatedElement = document.getElementById('last-updated');
    this.stationNameElement = document.getElementById('station-name');

    this.departures = [];
    this.isLoading = false;
    this.error = null;

    this.init();
  }

  init() {
    // Start clock
    this.updateClock();
    setInterval(() => this.updateClock(), 1000);

    // Initial fetch
    this.fetchDepartures();

    // Set up auto-refresh
    setInterval(() => this.fetchDepartures(), this.refreshInterval);

    // Set up station selector if present
    const stationSelect = document.getElementById('station-select');
    if (stationSelect) {
      stationSelect.addEventListener('change', (e) => {
        this.stationCrs = e.target.value;
        this.fetchDepartures();
      });
      this.loadStations(stationSelect);
    }
  }

  updateClock() {
    const now = new Date();

    if (this.clockElement) {
      this.clockElement.textContent = now.toLocaleTimeString('en-GB', {
        hour: '2-digit',
        minute: '2-digit'
      });
    }

    if (this.dateElement) {
      this.dateElement.textContent = now.toLocaleDateString('en-GB', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    }
  }

  async loadStations(selectElement) {
    try {
      const response = await fetch('./api/stations');
      const data = await response.json();

      data.stations.forEach(station => {
        const option = document.createElement('option');
        option.value = station.crs;
        option.textContent = `${station.name} (${station.crs})`;
        if (station.crs === this.stationCrs) {
          option.selected = true;
        }
        selectElement.appendChild(option);
      });
    } catch (error) {
      console.error('Failed to load stations:', error);
    }
  }

  async fetchDepartures() {
    if (this.isLoading) return;

    this.isLoading = true;
    this.showLoading();

    try {
      const url = `./api/departures?station=${this.stationCrs}&num=${this.numDepartures}`;
      const response = await fetch(url);
      const data = await response.json();

      if (data.error) {
        this.showError(data.error);
        return;
      }

      this.departures = data.departures;
      this.renderDepartures();

      if (this.stationNameElement) {
        this.stationNameElement.textContent = data.station_name;
      }

      if (this.lastUpdatedElement) {
        this.lastUpdatedElement.textContent = `Last updated: ${data.time}`;
      }

      this.error = null;
    } catch (error) {
      console.error('Failed to fetch departures:', error);
      this.showError('Failed to connect to departure service');
    } finally {
      this.isLoading = false;
    }
  }

  showLoading() {
    if (!this.container) return;

    // Only show loading on initial load
    if (this.departures.length === 0) {
      this.container.innerHTML = `
        <div class="loading">
          Loading departures<span class="loading-dots"></span>
        </div>
      `;
    }
  }

  showError(message) {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="error-message">
        <strong>Error:</strong> ${this.escapeHtml(message)}
      </div>
    `;
  }

  renderDepartures() {
    if (!this.container) return;

    if (this.departures.length === 0) {
      this.container.innerHTML = `
        <div class="no-departures">
          No departures currently scheduled
        </div>
      `;
      return;
    }

    const html = this.departures.map((dep, index) => this.renderDepartureRow(dep, index)).join('');
    this.container.innerHTML = html;

    // Start calling points animations
    this.animateCallingPoints();
  }

  renderDepartureRow(departure, index) {
    const statusClass = this.getStatusClass(departure.status, departure.is_cancelled);
    const expectedText = departure.is_cancelled ? 'Cancelled' : departure.expected_time;
    const callingPoints = departure.calling_points || [];
    const callingPointsText = callingPoints.map(cp => cp.station).join('  •  ');

    const cancelledClass = departure.is_cancelled ? 'cancelled' : '';
    const reason = departure.cancel_reason || departure.delay_reason || '';

    return `
      <div class="departure-row ${cancelledClass}" data-time="${departure.scheduled_time}">
        <div class="time">${departure.scheduled_time}</div>
        <div class="destination-col">
          <div class="destination">${this.escapeHtml(departure.destination)}</div>
          <div class="operator">${this.escapeHtml(departure.operator)}</div>
          ${callingPointsText ? `
            <div class="calling-points-container">
              <span class="calling-points ${index === 0 ? 'scrolling' : ''}" data-text="${this.escapeHtml(callingPointsText)}">
                <span class="calling-label">Calling at: </span>${this.escapeHtml(callingPointsText)}
              </span>
            </div>
          ` : ''}
        </div>
        <div class="platform">${departure.platform}</div>
        <div class="expected ${statusClass}">
          ${expectedText}
          ${reason ? `<div class="reason">${this.escapeHtml(reason)}</div>` : ''}
        </div>
      </div>
    `;
  }

  getStatusClass(status, isCancelled) {
    if (isCancelled) return 'cancelled';
    switch (status) {
      case 'delayed':
        return 'delayed';
      case 'cancelled':
        return 'cancelled';
      case 'on_time':
      default:
        return 'on-time';
    }
  }

  animateCallingPoints() {
    // The first departure has scrolling calling points
    const scrollingElements = this.container.querySelectorAll('.calling-points.scrolling');
    scrollingElements.forEach(el => {
      const text = el.getAttribute('data-text');
      if (text && text.length > 50) {
        // Long text gets animation
        el.style.animationDuration = `${Math.max(15, text.length / 5)}s`;
      } else {
        // Short text doesn't scroll
        el.classList.remove('scrolling');
      }
    });
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Get station from data attribute or URL
  const boardElement = document.querySelector('.departure-board');
  const stationCrs = boardElement?.dataset.station ||
                     new URLSearchParams(window.location.search).get('station') ||
                     'PAD';

  window.departureBoard = new DepartureBoard({
    stationCrs: stationCrs,
    refreshInterval: 30000,
    numDepartures: 6
  });
});
