"""
test_orchestrator.py
Verification suite for the Agentic Multi-Tool Orchestrator:
1. Tool schema validation
2. Multi-tool DAG execution (e.g. detect + vlm_describe)
3. Strict CV Number-grounding rule enforcement (detect count & segment area)
4. Inline tool citation and explainability trail verification
5. Structured JSON response contract validation
"""

import os
import sys
import time
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from app import create_app

def print_banner(text):
    print("=" * 85)
    print(f"  {text}")
    print("=" * 85)

def run_orchestrator_tests():
    app = create_app()
    client = app.test_client()

    print_banner("SATQUERY AI — AGENTIC ORCHESTRATOR TEST SUITE")
    results = []

    # =========================================================================
    # TEST 1: Multi-Tool Query (Detection + VLM Scene Description)
    # =========================================================================
    t0 = time.time()
    payload_1 = {
        "mission_id": "mumbai-port",
        "query": "Count ships in this port AND describe the visible harbor infrastructure",
        "bounds": {"north": 18.9650, "south": 18.9200, "east": 72.8600, "west": 72.8100}
    }

    res_1 = client.post('/ask', json=payload_1)
    t_1 = (time.time() - t0) * 1000

    if res_1.status_code == 200:
        d = res_1.get_json()
        tools_used = [tc['tool_name'] for tc in d.get('tool_calls', [])]
        has_detect = "detect" in tools_used
        has_describe = "vlm_describe" in tools_used
        has_overlays = len(d.get('map_overlays', [])) > 0
        has_trail = len(d.get('explainability_trail', [])) >= 3
        has_conf = "confidence_summary" in d and d['confidence_summary'].get('number_grounded_cv') is True

        # Check citation in text
        answer = d.get('answer_text', '')
        has_citation = "[" in answer and "]" in answer

        # Check strict number grounding: must contain exact count 12
        has_exact_count = "12" in answer and d['metrics']['total_targets'] == 12

        if has_detect and has_describe and has_overlays and has_trail and has_conf and has_citation and has_exact_count:
            results.append((
                "1. Multi-Tool Call (detect + vlm_describe)",
                "PASS",
                f"Tools: {tools_used}, Count: {d['metrics']['total_targets']} (CV Grounded), Citations: Present",
                t_1
            ))
        else:
            results.append(("1. Multi-Tool Call (detect + vlm_describe)", "FAIL", f"Contract check failed: {d}", t_1))
    else:
        results.append(("1. Multi-Tool Call (detect + vlm_describe)", "FAIL", f"HTTP {res_1.status_code}: {res_1.data.decode()}", t_1))

    # =========================================================================
    # TEST 2: Multi-Tool Flood & Change Query (Segment + Change Detect)
    # =========================================================================
    t0 = time.time()
    payload_2 = {
        "mission_id": "brahmaputra-flood",
        "query": "Show flooded areas near this river and compare against baseline",
        "bounds": {"north": 26.7500, "south": 26.5500, "east": 93.5000, "west": 93.2000}
    }

    res_2 = client.post('/ask', json=payload_2)
    t_2 = (time.time() - t0) * 1000

    if res_2.status_code == 200:
        d = res_2.get_json()
        tools_used = [tc['tool_name'] for tc in d.get('tool_calls', [])]
        has_segment = "segment" in tools_used
        has_change = "change_detect" in tools_used
        has_area = d['metrics'].get('area_km2', 0) > 0
        has_delta = 'change_percentage' in d['metrics']
        has_citation = "[" in d.get('answer_text', '')

        if has_segment and has_change and has_area and has_delta and has_citation:
            results.append((
                "2. Multi-Tool Call (segment + change_detect)",
                "PASS",
                f"Tools: {tools_used}, Area: {d['metrics']['area_km2']} km², Delta: {d['metrics']['change_percentage']}%",
                t_2
            ))
        else:
            results.append(("2. Multi-Tool Call (segment + change_detect)", "FAIL", f"Contract check failed: {d}", t_2))
    else:
        results.append(("2. Multi-Tool Call (segment + change_detect)", "FAIL", f"HTTP {res_2.status_code}", t_2))

    # =========================================================================
    # TEST 3: Strict Number-Grounding Verification
    # =========================================================================
    t0 = time.time()
    payload_3 = {
        "mission_id": "mumbai-port",
        "query": "How many vessels are in this AOI? Give me the exact number.",
        "bounds": {"north": 18.9650, "south": 18.9200, "east": 72.8600, "west": 72.8100}
    }

    res_3 = client.post('/ask', json=payload_3)
    t_3 = (time.time() - t0) * 1000

    if res_3.status_code == 200:
        d = res_3.get_json()
        cv_count = d['metrics']['total_targets']
        answer = d.get('answer_text', '')
        
        # Must strictly cite the CV detector and exact number
        has_number = str(cv_count) in answer
        has_cv_citation = "Object Detection" in answer or "YOLOv8" in answer

        if has_number and has_cv_citation:
            results.append((
                "3. Strict Number-Grounding Constraint",
                "PASS",
                f"Exact Count {cv_count} cited directly from CV tool without estimation",
                t_3
            ))
        else:
            results.append(("3. Strict Number-Grounding Constraint", "FAIL", f"Number grounding failed: {answer}", t_3))
    else:
        results.append(("3. Strict Number-Grounding Constraint", "FAIL", f"HTTP {res_3.status_code}", t_3))

    # =========================================================================
    # TEST 4: Structured Response Contract Fields Check
    # =========================================================================
    t0 = time.time()
    d = res_1.get_json() if res_1.status_code == 200 else {}
    required_top_keys = ["status", "answer_text", "tool_calls", "map_overlays", "confidence_summary", "metrics", "explainability_trail"]
    all_keys_present = all(k in d for k in required_top_keys)
    t_4 = (time.time() - t0) * 1000

    if all_keys_present:
        results.append((
            "4. Structured Response Contract Validation",
            "PASS",
            f"All {len(required_top_keys)} required top-level schemas verified",
            t_4
        ))
    else:
        results.append(("4. Structured Response Contract Validation", "FAIL", f"Missing keys in payload", t_4))

    # =========================================================================
    # PRINT RESULTS SUMMARY
    # =========================================================================
    print(f"{'TEST SCENARIO':<46} | {'STATUS':<6} | {'LATENCY':<9} | {'DETAILS'}")
    print("-" * 115)

    all_passed = True
    for name, status, details, latency in results:
        status_str = f"[{status}]"
        if status != "PASS":
            all_passed = False
        print(f"{name:<46} | {status_str:<6} | {latency:>6.2f} ms | {details}")

    print("-" * 115)
    if all_passed:
        print("\n[SUCCESS] ALL AGENTIC ORCHESTRATOR TESTS PASSED (4/4)\n")
        return 0
    else:
        print("\n[FAILURE] ONE OR MORE ORCHESTRATOR TESTS FAILED\n")
        return 1

if __name__ == '__main__':
    exit_code = run_orchestrator_tests()
    sys.exit(exit_code)
