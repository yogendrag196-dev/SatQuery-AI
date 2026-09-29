"""
test_scenario_2_and_3_queries.py
Executes all 3 Bi-Temporal queries and all 3 Cross-Modal queries against the live running server:

Scenario 2 — Bi-Temporal Mode:
  Files: satellite_scene_A.tif (T1) + satellite_scene_B.tif (T2)
  Q2.1: "What changed between these two dates, and where did the change occur?"
  Q2.2: "Has the built-up area increased, decreased, or remained unchanged?"
  Q2.3: "Analyze deforestation or burn scar extent in km² across this scene."

Scenario 3 — Cross-Modal Mode:
  Files: cross_modal_scene_A.tif (Optical) + cross_modal_scene_B.tif (SAR)
  Q3.1: "Use the optical and SAR images together to identify built-up and water-covered regions."
  Q3.2: "Compare features visible in the optical image versus the SAR image and highlight any discrepancies."
  Q3.3: "Extract water bodies using SAR backscatter and validate against the optical image."
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "test_fixtures")

def post_multipart(url, fields, files):
    boundary = "----WebKitFormBoundary8J3K1A4YWxkTrZu0gW"
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

def run_scenarios_2_and_3():
    print("=" * 80)
    print("SCENARIO 2 (BI-TEMPORAL) & SCENARIO 3 (CROSS-MODAL) — 6-QUERY VERIFICATION")
    print("=" * 80)

    # =========================================================================
    # SCENARIO 2: Bi-Temporal Mode
    # =========================================================================
    print("\n" + "=" * 70)
    print("▶ SCENARIO 2: BI-TEMPORAL MODE (satellite_scene_A.tif + B.tif)")
    print("=" * 70)

    f2a_path = os.path.join(FIXTURES_DIR, "satellite_scene_A.tif")
    f2b_path = os.path.join(FIXTURES_DIR, "satellite_scene_B.tif")
    with open(f2a_path, "rb") as fa, open(f2b_path, "rb") as fb:
        f2a_bytes = fa.read()
        f2b_bytes = fb.read()

    # Step 2.1: Validate
    val_2 = post_multipart(f"{BASE_URL}/upload/validate",
                           {"mode": "bitemporal"},
                           {"file_primary": ("satellite_scene_A.tif", f2a_bytes),
                            "file_secondary": ("satellite_scene_B.tif", f2b_bytes)})
    print(f"Validation Status: {val_2['status']} | Passed: {val_2['passed']}")
    for c in val_2['checks']:
        print(f"  [{c['status'].upper()}] {c['name']}: {c['message']}")
    assert val_2["passed"] is True

    # Step 2.2: Ingest & Anchor (Confirm no crash on undefined '0')
    ingest_2 = post_multipart(f"{BASE_URL}/upload/ingest",
                             {"mode": "bitemporal"},
                             {"file_primary": ("satellite_scene_A.tif", f2a_bytes),
                              "file_secondary": ("satellite_scene_B.tif", f2b_bytes)})
    s2_id = ingest_2["session_id"]
    print(f"Session Registered: {s2_id} (No crash on anchor)")
    print(f"Anchored Georeferenced Coordinates: {ingest_2['bounds']}")
    assert ingest_2["status"] == "INGESTED"
    assert ingest_2["bounds"] is not None

    s2_history = []

    # Q2.1
    q2_1 = "What changed between these two dates, and where did the change occur?"
    print(f"\n--- QUERY 2.1: \"{q2_1}\" ---")
    t0 = time.time()
    r2_1 = post_json(f"{BASE_URL}/ask", {"query": q2_1, "mission_id": s2_id, "history": s2_history})
    lat2_1 = (time.time() - t0) * 1000
    print(f"Response Time: {lat2_1:.1f}ms | Task Category: {r2_1.get('task_type')} | Delta: {r2_1.get('change_percentage')}% | Area: {r2_1.get('area_km2')} km²")
    print(f"Answer: {r2_1.get('answer_text')}")
    print("Model Trail Steps:")
    for step in r2_1.get('explainability_trail', []):
        print(f"  Step {step.get('step')}: {step.get('action')} -> {step.get('decision', '')[:70]}...")
    assert "answer_text" in r2_1
    assert r2_1.get('task_type') == "CHANGE_ANALYSIS"
    assert r2_1.get('change_percentage') is not None
    s2_history.append({"query": q2_1, "answer": r2_1["answer_text"]})

    # Q2.2
    q2_2 = "Has the built-up area increased, decreased, or remained unchanged?"
    print(f"\n--- QUERY 2.2: \"{q2_2}\" ---")
    t0 = time.time()
    r2_2 = post_json(f"{BASE_URL}/ask", {"query": q2_2, "mission_id": s2_id, "history": s2_history})
    lat2_2 = (time.time() - t0) * 1000
    print(f"Response Time: {lat2_2:.1f}ms | Task Category: {r2_2.get('task_type')} | Delta: {r2_2.get('change_percentage')}% | Area: {r2_2.get('area_km2')} km²")
    print(f"Answer: {r2_2.get('answer_text')}")
    assert "answer_text" in r2_2
    assert r2_2.get('task_type') == "CHANGE_ANALYSIS"
    s2_history.append({"query": q2_2, "answer": r2_2["answer_text"]})

    # Q2.3
    q2_3 = "Analyze deforestation or burn scar extent in km² across this scene."
    print(f"\n--- QUERY 2.3: \"{q2_3}\" ---")
    t0 = time.time()
    r2_3 = post_json(f"{BASE_URL}/ask", {"query": q2_3, "mission_id": s2_id, "history": s2_history})
    lat2_3 = (time.time() - t0) * 1000
    print(f"Response Time: {lat2_3:.1f}ms | Task Category: {r2_3.get('task_type')} | Area Extent: {r2_3.get('area_km2')} km²")
    print(f"Answer: {r2_3.get('answer_text')}")
    assert "answer_text" in r2_3
    assert r2_3.get('task_type') in ["CHANGE_ANALYSIS", "SEGMENTATION"]
    assert r2_3.get('area_km2') is not None
    s2_history.append({"query": q2_3, "answer": r2_3["answer_text"]})
    print("\n✔ [SCENARIO 2 VERIFIED] All 3 Bi-Temporal queries passed.")

    # =========================================================================
    # SCENARIO 3: Cross-Modal Mode
    # =========================================================================
    print("\n" + "=" * 70)
    print("▶ SCENARIO 3: CROSS-MODAL MODE (cross_modal_scene_A.tif + B.tif)")
    print("=" * 70)

    f3a_path = os.path.join(FIXTURES_DIR, "cross_modal_scene_A.tif")
    f3b_path = os.path.join(FIXTURES_DIR, "cross_modal_scene_B.tif")
    with open(f3a_path, "rb") as fa, open(f3b_path, "rb") as fb:
        f3a_bytes = fa.read()
        f3b_bytes = fb.read()

    # Step 3.1: Validate
    val_3 = post_multipart(f"{BASE_URL}/upload/validate",
                           {"mode": "cross_modal"},
                           {"file_primary": ("cross_modal_scene_A.tif", f3a_bytes),
                            "file_secondary": ("cross_modal_scene_B.tif", f3b_bytes)})
    print(f"Validation Status: {val_3['status']} | Passed: {val_3['passed']}")
    for c in val_3['checks']:
        print(f"  [{c['status'].upper()}] {c['name']}: {c['message']}")
    assert val_3["passed"] is True

    # Step 3.2: Ingest & Anchor
    ingest_3 = post_multipart(f"{BASE_URL}/upload/ingest",
                             {"mode": "cross_modal"},
                             {"file_primary": ("cross_modal_scene_A.tif", f3a_bytes),
                              "file_secondary": ("cross_modal_scene_B.tif", f3b_bytes)})
    s3_id = ingest_3["session_id"]
    print(f"Session Registered: {s3_id}")
    print(f"Sensors: Optical={ingest_3['metadata_primary']['sensor_type']} | SAR={ingest_3['metadata_secondary']['sensor_type']}")
    print(f"Anchored Coordinates: {ingest_3['bounds']}")
    assert ingest_3["status"] == "INGESTED"

    s3_history = []

    # Q3.1
    q3_1 = "Use the optical and SAR images together to identify built-up and water-covered regions."
    print(f"\n--- QUERY 3.1: \"{q3_1}\" ---")
    t0 = time.time()
    r3_1 = post_json(f"{BASE_URL}/ask", {"query": q3_1, "mission_id": s3_id, "history": s3_history})
    lat3_1 = (time.time() - t0) * 1000
    print(f"Response Time: {lat3_1:.1f}ms | Task Category: {r3_1.get('task_type')} | Models: {r3_1.get('models_used')}")
    print(f"Answer: {r3_1.get('answer_text')}")
    print("Model Trail Steps (Dual Modality Steps):")
    for step in r3_1.get('explainability_trail', []):
        print(f"  Step {step.get('step')}: {step.get('action')} -> {step.get('decision', '')[:70]}...")
    assert "answer_text" in r3_1
    assert r3_1.get('task_type') == "FUSION"
    trail_actions = [s.get('action', '') for s in r3_1.get('explainability_trail', [])]
    assert any("Optical" in a for a in trail_actions), "Model Trail must contain Optical Analysis step"
    assert any("SAR" in a for a in trail_actions), "Model Trail must contain SAR Analysis step"
    s3_history.append({"query": q3_1, "answer": r3_1["answer_text"]})

    # Q3.2
    q3_2 = "Compare features visible in the optical image versus the SAR image and highlight any discrepancies."
    print(f"\n--- QUERY 3.2: \"{q3_2}\" ---")
    t0 = time.time()
    r3_2 = post_json(f"{BASE_URL}/ask", {"query": q3_2, "mission_id": s3_id, "history": s3_history})
    lat3_2 = (time.time() - t0) * 1000
    print(f"Response Time: {lat3_2:.1f}ms | Task Category: {r3_2.get('task_type')} | Models: {r3_2.get('models_used')}")
    print(f"Answer: {r3_2.get('answer_text')}")
    assert "answer_text" in r3_2
    assert r3_2.get('task_type') == "FUSION"
    s3_history.append({"query": q3_2, "answer": r3_2["answer_text"]})

    # Q3.3
    q3_3 = "Extract water bodies using SAR backscatter and validate against the optical image."
    print(f"\n--- QUERY 3.3: \"{q3_3}\" ---")
    t0 = time.time()
    r3_3 = post_json(f"{BASE_URL}/ask", {"query": q3_3, "mission_id": s3_id, "history": s3_history})
    lat3_3 = (time.time() - t0) * 1000
    print(f"Response Time: {lat3_3:.1f}ms | Task Category: {r3_3.get('task_type')} | Models: {r3_3.get('models_used')}")
    print(f"Answer: {r3_3.get('answer_text')}")
    assert "answer_text" in r3_3
    assert r3_3.get('task_type') == "FUSION"
    s3_history.append({"query": q3_3, "answer": r3_3["answer_text"]})
    print("\n✔ [SCENARIO 3 VERIFIED] All 3 Cross-Modal queries passed.")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("ALL 6 PREDEFINED QUERIES (SCENARIOS 2 & 3) EXECUTED WITH 100% SUCCESS")
    print("=" * 80)

if __name__ == "__main__":
    run_scenarios_2_and_3()
