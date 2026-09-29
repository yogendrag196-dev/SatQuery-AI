<div align="center">

<h1>SatQuery AI</h1>

<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&pause=1100&color=00E5FF&center=true&vCenter=true&width=820&lines=Ask+your+satellite+imagery+anything.+%F0%9F%9B%B0%EF%B8%8F;Question+%E2%86%92+AI+agent+%E2%86%92+specialist+models+%E2%86%92+evidence;Detect+%C2%B7+Compare+%C2%B7+Segment+%C2%B7+Fuse;Every+answer+grounded%2C+scored%2C+and+explainable+%F0%9F%94%8D" alt="Typing animation"/>
</a>

<br/><br/>

<img src="radar-hero.svg" width="100%" alt="SatQuery AI animated radar"/>

<br/>

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_VLM-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-00FFFF?style=for-the-badge&logoColor=black)

![Modes](https://img.shields.io/badge/Modes-Single_%7C_Cross--modal_%7C_Bi--temporal-00e5ff?style=flat-square)
![Sensors](https://img.shields.io/badge/Sensors-Optical_%7C_SAR_%7C_Fused-4dffb8?style=flat-square)
![Export](https://img.shields.io/badge/Export-PDF_%7C_GeoJSON_%7C_CSV-ffb020?style=flat-square)

<br/>

<img src="landing.png" width="92%" alt="SatQuery AI landing page"/>

</div>

---

## 📖 Contents

[Why SatQuery](#-why-satquery) · [How It Works](#-how-it-works) · [Capabilities](#-capabilities) · [Interface Tour](#-interface-tour) · [A Mission, Start to Finish](#-a-mission-start-to-finish) · [Trust & Explainability](#-trust--explainability) · [Architecture](#-architecture) · [How It Compares](#-how-it-compares) · [Tech Stack](#-tech-stack) · [Getting Started](#-getting-started) · [Limitations](#-honest-limitations) · [Roadmap](#-roadmap)

---

## 🌍 Why SatQuery

Satellite imagery holds answers to urgent questions: *Where did the flood spread? How much forest was lost? How many vessels are in this port?* But getting those answers normally means picking tools, preparing rasters, writing scripts and interpreting the output by hand.

**SatQuery AI replaces that workflow with a conversation.**

| Traditional workflow | SatQuery AI |
|---|---|
| Data → pick tools → manual GIS analysis → human interpretation | **Question → AI agent → specialist models → multi-sensor evidence → actionable answer** |
| Needs GIS / remote-sensing expertise | Plain-language questions, voice input included |
| Results are maps and numbers you must explain yourself | Grounded answers with regions, metrics, confidence and stated uncertainty |
| One tool per task | An agent that routes each question to the right specialist |

---

## ⚙️ How It Works

<div align="center">
  <img src="agent-flow.svg" width="100%" alt="Animated SatQuery AI agent pipeline"/>
</div>

<br/>

You type a question such as *"What changed between these two dates, and where? Quantify area variance."* The agent then:

1. **Understands** the query and identifies the task (detection, change analysis, segmentation, fusion, captioning).
2. **Validates** the imagery: file format, radiometric bands, spatial resolution (GSD), georeferencing / CRS and acquisition dates.
3. **Plans** an execution graph and calls the specialist tools it needs.
4. **Fuses & verifies** evidence across time and sensors, and scores its confidence.
5. **Delivers** a structured intelligence card, map overlays and an exportable dossier.

```mermaid
flowchart LR
    Q([💬 Natural-language query]) --> V{🛰️ Validate imagery<br/>format · bands · GSD · CRS · dates}
    V -- "fails checks" --> R[/⚠️ Explain what is incompatible/]
    V -- "passes" --> P[🧠 Intent planner]
    P --> O[🧭 Orchestrator<br/>tool-calling DAG]
    O --> D[🎯 Detect<br/>YOLOv8]
    O --> C[🔄 Compare<br/>SSIM + CVA]
    O --> S[🌿 Segment<br/>NDWI · NDVI · NBR]
    O --> F[📡 Fuse<br/>Optical + SAR]
    D & C & S & F --> G[✨ Gemini VLM<br/>grounded synthesis]
    G --> E{Confidence<br/>below threshold?}
    E -- "yes" --> H[🙋 Flag for human verification]
    E -- "no" --> A[✅ Verified answer + alerts]
    H --> A
    A --> X[(📄 PDF · GeoJSON · CSV)]

    style O fill:#0a1c2e,stroke:#4dffb8,color:#fff
    style G fill:#0a1c2e,stroke:#4dffb8,color:#fff
    style V fill:#0e3a52,stroke:#00e5ff,color:#fff
    style E fill:#0e3a52,stroke:#ffb020,color:#fff
    style R fill:#4a1c24,stroke:#ff5c6c,color:#fff
```

<details>
<summary><b>🎬 Watch a request move through the system (sequence diagram)</b></summary>

```mermaid
sequenceDiagram
    autonumber
    actor A as Analyst
    participant UI as Console (React)
    participant API as Backend API
    participant AG as Agent / Orchestrator
    participant CV as CV Ensemble
    participant VLM as Gemini VLM

    A->>UI: Load imagery + ask a question
    UI->>API: query + AOI + dates
    API->>AG: validate + parse intent
    AG-->>UI: status: Processing
    AG->>CV: run detection / change / spectral tools
    CV-->>AG: boxes · masks · metrics
    AG->>VLM: evidence + question
    VLM-->>AG: grounded narrative + uncertainty
    AG-->>API: structured intelligence card + confidence
    API-->>UI: status: Verified · map overlays
    UI-->>A: answer · model trail · export
```

</details>

---

## 🎯 Capabilities

<div align="center">

| 🎯 **Detect** | 🔄 **Compare** | 🌿 **Segment** | 📡 **Fuse** |
|:---:|:---:|:---:|:---:|
| High-resolution **YOLOv8** object detection tuned for aerial imagery | Sub-pixel **bi-temporal change detection** (SSIM + CVA differencing) | Multispectral indices: **NDWI**, **NDVI**, **NBR** | **Optical + SAR** fusion when one sensor is not enough |
| Vessels, naval craft, aircraft, launch complexes | Urban encroachment, infrastructure growth, deforestation | Water boundaries, vegetation vigor, burn scars | Cloud-cover fallback, complementary evidence |
| Bounding boxes, geo-referenced | Interactive swipe / split compare | Calibrated area in **km²** | Cross-modal analysis |

</div>

**Also included**

- 🗣️ **Voice queries** and **Read Aloud** for answers
- 🖼️ **Describe scene**: detailed captioning of land use, terrain and infrastructure
- 🎛️ **Sensor composites**: RGB true colour, NIR false colour, NDWI water, NDVI vegetation, SAR radar, thermal
- 🗺️ **Map layers**: optical, SAR, fused, detections, masks, split compare, reticle and radar view
- 🔔 **Proactive monitoring alerts** for surges and anomalies in watched zones
- 🧾 **Audit log** and role-based access (Analyst · Decision maker · Admin)

---

## 🖥️ Interface Tour

<div align="center">

### Mission console
<img src="console-monitored.png" width="96%" alt="Monitored zones and agentic query console"/>

<sub>Monitored zones on the left, live map in the centre, the agentic query console with suggested analytical queries and session history on the right.</sub>

<br/><br/>

### Bring your own imagery
<img src="upload-ingest.png" width="96%" alt="Upload and validation of GeoTIFF imagery"/>

<sub>Drop in a GeoTIFF. A compatibility check verifies file format, radiometric bands, spatial resolution and georeferencing before any analysis runs.</sub>

<br/><br/>

| Query routing | Structured intelligence card |
|:---:|:---:|
| <img src="query-routing.png" width="360" alt="Query routing"/> | <img src="intelligence-card.png" width="360" alt="Structured intelligence card"/> |
| The agent acknowledges the query and routes it to the right tools | Answer, tools used, confidence, model trail and orchestrator telemetry |

<br/>

### Intelligence dossier
<img src="intelligence-report.png" width="96%" alt="Exportable intelligence dossier"/>

<sub>A full report: mission area, task type, primary sensor, confidence, grounded synthesis, stated uncertainties and quantitative spatial measurements. Export as PDF, GeoJSON or CSV.</sub>

</div>

---

## 🚀 A Mission, Start to Finish

**Example: Mumbai port vessel inventory**

| Step | What happens |
|---|---|
| 1. Pick a zone | Choose a monitored zone (or draw a custom AOI) and a sensor composite |
| 2. Ask | *"Describe this image in detail: identify geography, terrain features, and naval berths"* |
| 3. Route | The agent plans the run: intent planner → orchestrator → multimodal CV ensemble → VLM grounding |
| 4. Detect | YOLOv8 locates **11 vessels**; the VLM assesses land use and port infrastructure |
| 5. Explain | The card lists visible infrastructure **and what it could not determine** (for example cargo status hidden by sun-glint, or small craft below the resolution limit) |
| 6. Export | Download the dossier as PDF, or the detections as GeoJSON / CSV for GIS tools |

**Quick-launch missions built in:** Mumbai port vessel inventory · Brahmaputra river inundation · Western Ghats deforestation · Sriharikota spaceport · Chennai urban expansion.

---

## 🔍 Trust & Explainability

SatQuery AI is built so that an answer can be checked, not just believed.

| Feature | What it gives you |
|---|---|
| **Evidence-grounded answers** | Every claim is tied to detections, masks, metrics or source imagery |
| **Confidence score** | Shown on each intelligence card, with a *Grounded* flag |
| **Uncertainties & limitations** | The report states what could not be verified and why |
| **Tools used** | Each answer lists the models that produced it (for example YOLOv8, Gemini VLM) |
| **Model trail** | Step-by-step explainability view of how the answer was built |
| **Orchestrator telemetry** | Timed steps for parsing, planning, CV inference and grounding |
| **Human verification flag** | Low-confidence results are routed for review instead of auto-approved |
| **Audit log** | Actions are recorded for accountability |

> The confidence value is the system's own estimate. It is a guide for prioritising human review, not a calibrated statistical guarantee.

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Client["🖥️ Frontend"]
        U1[React + TypeScript + Tailwind]
        U2[Interactive map<br/>layers · swipe compare · reticle]
        U3[Query console · voice · read aloud]
    end
    subgraph Backend["⚙️ Backend"]
        B1[Python REST API]
        B2[Validation<br/>format · bands · GSD · CRS]
        B3[Agentic orchestrator<br/>tool-calling DAG]
    end
    subgraph Models["🧠 Specialist models"]
        M1[YOLOv8 detector]
        M2[Change engine<br/>SSIM + CVA]
        M3[Spectral indices<br/>NDWI · NDVI · NBR]
        M4[Optical–SAR fusion CNN]
        M5[Gemini VLM<br/>grounded synthesis]
    end
    subgraph Geo["🗺️ Geospatial layer"]
        G1[GeoTIFF / COG rasters]
        G2[GeoJSON outputs]
    end
    Client --> B1 --> B2 --> B3
    B3 --> M1 & M2 & M3 & M4
    M1 & M2 & M3 & M4 --> M5
    B3 <--> Geo
    M5 --> Client

    style B3 fill:#0a1c2e,stroke:#4dffb8,color:#fff
    style M5 fill:#0a1c2e,stroke:#4dffb8,color:#fff
```

**Design principle:** no single generic model does everything. A lightweight agent decides *which specialist to call*, and the VLM turns their evidence into a readable, grounded answer. Specialists can be upgraded or swapped independently.

---

## ⚖️ How It Compares

| | Desktop GIS | Code-based EO platforms | Imagery viewers | **SatQuery AI** |
|---|:---:|:---:|:---:|:---:|
| Ask in plain language | ✖ | ✖ | ✖ | ✔ |
| Agent picks the right model / tool | ✖ | ✖ | ✖ | ✔ |
| Detection + change + segmentation + fusion in one place | manual | scripted | limited | ✔ |
| Confidence and uncertainty on every answer | ✖ | ✖ | ✖ | ✔ |
| Explainable model trail | ✖ | ✖ | ✖ | ✔ |
| Exportable dossier (PDF / GeoJSON / CSV) | manual | scripted | limited | ✔ |
| Needs GIS / coding skill | high | high | low | **low** |

<sub>Comparison is by category of tool, not a benchmark of specific products.</sub>

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Tailwind CSS, Leaflet map |
| Backend | Python REST API with an agentic tool-calling orchestrator |
| Vision-language | Gemini VLM (grounded synthesis and agent reasoning) |
| Detection | YOLOv8, fine-tuned for aerial / remote-sensing imagery |
| Remote-sensing VQA | GeoChat / RemoteCLIP-family models |
| Change analysis | SSIM + CVA differencing |
| Spectral analysis | NDWI, NDVI, NBR indices |
| Fusion | Optical–SAR fusion CNN |
| Geospatial | GeoTIFF / COG rasters, GeoJSON output, WGS-84 / EPSG:4326 |
| Sensors shown | Cartosat-3, RISAT-2B, Sentinel-1/2 |

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- A Gemini API key

### Run locally

```bash
# 1. Clone
git clone https://github.com/<your-username>/SatQuery-AI.git
cd SatQuery-AI

# 2. Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add your Gemini API key
python app.py

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

> Folder names and commands above are typical defaults. Adjust them to match your repository layout. Never commit real API keys, only `.env.example`.

---

## ⚠️ Honest Limitations

- **Optical imagery is blocked by clouds.** SAR fallback helps, but fusion quality depends on alignment between sensors.
- **Small objects have resolution limits.** The report states this rather than guessing.
- **Confidence is model-reported**, not statistically calibrated.
- **Demo runs use benchmark and sample imagery.** Results on new sensors and regions still need independent validation.
- Depends on network access to a third-party vision-language API.

---

## 🗺️ Roadmap

- [x] Natural-language query console with agentic routing
- [x] Detection, bi-temporal comparison, spectral segmentation and Optical–SAR fusion
- [x] Imagery validation (format, bands, GSD, CRS)
- [x] Confidence, uncertainty, model trail and telemetry
- [x] PDF / GeoJSON / CSV export
- [ ] Live satellite feed adapters for continuous monitoring
- [ ] Independent accuracy benchmarking on held-out imagery
- [ ] Fine-tuned domain models for more object classes
- [ ] Multi-user workspaces and scheduled monitoring reports

---

<div align="center">

**If SatQuery AI made you want to ask your own satellite images a question, consider giving it a ⭐**


</div>
