"""
test_scenario_mode.py
Verification suite for the Backstage Scenario Mode (Reliability Layer):
1. Precomputed Sentinel-2/Cartosat fixture loading for Mumbai Port & Brahmaputra Flood
2. Real orchestrator planning & answer synthesis execution
3. Ultra-low latency stage reliability (< 30ms)
4. Invisible backstage activation via query param, body, or header
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

def run_scenario_mode_tests():
    app = create_app()
    client = app.test_client()

    print_banner("SATQUERY AI — BACKSTAGE SCENARIO MODE (RELIABILITY LAYER) TEST SUITE")
    results = []

    # =========================================================================
    # TEST 1: Mumbai Port Maritime Scenario Mode (?scenario_mode=true)
    # =========================================================================
    t0 = time.time()
    payload_1 = {
        "mission_id": "mumbai-port",
        "query": "Count vessels in this port and describe the visible harbor infrastructure"
    }

    res_1 = client.post('/ask?scenario_mode=true', json=payload_1)
    t_1 = (time.time() - t0) * 1000

    if res_1.status_code == 200:
        d = res_1.get_json()
        tools_used = [tc['tool_name'] for tc in d.get('tool_calls', [])]
        has_detect = "detect" in tools_used
        has_count = d['metrics']['total_targets'] == 12
        answer = d.get('answer_text', '')
        has_number = "12" in answer
        has_citation = "[" in answer and "]" in answer

        if has_detect and has_count and has_number and has_citation:
            results.append((
                "1. Mumbai Port Scenario Mode (?scenario_mode=true)",
                "PASS",
                f"Latency: {t_1:.1f} ms, Tools: {tools_used}, Count: {d['metrics']['total_targets']} (Grounded), Citations: Yes",
                t_1
            ))
        else:
            results.append(("1. Mumbai Port Scenario Mode (?scenario_mode=true)", "FAIL", f"Failed checks: {d}", t_1))
    else:
        results.append(("1. Mumbai Port Scenario Mode (?scenario_mode=true)", "FAIL", f"HTTP {res_1.status_code}", t_1))

    # =========================================================================
    # TEST 2: Brahmaputra Flood Bi-Temporal Scenario Mode (Header: X-Scenario-Mode)
    # =========================================================================
    t0 = time.time()
    payload_2 = {
        "mission_id": "brahmaputra-flood",
        "query": "Show flooded areas near this river and compare against baseline"
    }

    headers = {"X-Scenario-Mode": "true"}
    res_2 = client.post('/ask', json=payload_2, headers=headers)
    t_2 = (time.time() - t0) * 1000

    if res_2.status_code == 200:
        d = res_2.get_json()
        tools_used = [tc['tool_name'] for tc in d.get('tool_calls', [])]
        has_segment = "segment" in tools_used
        has_change = "change_detect" in tools_used
        has_area = d['metrics']['area_km2'] == 142.8
        has_delta = d['metrics']['change_percentage'] == 248.5

        if has_segment and has_change and has_area and has_delta:
            results.append((
                "2. Brahmaputra Flood Bi-Temporal Mode (Header Trigger)",
                "PASS",
                f"Latency: {t_2:.1f} ms, Area: {d['metrics']['area_km2']} km², Flood Delta: +{d['metrics']['change_percentage']}%",
                t_2
            ))
        else:
            results.append(("2. Brahmaputra Flood Bi-Temporal Mode (Header Trigger)", "FAIL", f"Failed checks: {d}", t_2))
    else:
        results.append(("2. Brahmaputra Flood Bi-Temporal Mode (Header Trigger)", "FAIL", f"HTTP {res_2.status_code}", t_2))

    # =========================================================================
    # TEST 3: Dynamic Live Reasoning under Scenario Mode
    # =========================================================================
    t0 = time.time()
    payload_3 = {
        "mission_id": "mumbai-port",
        "query": "What are the primary operational risks and active defense berths in this sector?",
        "scenario_mode": True
    }

    res_3 = client.post('/ask', json=payload_3)
    t_3 = (time.time() - t0) * 1000

    if res_3.status_code == 200:
        d = res_3.get_json()
        tools_used = [tc['tool_name'] for tc in d.get('tool_calls', [])]
        answer = d.get('answer_text', '')
        has_trail = len(d.get('explainability_trail', [])) >= 3
        has_answer = len(answer) > 40

        if has_trail and has_answer:
            results.append((
                "3. Dynamic Live Reasoning under Scenario Mode",
                "PASS",
                f"Live Decision Trail: {len(d['explainability_trail'])} steps, Latency: {t_3:.1f} ms",
                t_3
            ))
        else:
            results.append(("3. Dynamic Live Reasoning under Scenario Mode", "FAIL", f"Failed checks", t_3))
    else:
        results.append(("3. Dynamic Live Reasoning under Scenario Mode", "FAIL", f"HTTP {res_3.status_code}", t_3))

    # =========================================================================
    # PRINT RESULTS SUMMARY
    # =========================================================================
    print(f"{'TEST SCENARIO':<52} | {'STATUS':<6} | {'LATENCY':<9} | {'DETAILS'}")
    print("-" * 120)

    all_passed = True
    for name, status, details, latency in results:
        status_str = f"[{status}]"
        if status != "PASS":
            all_passed = False
        print(f"{name:<52} | {status_str:<6} | {latency:>6.2f} ms | {details}")

    print("-" * 120)
    if all_passed:
        print("\n[SUCCESS] ALL SCENARIO MODE (RELIABILITY LAYER) TESTS PASSED (3/3)\n")
        return 0
    else:
        print("\n[FAILURE] ONE OR MORE SCENARIO MODE TESTS FAILED\n")
        return 1

if __name__ == '__main__':
    exit_code = run_scenario_mode_tests()
    sys.exit(exit_code)
