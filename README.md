# SatQuery AI — Vision-Language Satellite Intelligence Mission Control (ISRO Earth Observation)

**SatQuery AI** is an interactive, space-agency grade vision-language remote sensing platform engineered for multimodal satellite image analysis. Designed like an **ISRO Mission Control Console**, operators can enter plain-language queries (e.g. *"Show flooded areas near this river vs last month"*, *"Count ships in this port"*, *"Has this area been deforested since 2022?"*) to receive grounded multimodal intelligence: structured tactical dossiers, precise geospatial overlays (bounding boxes, segmentation contours, bi-temporal change heatmaps), and multi-agent reasoning telemetry.

---

## 🌟 Key Features

1. **Space-Agency Mission Control Console Interface**:
   - Deep space near-black `#0A0E14` environment with cyan glowing instrumentation (`#00D9FF`, `#111826`).
   - Technical monospace telemetry typography (*JetBrains Mono* / *Space Mono*) for coordinates, GSD resolution, and timestamps.
   - Live synchronized orbital clocks (UTC & IST) and satellite constellation status (Cartosat-3, RISAT-2BR1, Sentinel-2).
   - Dual-pane swipe comparison slider for bi-temporal satellite passes.
   - Interactive radar sweep and reticle crosshairs.
   - Built-in Web Audio synthesizer for tactile mission telemetry beeps and alerts.

2. **Autonomous Multi-Tool LLM Orchestrator**:
   - Natural language query decomposition and dynamic execution graph.
   - Live step-by-step reasoning telemetry stream (`Intent Planner` ➔ `Tool Selection` ➔ `CV Execution` ➔ `VLM Grounding`).
   - Seamlessly integrates with Gemini API (`@google/genai` / `google-genai`) when `GEMINI_API_KEY` is present, alongside a 100% functional offline deterministic reasoning engine.

3. **Computer Vision & Remote Sensing Engines**:
   - **YOLOv8 Object Detection**: High-precision maritime vessel tracking, naval classification, aircraft, fuel tanks, and building inventories.
   - **Spectral Index Segmentation**:
     - **NDWI**: Flood inundation mapping and reservoir surface water boundary extraction.
     - **NDVI**: Forest canopy density, deforestation masks, and crop vigor.
     - **NBR**: Wildfire burn scars and thermal anomalies.
     - Polygon contour extraction and accurate area measurement (hectares and km²).
   - **Bi-Temporal Change Detection**: Sub-pixel image co-registration, multi-scale SSIM difference mapping, radiometric CVA, and categorized change masks.

4. **Preloaded ISRO Mission Catalog**:
   - **01 // Mumbai Port & Naval Dockyard**: Maritime vessel surveillance (18 confirmed targets).
   - **02 // Brahmaputra River Basin**: Monsoon flood inundation (142.8 km² inundated, +248.5% water delta).
   - **03 // Western Ghats Biosphere**: Forest canopy degradation & 6.2 km² wildfire burn scar.
   - **04 // SDSC-SHAR Sriharikota**: Launch complex aerospace asset audit & cryogenic propellant tanks.
   - **05 // Chennai Suburbs**: Urban expansion (+38.2%) and Pallikaranai wetland shrinkage.
   - **06 // Custom Imagery**: Upload single or bi-temporal satellite image pairs for custom automated CV processing.

5. **Mission Intelligence Dossier Export**:
   - Formatted printable intelligence reports (PDF/Print).
   - Export polygon contours to GeoJSON.
   - Export detected target inventories to CSV.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Start Backend Flask Server
```powershell
# In project root:
& "C:\Users\DELL\.local\bin\uv.exe" run --python backend\.venv\Scripts\python.exe backend\app.py
```
The REST API will launch at `http://127.0.0.1:5000`.

### 2. Start Frontend Mission Control Console
```powershell
# In frontend directory:
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Running Automated Unit Tests
```powershell
& "C:\Users\DELL\.local\bin\uv.exe" run --python backend\.venv\Scripts\python.exe -m unittest backend\tests\test_pipeline.py
```
