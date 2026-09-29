"""
test_ingestion_pipeline.py
End-to-End Test Suite for Satellite Image Ingestion & Validation Pipeline
"""

import io
import requests
from PIL import Image

def run_tests():
    base_url = "http://127.0.0.1:5000"
    print("=== STARTING INGESTION PIPELINE TEST SUITE ===")

    # Create synthetic test rasters
    img_opt = Image.new('RGB', (400, 400), color=(60, 100, 160))
    buf_opt = io.BytesIO()
    img_opt.save(buf_opt, format='PNG')
    opt_bytes = buf_opt.getvalue()

    img_sar = Image.new('L', (400, 400), color=120)
    buf_sar = io.BytesIO()
    img_sar.save(buf_sar, format='PNG')
    sar_bytes = buf_sar.getvalue()

    # -------------------------------------------------------------
    # TEST 1: Single PNG without Benchmark Flag -> Must FAIL
    # -------------------------------------------------------------
    files_1 = {'file_primary': ('test_sample.png', opt_bytes, 'image/png')}
    data_1 = {'mode': 'single', 'is_benchmark': 'false'}
    r1 = requests.post(f"{base_url}/upload/validate", files=files_1, data=data_1)
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    res1 = r1.json()
    assert res1['passed'] is False, "Expected validation to fail without benchmark flag"
    print("[PASS] Test 1: Non-GeoTIFF without benchmark flag rejected correctly.")

    # -------------------------------------------------------------
    # TEST 2: Single PNG WITH Benchmark Flag -> Must PASS
    # -------------------------------------------------------------
    files_2 = {'file_primary': ('test_sample.png', opt_bytes, 'image/png')}
    data_2 = {'mode': 'single', 'is_benchmark': 'true', 'sensor_type_p': 'Cartosat-3 Optical (0.28m)'}
    r2 = requests.post(f"{base_url}/upload/validate", files=files_2, data=data_2)
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
    res2 = r2.json()
    assert res2['passed'] is True, "Expected validation to pass with benchmark flag"
    assert res2['metadata_primary']['width'] == 400
    assert res2['metadata_primary']['bands'] == 3
    assert res2['metadata_primary']['preview_base64'] is not None
    print("[PASS] Test 2: Benchmark sample validated with extracted metadata & preview.")

    # -------------------------------------------------------------
    # TEST 3: Cross-Modal CRS Mismatch Check -> Must FAIL
    # -------------------------------------------------------------
    files_3 = {
        'file_primary': ('optical.png', opt_bytes, 'image/png'),
        'file_secondary': ('sar.png', sar_bytes, 'image/png')
    }
    data_3 = {
        'mode': 'cross_modal',
        'is_benchmark': 'true',
        'crs_p': 'EPSG:4326',
        'crs_s': 'EPSG:32643',
        'sensor_type_s': 'RISAT-2B SAR'
    }
    r3 = requests.post(f"{base_url}/upload/validate", files=files_3, data=data_3)
    res3 = r3.json()
    assert res3['passed'] is False, "Expected CRS mismatch to fail"
    failed_checks = [c['message'] for c in res3['checks'] if not c['passed']]
    assert any("CRS mismatch: EPSG:4326 vs EPSG:32643" in m for m in failed_checks), f"Expected CRS mismatch message, got {failed_checks}"
    print("[PASS] Test 3: Cross-Modal CRS mismatch surfaced with exact reason:", failed_checks[0])

    # -------------------------------------------------------------
    # TEST 4: Bi-Temporal Inverted Chronology Check -> Must FAIL
    # -------------------------------------------------------------
    files_4 = {
        'file_primary': ('t1_post.png', opt_bytes, 'image/png'),
        'file_secondary': ('t2_pre.png', opt_bytes, 'image/png')
    }
    data_4 = {
        'mode': 'bitemporal',
        'is_benchmark': 'true',
        'date_p': '2026-08-30',
        'date_s': '2022-04-12'
    }
    r4 = requests.post(f"{base_url}/upload/validate", files=files_4, data=data_4)
    res4 = r4.json()
    assert res4['passed'] is False, "Expected inverted dates to fail"
    failed_date_check = [c['message'] for c in res4['checks'] if not c['passed']][0]
    assert "Temporal sequence inverted" in failed_date_check
    print("[PASS] Test 4: Inverted Bi-Temporal chronology surfaced with exact reason:", failed_date_check)

    # -------------------------------------------------------------
    # TEST 5: Successful Ingestion & Orchestrator Query
    # -------------------------------------------------------------
    files_5 = {'file_primary': ('mumbai_custom.png', opt_bytes, 'image/png')}
    data_5 = {'mode': 'single', 'is_benchmark': 'true', 'sensor_type_p': 'Cartosat-3 Optical (0.28m)'}
    r5 = requests.post(f"{base_url}/upload/ingest", files=files_5, data=data_5)
    assert r5.status_code == 200, f"Ingestion failed: {r5.text}"
    sess = r5.json()
    sess_id = sess['session_id']
    assert sess_id.startswith("custom_session_")
    assert sess['bounds'] is not None
    assert sess['preview_primary'] is not None

    # Query the ingested session
    r_query = requests.post(f"{base_url}/ask", json={
        'mission_id': sess_id,
        'query': 'Count all vessels in this custom uploaded raster'
    })
    assert r_query.status_code == 200, f"Query failed: {r_query.text}"
    ans = r_query.json()
    assert ans['status'] == 'SUCCESS'
    assert 'tool_calls' in ans
    assert len(ans['tool_calls']) > 0
    assert ans['metrics']['total_targets'] is not None
    print(f"[PASS] Test 5: End-to-end ingestion & query succeeded for session {sess_id} (Targets: {ans['metrics']['total_targets']})")

    print("\n[SUCCESS] ALL INGESTION & VALIDATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
