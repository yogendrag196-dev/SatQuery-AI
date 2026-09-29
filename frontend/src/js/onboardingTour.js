/**
 * onboardingTour.js
 * Minimal 3-Step Guided Highlight Spotlight Tour for SatQuery AI
 */

import { sound } from './soundEngine.js';

export class OnboardingTour {
  constructor() {
    this.storageKey = 'satquery_tour_seen';
    this.currentStep = 0;
    this.isActive = false;

    this.steps = [
      {
        targetId: 'query-panel',
        title: '1. Monitored AOI Zones',
        desc: 'Select an Earth Observation operational zone (Mumbai Port Maritime, Brahmaputra Flood Inundation, Western Ghats Canopy, or SDSC Spaceport).',
        preferredSide: 'right'
      },
      {
        targetId: 'map-panel',
        title: '2. Tactical Geospatial Canvas',
        desc: 'Inspect high-resolution imagery, toggle YOLOv8 radar markers, spectral NDWI/NDVI segmentation masks, and bi-temporal change heatmaps.',
        preferredSide: 'bottom'
      },
      {
        targetId: 'dossier-panel',
        title: '3. Agentic Tasking & Intelligence Dossier',
        desc: 'Dispatch natural language questions or click suggested prompt chips. Inspect the explainability Model Trail and export verified mission dossiers.',
        preferredSide: 'left'
      }
    ];

    this.initDOM();
    this.initEvents();
  }

  initDOM() {
    this.overlay = document.createElement('div');
    this.overlay.className = 'onboarding-overlay';
    this.overlay.id = 'onboarding-overlay';

    this.overlay.innerHTML = `
      <div class="onboarding-backdrop"></div>
      <div class="onboarding-spotlight" id="onboarding-spotlight"></div>
      <div class="onboarding-tooltip" id="onboarding-tooltip">
        <div class="onboarding-tooltip-header">
          <span class="onboarding-step-badge" id="onboarding-step-badge">STEP 1 / 3</span>
          <button class="onboarding-skip-btn" id="onboarding-skip-btn">SKIP TOUR (ESC)</button>
        </div>
        <h4 class="onboarding-title" id="onboarding-title">Step Title</h4>
        <p class="onboarding-desc" id="onboarding-desc">Step Description</p>
        <div class="onboarding-actions">
          <div class="onboarding-dots" id="onboarding-dots">
            <span class="onboarding-dot active"></span>
            <span class="onboarding-dot"></span>
            <span class="onboarding-dot"></span>
          </div>
          <div class="onboarding-nav-btns">
            <button class="onboarding-btn secondary" id="onboarding-prev-btn">PREV</button>
            <button class="onboarding-btn" id="onboarding-next-btn">NEXT ➔</button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.overlay);

    this.spotlightEl = document.getElementById('onboarding-spotlight');
    this.tooltipEl = document.getElementById('onboarding-tooltip');
    this.stepBadgeEl = document.getElementById('onboarding-step-badge');
    this.titleEl = document.getElementById('onboarding-title');
    this.descEl = document.getElementById('onboarding-desc');
    this.dotsContainer = document.getElementById('onboarding-dots');
    this.skipBtn = document.getElementById('onboarding-skip-btn');
    this.prevBtn = document.getElementById('onboarding-prev-btn');
    this.nextBtn = document.getElementById('onboarding-next-btn');
  }

  initEvents() {
    if (this.skipBtn) {
      this.skipBtn.addEventListener('click', () => this.endTour());
    }

    if (this.prevBtn) {
      this.prevBtn.addEventListener('click', () => {
        sound.playClick();
        this.prevStep();
      });
    }

    if (this.nextBtn) {
      this.nextBtn.addEventListener('click', () => {
        sound.playClick();
        this.nextStep();
      });
    }

    window.addEventListener('keydown', (e) => {
      if (this.isActive) {
        if (e.key === 'Escape') this.endTour();
        else if (e.key === 'ArrowRight' || e.key === 'Enter') this.nextStep();
        else if (e.key === 'ArrowLeft') this.prevStep();
      }
    });

    window.addEventListener('resize', () => {
      if (this.isActive) this.positionStep(this.currentStep);
    });
  }

  shouldAutoStart() {
    try {
      return !localStorage.getItem(this.storageKey);
    } catch (e) {
      return true;
    }
  }

  startTour(force = false) {
    if (!force && !this.shouldAutoStart()) return;
    this.currentStep = 0;
    this.isActive = true;
    this.overlay.classList.add('active');
    sound.playRadarPing();
    this.renderStep(this.currentStep);
  }

  renderStep(index) {
    if (index < 0 || index >= this.steps.length) return;
    const step = this.steps[index];

    if (this.stepBadgeEl) this.stepBadgeEl.textContent = `STEP ${index + 1} / ${this.steps.length}`;
    if (this.titleEl) this.titleEl.textContent = step.title;
    if (this.descEl) this.descEl.textContent = step.desc;

    // Update dots
    if (this.dotsContainer) {
      const dots = this.dotsContainer.querySelectorAll('.onboarding-dot');
      dots.forEach((d, i) => d.classList.toggle('active', i === index));
    }

    // Update buttons
    if (this.prevBtn) {
      this.prevBtn.style.display = index === 0 ? 'none' : 'inline-block';
    }
    if (this.nextBtn) {
      this.nextBtn.textContent = index === this.steps.length - 1 ? 'FINISH TOUR ✓' : 'NEXT ➔';
    }

    this.positionStep(index);
  }

  positionStep(index) {
    const step = this.steps[index];
    const targetEl = document.getElementById(step.targetId);
    if (!targetEl || !this.spotlightEl || !this.tooltipEl) return;

    const rect = targetEl.getBoundingClientRect();
    const pad = 6;

    // Position spotlight rectangle around target element
    this.spotlightEl.style.top = `${rect.top - pad}px`;
    this.spotlightEl.style.left = `${rect.left - pad}px`;
    this.spotlightEl.style.width = `${rect.width + pad * 2}px`;
    this.spotlightEl.style.height = `${rect.height + pad * 2}px`;

    // Position tooltip relative to target
    const tooltipWidth = 340;
    const tooltipHeight = 180;
    let top = rect.top + 20;
    let left = rect.left + 20;

    if (step.preferredSide === 'right') {
      left = Math.min(window.innerWidth - tooltipWidth - 20, rect.right + 20);
      top = Math.max(70, Math.min(window.innerHeight - tooltipHeight - 20, rect.top + 30));
    } else if (step.preferredSide === 'left') {
      left = Math.max(20, rect.left - tooltipWidth - 20);
      top = Math.max(70, Math.min(window.innerHeight - tooltipHeight - 20, rect.top + 30));
    } else if (step.preferredSide === 'bottom') {
      top = Math.min(window.innerHeight - tooltipHeight - 20, rect.bottom - tooltipHeight - 40);
      left = Math.max(20, Math.min(window.innerWidth - tooltipWidth - 20, rect.left + rect.width / 2 - tooltipWidth / 2));
    }

    this.tooltipEl.style.top = `${top}px`;
    this.tooltipEl.style.left = `${left}px`;
  }

  nextStep() {
    if (this.currentStep < this.steps.length - 1) {
      this.currentStep++;
      this.renderStep(this.currentStep);
    } else {
      this.endTour();
    }
  }

  prevStep() {
    if (this.currentStep > 0) {
      this.currentStep--;
      this.renderStep(this.currentStep);
    }
  }

  endTour() {
    this.isActive = false;
    this.overlay.classList.remove('active');
    sound.playClick();
    try {
      localStorage.setItem(this.storageKey, 'true');
    } catch (e) {}
  }
}
