"""
api.py
Flask REST API Routes for SatQuery AI
Strictly implements endpoints for Object Detection, Spectral Segmentation, and Bi-Temporal Change Detection.
"""

import os
import json
import time
from flask import Blueprint, request, jsonify
from config import Config
from services.orchestrator import OrchestratorAgent
from services.yolo_detector import YOLODetector
from services.spectral_segmenter import SpectralSegmenter
from services.change_detector import ChangeDetector
from services.fusion_engine import CrossModalFusionEngine
from services.vlm_engine import VLMEngine
from services.vlm_logger import vlm_logger

api_bp = Blueprint('api', __name__)
orchestrator = OrchestratorAgent()
yolo_detector = YOLODetector()
spectral_segmenter = SpectralSegmenter()
change_detector = ChangeDetector()
fusion_engine = CrossModalFusionEngine()
vlm_engine = VLMEngine()

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "SYS_NOMINAL",
        "service": "SatQuery AI REST API",
        "version": "2.4.0",
        "orchestrator": "Autonomous Multi-Tool Agent"
    })

@api_bp.route('/missions', methods=['GET'])
def get_missions():
    missions_path = os.path.join(Config.DATA_DIR, "missions.json")
    if os.path.exists(missions_path):
        with open(missions_path, "r") as f:
            data = json.load(f)
            return jsonify({"missions": data})
    return jsonify({"missions": {}})

@api_bp.route('/analyze', methods=['POST'])
@api_bp.route('/ask', methods=['POST'])
@api_bp.route('/vqa', methods=['POST'])
def analyze():
    """
    Agentic Orchestrator & VQA Endpoint (/ask, /analyze, /vqa)
    Accepts:
      - JSON: { question / query: str, mission_id / scenario?: str, bounds?: obj, time_range?: str, image_path?: str }
    Returns:
      {
        "status": "SUCCESS",
        "answer_text": str,
        "tool_calls": [ ... ],
        "map_overlays": [ ... ],
        "confidence_summary": { ... },
        "metrics": { ... },
        "explainability_trail": [ ... ]
      }
    """
    body = request.get_json(silent=True) or {}
    if not body and request.form:
        body = request.form.to_dict()

    mission_id = body.get('mission_id') or body.get('scenario')
    query = body.get('query') or body.get('question', '')
    bounds = body.get('bounds')
    time_range = body.get('time_range')
    image_input = body.get('image_path') or body.get('image_base64') or body.get('image')

    history = body.get('history') or []

    # Step 1 Hard Dependency Check for custom uploads
    if (mission_id in ["custom-upload", "custom_upload"] or (mission_id and str(mission_id).startswith("custom_session_"))) and mission_id not in INGESTION_SESSIONS and not image_input:
        # Check if there are any uploaded files in uploads dir to auto-recover session
        upload_files = [f for f in os.listdir(Config.UPLOAD_DIR) if not f.startswith('.')] if os.path.exists(Config.UPLOAD_DIR) else []
        if upload_files:
            latest_file = os.path.join(Config.UPLOAD_DIR, upload_files[-1])
            image_input = latest_file
        else:
            # Fall back to sample scene for custom upload
            sample_dir = os.path.join(Config.DATA_DIR, "sample_imagery")
            default_sample = os.path.join(sample_dir, "mumbai_port_rgb.png")
            if os.path.exists(default_sample):
                image_input = default_sample

    # Resolve custom uploaded session if active
    if mission_id and mission_id in INGESTION_SESSIONS:
        sess = INGESTION_SESSIONS[mission_id]
        if not image_input and sess.get('primary_path'):
            image_input = sess['primary_path']
        if not bounds and sess.get('validation_report', {}).get('metadata_primary', {}).get('bounds'):
            bounds = sess['validation_report']['metadata_primary']['bounds']

    # Backstage Scenario Mode (via query param, request body, or header)
    scenario_mode = (
        request.args.get('scenario_mode') in ['1', 'true', 'True'] or
        request.args.get('fixture') in ['1', 'true', 'True'] or
        body.get('scenario_mode') is True or
        request.headers.get('X-Scenario-Mode') in ['1', 'true', 'True']
    )

    if not query:
        return jsonify({"error": "Query or question string is required"}), 400

    try:
        result = orchestrator.analyze_mission_query(
            mission_id=mission_id,
            query=query,
            bounds=bounds,
            time_range=time_range,
            image_input=image_input,
            scenario_mode=scenario_mode,
            history=history
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/detect', methods=['POST'])
@api_bp.route('/ground', methods=['POST'])
def direct_detect():
    """
    Object Detection & Grounding Endpoint (/detect, /ground)
    Accepts:
      - JSON: { image_path?, image_base64?, scenario?, bounds?, conf_threshold? }
      - Form-data: file 'image', form fields 'bounds', 'scenario'
    Returns:
      {
        "status": "SUCCESS",
        "count": int,
        "bboxes": [ { "class": str, "label": str, "confidence": float, "bbox_pixel": [...], "bbox_geo": [...], "lat": float, "lon": float } ],
        "model_version": str
      }
    """
    image_input = None
    bounds = None
    scenario = "mumbai-port"
    conf_threshold = 0.35

    if request.is_json:
        body = request.get_json() or {}
        image_input = body.get('image_path') or body.get('image_base64') or body.get('image')
        bounds = body.get('bounds')
        scenario = body.get('scenario', 'mumbai-port')
        conf_threshold = float(body.get('conf_threshold', 0.35))
    else:
        if 'image' in request.files:
            file = request.files['image']
            image_input = file.read()
        scenario = request.form.get('scenario', 'mumbai-port')
        conf_str = request.form.get('bounds')
        if conf_str:
            try: bounds = json.loads(conf_str)
            except Exception: pass

    res = yolo_detector.detect_objects(image_input, bounds=bounds, conf_threshold=conf_threshold, scenario=scenario)
    return jsonify(res)

@api_bp.route('/segment', methods=['POST'])
def direct_segment():
    """
    Spectral & Morphological Segmentation Endpoint
    Accepts:
      - JSON: { image_path?, image_base64?, feature_type? ('water'|'vegetation'|'burn_scar'), bounds?, scenario? }
      - Form-data: file 'image', form fields 'feature_type', 'bounds'
    Returns:
      {
        "status": "SUCCESS",
        "feature_type": str,
        "index_type": str,
        "area_km2": float,
        "area_hectares": float,
        "polygon_count": int,
        "geojson": { "type": "FeatureCollection", "features": [...] },
        "mask_base64": str
      }
    """
    image_input = None
    feature_type = "water"
    bounds = None
    scenario = "brahmaputra-flood"

    if request.is_json:
        body = request.get_json() or {}
        image_input = body.get('image_path') or body.get('image_base64') or body.get('image')
        feature_type = body.get('feature_type') or body.get('index', 'water')
        bounds = body.get('bounds')
        scenario = body.get('scenario', 'brahmaputra-flood')
    else:
        if 'image' in request.files:
            file = request.files['image']
            image_input = file.read()
        feature_type = request.form.get('feature_type', 'water')
        scenario = request.form.get('scenario', 'brahmaputra-flood')
        conf_str = request.form.get('bounds')
        if conf_str:
            try: bounds = json.loads(conf_str)
            except Exception: pass

    res = spectral_segmenter.segment_image(image_input, feature_type=feature_type, bounds=bounds, scenario=scenario)
    return jsonify(res)

@api_bp.route('/change-detect', methods=['POST'])
@api_bp.route('/change', methods=['POST'])
def direct_change():
    """
    Bi-Temporal Change Detection Endpoint (/change-detect, /change)
    Accepts:
      - JSON: { image_t1?, image_t2?, scenario?, bounds? }
      - Form-data: files 'image_t1', 'image_t2', form fields 'scenario', 'bounds'
    Returns:
      {
        "status": "SUCCESS",
        "change_percentage": float,
        "change_type_guess": str,
        "area_km2": float,
        "aligned": bool,
        "change_polygons": [...],
        "geojson": { "type": "FeatureCollection", "features": [...] },
        "diff_mask_base64": str
      }
    """
    img_t1 = None
    img_t2 = None
    scenario = "chennai-urban"
    bounds = None

    if request.is_json:
        body = request.get_json() or {}
        img_t1 = body.get('image_t1')
        img_t2 = body.get('image_t2')
        scenario = body.get('scenario', 'chennai-urban')
        bounds = body.get('bounds')
    else:
        if 'image_t1' in request.files:
            img_t1 = request.files['image_t1'].read()
        if 'image_t2' in request.files:
            img_t2 = request.files['image_t2'].read()
        scenario = request.form.get('scenario', 'chennai-urban')
        conf_str = request.form.get('bounds')
        if conf_str:
            try: bounds = json.loads(conf_str)
            except Exception: pass

    res = change_detector.compute_bitemporal_change(image_t1=img_t1, image_t2=img_t2, scenario=scenario, bounds=bounds)
    return jsonify(res)

@api_bp.route('/fusion', methods=['POST'])
@api_bp.route('/api/fusion', methods=['POST'])
def direct_fusion():
    """
    Cross-Modal Optical–SAR Fusion Endpoint (Step 5)
    Accepts:
      - JSON: { optical_image?, sar_image?, scenario?, bounds?, query? }
      - Form-data: files 'optical', 'sar', form fields 'scenario', 'bounds', 'query'
    Returns:
      {
        "status": "SUCCESS",
        "optical_sensor": str,
        "sar_sensor": str,
        "optical_contribution_pct": float,
        "sar_contribution_pct": float,
        "total_targets": int,
        "area_km2": float,
        "summary_description": str,
        "geojson": { ... },
        "detections": [ ... ]
      }
    """
    opt_img = None
    sar_img = None
    scenario = "mumbai-port"
    bounds = None
    query = ""

    if request.is_json:
        body = request.get_json() or {}
        opt_img = body.get('optical_image') or body.get('image_optical') or body.get('primary_image')
        sar_img = body.get('sar_image') or body.get('image_sar') or body.get('secondary_image')
        scenario = body.get('scenario') or body.get('mission_id', 'mumbai-port')
        bounds = body.get('bounds')
        query = body.get('query') or body.get('question', '')
    else:
        if 'optical' in request.files:
            opt_img = request.files['optical'].read()
        elif 'file_primary' in request.files:
            opt_img = request.files['file_primary'].read()
        if 'sar' in request.files:
            sar_img = request.files['sar'].read()
        elif 'file_secondary' in request.files:
            sar_img = request.files['file_secondary'].read()

        scenario = request.form.get('scenario', 'mumbai-port')
        query = request.form.get('query', '')
        conf_str = request.form.get('bounds')
        if conf_str:
            try: bounds = json.loads(conf_str)
            except Exception: pass

    res = fusion_engine.fuse_optical_sar(
        optical_input=opt_img,
        sar_input=sar_img,
        bounds=bounds,
        scenario=scenario,
        query=query
    )
    return jsonify(res)

from services.imagery_validator import imagery_validator
import uuid

# In-memory registry of active custom ingestion sessions
INGESTION_SESSIONS = {}

@api_bp.route('/upload/validate', methods=['POST'])
@api_bp.route('/validate', methods=['POST'])
def validate_uploaded_imagery():
    """
    Validate uploaded imagery files (single, cross-modal, or bi-temporal pair).
    Returns granular pass/fail checks, extracted metadata, and preview data-URL.
    """
    mode = request.form.get('mode', 'single')
    is_benchmark = request.form.get('is_benchmark', 'false').lower() in ['true', '1', 'yes']
    sensor_type_p = request.form.get('sensor_type_p', '')
    sensor_type_s = request.form.get('sensor_type_s', '')
    date_p = request.form.get('date_p', '')
    date_s = request.form.get('date_s', '')
    crs_p = request.form.get('crs_p', '')
    crs_s = request.form.get('crs_s', '')

    bounds_p = None
    bounds_p_str = request.form.get('bounds_p')
    if bounds_p_str:
        try: bounds_p = json.loads(bounds_p_str)
        except Exception: pass

    bounds_s = None
    bounds_s_str = request.form.get('bounds_s')
    if bounds_s_str:
        try: bounds_s = json.loads(bounds_s_str)
        except Exception: pass

    if 'file_primary' not in request.files:
        return jsonify({
            "passed": False,
            "status": "FAIL",
            "summary_message": "Missing primary image file.",
            "checks": [{
                "name": "File Upload",
                "passed": False,
                "status": "fail",
                "message": "Primary imagery file was not provided in the upload request."
            }]
        }), 400

    f_p = request.files['file_primary']
    primary_data = {
        "filename": f_p.filename,
        "bytes": f_p.read()
    }

    secondary_data = None
    if 'file_secondary' in request.files:
        f_s = request.files['file_secondary']
        if f_s.filename != '':
            secondary_data = {
                "filename": f_s.filename,
                "bytes": f_s.read()
            }

    opts = {
        "is_benchmark": is_benchmark,
        "sensor_type_p": sensor_type_p,
        "sensor_type_s": sensor_type_s,
        "date_p": date_p,
        "date_s": date_s,
        "crs_p": crs_p,
        "crs_s": crs_s,
        "bounds_p": bounds_p,
        "bounds_s": bounds_s
    }

    report = imagery_validator.validate_ingestion(
        mode=mode,
        primary_file=primary_data,
        secondary_file=secondary_data,
        user_opts=opts
    )

    return jsonify(report)

@api_bp.route('/upload/ingest', methods=['POST'])
@api_bp.route('/api/upload/ingest', methods=['POST'])
@api_bp.route('/api/ingest_imagery_session', methods=['POST'])
def ingest_uploaded_imagery():
    """
    Ingests, saves, and registers validated imagery into an active session.
    Accepts both multipart/form-data and JSON pre-validated session registration.
    """
    session_id = f"custom_session_{uuid.uuid4().hex[:8]}"

    if request.is_json:
        body = request.get_json() or {}
        mode = body.get('mode', 'single')
        meta_p = body.get('metadata_primary') or {}
        meta_s = body.get('metadata_secondary')
        bounds = meta_p.get('bounds') or [[18.9200, 72.8100], [18.9650, 72.8600]]
        
        # Look for existing sample image or uploaded file
        primary_path = meta_p.get('filename')
        if primary_path and os.path.isabs(primary_path) and os.path.exists(primary_path):
            p_path = primary_path
        else:
            p_path = os.path.join(Config.UPLOAD_DIR, meta_p.get('filename', 'sample.tif'))
        
        session_rec = {
            "session_id": session_id,
            "mode": mode,
            "primary_path": p_path,
            "secondary_path": None,
            "validation_report": {
                "passed": True,
                "status": "PASS",
                "mode": mode,
                "metadata_primary": meta_p,
                "metadata_secondary": meta_s,
                "summary_message": "Imagery session registered and anchored to operational AOI."
            },
            "timestamp": time.time()
        }
        INGESTION_SESSIONS[session_id] = session_rec

        return jsonify({
            "status": "INGESTED",
            "session_id": session_id,
            "mode": mode,
            "primary_path": session_rec["primary_path"],
            "secondary_path": session_rec["secondary_path"],
            "metadata_primary": meta_p,
            "metadata_secondary": meta_s,
            "bounds": bounds,
            "preview_primary": meta_p.get("preview_base64"),
            "preview_secondary": meta_s.get("preview_base64") if meta_s else None,
            "summary": "Imagery session registered and anchored to operational AOI."
        })

    mode = request.form.get('mode', 'single')
    is_benchmark = request.form.get('is_benchmark', 'false').lower() in ['true', '1', 'yes']

    if 'file_primary' not in request.files:
        return jsonify({"error": "Primary file required"}), 400

    f_p = request.files['file_primary']
    primary_data = {"filename": f_p.filename, "bytes": f_p.read()}

    secondary_data = None
    if 'file_secondary' in request.files:
        f_s = request.files['file_secondary']
        if f_s.filename != '':
            secondary_data = {"filename": f_s.filename, "bytes": f_s.read()}

    opts = {
        "is_benchmark": is_benchmark,
        "sensor_type_p": request.form.get('sensor_type_p', ''),
        "sensor_type_s": request.form.get('sensor_type_s', ''),
        "date_p": request.form.get('date_p', ''),
        "date_s": request.form.get('date_s', ''),
        "crs_p": request.form.get('crs_p', ''),
        "crs_s": request.form.get('crs_s', '')
    }

    report = imagery_validator.validate_ingestion(
        mode=mode,
        primary_file=primary_data,
        secondary_file=secondary_data,
        user_opts=opts
    )

    if not report["passed"]:
        return jsonify({
            "error": "Ingestion rejected: validation checks failed.",
            "report": report
        }), 400

    session_rec = imagery_validator.save_ingested_session(
        session_id=session_id,
        primary_file=primary_data,
        secondary_file=secondary_data,
        validation_report=report
    )

    INGESTION_SESSIONS[session_id] = session_rec

    return jsonify({
        "status": "INGESTED",
        "session_id": session_id,
        "mode": mode,
        "primary_path": session_rec["primary_path"],
        "secondary_path": session_rec["secondary_path"],
        "metadata_primary": report["metadata_primary"],
        "metadata_secondary": report["metadata_secondary"],
        "bounds": report["metadata_primary"].get("bounds"),
        "preview_primary": report["metadata_primary"].get("preview_base64"),
        "preview_secondary": report["metadata_secondary"].get("preview_base64") if report["metadata_secondary"] else None,
        "summary": report["summary_message"]
    })

@api_bp.route('/upload/session/<session_id>', methods=['GET'])
def get_ingestion_session(session_id):
    if session_id in INGESTION_SESSIONS:
        return jsonify(INGESTION_SESSIONS[session_id])
    return jsonify({"error": "Session not found"}), 404

@api_bp.route('/upload', methods=['POST'])
def upload_imagery():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    save_path = os.path.join(Config.UPLOAD_DIR, file.filename)
    file.save(save_path)

    return jsonify({
        "status": "UPLOAD_SUCCESS",
        "filename": file.filename,
        "path": save_path
    })

@api_bp.route('/vlm/describe', methods=['POST'])
@api_bp.route('/caption', methods=['POST'])
@api_bp.route('/describe', methods=['POST'])
def vlm_describe():
    """
    Vision-Language Remote Sensing Scene Description Endpoint (/vlm/describe, /caption, /describe)
    Accepts:
      - JSON: { image_path?, image_base64?, crop_box?: [x, y, w, h], scenario?, bounds? }
      - Form-data: file 'image', form fields 'crop_box', 'scenario', 'bounds'
    Returns:
      {
        "status": "SUCCESS",
        "description": str,
        "land_use": list[str],
        "visible_infrastructure": list[str],
        "notable_features": list[str],
        "uncertainties": list[str],
        "confidence_score": float,
        "model": str,
        "latency_ms": float
      }
    """
    image_input = None
    crop_box = None
    scenario = "mumbai-port"
    bounds = None

    if request.is_json:
        body = request.get_json() or {}
        image_input = body.get('image_path') or body.get('image_base64') or body.get('image')
        crop_box = body.get('crop_box')
        scenario = body.get('scenario', 'mumbai-port')
        bounds = body.get('bounds')
    else:
        if 'image' in request.files:
            image_input = request.files['image'].read()
        scenario = request.form.get('scenario', 'mumbai-port')
        cb_str = request.form.get('crop_box')
        if cb_str:
            try: crop_box = json.loads(cb_str)
            except Exception: pass
        b_str = request.form.get('bounds')
        if b_str:
            try: bounds = json.loads(b_str)
            except Exception: pass

    res = vlm_engine.describe_scene(image_input=image_input, crop_box=crop_box, scenario=scenario, bounds=bounds)
    return jsonify(res)

@api_bp.route('/vlm/ask', methods=['POST'])
def vlm_ask():
    """
    Open-Ended Qualitative Scene Q&A Endpoint
    Accepts:
      - JSON: { question / query: str, image_path?, image_base64?, crop_box?: [x, y, w, h], scenario?, bounds? }
      - Form-data: file 'image', form fields 'question', 'crop_box', 'scenario'
    Returns:
      {
        "status": "SUCCESS",
        "question": str,
        "answer": str,
        "confidence_score": float,
        "model": str,
        "latency_ms": float
      }
    """
    question = ""
    image_input = None
    crop_box = None
    scenario = "mumbai-port"
    bounds = None

    if request.is_json:
        body = request.get_json() or {}
        question = body.get('question') or body.get('query', '')
        image_input = body.get('image_path') or body.get('image_base64') or body.get('image')
        crop_box = body.get('crop_box')
        scenario = body.get('scenario', 'mumbai-port')
        bounds = body.get('bounds')
    else:
        question = request.form.get('question') or request.form.get('query', '')
        if 'image' in request.files:
            image_input = request.files['image'].read()
        scenario = request.form.get('scenario', 'mumbai-port')
        cb_str = request.form.get('crop_box')
        if cb_str:
            try: crop_box = json.loads(cb_str)
            except Exception: pass
        b_str = request.form.get('bounds')
        if b_str:
            try: bounds = json.loads(b_str)
            except Exception: pass

    if not question:
        return jsonify({"error": "Question field is required"}), 400

    res = vlm_engine.ask_open_ended(question=question, image_input=image_input, crop_box=crop_box, scenario=scenario, bounds=bounds)
    return jsonify(res)

@api_bp.route('/vlm/logs', methods=['GET'])
def vlm_logs():
    """
    Retrieves recent VLM prompt/response audit logs (from MongoDB with JSON fallback).
    """
    limit = int(request.args.get('limit', 50))
    logs = vlm_logger.get_logs(limit=limit)
    return jsonify({
        "status": "SUCCESS",
        "total": len(logs),
        "logs": logs
    })
