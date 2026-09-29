/**
 * mapEngine.js
 * Geospatial Tactical Canvas & Leaflet GIS Engine
 */

export class MapEngine {
  constructor(telemetryHUD) {
    this.hud = telemetryHUD;
    this.map = null;
    this.canvas = document.getElementById('tactical-canvas');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    
    this.markersLayer = null;
    this.geojsonLayer = null;
    this.imageOverlay = null;
    this.imageOverlayT2 = null;

    // Feature toggles
    this.showDetections = true;
    this.showMasks = true;
    this.showCrosshairs = true;
    this.showRadar = false;
    this.splitMode = false;
    this.sliderPosition = 0.5; // 50%

    this.currentDetections = [];
    this.currentMaskPolygons = [];
    this.currentMissionData = null;

    this.initMap();
    this.initCanvasResize();
    this.initSplitSlider();
  }

  initMap() {
    // Default center on Mumbai Port
    this.map = L.map('leaflet-map', {
      center: [18.9438, 72.8354],
      zoom: 14,
      minZoom: 2,
      maxZoom: 18,
      zoomControl: true,
      attributionControl: true
    });

    // ESRI High-Resolution Optical Satellite Imagery (Default - 100% Free & No API key)
    const satelliteImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri, Maxar, Earthstar Geographics, ISRO',
      maxNativeZoom: 18,
      maxZoom: 19,
      crossOrigin: true,
      keepBuffer: 8,
      updateWhenIdle: false,
      updateWhenZooming: true
    });

    // ESRI Dark Gray Canvas Basemap (Free & Clean)
    const darkCanvas = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri, HERE, Garmin, OpenStreetMap',
      maxNativeZoom: 16,
      maxZoom: 18,
      crossOrigin: true,
      keepBuffer: 8,
      updateWhenIdle: false,
      updateWhenZooming: true
    });

    // Set Satellite Optical as default
    satelliteImagery.addTo(this.map);

    this.baseMaps = {
      "Satellite Optical": satelliteImagery,
      "Tactical Dark": darkCanvas
    };

    L.control.layers(this.baseMaps, null, { position: 'topright' }).addTo(this.map);

    this.markersLayer = L.layerGroup().addTo(this.map);
    this.geojsonHaloLayer = L.geoJSON(null, {
      style: (feature) => ({
        color: feature.properties?.color || '#00D9FF',
        weight: 7,
        opacity: 0.35,
        fillColor: 'transparent',
        dashArray: '2, 4',
        lineCap: 'round',
        lineJoin: 'round'
      })
    }).addTo(this.map);

    this.geojsonLayer = L.geoJSON(null, {
      style: (feature) => ({
        color: feature.properties?.color || '#00D9FF',
        weight: 1.8,
        opacity: 0.9,
        fillColor: feature.properties?.fillColor || '#00D9FF',
        fillOpacity: feature.properties?.fillOpacity || 0.32
      }),
      onEachFeature: (feature, layer) => {
        const featType = feature.properties?.label || feature.properties?.name || 'Segmented Surface Feature';
        const areaVal = feature.properties?.area_km2 ? `${feature.properties.area_km2} km²` : 'Calculated Inundation Mask';
        layer.bindPopup(`
          <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #00D9FF; background: #0A0E18; padding: 8px; border: 1px solid #00D9FF; border-radius: 2px;">
            <strong style="color: #FFFFFF; text-transform: uppercase;">${featType}</strong><br/>
            <span>EXTENT: ${areaVal}</span><br/>
            <span style="color: #FCD34D;">⚡ BOUNDARY: Probabilistic Gradient (±5m)</span><br/>
            <span style="color: #94A3B8; font-size: 9.5px;">SENSOR: Multi-Sensor Radar/MSI Fusion</span>
          </div>
        `);
      }
    }).addTo(this.map);

    // Mouse coordinate tracking
    this.map.on('mousemove', (e) => {
      this.hud.updateCursor(e.latlng.lat, e.latlng.lng, this.map.getZoom());
    });

    this.map.on('zoomend moveend', () => {
      this.drawCanvasOverlay();
    });
  }

  initCanvasResize() {
    const resize = () => {
      if (!this.canvas) return;
      const rect = this.canvas.parentElement.getBoundingClientRect();
      this.canvas.width = rect.width;
      this.canvas.height = rect.height;
      this.drawCanvasOverlay();
    };

    window.addEventListener('resize', resize);
    setTimeout(resize, 100);
  }

  initSplitSlider() {
    const sliderWrap = document.getElementById('comparison-slider-wrap');
    const divider = document.getElementById('slider-divider');
    if (!sliderWrap || !divider) return;

    let isDragging = false;

    const onMove = (clientX) => {
      const rect = sliderWrap.getBoundingClientRect();
      let x = clientX - rect.left;
      x = Math.max(20, Math.min(rect.width - 20, x));
      const pct = x / rect.width;
      this.sliderPosition = pct;
      divider.style.left = `${pct * 100}%`;
      this.drawCanvasOverlay();
    };

    divider.addEventListener('mousedown', (e) => {
      isDragging = true;
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (isDragging) onMove(e.clientX);
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });
  }

  toggleSplitMode(enable) {
    this.splitMode = enable !== undefined ? enable : !this.splitMode;
    const sliderWrap = document.getElementById('comparison-slider-wrap');
    if (sliderWrap) {
      if (this.splitMode) {
        sliderWrap.classList.add('active');
      } else {
        sliderWrap.classList.remove('active');
      }
    }
    this.drawCanvasOverlay();
    return this.splitMode;
  }

  loadMissionScene(mission) {
    this.currentMissionData = mission;
    if (!mission || !mission.center) return;

    // Pan & zoom to mission AOI
    this.map.setView(mission.center, mission.zoom || 14);

    // Update T1/T2 labels
    const t1Label = document.getElementById('t1-label');
    const t2Label = document.getElementById('t2-label');
    if (t1Label && mission.t1_date) t1Label.textContent = `T1: PRE-EVENT (${mission.t1_date})`;
    if (t2Label && mission.t2_date) t2Label.textContent = `T2: POST-EVENT (${mission.t2_date})`;

    this.clearOverlays();
    setTimeout(() => {
      if (this.map) this.map.invalidateSize();
    }, 100);
  }

  renderUploadedImageryPreview(session) {
    if (!session || !this.map) return;

    this.clearOverlays();

    // Validate and sanitize bounds
    let bounds = session.bounds || session.metadata_primary?.bounds;
    if (!Array.isArray(bounds) || bounds.length < 2 || 
        Math.abs(bounds[0][0]) > 90 || Math.abs(bounds[0][1]) > 180 ||
        Math.abs(bounds[1][0]) > 90 || Math.abs(bounds[1][1]) > 180) {
      bounds = [[18.9200, 72.8100], [18.9650, 72.8600]];
    }

    let previewP = session.preview_primary || session.metadata_primary?.preview_base64;
    let previewS = session.preview_secondary || session.metadata_secondary?.preview_base64;

    if (previewP && !previewP.startsWith('data:') && !previewP.startsWith('http') && !previewP.startsWith('/')) {
      previewP = `data:image/jpeg;base64,${previewP}`;
    }
    if (previewS && !previewS.startsWith('data:') && !previewS.startsWith('http') && !previewS.startsWith('/')) {
      previewS = `data:image/jpeg;base64,${previewS}`;
    }

    // Remove existing image overlays and tactical rectangles
    if (this.imageOverlay) {
      this.map.removeLayer(this.imageOverlay);
      this.imageOverlay = null;
    }
    if (this.imageOverlayT2) {
      this.map.removeLayer(this.imageOverlayT2);
      this.imageOverlayT2 = null;
    }
    if (this.uploadedAoiRect) {
      this.map.removeLayer(this.uploadedAoiRect);
      this.uploadedAoiRect = null;
    }
    if (this.uploadedMarker) {
      this.map.removeLayer(this.uploadedMarker);
      this.uploadedMarker = null;
    }

    // Render Primary Ingested Raster Overlay
    if (previewP) {
      this.imageOverlay = L.imageOverlay(previewP, bounds, {
        opacity: 0.95,
        interactive: false,
        zIndex: 450
      }).addTo(this.map);
      if (this.imageOverlay.bringToFront) {
        this.imageOverlay.bringToFront();
      }
    }

    // Render Tactical AOI Bounding Rectangle & Callout Pin
    this.uploadedAoiRect = L.rectangle(bounds, {
      color: '#00F3FF',
      weight: 2,
      dashArray: '6, 6',
      fillColor: '#00F3FF',
      fillOpacity: 0.06
    }).addTo(this.map);

    const centerLat = (bounds[0][0] + bounds[1][0]) / 2;
    const centerLon = (bounds[0][1] + bounds[1][1]) / 2;
    const sensorLabel = session.metadata_primary?.sensor_type || 'INGESTED SCENE';

    const customPin = L.divIcon({
      className: 'custom-aoi-pin',
      html: `<div style="background:rgba(3,7,13,0.92); border:1px solid #00F3FF; color:#00F3FF; font-family:var(--font-mono, monospace); font-size:9.5px; font-weight:bold; padding:3px 8px; border-radius:3px; white-space:nowrap; box-shadow:0 0 12px rgba(0,243,255,0.5); text-transform:uppercase;">🛰️ ${sensorLabel} (ACTIVE)</div>`,
      iconAnchor: [70, 24]
    });
    this.uploadedMarker = L.marker([centerLat, centerLon], { icon: customPin }).addTo(this.map);

    if (previewS && (session.mode === 'bitemporal' || session.mode === 'cross_modal')) {
      this.imageOverlayT2 = L.imageOverlay(previewS, bounds, {
        opacity: 0.95,
        interactive: false,
        zIndex: 460
      });
      this.setSplitMode(true);
    } else {
      this.setSplitMode(false);
    }

    // Fit map view to exact uploaded bounds with smooth animation
    this.map.fitBounds(bounds, { padding: [30, 30], maxZoom: 16 });
    setTimeout(() => {
      if (this.map) this.map.invalidateSize();
    }, 150);

    // Update HUD telemetry
    const center = this.map.getCenter();
    if (this.hud) {
      this.hud.updateCursor(center.lat, center.lng, this.map.getZoom());
    }

    const gsdEl = document.getElementById('hud-gsd');
    if (gsdEl && session.metadata_primary?.gsd_m) {
      gsdEl.textContent = `${session.metadata_primary.gsd_m} m/px`;
    }

    // Update AOI coordinates in left panel
    const nEl = document.getElementById('aoi-n');
    const sEl = document.getElementById('aoi-s');
    const eEl = document.getElementById('aoi-e');
    const wEl = document.getElementById('aoi-w');
    if (nEl) nEl.textContent = `${bounds[1][0].toFixed(4)}°`;
    if (sEl) sEl.textContent = `${bounds[0][0].toFixed(4)}°`;
    if (eEl) eEl.textContent = `${bounds[1][1].toFixed(4)}°`;
    if (wEl) wEl.textContent = `${bounds[0][1].toFixed(4)}°`;
  }

  clearOverlays() {
    this.currentDetections = [];
    this.currentMaskPolygons = [];
    if (this.markersLayer) this.markersLayer.clearLayers();
    if (this.geojsonLayer) this.geojsonLayer.clearLayers();
    if (this.ctx && this.canvas) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  toggleDetections(enable) {
    this.showDetections = enable !== undefined ? enable : !this.showDetections;
    if (this.showDetections) {
      if (!this.map.hasLayer(this.markersLayer)) {
        this.markersLayer.addTo(this.map);
      }
      this.renderDetections(this.currentDetections);
    } else {
      this.markersLayer.clearLayers();
      if (this.ctx && this.canvas) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      }
    }
    return this.showDetections;
  }

  toggleMasks(enable) {
    this.showMasks = enable !== undefined ? enable : !this.showMasks;
    if (this.showMasks) {
      if (this.geojsonLayer && !this.map.hasLayer(this.geojsonLayer)) {
        this.geojsonLayer.addTo(this.map);
      }
      if (this.geojsonHaloLayer && !this.map.hasLayer(this.geojsonHaloLayer)) {
        this.geojsonHaloLayer.addTo(this.map);
      }
    } else {
      if (this.geojsonLayer && this.map.hasLayer(this.geojsonLayer)) {
        this.map.removeLayer(this.geojsonLayer);
      }
      if (this.geojsonHaloLayer && this.map.hasLayer(this.geojsonHaloLayer)) {
        this.map.removeLayer(this.geojsonHaloLayer);
      }
    }
    return this.showMasks;
  }

  setSplitMode(enable) {
    return this.toggleSplitMode(enable);
  }

  renderDetections(detections) {
    this.currentDetections = detections || [];
    this.markersLayer.clearLayers();

    if (!this.showDetections) return;

    this.currentDetections.forEach((det, idx) => {
      if (!det.lat || !det.lon) return;

      const markerHtml = `
        <div class="target-radar-marker">
          <div class="marker-pulse-ring"></div>
          <div class="marker-center-dot ${det.type || 'ship'}"></div>
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-radar-icon',
        html: markerHtml,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      const marker = L.marker([det.lat, det.lon], { icon: customIcon });
      const confPct = ((det.confidence || 0.9) * 100).toFixed(0);
      marker.bindPopup(`
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #00D9FF; background: #111826; padding: 6px; border: 1px solid #00D9FF;">
          <strong>TARGET #${idx + 1}</strong>: ${det.label || 'Vessel'}<br/>
          CONFIDENCE: ${confPct}%<br/>
          COORDS: ${det.lat.toFixed(4)}°N, ${det.lon.toFixed(4)}°E<br/>
          CLASS: ${det.type?.toUpperCase() || 'MARITIME'}
        </div>
      `);

      this.markersLayer.addLayer(marker);
    });

    this.drawCanvasOverlay();
  }

  renderMasksAndChange(geojsonFeatureCollection) {
    this.currentMaskPolygons = geojsonFeatureCollection;
    if (this.geojsonLayer && geojsonFeatureCollection) {
      this.geojsonLayer.clearLayers();
      if (this.geojsonHaloLayer) this.geojsonHaloLayer.clearLayers();

      this.geojsonLayer.addData(geojsonFeatureCollection);
      if (this.geojsonHaloLayer) this.geojsonHaloLayer.addData(geojsonFeatureCollection);

      if (!this.showMasks) {
        if (this.map.hasLayer(this.geojsonLayer)) this.map.removeLayer(this.geojsonLayer);
        if (this.map.hasLayer(this.geojsonHaloLayer)) this.map.removeLayer(this.geojsonHaloLayer);
      } else {
        if (!this.map.hasLayer(this.geojsonLayer)) this.geojsonLayer.addTo(this.map);
        if (!this.map.hasLayer(this.geojsonHaloLayer)) this.geojsonHaloLayer.addTo(this.map);
      }
    }
  }

  drawCanvasOverlay() {
    if (!this.ctx || !this.canvas) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    if (!this.showDetections) return;

    // Draw vector bounding boxes & telemetry tags on tactical canvas
    this.currentDetections.forEach((det, idx) => {
      if (!det.lat || !det.lon) return;

      const point = this.map.latLngToContainerPoint([det.lat, det.lon]);
      const w = det.box_width || 38;
      const h = det.box_height || 24;
      const x = point.x - w / 2;
      const y = point.y - h / 2;

      // Color based on class
      let strokeColor = '#00D9FF';
      if (det.type === 'aircraft') strokeColor = '#FFB800';
      if (det.type === 'building') strokeColor = '#3DDC97';
      if (det.type === 'tank') strokeColor = '#00E5FF';
      if (det.type === 'hazard' || det.type === 'fire') strokeColor = '#FF5C5C';

      this.ctx.strokeStyle = strokeColor;
      this.ctx.lineWidth = 1.5;
      this.ctx.shadowColor = strokeColor;
      this.ctx.shadowBlur = 6;

      // Corner brackets (tactical styling)
      const bracketLen = 7;
      // Top-Left
      this.ctx.beginPath();
      this.ctx.moveTo(x, y + bracketLen);
      this.ctx.lineTo(x, y);
      this.ctx.lineTo(x + bracketLen, y);
      this.ctx.stroke();

      // Top-Right
      this.ctx.beginPath();
      this.ctx.moveTo(x + w - bracketLen, y);
      this.ctx.lineTo(x + w, y);
      this.ctx.lineTo(x + w, y + bracketLen);
      this.ctx.stroke();

      // Bottom-Left
      this.ctx.beginPath();
      this.ctx.moveTo(x, y + h - bracketLen);
      this.ctx.lineTo(x, y + h);
      this.ctx.lineTo(x + bracketLen, y + h);
      this.ctx.stroke();

      // Bottom-Right
      this.ctx.beginPath();
      this.ctx.moveTo(x + w - bracketLen, y + h);
      this.ctx.lineTo(x + w, y + h);
      this.ctx.lineTo(x + w, y + h - bracketLen);
      this.ctx.stroke();

      // Target Label
      this.ctx.shadowBlur = 0;
      this.ctx.fillStyle = strokeColor;
      this.ctx.font = '9px "JetBrains Mono", monospace';
      const labelText = `[T-${idx + 1}] ${det.label || 'OBJ'} ${(det.confidence * 100).toFixed(0)}%`;
      this.ctx.fillText(labelText, x, y - 4);
    });
  }

  setScanning(isScanning) {
    const sweepOverlay = document.getElementById('map-scanning-sweep');
    if (sweepOverlay) {
      sweepOverlay.classList.toggle('active', isScanning);
    }
  }

  setModalityLayer(mode) {
    // mode: 'optical' | 'sar' | 'fused'
    const mapEl = document.getElementById('leaflet-map');
    if (!mapEl) return;
    mapEl.classList.remove('mode-optical', 'mode-sar', 'mode-fused');
    mapEl.classList.add(`mode-${mode}`);
    this.currentModalityMode = mode;
  }
}
