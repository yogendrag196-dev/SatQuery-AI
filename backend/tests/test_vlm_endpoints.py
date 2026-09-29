"""
test_vlm_endpoints.py
Verification suite for VLM Reasoning endpoints:
1. /vlm/describe (specialized remote-sensing land use, infrastructure, uncertainties)
2. /vlm/ask (open-ended scene qualitative questions)
3. /vlm/logs (MongoDB / JSON audit logging verification)
"""

import os
import sys
import time
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from app import create_app

def print_banner(text):
    print("=" * 80)
    print(f"  {text}")
    print("=" * 80)

def run_vlm_tests():
    app = create_app()
    client = app.test_client()

    sample_dir = os.path.join(BASE_DIR, "data", "sample_imagery")
    print_banner("SATQUERY AI — VISION-LANGUAGE REASONING (VLM) TEST SUITE")
    print(f"[*] Sample Imagery Directory: {sample_dir}\n")

    results = []

    # =========================================================================
    # TEST 1: /vlm/describe - Full Scene Description & Uncertainty Reporting
    # =========================================================================
    t0 = time.time()
    mumbai_img = os.path.join(sample_dir, "mumbai_port_rgb.png")
    describe_payload = {
        "image_path": mumbai_img,
        "scenario": "mumbai-port",
        "crop_box": [100, 50, 400, 300],  # Test AOI crop
        "bounds": {"north": 18.9650, "south": 18.9200, "east": 72.8600, "west": 72.8100}
    }

    res_desc = client.post('/vlm/describe', json=describe_payload)
    t_desc = (time.time() - t0) * 1000

    if res_desc.status_code == 200:
        d = res_desc.get_json()
        has_status = d.get('status') == 'SUCCESS'
        has_desc = isinstance(d.get('description'), str) and len(d['description']) > 20
        has_land_use = isinstance(d.get('land_use'), list) and len(d['land_use']) > 0
        has_infra = isinstance(d.get('visible_infrastructure'), list) and len(d['visible_infrastructure']) > 0
        has_uncertainty = isinstance(d.get('uncertainties'), list) and len(d['uncertainties']) > 0
        has_conf = isinstance(d.get('confidence_score'), (int, float))

        if has_status and has_desc and has_land_use and has_infra and has_uncertainty and has_conf:
            results.append(("1. VLM Describe (/vlm/describe)", "PASS", f"Land Use: {len(d['land_use'])}, Infra: {len(d['visible_infrastructure'])}, Uncertainties: {len(d['uncertainties'])}, Conf: {d['confidence_score']}", t_desc))
        else:
            results.append(("1. VLM Describe (/vlm/describe)", "FAIL", f"Missing contract fields: {d}", t_desc))
    else:
        results.append(("1. VLM Describe (/vlm/describe)", "FAIL", f"HTTP {res_desc.status_code}: {res_desc.data.decode()}", t_desc))

    # =========================================================================
    # TEST 2: /vlm/ask - Open-Ended Qualitative Question
    # =========================================================================
    t0 = time.time()
    ask_payload = {
        "image_path": mumbai_img,
        "question": "What is the primary commercial and defense role of this waterfront?",
        "scenario": "mumbai-port"
    }

    res_ask = client.post('/vlm/ask', json=ask_payload)
    t_ask = (time.time() - t0) * 1000

    if res_ask.status_code == 200:
        d = res_ask.get_json()
        has_status = d.get('status') == 'SUCCESS'
        has_answer = isinstance(d.get('answer'), str) and len(d['answer']) > 20
        has_q = d.get('question') == ask_payload["question"]
        has_conf = isinstance(d.get('confidence_score'), (int, float))

        if has_status and has_answer and has_q and has_conf:
            results.append(("2. VLM Open-Ended Q&A (/vlm/ask)", "PASS", f"Model: {d.get('model')}, Answer Len: {len(d['answer'])} chars, Conf: {d['confidence_score']}", t_ask))
        else:
            results.append(("2. VLM Open-Ended Q&A (/vlm/ask)", "FAIL", f"Missing contract fields: {d}", t_ask))
    else:
        results.append(("2. VLM Open-Ended Q&A (/vlm/ask)", "FAIL", f"HTTP {res_ask.status_code}: {res_ask.data.decode()}", t_ask))

    # =========================================================================
    # TEST 3: /vlm/logs - MongoDB / JSON Audit Trail Retrieval
    # =========================================================================
    t0 = time.time()
    res_logs = client.get('/vlm/logs?limit=10')
    t_logs = (time.time() - t0) * 1000

    if res_logs.status_code == 200:
        d = res_logs.get_json()
        has_status = d.get('status') == 'SUCCESS'
        has_logs = isinstance(d.get('logs'), list) and len(d['logs']) > 0

        if has_status and has_logs:
            latest_log = d['logs'][0]
            results.append(("3. VLM Audit Trail (/vlm/logs)", "PASS", f"Total Records: {d.get('total')}, Latest Endpoint: '{latest_log.get('endpoint')}' ({latest_log.get('model')})", t_logs))
        else:
            results.append(("3. VLM Audit Trail (/vlm/logs)", "FAIL", f"No logs found in audit trail: {d}", t_logs))
    else:
        results.append(("3. VLM Audit Trail (/vlm/logs)", "FAIL", f"HTTP {res_logs.status_code}", t_logs))

    # =========================================================================
    # PRINT RESULTS SUMMARY
    # =========================================================================
    print(f"{'ENDPOINT / FEATURE TEST':<40} | {'STATUS':<6} | {'LATENCY':<9} | {'DETAILS'}")
    print("-" * 110)

    all_passed = True
    for name, status, details, latency in results:
        status_str = f"[{status}]"
        if status != "PASS":
            all_passed = False
        print(f"{name:<40} | {status_str:<6} | {latency:>6.2f} ms | {details}")

    print("-" * 110)
    if all_passed:
        print("\n[SUCCESS] ALL VLM REASONING ENDPOINTS & AUDIT LOGGING PASSED (3/3)\n")
        return 0
    else:
        print("\n[FAILURE] ONE OR MORE VLM TESTS FAILED\n")
        return 1

if __name__ == '__main__':
    exit_code = run_vlm_tests()
    sys.exit(exit_code)
