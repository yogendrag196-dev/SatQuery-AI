/**
 * SplashScreen.js
 * Realistic ISRO Mission Control Satellite Telemetry Splash Screen
 * Features:
 * - HTML5 Canvas rendering realistic Earth limb curvature, Rayleigh atmospheric glow,
 *   starfield depth, and 3D-angled low-Earth orbit satellite with active radar swath
 * - Real-time orbital telemetry HUD (Altitude, Velocity, Geodetic Coords, Doppler Shift)
 * - Authentic Ground Station typewriter log stream & frequency spectrum meter
 * - Audio-tactile telemetry integration using SoundEngine
 * - Clean zero-flicker single-session execution with onFinish callback
 */

import { sound } from '../js/soundEngine.js';
import './SplashScreen.css';

export function renderSplashScreen({ onFinish }) {
  // Prevent duplicate instances
  const existing = document.getElementById('splash');
  if (existing) existing.remove();

  const splashEl = document.createElement('div');
  splashEl.className = 'sq-splash';
  splashEl.id = 'splash';

  splashEl.innerHTML = `
    <!-- Background Realistic Earth Orbit Canvas -->
    <canvas class="sq-splash__canvas" id="splash-canvas"></canvas>
    <div class="sq-splash__vignette"></div>

    <!-- Foreground Space Agency Tactical HUD -->
    <div class="sq-splash__hud">
      
      <!-- Top Status Header -->
      <div class="sq-splash__top-bar">
        <div class="sq-splash__agency">
          <div class="sq-splash__badge">
            <span class="sq-splash__pulse-dot"></span>
            <span>ISRO // ISTRAC GROUND STATION</span>
          </div>
          <div class="sq-splash__station-meta">
            BENGALURU TRACKING NETWORK · <span>S-BAND 2240.50 MHz</span>
          </div>
        </div>

        <button class="sq-splash__skip" id="skipBtn" title="Press ESC to bypass sequence">
          <span>SKIP INTRO</span>
          <kbd>ESC</kbd>
        </button>
      </div>

      <!-- Center Brand & Orbital Radar Reticle -->
      <div class="sq-splash__center">
        <div class="sq-splash__reticle">
          <div class="sq-splash__ring-outer"></div>
          <div class="sq-splash__ring-inner"></div>
          <div class="sq-splash__radar-sweep-beam"></div>

          <!-- High-Detail Satellite SVG Icon with Dish & Solar Arrays -->
          <svg class="sq-splash__satellite-svg" viewBox="0 0 120 120" width="88" height="88">
            <defs>
              <linearGradient id="solarCellGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#1B4B8A" />
                <stop offset="50%" stop-color="#0E2F5E" />
                <stop offset="100%" stop-color="#00D9FF" stop-opacity="0.8" />
              </linearGradient>
              <linearGradient id="busGoldGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#E2B755" />
                <stop offset="50%" stop-color="#9C7728" />
                <stop offset="100%" stop-color="#D4AF37" />
              </linearGradient>
            </defs>

            <!-- Main Satellite Central Bus (Gold MLI Foil) -->
            <rect x="50" y="44" width="20" height="32" rx="2" fill="url(#busGoldGrad)" stroke="#FFE082" stroke-width="1" />
            <line x1="50" y1="52" x2="70" y2="52" stroke="#4A3B18" stroke-width="1" />
            <line x1="50" y1="60" x2="70" y2="60" stroke="#4A3B18" stroke-width="1" />
            <line x1="50" y1="68" x2="70" y2="68" stroke="#4A3B18" stroke-width="1" />

            <!-- Earth-Facing Optical / SAR Sensor Aperture -->
            <circle cx="60" cy="76" r="4.5" fill="#03060C" stroke="#00D9FF" stroke-width="1.5" />
            <circle cx="60" cy="76" r="1.8" fill="#00D9FF" />

            <!-- Left Photovoltaic Solar Array -->
            <rect x="8" y="50" width="38" height="20" rx="1.5" fill="url(#solarCellGrad)" stroke="#00D9FF" stroke-width="1" />
            <line x1="20" y1="50" x2="20" y2="70" stroke="rgba(0,217,255,0.4)" stroke-width="0.8" />
            <line x1="33" y1="50" x2="33" y2="70" stroke="rgba(0,217,255,0.4)" stroke-width="0.8" />
            <line x1="8" y1="60" x2="46" y2="60" stroke="rgba(0,217,255,0.4)" stroke-width="0.8" />
            <!-- Left Yoke Mount -->
            <rect x="46" y="58" width="4" height="4" fill="#8E9FB5" />

            <!-- Right Photovoltaic Solar Array -->
            <rect x="74" y="50" width="38" height="20" rx="1.5" fill="url(#solarCellGrad)" stroke="#00D9FF" stroke-width="1" />
            <line x1="86" y1="50" x2="86" y2="70" stroke="rgba(0,217,255,0.4)" stroke-width="0.8" />
            <line x1="99" y1="50" x2="99" y2="70" stroke="rgba(0,217,255,0.4)" stroke-width="0.8" />
            <line x1="74" y1="60" x2="112" y2="60" stroke="rgba(0,217,255,0.4)" stroke-width="0.8" />
            <!-- Right Yoke Mount -->
            <rect x="70" y="58" width="4" height="4" fill="#8E9FB5" />

            <!-- High-Gain Parabolic Telemetry Dish Antenna (Pointing to Earth) -->
            <path d="M50,44 Q60,32 70,44" fill="none" stroke="#E2EDF8" stroke-width="2" />
            <line x1="60" y1="36" x2="60" y2="28" stroke="#00D9FF" stroke-width="1.5" />
            <circle cx="60" cy="27" r="2" fill="#00D9FF" />
          </svg>

          <div class="sq-splash__lock-indicator" id="lock-indicator">CARRIER SEARCHING</div>
        </div>

        <div class="sq-splash__wordmark" id="wordmark"></div>
        <div class="sq-splash__subtitle">AUTONOMOUS MULTIMODAL EARTH OBSERVATION INTELLIGENCE</div>
      </div>

      <!-- Bottom Telemetry Console -->
      <div class="sq-splash__bottom">
        
        <!-- 4-Card Real-Time Telemetry Grid -->
        <div class="sq-splash__telemetry-grid">
          <div class="sq-splash__telemetry-card">
            <span class="sq-splash__telem-lbl">ORBIT ALTITUDE</span>
            <span class="sq-splash__telem-val" id="telem-alt">506.42 km</span>
          </div>
          <div class="sq-splash__telemetry-card">
            <span class="sq-splash__telem-lbl">ORBITAL VELOCITY</span>
            <span class="sq-splash__telem-val" id="telem-vel">7.612 km/s</span>
          </div>
          <div class="sq-splash__telemetry-card">
            <span class="sq-splash__telem-lbl">SUB-SATELLITE POINT</span>
            <span class="sq-splash__telem-val" id="telem-coords">18.94°N, 72.84°E</span>
          </div>
          <div class="sq-splash__telemetry-card">
            <span class="sq-splash__telem-lbl">DOPPLER DRIFT</span>
            <span class="sq-splash__telem-val" id="telem-doppler">-1.42 kHz</span>
          </div>
        </div>

        <!-- Terminal Log Box & Signal Wave -->
        <div class="sq-splash__terminal-box">
          <div class="sq-splash__terminal-header">
            <span class="sq-splash__term-title">> ISTRAC S-BAND TELEMETRY DOWNLINK STREAM</span>
            
            <!-- Live RF Spectrum Meter -->
            <div class="sq-splash__rf-meter" title="Downlink Signal Strength SNR: +22.4 dB">
              <span class="sq-splash__rf-bar"></span>
              <span class="sq-splash__rf-bar"></span>
              <span class="sq-splash__rf-bar"></span>
              <span class="sq-splash__rf-bar"></span>
              <span class="sq-splash__rf-bar"></span>
              <span class="sq-splash__rf-bar"></span>
            </div>
          </div>

          <div class="sq-splash__log-stream" id="log-stream">
            <div class="sq-splash__log-line active" id="current-log-line">
              <span class="sq-splash__cursor"></span>
            </div>
          </div>

          <div class="sq-splash__progress-row">
            <div class="sq-splash__progress-track">
              <div class="sq-splash__progress-fill" id="progress-fill"></div>
            </div>
            <span class="sq-splash__progress-val" id="progress-val">0%</span>
          </div>
        </div>

        <!-- Constellation Synchronization Chips -->
        <div class="sq-splash__chips-row">
          <div class="sq-splash__chip-item locked" id="chip-cartosat">
            <span class="sq-splash__chip-dot"></span>
            <span>CARTOSAT-3 [0.28m PAN] : SYNCING</span>
          </div>
          <div class="sq-splash__chip-item" id="chip-risat">
            <span class="sq-splash__chip-dot" style="background:#64748B; box-shadow:none;"></span>
            <span>RISAT-2B [X-SAR] : STANDBY</span>
          </div>
          <div class="sq-splash__chip-item" id="chip-sentinel">
            <span class="sq-splash__chip-dot" style="background:#64748B; box-shadow:none;"></span>
            <span>SENTINEL-2 [MSI 10m] : QUEUED</span>
          </div>
          <div class="sq-splash__chip-item">
            <span>ENCLAVE: TLS-256 AES-GCM</span>
          </div>
        </div>

      </div>

    </div>
  `;

  document.body.appendChild(splashEl);

  // Initialize Canvas Orbital Scene
  const canvas = splashEl.querySelector('#splash-canvas');
  const ctx = canvas ? canvas.getContext('2d') : null;
  let animFrameId = null;

  // Render Wordmark with letter animations
  const wordmarkEl = splashEl.querySelector('#wordmark');
  const WORDMARK = "SATQUERY AI";
  WORDMARK.split('').forEach((ch, i) => {
    const span = document.createElement('span');
    span.className = 'sq-letter';
    if (ch === 'A' && i === 9) span.classList.add('highlight');
    if (ch === 'I' && i === 10) span.classList.add('highlight');
    span.style.animationDelay = `${i * 50}ms`;
    span.textContent = ch === ' ' ? '\u00A0' : ch;
    wordmarkEl.appendChild(span);
  });

  // Dynamic Telemetry Elements
  const altEl = splashEl.querySelector('#telem-alt');
  const velEl = splashEl.querySelector('#telem-vel');
  const coordsEl = splashEl.querySelector('#telem-coords');
  const dopplerEl = splashEl.querySelector('#telem-doppler');
  const progressFill = splashEl.querySelector('#progress-fill');
  const progressVal = splashEl.querySelector('#progress-val');
  const lockIndicator = splashEl.querySelector('#lock-indicator');
  const logStream = splashEl.querySelector('#log-stream');
  const chipCartosat = splashEl.querySelector('#chip-cartosat');
  const chipRisat = splashEl.querySelector('#chip-risat');
  const chipSentinel = splashEl.querySelector('#chip-sentinel');
  const skipBtn = splashEl.querySelector('#skipBtn');

  // Starfield Simulation Data
  let stars = [];
  const initStarfield = () => {
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    stars = [];
    const count = Math.min(220, Math.floor((canvas.width * canvas.height) / 6000));
    for (let i = 0; i < count; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height * 0.75, // concentrate above Earth limb
        radius: Math.random() * 1.5 + 0.3,
        alpha: Math.random() * 0.8 + 0.2,
        twinkleSpeed: Math.random() * 0.03 + 0.01,
        twinklePhase: Math.random() * Math.PI * 2
      });
    }
  };

  initStarfield();
  window.addEventListener('resize', initStarfield);

  // Realistic Canvas Orbit & Earth Limb Rendering Loop
  let orbitAngle = 0;
  const renderCanvasScene = () => {
    if (!ctx || !canvas) return;
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    // 1. Draw Starfield with realistic depth and twinkle
    stars.forEach(s => {
      s.twinklePhase += s.twinkleSpeed;
      const currentAlpha = s.alpha * (0.65 + 0.35 * Math.sin(s.twinklePhase));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(226, 237, 248, ${currentAlpha})`;
      ctx.fill();
    });

    // 2. Realistic Curved Earth Limb Arc
    // Place planet curvature center well below the viewport to create vast planetary curvature
    const earthCenterX = w * 0.5;
    const earthCenterY = h + w * 0.65;
    const earthRadius = w * 0.88;

    // A. Outer Rayleigh Atmospheric Scattering Glow (Cyan to Deep Space)
    const atmoGlow = ctx.createRadialGradient(
      earthCenterX, earthCenterY, earthRadius * 0.96,
      earthCenterX, earthCenterY, earthRadius * 1.08
    );
    atmoGlow.addColorStop(0.0, 'rgba(0, 217, 255, 0.45)');
    atmoGlow.addColorStop(0.2, 'rgba(0, 180, 255, 0.25)');
    atmoGlow.addColorStop(0.5, 'rgba(14, 50, 110, 0.12)');
    atmoGlow.addColorStop(1.0, 'rgba(3, 6, 12, 0)');

    ctx.beginPath();
    ctx.arc(earthCenterX, earthCenterY, earthRadius * 1.08, 0, Math.PI * 2);
    ctx.fillStyle = atmoGlow;
    ctx.fill();

    // B. Planet Body (Day/Night Terminator Gradient & Deep Blue Oceans)
    const earthGrad = ctx.createRadialGradient(
      earthCenterX - w * 0.25, earthCenterY - earthRadius * 0.8, earthRadius * 0.1,
      earthCenterX, earthCenterY, earthRadius
    );
    earthGrad.addColorStop(0.0, '#0C2B54'); // illuminated oceanic surface
    earthGrad.addColorStop(0.3, '#081C38');
    earthGrad.addColorStop(0.7, '#040C1A');
    earthGrad.addColorStop(1.0, '#02050A'); // dark space boundary

    ctx.beginPath();
    ctx.arc(earthCenterX, earthCenterY, earthRadius, 0, Math.PI * 2);
    ctx.fillStyle = earthGrad;
    ctx.fill();

    // C. Crisp Thin Atmospheric Blue Horizon Edge
    ctx.beginPath();
    ctx.arc(earthCenterX, earthCenterY, earthRadius, Math.PI * 1.15, Math.PI * 1.85);
    ctx.strokeStyle = 'rgba(103, 232, 249, 0.85)';
    ctx.lineWidth = 1.8;
    ctx.shadowColor = '#00D9FF';
    ctx.shadowBlur = 12;
    ctx.stroke();
    ctx.shadowBlur = 0; // reset shadow

    // 3. Orbiting Low-Earth Satellite Scanning Swath
    orbitAngle += 0.008;
    const satOrbitRadius = earthRadius + 60;
    const satAngle = Math.PI * 1.35 + Math.sin(orbitAngle * 0.6) * 0.25;
    const satX = earthCenterX + Math.cos(satAngle) * satOrbitRadius;
    const satY = earthCenterY + Math.sin(satAngle) * satOrbitRadius;

    // Ground Track Target on Earth Surface directly beneath satellite
    const groundTargetX = earthCenterX + Math.cos(satAngle) * earthRadius;
    const groundTargetY = earthCenterY + Math.sin(satAngle) * earthRadius;

    // Draw Active Radar/Optical Sensor Swath Cone
    const swathGrad = ctx.createLinearGradient(satX, satY, groundTargetX, groundTargetY);
    swathGrad.addColorStop(0.0, 'rgba(0, 217, 255, 0.45)');
    swathGrad.addColorStop(1.0, 'rgba(0, 217, 255, 0.03)');

    ctx.beginPath();
    ctx.moveTo(satX, satY);
    ctx.lineTo(groundTargetX - 45, groundTargetY);
    ctx.lineTo(groundTargetX + 45, groundTargetY);
    ctx.closePath();
    ctx.fillStyle = swathGrad;
    ctx.fill();

    // Ground Track Scan Line
    ctx.beginPath();
    ctx.moveTo(groundTargetX - 45, groundTargetY);
    ctx.lineTo(groundTargetX + 45, groundTargetY);
    ctx.strokeStyle = 'rgba(61, 220, 151, 0.8)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Orbit Path Line Arc
    ctx.beginPath();
    ctx.arc(earthCenterX, earthCenterY, satOrbitRadius, Math.PI * 1.25, Math.PI * 1.75);
    ctx.strokeStyle = 'rgba(0, 217, 255, 0.18)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 8]);
    ctx.stroke();
    ctx.setLineDash([]); // reset

    animFrameId = requestAnimationFrame(renderCanvasScene);
  };

  animFrameId = requestAnimationFrame(renderCanvasScene);

  // Telemetry Simulation Timers & Sequence
  let isFinished = false;
  let timers = [];

  const clearAllTimers = () => {
    timers.forEach(t => clearTimeout(t) || clearInterval(t));
    timers = [];
    if (animFrameId) cancelAnimationFrame(animFrameId);
    window.removeEventListener('resize', initStarfield);
  };

  const finishSplash = () => {
    if (isFinished) return;
    isFinished = true;
    clearAllTimers();

    // Play final authorization chime
    try { sound.playMissionComplete(); } catch (e) {}

    splashEl.classList.add('sq-splash--out', 'sq-out');
    setTimeout(() => {
      splashEl.remove();
      if (onFinish) onFinish();
    }, 700);
  };

  // Keyboard shortcut listener: ESC or Enter finishes splash
  const handleKeydown = (e) => {
    if (e.key === 'Escape' || e.key === 'Enter') {
      finishSplash();
    }
  };
  window.addEventListener('keydown', handleKeydown, { once: true });

  if (skipBtn) {
    skipBtn.addEventListener('click', finishSplash);
  }

  // Real-Time Micro-Fluctuation Telemetry Loop
  let currentPct = 0;
  let currentAlt = 506.42;
  let currentVel = 7.612;
  let currentDoppler = -1.42;
  let latBase = 18.9438;
  let lonBase = 72.8354;

  const telemetryTicker = setInterval(() => {
    currentAlt += (Math.random() - 0.5) * 0.04;
    currentVel += (Math.random() - 0.5) * 0.002;
    currentDoppler += (Math.random() - 0.48) * 0.03;
    latBase += 0.0012;
    lonBase += 0.0008;

    if (altEl) altEl.textContent = `${currentAlt.toFixed(2)} km`;
    if (velEl) velEl.textContent = `${currentVel.toFixed(3)} km/s`;
    if (dopplerEl) dopplerEl.textContent = `${currentDoppler >= 0 ? '+' : ''}${currentDoppler.toFixed(2)} kHz`;
    if (coordsEl) coordsEl.textContent = `${latBase.toFixed(4)}°N, ${lonBase.toFixed(4)}°E`;
  }, 120);
  timers.push(telemetryTicker);

  // Smooth High-Precision Progress Bar Stream (0% -> 100% over 3.2s)
  const progressInterval = setInterval(() => {
    currentPct += 1.25;
    if (currentPct > 100) currentPct = 100;
    if (progressFill) progressFill.style.width = `${currentPct}%`;
    if (progressVal) progressVal.textContent = `${Math.floor(currentPct)}%`;
    if (currentPct >= 100) clearInterval(progressInterval);
  }, 40);
  timers.push(progressInterval);

  // Typewriter Log Steps & Constellation Handshake Pipeline
  const logSteps = [
    {
      time: 100,
      text: "[00:01] ACQUIRING DOWNLINK CARRIER · ISTRAC S-BAND RECEIVER LOCK...",
      action: () => {
        try { sound.playRadarPing(); } catch (e) {}
        if (lockIndicator) {
          lockIndicator.textContent = "CARRIER SYNCHRONIZED";
          lockIndicator.style.color = "#00D9FF";
          lockIndicator.style.borderColor = "rgba(0, 217, 255, 0.4)";
        }
      }
    },
    {
      time: 900,
      text: "[00:02] CARRIER LOCK DETECTED (SNR +22.4 dB) · DECRYPTING EPHEMERIS...",
      action: () => {
        if (chipCartosat) {
          chipCartosat.innerHTML = `<span class="sq-splash__chip-dot"></span><span>CARTOSAT-3 [0.28m PAN] : LOCKED</span>`;
          chipCartosat.classList.add('locked');
        }
      }
    },
    {
      time: 1800,
      text: "[00:03] SYNCHRONIZING CARTOSAT-3 / RISAT-2B · GEMINI VLM ENCLAVE READY...",
      action: () => {
        try { sound.playClick(); } catch (e) {}
        if (chipRisat) {
          chipRisat.innerHTML = `<span class="sq-splash__chip-dot"></span><span>RISAT-2B [X-SAR] : LOCKED</span>`;
          chipRisat.classList.add('locked');
        }
        if (chipSentinel) {
          chipSentinel.innerHTML = `<span class="sq-splash__chip-dot"></span><span>SENTINEL-2 [MSI 10m] : ONLINE</span>`;
          chipSentinel.classList.add('locked');
        }
      }
    },
    {
      time: 2600,
      text: "[00:04] ALL SENSORS NOMINAL · OPERATOR CLEARANCE GATEWAY AUTHORIZED.",
      action: () => {
        if (lockIndicator) {
          lockIndicator.textContent = "● 100% TELEMETRY NOMINAL";
          lockIndicator.style.color = "#3DDC97";
          lockIndicator.style.borderColor = "rgba(61, 220, 151, 0.6)";
        }
      }
    }
  ];

  logSteps.forEach(step => {
    timers.push(setTimeout(() => {
      if (logStream) {
        // Append completed step
        const line = document.createElement('div');
        line.className = 'sq-splash__log-line active';
        line.textContent = step.text;
        logStream.appendChild(line);
        if (logStream.children.length > 3) {
          logStream.removeChild(logStream.children[0]);
        }
      }
      if (step.action) step.action();
    }, step.time));
  });

  // Automatically finish after 3.4 seconds
  timers.push(setTimeout(finishSplash, 3400));

  return {
    finish: finishSplash
  };
}
