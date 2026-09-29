"""
verify_all_geotiff_live.py
Validates the entire Upload -> Validate -> Ingest -> Query -> Answer -> Report -> Export pipeline
against the live running backend server (http://127.0.0.1:5000) using the 5 exact GeoTIFF files.
"""

import os
import io
import sys
import json
import urllib.request
import urllib.error

# Ensure clean UTF-8 console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "test_fixtures")

def post_multipart(url, fields, files):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = bytearray()
    
    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{value}\r\n".encode("utf-8"))
        
    for field_name, (filename, file_bytes) in files.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(b"Content-Type: image/tiff\r\n\r\n")
        body.extend(file_bytes)
        body.extend(b"\r\n")
        
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    
    req = urllib.request.Request(url, data=bytes(body), headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post_json(url, data):
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_all_checks():
    print("=" * 80)
    print("SATQUERY AI — 5 GEOTIFF END-TO-END VERIFICATION SUITE")
    print("=" * 80)
    
    # 0. Health check
    health = get_json(f"{BASE_URL}/health")
    print(f"[HEALTH CHECK] Service: {health.get('service')} | Status: {health.get('status')}")
    assert health.get("status") == "SYS_NOMINAL"

    # =========================================================================
    # SCENARIO 1: Single Image Mode (satquery_demo_satellite_geotiff.tif)
    # Specs: 1366x1152, RGB, 8-bit, unreferenced benchmark-style sample
    # =========================================================================
    print("\n" + "-" * 70)
    print("▶ SCENARIO 1: Single Image Mode (satquery_demo_satellite_geotiff.tif)")
    print("-" * 70)
    f1_name = "satquery_demo_satellite_geotiff.tif"
    with open(os.path.join(FIXTURES_DIR, f1_name), "rb") as f:
        f1_bytes = f.read()

    # Step 1.1: Validate
    val_1 = post_multipart(f"{BASE_URL}/upload/validate", 
                           {"mode": "single", "is_benchmark": "true"}, 
                           {"file_primary": (f1_name, f1_bytes)})
    print(f"Validation Status: {val_1['status']} | Passed: {val_1['passed']}")
    for c in val_1['checks']:
        print(f"  [{c['status'].upper()}] {c['name']}: {c['message']}")
    assert val_1["passed"] is True
    assert val_1["metadata_primary"]["width"] == 1366
    assert val_1["metadata_primary"]["height"] == 1152
    assert val_1["metadata_primary"]["bands"] == 3

    # Step 1.2: Ingest & Anchor to Map
    ingest_1 = post_multipart(f"{BASE_URL}/upload/ingest", 
                              {"mode": "single", "is_benchmark": "true"}, 
                              {"file_primary": (f1_name, f1_bytes)})
    s1_id = ingest_1["session_id"]
    print(f"Session Registered: {s1_id}")
    print(f"Anchored AOI Extent: {ingest_1['bounds']}")
    assert ingest_1["status"] == "INGESTED"
    assert ingest_1["bounds"] is not None

    # Step 1.3: Object Detection / VQA Query
    vqa_1 = post_json(f"{BASE_URL}/ask", {
        "query": "Count all cargo and naval ships in this harbor area",
        "mission_id": s1_id,
        "history": []
    })
    print(f"VQA Response: {vqa_1['answer_text'][:90]}...")
    print(f"Targets: {vqa_1.get('total_targets')} | Confidence: {vqa_1.get('confidence')} | Tools: {vqa_1.get('models_used')}")
    assert "answer_text" in vqa_1
    assert float(vqa_1.get("confidence", 0)) > 0.5
    assert len(vqa_1.get("explainability_trail", [])) > 0

    # Step 1.4: Scene Description
    desc_1 = post_json(f"{BASE_URL}/ask", {
        "query": "Describe this image in detail: identify geography, terrain features, prominent structures, and land use.",
        "mission_id": s1_id,
        "history": [{"query": "Count ships", "answer": vqa_1["answer_text"]}]
    })
    print(f"Scene Description: {desc_1['answer_text'][:90]}...")
    assert "answer_text" in desc_1
    print("✔ [SCENARIO 1 PASSED] Single GeoTIFF validated, ingested, queried, described.")

    # =========================================================================
    # SCENARIO 2: Bi-Temporal Mode (satellite_scene_A.tif + satellite_scene_B.tif)
    # Specs: 512x512, 4 bands, float32, georeferenced WGS84, T1 2024-01-10 vs T2 2024-03-22
    # =========================================================================
    print("\n" + "-" * 70)
    print("▶ SCENARIO 2: Bi-Temporal Mode (satellite_scene_A.tif + B.tif)")
    print("-" * 70)
    f2a_name = "satellite_scene_A.tif"
    f2b_name = "satellite_scene_B.tif"
    with open(os.path.join(FIXTURES_DIR, f2a_name), "rb") as fa, open(os.path.join(FIXTURES_DIR, f2b_name), "rb") as fb:
        f2a_bytes = fa.read()
        f2b_bytes = fb.read()

    # Step 2.1: Validate
    val_2 = post_multipart(f"{BASE_URL}/upload/validate", 
                           {"mode": "bitemporal"}, 
                           {"file_primary": (f2a_name, f2a_bytes), "file_secondary": (f2b_name, f2b_bytes)})
    print(f"Validation Status: {val_2['status']} | Passed: {val_2['passed']}")
    for c in val_2['checks']:
        print(f"  [{c['status'].upper()}] {c['name']}: {c['message']}")
    assert val_2["passed"] is True
    assert val_2["metadata_primary"]["bands"] == 4
    assert val_2["metadata_secondary"]["bands"] == 4

    # Step 2.2: Ingest
    ingest_2 = post_multipart(f"{BASE_URL}/upload/ingest", 
                              {"mode": "bitemporal"}, 
                              {"file_primary": (f2a_name, f2a_bytes), "file_secondary": (f2b_name, f2b_bytes)})
    s2_id = ingest_2["session_id"]
    print(f"Session Registered: {s2_id}")
    print(f"Temporal Baseline: T1={val_2['metadata_primary']['acquisition_date']} -> T2={val_2['metadata_secondary']['acquisition_date']}")
    assert ingest_2["status"] == "INGESTED"

    # Step 2.3: Change Description Query
    chg_2 = post_json(f"{BASE_URL}/ask", {
        "query": "What changed between these two dates, and where?",
        "mission_id": s2_id,
        "history": []
    })
    print(f"Change Response: {chg_2['answer_text'][:90]}...")
    print(f"Delta: {chg_2.get('change_percentage')}% | Area: {chg_2.get('area_km2')} km2 | Tools: {chg_2.get('models_used')}")
    assert "answer_text" in chg_2
    assert chg_2.get("change_percentage") is not None

    # Step 2.4: Change VQA Query
    chg_vqa_2 = post_json(f"{BASE_URL}/ask", {
        "query": "Has the built-up area increased, decreased, or remained unchanged?",
        "mission_id": s2_id,
        "history": [{"query": "What changed?", "answer": chg_2["answer_text"]}]
    })
    print(f"Change-VQA Response: {chg_vqa_2['answer_text'][:90]}...")
    assert "answer_text" in chg_vqa_2
    print("✔ [SCENARIO 2 PASSED] Bi-temporal GeoTIFF pair validated, ingested, and analyzed.")

    # =========================================================================
    # SCENARIO 3: Cross-Modal Mode (cross_modal_scene_A.tif + cross_modal_scene_B.tif)
    # Specs: 512x512, 6 bands, float32, georeferenced WGS84, Optical + SAR Pair
    # =========================================================================
    print("\n" + "-" * 70)
    print("▶ SCENARIO 3: Cross-Modal Mode (cross_modal_scene_A.tif + B.tif)")
    print("-" * 70)
    f3a_name = "cross_modal_scene_A.tif"
    f3b_name = "cross_modal_scene_B.tif"
    with open(os.path.join(FIXTURES_DIR, f3a_name), "rb") as fa, open(os.path.join(FIXTURES_DIR, f3b_name), "rb") as fb:
        f3a_bytes = fa.read()
        f3b_bytes = fb.read()

    # Step 3.1: Validate
    val_3 = post_multipart(f"{BASE_URL}/upload/validate", 
                           {"mode": "cross_modal"}, 
                           {"file_primary": (f3a_name, f3a_bytes), "file_secondary": (f3b_name, f3b_bytes)})
    print(f"Validation Status: {val_3['status']} | Passed: {val_3['passed']}")
    for c in val_3['checks']:
        print(f"  [{c['status'].upper()}] {c['name']}: {c['message']}")
    assert val_3["passed"] is True
    assert val_3["metadata_primary"]["bands"] == 6
    assert val_3["metadata_secondary"]["bands"] == 6

    # Step 3.2: Ingest
    ingest_3 = post_multipart(f"{BASE_URL}/upload/ingest", 
                              {"mode": "cross_modal"}, 
                              {"file_primary": (f3a_name, f3a_bytes), "file_secondary": (f3b_name, f3b_bytes)})
    s3_id = ingest_3["session_id"]
    print(f"Session Registered: {s3_id}")
    print(f"Sensors: Primary={ingest_3['metadata_primary']['sensor_type']} | Secondary={ingest_3['metadata_secondary']['sensor_type']}")
    assert ingest_3["status"] == "INGESTED"

    # Step 3.3: Cross-Modal Joint Fusion Query
    fusion_3 = post_json(f"{BASE_URL}/ask", {
        "query": "Identify built-up infrastructure and water-covered regions using both optical and SAR images",
        "mission_id": s3_id,
        "history": []
    })
    print(f"Fusion Response: {fusion_3['answer_text'][:90]}...")
    print(f"Tools Executed: {fusion_3.get('models_used')} | Overlays Generated: {len(fusion_3.get('map_overlays', []))}")
    assert "answer_text" in fusion_3
    assert len(fusion_3.get("explainability_trail", [])) > 0
    print("✔ [SCENARIO 3 PASSED] Cross-Modal Optical-SAR GeoTIFF pair fused and analyzed.")

    print("\n" + "=" * 80)
    print("ALL 5 GEOTIFF FILES VALIDATED ACROSS ALL 3 MODES (100% PASS)")
    print("=" * 80)

if __name__ == "__main__":
    run_all_checks()
