"""
test_cv_endpoints.py
Stand-alone test script that runs Object Detection, Spectral Segmentation, and Bi-Temporal Change Detection
against sample images in /data/sample_imagery and prints strict PASS/FAIL verification.
"""

import os
import sys
import time
import json

# Add backend directory to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from app import create_app

def print_banner(text):
    print("=" * 75)
    print(f"  {text}")
    print("=" * 75)

def run_cv_tests():
    app = create_app()
    client = app.test_client()

    sample_dir = os.path.join(BASE_DIR, "data", "sample_imagery")
    print_banner("SATQUERY AI — CV TASK MODELS VERIFICATION SUITE")
    print(f"[*] Sample Imagery Directory: {sample_dir}\n")

    results = []

    # =========================================================================
    # TEST 1: Object Detection Endpoint (/api/detect)
    # =========================================================================
    t0 = time.time()
    mumbai_img = os.path.join(sample_dir, "mumbai_port_rgb.png")
    detect_payload = {
        "image_path": mumbai_img,
        "scenario": "mumbai-port",
        "bounds": {"north": 18.9650, "south": 18.9200, "east": 72.8600, "west": 72.8100},
        "conf_threshold": 0.35
    }

    res_detect = client.post('/api/detect', json=detect_payload)
    t_detect = (time.time() - t0) * 1000

    if res_detect.status_code == 200:
        d = res_detect.get_json()
        has_status = d.get('status') == 'SUCCESS'
        has_count = isinstance(d.get('count'), int) and d['count'] > 0
        has_bboxes = isinstance(d.get('bboxes'), list) and len(d['bboxes']) > 0
        first_box = d['bboxes'][0] if has_bboxes else {}
        has_props = all(k in first_box for k in ['class', 'confidence', 'bbox_pixel', 'bbox_geo', 'lat', 'lon'])

        if has_status and has_count and has_bboxes and has_props:
            results.append(("1. Object Detection (/api/detect)", "PASS", f"Count: {d['count']} targets, Top Class: '{first_box['class']}' ({first_box['confidence']})", t_detect))
        else:
            results.append(("1. Object Detection (/api/detect)", "FAIL", f"Missing contract fields: {d}", t_detect))
    else:
        results.append(("1. Object Detection (/api/detect)", "FAIL", f"HTTP {res_detect.status_code}: {res_detect.data.decode()}", t_detect))

    # =========================================================================
    # TEST 2: Spectral Segmentation Endpoint (/api/segment - Water / NDWI)
    # =========================================================================
    t0 = time.time()
    flood_img = os.path.join(sample_dir, "brahmaputra_t2_flood.png")
    seg_payload = {
        "image_path": flood_img,
        "feature_type": "water",
        "scenario": "brahmaputra-flood",
        "bounds": {"north": 26.7500, "south": 26.5500, "east": 93.5000, "west": 93.2000}
    }

    res_seg = client.post('/api/segment', json=seg_payload)
    t_seg = (time.time() - t0) * 1000

    if res_seg.status_code == 200:
        d = res_seg.get_json()
        has_status = d.get('status') == 'SUCCESS'
        has_area = isinstance(d.get('area_km2'), (int, float)) and d['area_km2'] > 0
        has_hectares = isinstance(d.get('area_hectares'), (int, float))
        has_geojson = isinstance(d.get('geojson'), dict) and d['geojson'].get('type') == 'FeatureCollection'
        has_mask_b64 = isinstance(d.get('mask_base64'), str)

        if has_status and has_area and has_hectares and has_geojson and has_mask_b64:
            results.append(("2. Spectral Segmentation (/api/segment - Water)", "PASS", f"Area: {d['area_km2']} km² ({d['area_hectares']} ha), Polygons: {d['polygon_count']}", t_seg))
        else:
            results.append(("2. Spectral Segmentation (/api/segment - Water)", "FAIL", f"Missing contract fields: {d}", t_seg))
    else:
        results.append(("2. Spectral Segmentation (/api/segment - Water)", "FAIL", f"HTTP {res_seg.status_code}: {res_seg.data.decode()}", t_seg))

    # =========================================================================
    # TEST 3: Spectral Segmentation Endpoint (/api/segment - Canopy / NDVI)
    # =========================================================================
    t0 = time.time()
    canopy_img = os.path.join(sample_dir, "western_ghats_t2_2026.png")
    seg_canopy_payload = {
        "image_path": canopy_img,
        "feature_type": "vegetation",
        "scenario": "western-ghats",
        "bounds": {"north": 8.7500, "south": 8.5500, "east": 77.3500, "west": 77.1500}
    }

    res_canopy = client.post('/api/segment', json=seg_canopy_payload)
    t_canopy = (time.time() - t0) * 1000

    if res_canopy.status_code == 200:
        d = res_canopy.get_json()
        if d.get('status') == 'SUCCESS' and 'area_km2' in d and 'geojson' in d:
            results.append(("3. Spectral Segmentation (/api/segment - Canopy)", "PASS", f"Feature: {d['feature_type']}, Area: {d['area_km2']} km²", t_canopy))
        else:
            results.append(("3. Spectral Segmentation (/api/segment - Canopy)", "FAIL", f"Invalid response: {d}", t_canopy))
    else:
        results.append(("3. Spectral Segmentation (/api/segment - Canopy)", "FAIL", f"HTTP {res_canopy.status_code}", t_canopy))

    # =========================================================================
    # TEST 4: Bi-Temporal Change Detection Endpoint (/api/change-detect)
    # =========================================================================
    t0 = time.time()
    t1_img = os.path.join(sample_dir, "chennai_urban_t1_2020.png")
    t2_img = os.path.join(sample_dir, "chennai_urban_t2_2026.png")
    chg_payload = {
        "image_t1": t1_img,
        "image_t2": t2_img,
        "scenario": "chennai-urban",
        "bounds": {"north": 12.9700, "south": 12.9000, "east": 80.2500, "west": 80.1800}
    }

    res_chg = client.post('/api/change-detect', json=chg_payload)
    t_chg = (time.time() - t0) * 1000

    if res_chg.status_code == 200:
        d = res_chg.get_json()
        has_status = d.get('status') == 'SUCCESS'
        has_pct = 'change_percentage' in d
        has_type = isinstance(d.get('change_type_guess'), str)
        has_polygons = isinstance(d.get('change_polygons'), list)
        has_aligned = d.get('aligned') is True
        has_mask = 'diff_mask_base64' in d

        if has_status and has_pct and has_type and has_polygons and has_aligned and has_mask:
            results.append(("4. Bi-Temporal Change Detection (/api/change-detect)", "PASS", f"Delta: {d['change_percentage']}%, Guess: '{d['change_type_guess']}', Aligned: True", t_chg))
        else:
            results.append(("4. Bi-Temporal Change Detection (/api/change-detect)", "FAIL", f"Missing contract fields: {d}", t_chg))
    else:
        results.append(("4. Bi-Temporal Change Detection (/api/change-detect)", "FAIL", f"HTTP {res_chg.status_code}: {res_chg.data.decode()}", t_chg))

    # =========================================================================
    # PRINT RESULTS SUMMARY
    # =========================================================================
    print(f"{'ENDPOINT / MODEL TEST':<48} | {'STATUS':<6} | {'LATENCY':<9} | {'DETAILS'}")
    print("-" * 110)

    all_passed = True
    for name, status, details, latency in results:
        status_str = f"[{status}]"
        if status != "PASS":
            all_passed = False
        print(f"{name:<48} | {status_str:<6} | {latency:>6.2f} ms | {details}")

    print("-" * 110)
    if all_passed:
        print("\n[SUCCESS] ALL CV TASK MODEL ENDPOINTS PASSED STRICT JSON CONTRACT VALIDATION (4/4)\n")
        return 0
    else:
        print("\n[FAILURE] ONE OR MORE CV MODEL TESTS FAILED\n")
        return 1

if __name__ == '__main__':
    exit_code = run_cv_tests()
    sys.exit(exit_code)
