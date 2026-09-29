/**
 * imageryIngestion.js
 * Frontend Controller for Satellite Imagery Ingestion & Validation Pipeline
 * Supports Single GeoTIFF, Cross-Modal (Optical + SAR) and Bi-Temporal (T1 + T2) uploads.
 */

export class ImageryIngestionController {
  constructor(mapEngine, telemetryHUD, onSessionIngested = null) {
    this.mapEngine = mapEngine;
    this.hud = telemetryHUD;
    this.onSessionIngested = onSessionIngested;

    this.currentMode = 'single'; // 'single' | 'cross_modal' | 'bitemporal'
    this.primaryFile = null;
    this.secondaryFile = null;
    this.isBenchmark = false;
    this.lastValidationReport = null;
    this.activeSessionId = null;

    this.initDOM();
  }

  initDOM() {
    // Mode Switcher Tabs
    this.modeBtns = document.querySelectorAll('.ingest-mode-tab-btn');
    this.modeBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        this.setMode(btn.dataset.mode);
      });
    });

    // Benchmark flag toggle
    this.benchmarkToggle = document.getElementById('ingest-benchmark-toggle');
    if (this.benchmarkToggle) {
      this.benchmarkToggle.addEventListener('change', (e) => {
        this.isBenchmark = e.target.checked;
        this.validateCurrentFiles();
      });
    }

    // Dropzones & File Pickers
    this.dropzoneP = document.getElementById('dropzone-primary');
    this.fileInputP = document.getElementById('file-input-primary');
    this.dropzoneS = document.getElementById('dropzone-secondary');
    this.fileInputS = document.getElementById('file-input-secondary');

    if (this.dropzoneP && this.fileInputP) {
      this.setupDropzone(this.dropzoneP, this.fileInputP, (file) => {
        this.primaryFile = file;
        this.updateFileChip('primary', file);
        this.validateCurrentFiles();
      });
    }

    if (this.dropzoneS && this.fileInputS) {
      this.setupDropzone(this.dropzoneS, this.fileInputS, (file) => {
        this.secondaryFile = file;
        this.updateFileChip('secondary', file);
        this.validateCurrentFiles();
      });
    }

    // Ingest Action Button
    this.ingestBtn = document.getElementById('btn-ingest-and-preview');
    if (this.ingestBtn) {
      this.ingestBtn.addEventListener('click', () => {
        this.executeIngestion();
      });
    }

    // Reset Action Button
    this.resetBtn = document.getElementById('btn-reset-upload');
    if (this.resetBtn) {
      this.resetBtn.addEventListener('click', () => {
        this.reset();
      });
    }

    // Date inputs
    this.dateInputP = document.getElementById('ingest-date-primary');
    this.dateInputS = document.getElementById('ingest-date-secondary');
    if (this.dateInputP) this.dateInputP.addEventListener('change', () => this.validateCurrentFiles());
    if (this.dateInputS) this.dateInputS.addEventListener('change', () => this.validateCurrentFiles());
  }

  setMode(mode) {
    this.currentMode = mode;
    this.modeBtns.forEach(b => {
      b.classList.toggle('active', b.dataset.mode === mode);
    });

    const secDropzoneWrap = document.getElementById('secondary-dropzone-wrap');
    const secDropzoneTitle = document.getElementById('secondary-dropzone-title');
    const secDateWrap = document.getElementById('secondary-date-wrap');

    if (mode === 'single') {
      if (secDropzoneWrap) secDropzoneWrap.style.display = 'none';
      if (secDateWrap) secDateWrap.style.display = 'none';
    } else if (mode === 'cross_modal') {
      if (secDropzoneWrap) secDropzoneWrap.style.display = 'flex';
      if (secDropzoneTitle) secDropzoneTitle.textContent = 'SECONDARY SENSOR (SAR RADAR / AMPLITUDE)';
      if (secDateWrap) secDateWrap.style.display = 'none';
    } else if (mode === 'bitemporal') {
      if (secDropzoneWrap) secDropzoneWrap.style.display = 'flex';
      if (secDropzoneTitle) secDropzoneTitle.textContent = 'POST-EVENT IMAGERY (T2 POST-CHANGE)';
      if (secDateWrap) secDateWrap.style.display = 'flex';
    }

    this.validateCurrentFiles();
  }

  setupDropzone(dropzoneEl, fileInputEl, onFileSelected) {
    dropzoneEl.addEventListener('click', () => fileInputEl.click());

    fileInputEl.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        onFileSelected(e.target.files[0]);
      }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzoneEl.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzoneEl.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzoneEl.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzoneEl.classList.remove('dragover');
      });
    });

    dropzoneEl.addEventListener('drop', (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        onFileSelected(e.dataTransfer.files[0]);
      }
    });
  }

  updateFileChip(slot, file) {
    const chipEl = document.getElementById(`file-chip-${slot}`);
    if (chipEl) {
      if (file) {
        const sizeKb = (file.size / 1024).toFixed(1);
        chipEl.innerHTML = `
          <div class="uploaded-file-chip">
            <span class="file-icon">📄</span>
            <span class="file-name" title="${file.name}">${file.name}</span>
            <span class="file-size">${sizeKb} KB</span>
          </div>
        `;
        chipEl.style.display = 'block';
      } else {
        chipEl.style.display = 'none';
        chipEl.innerHTML = '';
      }
    }
  }

  async validateCurrentFiles() {
    if (!this.primaryFile) {
      this.renderChecklistEmpty();
      if (this.ingestBtn) this.ingestBtn.disabled = true;
      return;
    }

    const formData = new FormData();
    formData.append('mode', this.currentMode);
    formData.append('is_benchmark', this.isBenchmark ? 'true' : 'false');
    formData.append('file_primary', this.primaryFile);

    if (this.currentMode !== 'single' && this.secondaryFile) {
      formData.append('file_secondary', this.secondaryFile);
    }

    if (this.dateInputP && this.dateInputP.value) formData.append('date_p', this.dateInputP.value);
    if (this.dateInputS && this.dateInputS.value) formData.append('date_s', this.dateInputS.value);

    // Render assessing status
    this.renderChecklistEvaluating();

    try {
      const res = await fetch('http://127.0.0.1:5000/upload/validate', {
        method: 'POST',
        body: formData
      });

      const report = await res.json();
      this.lastValidationReport = report;
      this.renderValidationReport(report);

      if (this.ingestBtn) {
        this.ingestBtn.disabled = !report.passed;
      }
    } catch (err) {
      this.renderChecklistError(err.message);
      if (this.ingestBtn) this.ingestBtn.disabled = true;
    }
  }

  renderChecklistEmpty() {
    const listEl = document.getElementById('ingest-checks-list');
    const badgeEl = document.getElementById('ingest-status-badge');
    const metaEl = document.getElementById('ingest-meta-grid');

    if (badgeEl) {
      badgeEl.textContent = 'AWAITING FILES';
      badgeEl.className = 'panel-badge';
      badgeEl.style.color = 'var(--text-muted)';
      badgeEl.style.borderColor = 'rgba(255,255,255,0.15)';
    }

    if (listEl) {
      listEl.innerHTML = `
        <div class="check-item-row idle">
          <span class="check-icon">○</span>
          <div class="check-info">
            <span class="check-title">Format & Header Validation</span>
            <span class="check-desc">Awaiting GeoTIFF or benchmark sample upload...</span>
          </div>
        </div>
      `;
    }

    if (metaEl) {
      metaEl.style.display = 'none';
    }
  }

  renderChecklistEvaluating() {
    const badgeEl = document.getElementById('ingest-status-badge');
    if (badgeEl) {
      badgeEl.textContent = 'EVALUATING...';
      badgeEl.className = 'panel-badge';
      badgeEl.style.color = 'var(--amber-alert)';
      badgeEl.style.borderColor = 'var(--amber-alert)';
    }
  }

  renderValidationReport(report) {
    const listEl = document.getElementById('ingest-checks-list');
    const badgeEl = document.getElementById('ingest-status-badge');
    const metaGrid = document.getElementById('ingest-meta-grid');
    const bannerEl = document.getElementById('ingest-summary-banner');

    if (badgeEl) {
      badgeEl.textContent = report.status === 'PASS' ? '● PASSED (100%)' : (report.status === 'WARN' ? '◆ NOTICE (PASS)' : '▲ FAILED');
      badgeEl.className = `panel-badge ${report.status.toLowerCase()}`;
      if (report.status === 'PASS') {
        badgeEl.style.color = 'var(--green-nominal)';
        badgeEl.style.borderColor = 'var(--green-nominal)';
      } else if (report.status === 'WARN') {
        badgeEl.style.color = 'var(--amber-alert)';
        badgeEl.style.borderColor = 'var(--amber-alert)';
      } else {
        badgeEl.style.color = 'var(--red-critical)';
        badgeEl.style.borderColor = 'var(--red-critical)';
      }
    }

    if (bannerEl) {
      bannerEl.textContent = report.summary_message || '';
      bannerEl.className = `ingest-summary-banner ${report.status.toLowerCase()}`;
      bannerEl.style.display = 'block';
    }

    if (listEl && report.checks) {
      listEl.innerHTML = report.checks.map(c => `
        <div class="check-item-row ${c.status}">
          <span class="check-icon">${c.status === 'pass' ? '✓' : (c.status === 'warn' ? '◆' : '✕')}</span>
          <div class="check-info">
            <span class="check-title">${c.name}</span>
            <span class="check-desc">${c.message}</span>
          </div>
        </div>
      `).join('');
    }

    // Populate Extracted Metadata Grid
    if (metaGrid && report.metadata_primary) {
      const p = report.metadata_primary;
      const boundsStr = p.bounds ? `[${p.bounds[0][0].toFixed(2)}°, ${p.bounds[0][1].toFixed(2)}°]` : 'Global WGS84';
      
      metaGrid.innerHTML = `
        <div class="meta-tile">
          <span class="meta-lbl">SENSOR</span>
          <span class="meta-val">${p.sensor_type}</span>
        </div>
        <div class="meta-tile">
          <span class="meta-lbl">GSD / RES</span>
          <span class="meta-val">${p.gsd_m} m/px</span>
        </div>
        <div class="meta-tile">
          <span class="meta-lbl">RASTER SIZE</span>
          <span class="meta-val">${p.width}x${p.height} px (${p.bands}B)</span>
        </div>
        <div class="meta-tile">
          <span class="meta-lbl">DATUM / CRS</span>
          <span class="meta-val">${p.crs}</span>
        </div>
        <div class="meta-tile">
          <span class="meta-lbl">DATE</span>
          <span class="meta-val">${p.acquisition_date}</span>
        </div>
        <div class="meta-tile">
          <span class="meta-lbl">BOUNDS</span>
          <span class="meta-val">${boundsStr}</span>
        </div>
      `;
      metaGrid.style.display = 'grid';
    }
  }

  renderChecklistError(errorMsg) {
    const listEl = document.getElementById('ingest-checks-list');
    const badgeEl = document.getElementById('ingest-status-badge');
    if (badgeEl) {
      badgeEl.textContent = 'API FAULT';
      badgeEl.style.color = 'var(--red-critical)';
      badgeEl.style.borderColor = 'var(--red-critical)';
    }
    if (listEl) {
      listEl.innerHTML = `<div class="check-item-row fail"><span class="check-icon">✕</span><div class="check-info"><span class="check-title">Validation Error</span><span class="check-desc">${errorMsg}</span></div></div>`;
    }
  }

  async executeIngestion() {
    if (!this.primaryFile || !this.lastValidationReport || !this.lastValidationReport.passed) {
      alert('Cannot ingest: Validation checks must pass first.');
      return;
    }

    const formData = new FormData();
    formData.append('mode', this.currentMode);
    formData.append('is_benchmark', this.isBenchmark ? 'true' : 'false');
    formData.append('file_primary', this.primaryFile);
    if (this.currentMode !== 'single' && this.secondaryFile) {
      formData.append('file_secondary', this.secondaryFile);
    }
    if (this.dateInputP && this.dateInputP.value) formData.append('date_p', this.dateInputP.value);
    if (this.dateInputS && this.dateInputS.value) formData.append('date_s', this.dateInputS.value);

    if (this.ingestBtn) {
      this.ingestBtn.disabled = true;
      this.ingestBtn.innerHTML = '<span>⚡</span> INGESTING & ANCHORING TO MAP...';
    }

    try {
      const res = await fetch('http://127.0.0.1:5000/upload/ingest', {
        method: 'POST',
        body: formData
      });

      const session = await res.json();
      if (!res.ok) {
        throw new Error(session.error || 'Ingestion failed');
      }

      this.activeSessionId = session.session_id;

      // Render on Map immediately
      if (this.mapEngine) {
        this.mapEngine.renderUploadedImageryPreview(session);
      }

      // Notify App controller to set active scenario/mission
      if (this.onSessionIngested) {
        this.onSessionIngested(session);
      }

      if (this.ingestBtn) {
        this.ingestBtn.disabled = false;
        this.ingestBtn.innerHTML = '<span>✓</span> INGESTED · READY FOR QUERIES';
        this.ingestBtn.style.background = 'var(--green-nominal)';
        this.ingestBtn.style.color = '#03070D';
        setTimeout(() => {
          this.ingestBtn.innerHTML = '<span>🛰️</span> INGEST & PREVIEW ON MAP';
          this.ingestBtn.style.background = '';
          this.ingestBtn.style.color = '';
        }, 4000);
      }
    } catch (err) {
      alert(`Ingestion failed: ${err.message}`);
      if (this.ingestBtn) {
        this.ingestBtn.disabled = false;
        this.ingestBtn.innerHTML = '<span>🛰️</span> INGEST & PREVIEW ON MAP';
      }
    }
  }

  reset() {
    this.primaryFile = null;
    this.secondaryFile = null;
    this.lastValidationReport = null;
    this.activeSessionId = null;

    if (this.fileInputP) this.fileInputP.value = '';
    if (this.fileInputS) this.fileInputS.value = '';
    this.updateFileChip('primary', null);
    this.updateFileChip('secondary', null);
    this.renderChecklistEmpty();

    const bannerEl = document.getElementById('ingest-summary-banner');
    if (bannerEl) bannerEl.style.display = 'none';

    if (this.ingestBtn) this.ingestBtn.disabled = true;
  }
}
