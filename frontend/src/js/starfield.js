/**
 * starfield.js
 * High-performance canvas-based deep space starfield & orbital satellite trajectory renderer
 */

export class StarfieldCanvas {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.stars = [];
    this.satellites = [];
    this.animationFrameId = null;

    this.init();
  }

  init() {
    this.resize();
    window.addEventListener('resize', () => this.resize());

    // Create background stars
    const starCount = Math.floor((this.width * this.height) / 3200);
    this.stars = [];
    for (let i = 0; i < starCount; i++) {
      this.stars.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        radius: Math.random() * 1.2 + 0.3,
        alpha: Math.random() * 0.7 + 0.2,
        twinkleSpeed: Math.random() * 0.02 + 0.005,
        twinkleDir: Math.random() > 0.5 ? 1 : -1
      });
    }

    // Create 3 orbiting satellite nodes along elliptical trajectories
    this.satellites = [
      { name: "CARTOSAT-3", radiusX: 380, radiusY: 160, tilt: -0.22, speed: 0.0008, angle: 0, color: "#00D9FF" },
      { name: "RISAT-2BR1", radiusX: 520, radiusY: 220, tilt: 0.35, speed: 0.0006, angle: 2.1, color: "#3DDC97" },
      { name: "SENTINEL-2", radiusX: 680, radiusY: 290, tilt: -0.12, speed: 0.0004, angle: 4.2, color: "#FFB800" }
    ];

    this.animate();
  }

  resize() {
    if (!this.canvas) return;
    this.width = this.canvas.parentElement.clientWidth;
    this.height = this.canvas.parentElement.clientHeight;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.centerX = this.width / 2;
    this.centerY = this.height / 2 + 30;
  }

  animate() {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Draw background stars
    this.stars.forEach(star => {
      star.alpha += star.twinkleSpeed * star.twinkleDir;
      if (star.alpha > 0.9) { star.alpha = 0.9; star.twinkleDir = -1; }
      else if (star.alpha < 0.15) { star.alpha = 0.15; star.twinkleDir = 1; }

      this.ctx.fillStyle = `rgba(226, 237, 248, ${star.alpha})`;
      this.ctx.beginPath();
      this.ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
      this.ctx.fill();
    });

    // Draw Center Globe / Earth Core Wireframe Horizon
    this.drawEarthHorizon();

    // Draw orbital tracks and moving satellites
    this.satellites.forEach(sat => {
      sat.angle += sat.speed;
      this.drawOrbitTrack(sat);
      this.drawSatelliteNode(sat);
    });

    this.animationFrameId = requestAnimationFrame(() => this.animate());
  }

  drawEarthHorizon() {
    const horizonY = this.height * 0.88;
    const horizonRadius = this.width * 0.9;

    // Earth glow arc
    const gradient = this.ctx.createRadialGradient(
      this.centerX, horizonY + horizonRadius * 0.7, horizonRadius * 0.5,
      this.centerX, horizonY + horizonRadius * 0.7, horizonRadius
    );
    gradient.addColorStop(0, 'rgba(0, 217, 255, 0.12)');
    gradient.addColorStop(0.6, 'rgba(0, 120, 220, 0.04)');
    gradient.addColorStop(1, 'transparent');

    this.ctx.fillStyle = gradient;
    this.ctx.beginPath();
    this.ctx.arc(this.centerX, horizonY + horizonRadius * 0.7, horizonRadius, 0, Math.PI * 2);
    this.ctx.fill();

    // Subtle Earth limb line
    this.ctx.strokeStyle = 'rgba(0, 217, 255, 0.25)';
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    this.ctx.arc(this.centerX, horizonY + horizonRadius * 0.7, horizonRadius, Math.PI * 1.25, Math.PI * 1.75);
    this.ctx.stroke();
  }

  drawOrbitTrack(sat) {
    this.ctx.save();
    this.ctx.translate(this.centerX, this.centerY);
    this.ctx.rotate(sat.tilt);

    this.ctx.strokeStyle = 'rgba(0, 217, 255, 0.08)';
    this.ctx.lineWidth = 1;
    this.ctx.setLineDash([4, 6]);

    this.ctx.beginPath();
    this.ctx.ellipse(0, 0, sat.radiusX, sat.radiusY, 0, 0, Math.PI * 2);
    this.ctx.stroke();

    this.ctx.restore();
  }

  drawSatelliteNode(sat) {
    this.ctx.save();
    this.ctx.translate(this.centerX, this.centerY);
    this.ctx.rotate(sat.tilt);

    const x = Math.cos(sat.angle) * sat.radiusX;
    const y = Math.sin(sat.angle) * sat.radiusY;

    // Glowing satellite point
    this.ctx.shadowColor = sat.color;
    this.ctx.shadowBlur = 10;
    this.ctx.fillStyle = sat.color;
    this.ctx.beginPath();
    this.ctx.arc(x, y, 3, 0, Math.PI * 2);
    this.ctx.fill();

    // Pulse radar ring around satellite
    const pulseRadius = 6 + (Math.sin(Date.now() * 0.005) + 1) * 3;
    this.ctx.strokeStyle = sat.color;
    this.ctx.lineWidth = 0.8;
    this.ctx.beginPath();
    this.ctx.arc(x, y, pulseRadius, 0, Math.PI * 2);
    this.ctx.stroke();

    // Satellite Label
    this.ctx.shadowBlur = 0;
    this.ctx.font = '9px "JetBrains Mono", monospace';
    this.ctx.fillStyle = 'rgba(226, 237, 248, 0.7)';
    this.ctx.fillText(sat.name, x + 8, y - 6);

    this.ctx.restore();
  }

  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }
}
