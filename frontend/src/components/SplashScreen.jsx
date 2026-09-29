import React, { useEffect, useState, useRef } from 'react';
import './SplashScreen.css';

export default function SplashScreen({ onFinish }) {
  const [isOut, setIsOut] = useState(false);
  const [telemetry, setTelemetry] = useState({
    alt: '506.42 km',
    vel: '7.612 km/s',
    coords: '18.9438°N, 72.8354°E',
    doppler: '-1.42 kHz'
  });
  const [carrierLock, setCarrierLock] = useState({
    text: 'CARRIER SEARCHING',
    color: '#3DDC97',
    borderColor: 'rgba(61, 220, 151, 0.4)'
  });
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([
    { id: 1, text: '[00:01] ACQUIRING DOWNLINK CARRIER · ISTRAC S-BAND RECEIVER LOCK...', active: true }
  ]);
  const [chips, setChips] = useState({
    cartosat: { text: 'CARTOSAT-3 [0.28m PAN] : SYNCING', locked: true },
    risat: { text: 'RISAT-2B [X-SAR] : STANDBY', locked: false },
    sentinel: { text: 'SENTINEL-2 [MSI 10m] : QUEUED', locked: false }
  });

  const canvasRef = useRef(null);
  const timersRef = useRef([]);
  const animFrameRef = useRef(null);
  const isFinishedRef = useRef(false);

  const finishSplash = () => {
    if (isFinishedRef.current) return;
    isFinishedRef.current = true;

    timersRef.current.forEach(t => clearTimeout(t) || clearInterval(t));
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);

    setIsOut(true);
    setTimeout(() => {
      if (onFinish) onFinish();
    }, 700);
  };

  useEffect(() => {
    // 1. Setup Canvas Orbital Simulation
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      let stars = [];

      const initStars = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        stars = [];
        const count = Math.min(220, Math.floor((canvas.width * canvas.height) / 6000));
        for (let i = 0; i < count; i++) {
          stars.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height * 0.75,
            radius: Math.random() * 1.5 + 0.3,
            alpha: Math.random() * 0.8 + 0.2,
            twinkleSpeed: Math.random() * 0.03 + 0.01,
            twinklePhase: Math.random() * Math.PI * 2
          });
        }
      };

      initStars();
      window.addEventListener('resize', initStars);

      let orbitAngle = 0;
      const render = () => {
        if (!ctx || !canvas) return;
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);

        // Starfield
        stars.forEach(s => {
          s.twinklePhase += s.twinkleSpeed;
          const alpha = s.alpha * (0.65 + 0.35 * Math.sin(s.twinklePhase));
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(226, 237, 248, ${alpha})`;
          ctx.fill();
        });

        // Curved Earth Limb Arc
        const earthCenterX = w * 0.5;
        const earthCenterY = h + w * 0.65;
        const earthRadius = w * 0.88;

        // Rayleigh Atmospheric Glow
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

        // Earth Body Gradient
        const earthGrad = ctx.createRadialGradient(
          earthCenterX - w * 0.25, earthCenterY - earthRadius * 0.8, earthRadius * 0.1,
          earthCenterX, earthCenterY, earthRadius
        );
        earthGrad.addColorStop(0.0, '#0C2B54');
        earthGrad.addColorStop(0.3, '#081C38');
        earthGrad.addColorStop(0.7, '#040C1A');
        earthGrad.addColorStop(1.0, '#02050A');

        ctx.beginPath();
        ctx.arc(earthCenterX, earthCenterY, earthRadius, 0, Math.PI * 2);
        ctx.fillStyle = earthGrad;
        ctx.fill();

        // Horizon Edge
        ctx.beginPath();
        ctx.arc(earthCenterX, earthCenterY, earthRadius, Math.PI * 1.15, Math.PI * 1.85);
        ctx.strokeStyle = 'rgba(103, 232, 249, 0.85)';
        ctx.lineWidth = 1.8;
        ctx.shadowColor = '#00D9FF';
        ctx.shadowBlur = 12;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Satellite Radar Swath
        orbitAngle += 0.008;
        const satOrbitRadius = earthRadius + 60;
        const satAngle = Math.PI * 1.35 + Math.sin(orbitAngle * 0.6) * 0.25;
        const satX = earthCenterX + Math.cos(satAngle) * satOrbitRadius;
        const satY = earthCenterY + Math.sin(satAngle) * satOrbitRadius;
        const groundTargetX = earthCenterX + Math.cos(satAngle) * earthRadius;
        const groundTargetY = earthCenterY + Math.sin(satAngle) * earthRadius;

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

        ctx.beginPath();
        ctx.moveTo(groundTargetX - 45, groundTargetY);
        ctx.lineTo(groundTargetX + 45, groundTargetY);
        ctx.strokeStyle = 'rgba(61, 220, 151, 0.8)';
        ctx.lineWidth = 2;
        ctx.stroke();

        animFrameRef.current = requestAnimationFrame(render);
      };

      animFrameRef.current = requestAnimationFrame(render);
    }

    // 2. Keyboard Bypass
    const handleKeydown = (e) => {
      if (e.key === 'Escape' || e.key === 'Enter') finishSplash();
    };
    window.addEventListener('keydown', handleKeydown);

    // 3. Telemetry Fluctuations
    let currentAlt = 506.42;
    let currentVel = 7.612;
    let currentDoppler = -1.42;
    let latBase = 18.9438;
    let lonBase = 72.8354;

    const telemTimer = setInterval(() => {
      currentAlt += (Math.random() - 0.5) * 0.04;
      currentVel += (Math.random() - 0.5) * 0.002;
      currentDoppler += (Math.random() - 0.48) * 0.03;
      latBase += 0.0012;
      lonBase += 0.0008;

      setTelemetry({
        alt: `${currentAlt.toFixed(2)} km`,
        vel: `${currentVel.toFixed(3)} km/s`,
        coords: `${latBase.toFixed(4)}°N, ${lonBase.toFixed(4)}°E`,
        doppler: `${currentDoppler >= 0 ? '+' : ''}${currentDoppler.toFixed(2)} kHz`
      });
    }, 120);
    timersRef.current.push(telemTimer);

    // 4. Progress Bar
    const progTimer = setInterval(() => {
      setProgress(p => {
        const next = p + 1.25;
        if (next >= 100) {
          clearInterval(progTimer);
          return 100;
        }
        return next;
      });
    }, 40);
    timersRef.current.push(progTimer);

    // 5. Downlink Log Steps
    const t1 = setTimeout(() => {
      setCarrierLock({
        text: 'CARRIER SYNCHRONIZED',
        color: '#00D9FF',
        borderColor: 'rgba(0, 217, 255, 0.4)'
      });
    }, 100);
    timersRef.current.push(t1);

    const t2 = setTimeout(() => {
      setLogs(prev => [
        ...prev.slice(-2),
        { id: 2, text: '[00:02] CARRIER LOCK DETECTED (SNR +22.4 dB) · DECRYPTING EPHEMERIS...', active: true }
      ]);
      setChips(prev => ({
        ...prev,
        cartosat: { text: 'CARTOSAT-3 [0.28m PAN] : LOCKED', locked: true }
      }));
    }, 900);
    timersRef.current.push(t2);

    const t3 = setTimeout(() => {
      setLogs(prev => [
        ...prev.slice(-2),
        { id: 3, text: '[00:03] SYNCHRONIZING CARTOSAT-3 / RISAT-2B · GEMINI VLM ENCLAVE READY...', active: true }
      ]);
      setChips(prev => ({
        ...prev,
        risat: { text: 'RISAT-2B [X-SAR] : LOCKED', locked: true },
        sentinel: { text: 'SENTINEL-2 [MSI 10m] : ONLINE', locked: true }
      }));
    }, 1800);
    timersRef.current.push(t3);

    const t4 = setTimeout(() => {
      setLogs(prev => [
        ...prev.slice(-2),
        { id: 4, text: '[00:04] ALL SENSORS NOMINAL · OPERATOR CLEARANCE GATEWAY AUTHORIZED.', active: true }
      ]);
      setCarrierLock({
        text: '● 100% TELEMETRY NOMINAL',
        color: '#3DDC97',
        borderColor: 'rgba(61, 220, 151, 0.6)'
      });
    }, 2600);
    timersRef.current.push(t4);

    const finishTimeout = setTimeout(finishSplash, 3400);
    timersRef.current.push(finishTimeout);

    return () => {
      timersRef.current.forEach(t => clearTimeout(t) || clearInterval(t));
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('keydown', handleKeydown);
    };
  }, []);

  const wordmark = "SATQUERY AI";

  return (
    <div className={`sq-splash ${isOut ? 'sq-splash--out sq-out' : ''}`} id="splash">
      {/* Background Orbital Canvas */}
      <canvas ref={canvasRef} className="sq-splash__canvas" id="splash-canvas" />
      <div className="sq-splash__vignette" />

      {/* Foreground Space Agency Tactical HUD */}
      <div className="sq-splash__hud">
        {/* Top Status Header */}
        <div className="sq-splash__top-bar">
          <div className="sq-splash__agency">
            <div className="sq-splash__badge">
              <span className="sq-splash__pulse-dot" />
              <span>ISRO // ISTRAC GROUND STATION</span>
            </div>
            <div className="sq-splash__station-meta">
              BENGALURU TRACKING NETWORK · <span>S-BAND 2240.50 MHz</span>
            </div>
          </div>

          <button className="sq-splash__skip" id="skipBtn" onClick={finishSplash} title="Press ESC to bypass sequence">
            <span>SKIP INTRO</span>
            <kbd>ESC</kbd>
          </button>
        </div>

        {/* Center Reticle & Brand */}
        <div className="sq-splash__center">
          <div className="sq-splash__reticle">
            <div className="sq-splash__ring-outer" />
            <div className="sq-splash__ring-inner" />
            <div className="sq-splash__radar-sweep-beam" />

            {/* High-Detail Satellite SVG Icon */}
            <svg className="sq-splash__satellite-svg" viewBox="0 0 120 120" width="88" height="88">
              <defs>
                <linearGradient id="solarCellGradReact" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#1B4B8A" />
                  <stop offset="50%" stopColor="#0E2F5E" />
                  <stop offset="100%" stopColor="#00D9FF" stopOpacity="0.8" />
                </linearGradient>
                <linearGradient id="busGoldGradReact" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#E2B755" />
                  <stop offset="50%" stopColor="#9C7728" />
                  <stop offset="100%" stopColor="#D4AF37" />
                </linearGradient>
              </defs>

              <rect x="50" y="44" width="20" height="32" rx="2" fill="url(#busGoldGradReact)" stroke="#FFE082" strokeWidth="1" />
              <line x1="50" y1="52" x2="70" y2="52" stroke="#4A3B18" strokeWidth="1" />
              <line x1="50" y1="60" x2="70" y2="60" stroke="#4A3B18" strokeWidth="1" />
              <line x1="50" y1="68" x2="70" y2="68" stroke="#4A3B18" strokeWidth="1" />

              <circle cx="60" cy="76" r="4.5" fill="#03060C" stroke="#00D9FF" strokeWidth="1.5" />
              <circle cx="60" cy="76" r="1.8" fill="#00D9FF" />

              <rect x="8" y="50" width="38" height="20" rx="1.5" fill="url(#solarCellGradReact)" stroke="#00D9FF" strokeWidth="1" />
              <line x1="20" y1="50" x2="20" y2="70" stroke="rgba(0,217,255,0.4)" strokeWidth="0.8" />
              <line x1="33" y1="50" x2="33" y2="70" stroke="rgba(0,217,255,0.4)" strokeWidth="0.8" />
              <line x1="8" y1="60" x2="46" y2="60" stroke="rgba(0,217,255,0.4)" strokeWidth="0.8" />
              <rect x="46" y="58" width="4" height="4" fill="#8E9FB5" />

              <rect x="74" y="50" width="38" height="20" rx="1.5" fill="url(#solarCellGradReact)" stroke="#00D9FF" strokeWidth="1" />
              <line x1="86" y1="50" x2="86" y2="70" stroke="rgba(0,217,255,0.4)" strokeWidth="0.8" />
              <line x1="99" y1="50" x2="99" y2="70" stroke="rgba(0,217,255,0.4)" strokeWidth="0.8" />
              <line x1="74" y1="60" x2="112" y2="60" stroke="rgba(0,217,255,0.4)" strokeWidth="0.8" />
              <rect x="70" y="58" width="4" height="4" fill="#8E9FB5" />

              <path d="M50,44 Q60,32 70,44" fill="none" stroke="#E2EDF8" strokeWidth="2" />
              <line x1="60" y1="36" x2="60" y2="28" stroke="#00D9FF" strokeWidth="1.5" />
              <circle cx="60" cy="27" r="2" fill="#00D9FF" />
            </svg>

            <div
              className="sq-splash__lock-indicator"
              style={{ color: carrierLock.color, borderColor: carrierLock.borderColor }}
            >
              {carrierLock.text}
            </div>
          </div>

          <div className="sq-splash__wordmark" id="wordmark">
            {wordmark.split('').map((ch, i) => (
              <span
                key={i}
                className={`sq-letter ${i >= 9 ? 'highlight' : ''}`}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                {ch === ' ' ? '\u00A0' : ch}
              </span>
            ))}
          </div>
          <div className="sq-splash__subtitle">
            AUTONOMOUS MULTIMODAL EARTH OBSERVATION INTELLIGENCE
          </div>
        </div>

        {/* Bottom Telemetry & Console */}
        <div className="sq-splash__bottom">
          <div className="sq-splash__telemetry-grid">
            <div className="sq-splash__telemetry-card">
              <span className="sq-splash__telem-lbl">ORBIT ALTITUDE</span>
              <span className="sq-splash__telem-val">{telemetry.alt}</span>
            </div>
            <div className="sq-splash__telemetry-card">
              <span className="sq-splash__telem-lbl">ORBITAL VELOCITY</span>
              <span className="sq-splash__telem-val">{telemetry.vel}</span>
            </div>
            <div className="sq-splash__telemetry-card">
              <span className="sq-splash__telem-lbl">SUB-SATELLITE POINT</span>
              <span className="sq-splash__telem-val">{telemetry.coords}</span>
            </div>
            <div className="sq-splash__telemetry-card">
              <span className="sq-splash__telem-lbl">DOPPLER DRIFT</span>
              <span className="sq-splash__telem-val">{telemetry.doppler}</span>
            </div>
          </div>

          <div className="sq-splash__terminal-box">
            <div className="sq-splash__terminal-header">
              <span className="sq-splash__term-title">&gt; ISTRAC S-BAND TELEMETRY DOWNLINK STREAM</span>
              <div className="sq-splash__rf-meter" title="Downlink Signal Strength SNR: +22.4 dB">
                <span className="sq-splash__rf-bar" />
                <span className="sq-splash__rf-bar" />
                <span className="sq-splash__rf-bar" />
                <span className="sq-splash__rf-bar" />
                <span className="sq-splash__rf-bar" />
                <span className="sq-splash__rf-bar" />
              </div>
            </div>

            <div className="sq-splash__log-stream">
              {logs.map((line) => (
                <div key={line.id} className="sq-splash__log-line active">
                  {line.text}
                </div>
              ))}
            </div>

            <div className="sq-splash__progress-row">
              <div className="sq-splash__progress-track">
                <div className="sq-splash__progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <span className="sq-splash__progress-val">{Math.floor(progress)}%</span>
            </div>
          </div>

          <div className="sq-splash__chips-row">
            <div className={`sq-splash__chip-item ${chips.cartosat.locked ? 'locked' : ''}`}>
              <span className="sq-splash__chip-dot" />
              <span>{chips.cartosat.text}</span>
            </div>
            <div className={`sq-splash__chip-item ${chips.risat.locked ? 'locked' : ''}`}>
              <span className="sq-splash__chip-dot" style={!chips.risat.locked ? { background: '#64748B', boxShadow: 'none' } : {}} />
              <span>{chips.risat.text}</span>
            </div>
            <div className={`sq-splash__chip-item ${chips.sentinel.locked ? 'locked' : ''}`}>
              <span className="sq-splash__chip-dot" style={!chips.sentinel.locked ? { background: '#64748B', boxShadow: 'none' } : {}} />
              <span>{chips.sentinel.text}</span>
            </div>
            <div className="sq-splash__chip-item">
              <span>ENCLAVE: TLS-256 AES-GCM</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

