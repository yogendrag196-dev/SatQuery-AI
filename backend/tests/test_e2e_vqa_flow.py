"""
test_e2e_vqa_flow.py
End-to-End HTTP User Journey Test for Single-Image VQA & Multi-Turn Session History
"""

import os
import sys
import json
import requests
import unittest

class TestE2EVQAFlow(unittest.TestCase):
    BASE_URL = "http://127.0.0.1:5000"

    def test_multi_turn_vqa_session_journey(self):
        print("\n=======================================================")
        print("  STARTING END-TO-END MULTI-TURN VQA USER JOURNEY")
        print("=======================================================")

        session_history = []
        mission_id = "mumbai-port"
        bounds = {"north": 18.9650, "south": 18.9200, "east": 72.8600, "west": 72.8100}

        # -------------------------------------------------------------
        # Turn 1: Initial Counting & Scene Identification Query
        # -------------------------------------------------------------
        query_1 = "Count all cargo and naval ships in this harbor area"
        print(f"\n[TURN 1] Dispatching Query: '{query_1}'")
        res1 = requests.post(f"{self.BASE_URL}/ask", json={
            "mission_id": mission_id,
            "query": query_1,
            "bounds": bounds,
            "history": session_history
        }, timeout=5.0)

        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertEqual(data1.get("status"), "SUCCESS")
        self.assertIn("answer_text", data1)
        self.assertGreater(data1.get("confidence", 0), 0.90)
        self.assertGreaterEqual(data1.get("total_targets", 0), 1)

        print(f"  -> Answer: {data1['answer_text'][:130]}...")
        print(f"  -> Calibrated Confidence: {data1['confidence']*100:.1f}% · GROUNDED")
        print(f"  -> Targets Found: {data1['total_targets']}")
        print(f"  -> Tools Used: {data1.get('models_used')}")

        session_history.append({
            "role": "user",
            "query": query_1,
            "answer": data1["answer_text"]
        })

        # -------------------------------------------------------------
        # Turn 2: Follow-up Query referencing earlier vessels
        # -------------------------------------------------------------
        query_2 = "Which ones are naval craft?"
        print(f"\n[TURN 2] Dispatching Follow-Up Query: '{query_2}'")
        res2 = requests.post(f"{self.BASE_URL}/ask", json={
            "mission_id": mission_id,
            "query": query_2,
            "bounds": bounds,
            "history": session_history
        }, timeout=5.0)

        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2.get("status"), "SUCCESS")
        self.assertIn("answer_text", data2)
        self.assertGreater(data2.get("confidence", 0), 0.90)

        ans_lower = data2["answer_text"].lower()
        self.assertTrue(any(w in ans_lower for w in ["naval", "frigate", "bravo", "dockyard"]))

        print(f"  -> Follow-up Answer: {data2['answer_text'][:150]}...")
        print(f"  -> Calibrated Confidence: {data2['confidence']*100:.1f}% · GROUNDED")
        print(f"  -> Tool Used: {data2.get('models_used')}")

        session_history.append({
            "role": "user",
            "query": query_2,
            "answer": data2["answer_text"]
        })

        # -------------------------------------------------------------
        # Turn 3: Second Follow-up Query regarding nearby infrastructure
        # -------------------------------------------------------------
        query_3 = "Are there any fuel storage tanks near them?"
        print(f"\n[TURN 3] Dispatching Follow-Up Query: '{query_3}'")
        res3 = requests.post(f"{self.BASE_URL}/ask", json={
            "mission_id": mission_id,
            "query": query_3,
            "bounds": bounds,
            "history": session_history
        }, timeout=5.0)

        self.assertEqual(res3.status_code, 200)
        data3 = res3.json()
        self.assertEqual(data3.get("status"), "SUCCESS")
        self.assertIn("answer_text", data3)
        self.assertGreater(data3.get("confidence", 0), 0.90)

        ans3_lower = data3["answer_text"].lower()
        self.assertTrue(any(w in ans3_lower for w in ["tank", "fuel", "storage", "petroleum", "bunkering"]))

        print(f"  -> Infrastructure Answer: {data3['answer_text'][:140]}...")
        print(f"  -> Calibrated Confidence: {data3['confidence']*100:.1f}% · GROUNDED")
        print(f"  -> Session History Depth: {len(session_history) + 1} queries logged")
        print("\n[SUCCESS] ALL MULTI-TURN VQA STEPS VERIFIED END-TO-END!")

if __name__ == "__main__":
    unittest.main()
