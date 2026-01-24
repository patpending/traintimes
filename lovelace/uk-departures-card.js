/**
 * UK Train Departures Card for Home Assistant
 * A custom Lovelace card that displays train departures in authentic UK station style
 */

class UKDeparturesCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this.config = {
      entity: config.entity,
      title: config.title || 'Departures',
      show_calling_points: config.show_calling_points !== false,
      show_clock: config.show_clock !== false,
      show_platform: config.show_platform !== false,
      num_departures: config.num_departures || 3,
      ...config
    };
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return {
      entity: 'sensor.train_departures',
      title: 'Departures',
      show_calling_points: true,
      show_clock: true,
      num_departures: 3
    };
  }

  render() {
    if (!this._hass || !this.config) return;

    const entity = this._hass.states[this.config.entity];
    if (!entity) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div style="padding: 16px; color: #ff6b6b;">
            Entity not found: ${this.config.entity}
          </div>
        </ha-card>
      `;
      return;
    }

    const departures = entity.attributes.departures || [];
    const stationName = entity.attributes.station_name || this.config.title;
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

    this.shadowRoot.innerHTML = `
      <style>
        ${this.getStyles()}
      </style>
      <ha-card>
        <div class="departure-board">
          <div class="board-header">
            <div class="station-name">${stationName}</div>
            ${this.config.show_clock ? `<div class="clock">${timeString}</div>` : ''}
          </div>
          <div class="board-content">
            <div class="header-row">
              <span class="col-time">Time</span>
              <span class="col-dest">Destination</span>
              ${this.config.show_platform ? '<span class="col-plat">Plat</span>' : ''}
              <span class="col-exp">Expected</span>
            </div>
            ${departures.slice(0, this.config.num_departures).map((dep, i) => this.renderDeparture(dep, i === 0)).join('')}
            ${departures.length === 0 ? this.renderNoDepartures() : ''}
          </div>
        </div>
      </ha-card>
    `;

    // Start clock update
    if (this.config.show_clock) {
      this.startClockUpdate();
    }

    // Start calling points animation for first departure
    if (this.config.show_calling_points && departures.length > 0) {
      this.animateCallingPoints();
    }
  }

  renderDeparture(departure, isFirst) {
    const statusClass = this.getStatusClass(departure.status, departure.is_cancelled);
    const expectedText = departure.is_cancelled ? 'Cancelled' : departure.expected_time;
    const callingPointsText = departure.calling_points
      ? departure.calling_points.map(cp => cp.station).join(', ')
      : '';

    return `
      <div class="departure-row ${isFirst ? 'first-departure' : ''}">
        <span class="col-time">${departure.scheduled_time}</span>
        <span class="col-dest">
          <span class="destination">${departure.destination}</span>
          ${isFirst && this.config.show_calling_points && callingPointsText ? `
            <span class="calling-points">
              <span class="calling-text">Calling at: ${callingPointsText}</span>
            </span>
          ` : ''}
        </span>
        ${this.config.show_platform ? `<span class="col-plat">${departure.platform || '-'}</span>` : ''}
        <span class="col-exp ${statusClass}">${expectedText}</span>
      </div>
    `;
  }

  renderNoDepartures() {
    return `
      <div class="no-departures">
        <span>No departures scheduled</span>
      </div>
    `;
  }

  getStatusClass(status, isCancelled) {
    if (isCancelled) return 'status-cancelled';
    switch (status) {
      case 'delayed': return 'status-delayed';
      case 'cancelled': return 'status-cancelled';
      default: return 'status-on-time';
    }
  }

  startClockUpdate() {
    if (this._clockInterval) clearInterval(this._clockInterval);
    this._clockInterval = setInterval(() => {
      const clockEl = this.shadowRoot.querySelector('.clock');
      if (clockEl) {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
      }
    }, 1000);
  }

  animateCallingPoints() {
    const callingText = this.shadowRoot.querySelector('.calling-text');
    if (callingText) {
      callingText.style.animation = 'scroll-text 15s linear infinite';
    }
  }

  disconnectedCallback() {
    if (this._clockInterval) {
      clearInterval(this._clockInterval);
    }
  }

  getStyles() {
    return `
      @font-face {
        font-family: 'Dot Matrix';
        src: url('https://cdn.jsdelivr.net/gh/DanielHartUK/Dot-Matrix-Typeface@master/fonts/Dot%20Matrix%20Bold.ttf') format('truetype');
        font-weight: bold;
        font-style: normal;
      }

      :host {
        --board-bg: #0a0a0a;
        --board-text: #ff9900;
        --board-text-dim: #cc7a00;
        --board-green: #00ff00;
        --board-red: #ff3333;
        --board-header-bg: #1a1a1a;
      }

      ha-card {
        background: var(--board-bg);
        border: none;
        overflow: hidden;
      }

      .departure-board {
        font-family: 'Dot Matrix', 'Courier New', monospace;
        background: var(--board-bg);
        color: var(--board-text);
        padding: 0;
      }

      .board-header {
        background: var(--board-header-bg);
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #333;
      }

      .station-name {
        font-size: 1.4em;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
      }

      .clock {
        font-size: 1.4em;
        font-weight: bold;
      }

      .board-content {
        padding: 8px 0;
      }

      .header-row {
        display: flex;
        padding: 8px 16px;
        font-size: 0.8em;
        color: var(--board-text-dim);
        border-bottom: 1px solid #333;
        text-transform: uppercase;
        letter-spacing: 1px;
      }

      .departure-row {
        display: flex;
        padding: 12px 16px;
        border-bottom: 1px solid #222;
        align-items: flex-start;
        min-height: 40px;
      }

      .departure-row.first-departure {
        background: rgba(255, 153, 0, 0.05);
      }

      .col-time {
        width: 60px;
        flex-shrink: 0;
        font-weight: bold;
      }

      .col-dest {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .destination {
        font-weight: bold;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .col-plat {
        width: 40px;
        text-align: center;
        flex-shrink: 0;
      }

      .col-exp {
        width: 80px;
        text-align: right;
        flex-shrink: 0;
        font-weight: bold;
      }

      .status-on-time {
        color: var(--board-green);
      }

      .status-delayed {
        color: var(--board-text);
      }

      .status-cancelled {
        color: var(--board-red);
      }

      .calling-points {
        font-size: 0.75em;
        color: var(--board-text-dim);
        overflow: hidden;
        white-space: nowrap;
        max-width: 100%;
      }

      .calling-text {
        display: inline-block;
        padding-left: 100%;
      }

      @keyframes scroll-text {
        0% {
          transform: translateX(0);
        }
        100% {
          transform: translateX(-100%);
        }
      }

      .no-departures {
        padding: 24px 16px;
        text-align: center;
        color: var(--board-text-dim);
        font-style: italic;
      }

      /* Flicker effect for authenticity */
      @keyframes flicker {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.98; }
      }

      .departure-board {
        animation: flicker 0.1s infinite;
      }
    `;
  }
}

// Register the card
customElements.define('uk-departures-card', UKDeparturesCard);

// Register with Home Assistant's custom card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'uk-departures-card',
  name: 'UK Departures Card',
  description: 'Display UK train departures in authentic station board style',
  preview: true,
  documentationURL: 'https://github.com/yourusername/uk-train-departures'
});

console.info(
  '%c UK-DEPARTURES-CARD %c v1.0.0 ',
  'color: white; background: #ff9900; font-weight: bold;',
  'color: #ff9900; background: white; font-weight: bold;'
);
