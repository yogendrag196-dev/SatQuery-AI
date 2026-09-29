/**
 * proactiveMonitor.js
 * Autonomous Background Change-Detection Watcher
 * Periodically evaluates monitored Earth Observation zones, detects threshold breaches,
 * and pushes unprompted alerts into the operator's alert feed with tactical audio & HUD pulses.
 */

import { sound } from './soundEngine.js';

export class ProactiveMonitor {
  constructor(onAlertTriggered = null) {
    this.onAlertTriggered = onAlertTriggered;
    this.intervalMs = 35000; // Background check interval (35s)
    this.timerId = null;
    this.isRunning = false;
    this.triggeredAlertsCount = 0;

    // Simulated background monitoring pool of real-world remote sensing events
    this.eventPool = [
      {
        id: 'proactive-alert-01',
        zone: 'brahmaputra-flood',
        zoneName: 'Zone 02 // Brahmaputra River Basin',
        sensor: 'EOS-04 (C-Band SAR) & RISAT-2BR1',
        severity: 'critical',
        shape: '▲',
        tag: '▲ CRITICAL · FLOOD EMBANKMENT BREACH',
        headline: 'Emergency +312.4% surface water expansion detected near Kaziranga North sector',
        details: 'Automated bi-temporal change threshold (Δ > 200%) exceeded. Microwave SAR backscatter indicates 184.6 km² inundation with rapid southward dispersion toward arterial highway NH-715.',
        query: 'What changed in Zone 2 (Brahmaputra) in the last 24 hours? Assess embankment breach extent in km²'
      },
      {
        id: 'proactive-alert-02',
        zone: 'mumbai-port',
        zoneName: 'Zone 01 // Mumbai Port & Naval Dockyard',
        sensor: 'Cartosat-3 (0.28m PAN) & Sentinel-2 MSI',
        severity: 'warning',
        shape: '◆',
        tag: '◆ WARNING · HIGH MARITIME CONGESTION',
        headline: 'Sudden +42.8% surge in anchorage vessel density outside offshore channel',
        details: 'YOLOv8 aerial detector identified 18 vessels (including 4 large container carriers and 2 naval craft) queued in outer anchorage basin exceeding standard harbor traffic thresholds.',
        query: 'Count all vessels in this AOI and identify naval craft in Mumbai harbor'
      },
      {
        id: 'proactive-alert-03',
        zone: 'western-ghats',
        zoneName: 'Zone 03 // Western Ghats Biosphere',
        sensor: 'Resourcesat-2A (LISS-4) & Sentinel-2 SWIR',
        severity: 'warning',
        shape: '◆',
        tag: '◆ WARNING · ACTIVE WILDFIRE THERMAL ANOMALY',
        headline: 'SWIR Band 12 detects 7.8 km² high-temperature burn scar in Southern Buffer',
        details: 'Normalized Burn Ratio (NBR) differential dropped by -0.34 over past 48 hours indicating active forest canopy smoldering along western ridge line.',
        query: 'Analyze deforestation and burn scar extent in km² across Western Ghats'
      },
      {
        id: 'proactive-alert-04',
        zone: 'sriharikota',
        zoneName: 'Zone 04 // SDSC-SHAR Sriharikota',
        sensor: 'Cartosat-3 (0.28m High-Res Optical)',
        severity: 'nominal',
        shape: '●',
        tag: '● NOTICE · LAUNCH COMPLEX ACTIVITY',
        headline: 'Mobile Service Tower (MST) repositioning detected at Launch Pad 2',
        details: 'Optical sub-meter spatial feature tracking detected vehicle movement and logistical staging activity adjacent to the propellant storage depot.',
        query: 'Describe the visible launch complex infrastructure and storage depots at Sriharikota'
      }
    ];

    this.currentIndex = 0;
  }

  start() {
    if (this.isRunning) return;
    this.isRunning = true;

    // Trigger first unprompted proactive event after 18 seconds of console session
    setTimeout(() => {
      if (this.isRunning) this.checkMonitoredZones();
    }, 18000);

    this.timerId = setInterval(() => {
      this.checkMonitoredZones();
    }, this.intervalMs);
  }

  stop() {
    this.isRunning = false;
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
  }

  checkMonitoredZones() {
    if (!this.isRunning) return;

    const eventData = this.eventPool[this.currentIndex % this.eventPool.length];
    this.currentIndex++;
    this.pushAlert(eventData);
  }

  pushAlert(eventData) {
    this.triggeredAlertsCount++;

    // 1. Play audio radar ping
    sound.playRadarPing();

    // 2. Update Alert Badge Count in Header
    const badgeCountEl = document.getElementById('alert-badge-count');
    if (badgeCountEl) {
      const currentCount = parseInt(badgeCountEl.textContent || '3', 10);
      const newCount = currentCount + 1;
      badgeCountEl.textContent = newCount;
      badgeCountEl.classList.remove('pulse');
      void badgeCountEl.offsetWidth; // Reflow to restart animation
      badgeCountEl.classList.add('pulse');
    }

    // 3. Inject new alert item into Alert Drawer list
    const alertListEl = document.getElementById('alert-items-list');
    if (alertListEl) {
      const alertItem = document.createElement('div');
      alertItem.className = `alert-item ${eventData.severity} proactive-pulse`;
      alertItem.dataset.mission = eventData.zone;
      alertItem.dataset.query = eventData.query;
      alertItem.innerHTML = `
        <div class="alert-item-header">
          <span class="alert-type-tag">${eventData.tag}</span>
          <span class="alert-time">JUST NOW</span>
        </div>
        <div class="alert-headline">${eventData.headline}</div>
        <div class="alert-details">${eventData.details}</div>
        <div class="alert-action-hint"><span>➔</span> Click to jump map & auto-task analysis</div>
      `;

      alertItem.addEventListener('click', () => {
        sound.playClick();
        if (this.onAlertTriggered) {
          this.onAlertTriggered(eventData);
        }
      });

      alertListEl.insertBefore(alertItem, alertListEl.firstChild);
    }

    // 4. Show transient in-UI banner notification pill
    this.showTransientNotification(eventData);

    // 5. Dispatch global event
    window.dispatchEvent(new CustomEvent('satquery:proactive-alert', { detail: eventData }));
  }

  showTransientNotification(eventData) {
    let notif = document.getElementById('proactive-toast-banner');
    if (!notif) {
      notif = document.createElement('div');
      notif.id = 'proactive-toast-banner';
      notif.className = 'proactive-toast-banner';
      document.body.appendChild(notif);
    }

    notif.innerHTML = `
      <div class="toast-left">
        <span class="toast-pulse-dot"></span>
        <div>
          <div class="toast-title">PROACTIVE MONITOR ALERT // ${eventData.sensor}</div>
          <div class="toast-body">${eventData.headline}</div>
        </div>
      </div>
      <button class="toast-inspect-btn" id="btn-toast-inspect">INSPECT AOI ➔</button>
    `;

    notif.classList.add('active');

    const inspectBtn = notif.querySelector('#btn-toast-inspect');
    if (inspectBtn) {
      inspectBtn.onclick = () => {
        notif.classList.remove('active');
        sound.playClick();
        if (this.onAlertTriggered) {
          this.onAlertTriggered(eventData);
        }
      };
    }

    setTimeout(() => {
      if (notif) notif.classList.remove('active');
    }, 9000);
  }

  // Allow instant testing from UI or console
  triggerNow(zoneKey = null) {
    const match = zoneKey ? this.eventPool.find(e => e.zone === zoneKey) : this.eventPool[this.currentIndex % this.eventPool.length];
    this.pushAlert(match || this.eventPool[0]);
  }
}
