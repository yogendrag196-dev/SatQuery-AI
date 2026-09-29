"""
test_vqa_inference.py
Automated Verification Suite for Single-Image VQA & Multi-Turn Session History
"""

import os
import sys
import unittest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.orchestrator import OrchestratorAgent
from services.vlm_engine import VLMEngine

class TestVQAInference(unittest.TestCase):
    def setUp(self):
        self.orchestrator = OrchestratorAgent()
        self.vlm = VLMEngine()

    def test_single_image_vqa_baseline(self):
        """
        Test 1: Single image VQA baseline query (vessel count in Mumbai Port).
        Verify natural-language answer and confidence score.
        """
        query = "Count all cargo and naval ships in this harbor area"
        res = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query=query,
            bounds={"north": 18.9650, "south": 18.9200, "east": 72.8600, "west": 72.8100}
        )

        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("answer_text", res)
        self.assertGreater(len(res["answer_text"]), 40)
        self.assertGreater(res["confidence"], 0.90)
        self.assertGreaterEqual(res["total_targets"], 1)
        self.assertTrue(len(res["tool_calls"]) > 0)
        print("\n[TEST 1 PASSED] Single-image VQA Baseline:")
        print(f"Confidence: {res['confidence']*100:.1f}% | Targets: {res['total_targets']}")
        print(f"Answer snippet: {res['answer_text'][:120]}...")

    def test_multi_turn_followup_vqa(self):
        """
        Test 2: Multi-turn follow-up question referencing earlier context.
        Query 1: 'Count all ships in this harbor'
        Query 2: 'Which ones are naval craft?'
        """
        # First turn
        history = [
            {
                "role": "user",
                "query": "Count all cargo and naval ships in this harbor area",
                "answer": "Identified and located 12 maritime vessels & naval craft across the active AOI."
            }
        ]

        followup_query = "Which ones are naval craft?"
        res = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query=followup_query,
            bounds={"north": 18.9650, "south": 18.9200, "east": 72.8600, "west": 72.8100},
            history=history
        )

        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("answer_text", res)
        self.assertGreater(len(res["answer_text"]), 40)
        self.assertGreater(res["confidence"], 0.90)

        # Check for naval grounding in answer
        ans_lower = res["answer_text"].lower()
        self.assertTrue(any(w in ans_lower for w in ["naval", "frigate", "bravo", "dockyard"]))
        print("\n[TEST 2 PASSED] Multi-Turn Follow-Up VQA:")
        print(f"Confidence: {res['confidence']*100:.1f}%")
        print(f"Follow-up Answer: {res['answer_text'][:160]}...")

    def test_vlm_direct_ask_with_history(self):
        """
        Test 3: Direct VLMEngine.ask_open_ended with history context.
        """
        history = [
            {
                "role": "user",
                "query": "Show flooded areas near this river vs pre-monsoon baseline",
                "answer": "Active flood inundation covers 142.8 km² across the Kaziranga buffer zone."
            }
        ]
        q = "Are there any roads cut or submerged by floodwaters?"
        res = self.vlm.ask_open_ended(
            question=q,
            scenario="brahmaputra-flood",
            history=history
        )

        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("answer", res)
        self.assertGreater(len(res["answer"]), 30)
        self.assertGreater(res["confidence_score"], 0.90)
        print("\n[TEST 3 PASSED] VLM Direct Ask with History:")
        print(f"Answer: {res['answer']}")

if __name__ == "__main__":
    unittest.main()
