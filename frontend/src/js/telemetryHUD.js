/**
 * telemetryHUD.js
 * Mission Control Telemetry Displays & Number Animations
 */

export class TelemetryHUD {
  constructor() {
    this.utcEl = document.getElementById('clock-utc');
    this.istEl = document.getElementById('clock-ist');
    this.cursorCoordsEl = document.getElementById('hud-cursor-coords');
    this.gsdEl = document.getElementById('hud-gsd');
    this.zoomEl = document.getElementById('hud-zoom');
    
    this.startClocks();
  }

  startClocks() {
    const update = () => {
      const now = new Date();
      
      // UTC Clock
      const utcHours = String(now.getUTCHours()).padStart(2, '0');
      const utcMins = String(now.getUTCMinutes()).padStart(2, '0');
      const utcSecs = String(now.getUTCSeconds()).padStart(2, '0');
      if (this.utcEl) this.utcEl.textContent = `${utcHours}:${utcMins}:${utcSecs} Z`;

      // IST Clock (UTC + 5:30)
      const istTime = new Date(now.getTime() + (5.5 * 60 * 60 * 1000));
      const istHours = String(istTime.getUTCHours()).padStart(2, '0');
      const istMins = String(istTime.getUTCMinutes()).padStart(2, '0');
      const istSecs = String(istTime.getUTCSeconds()).padStart(2, '0');
      if (this.istEl) this.istEl.textContent = `${istHours}:${istMins}:${istSecs} IST`;
    };

    update();
    setInterval(update, 1000);
  }

  updateCursor(lat, lon, zoom) {
    if (this.cursorCoordsEl) {
      const latStr = `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? 'N' : 'S'}`;
      const lonStr = `${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? 'E' : 'W'}`;
      this.cursorCoordsEl.textContent = `${latStr}, ${lonStr}`;
    }
    if (this.zoomEl && zoom !== undefined) {
      this.zoomEl.textContent = zoom.toFixed(1);
    }
    if (this.gsdEl && zoom !== undefined) {
      // Estimated Ground Sampling Distance based on zoom level
      const approxGsd = (156543.03392 * Math.cos((lat * Math.PI) / 180) / Math.pow(2, zoom));
      this.gsdEl.textContent = `${Math.max(0.28, approxGsd).toFixed(2)} m/px`;
    }
  }

  /**
   * Smoothly animates a numeric value counting up to target value with fallback handling
   */
  animateCount(elementId, targetValue, decimals = 0, suffix = '') {
    const el = document.getElementById(elementId);
    if (!el) return;

    if (targetValue === undefined || targetValue === null || targetValue === '—') {
      el.textContent = '—';
      return;
    }

    const start = parseFloat(el.textContent) || 0;
    const end = parseFloat(targetValue);
    if (isNaN(end)) {
      el.textContent = '—';
      return;
    }

    const duration = 900; // ms
    const startTime = performance.now();

    const updateFrame = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const currentVal = start + (end - start) * easeProgress;

      el.textContent = currentVal.toFixed(decimals) + suffix;

      if (progress < 1) {
        requestAnimationFrame(updateFrame);
      } else {
        el.textContent = end.toFixed(decimals) + suffix;
      }
    };

    requestAnimationFrame(updateFrame);
  }
}
