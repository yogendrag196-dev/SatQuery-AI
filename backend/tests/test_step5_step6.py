"""
test_step5_step6.py
Comprehensive End-to-End Verification for:
- Step 5: Cross-Modal Optical–SAR Remote Sensing Fusion Engine
- Step 6: Agentic Task Classification, Model Registry Sequencing & Full Explainability Trail
"""

import os
import sys
import unittest
import json

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.fusion_engine import CrossModalFusionEngine
from services.orchestrator import OrchestratorAgent
from app import create_app

class TestStep5AndStep6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fusion = CrossModalFusionEngine()
        cls.orchestrator = OrchestratorAgent()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_fusion_engine_mumbai_port(self):
        """Test optical-SAR fusion on Mumbai Port scenario"""
        res = self.fusion.fuse_optical_sar(scenario="mumbai-port", query="Identify vessels and fuel tanks using both optical and SAR")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["optical_sensor"], "Cartosat-3 (0.28m High-Res Optical)")
        self.assertEqual(res["sar_sensor"], "RISAT-2BR1 (1.0m X-Band Spotlight SAR)")
        self.assertGreater(res["optical_contribution_pct"], 0)
        self.assertGreater(res["sar_contribution_pct"], 0)
        self.assertEqual(res["optical_contribution_pct"] + res["sar_contribution_pct"], 100.0)
        self.assertGreater(res["total_targets"], 0)
        self.assertIn("geojson", res)
        self.assertIn("features", res["geojson"])
        self.assertGreater(len(res["detections"]), 0)

    def test_fusion_engine_brahmaputra_flood(self):
        """Test optical-SAR fusion on Brahmaputra flood scenario"""
        res = self.fusion.fuse_optical_sar(scenario="brahmaputra-flood", query="Map flood extent penetrating cloud cover")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("EOS-04", res["sar_sensor"])
        self.assertGreater(res["sar_contribution_pct"], res["optical_contribution_pct"])
        self.assertGreater(res["area_km2"], 100.0)

    def test_task_classification_step6(self):
        """Test query intent classifier covering all 5 standard tasks"""
        # Task 1: Fusion
        self.assertEqual(
            self.orchestrator.classify_task_type("Identify built-up infrastructure and water using both optical and SAR images"),
            "FUSION"
        )
        self.assertEqual(
            self.orchestrator.classify_task_type("Perform cross-modal optical–sar joint extraction"),
            "FUSION"
        )
        # Task 2: Change Analysis
        self.assertEqual(
            self.orchestrator.classify_task_type("What changed between these two dates, and where?"),
            "CHANGE_ANALYSIS"
        )
        self.assertEqual(
            self.orchestrator.classify_task_type("Has the built-up area increased, decreased, or remained unchanged?"),
            "CHANGE_ANALYSIS"
        )
        # Task 3: Grounding
        self.assertEqual(
            self.orchestrator.classify_task_type("Highlight the water body and flood zone"),
            "GROUNDING"
        )
        self.assertEqual(
            self.orchestrator.classify_task_type("Outline naval craft in sector Bravo"),
            "GROUNDING"
        )
        # Task 4: Captioning / Scene Description
        self.assertEqual(
            self.orchestrator.classify_task_type("Describe this image in detail: identify terrain and structures"),
            "CAPTIONING"
        )
        # Task 5: VQA
        self.assertEqual(
            self.orchestrator.classify_task_type("How many cargo vessels are berthed at the north pier?"),
            "VQA"
        )

    def test_orchestrator_fusion_query_execution(self):
        """Test full orchestrator execution DAG for a fusion query"""
        res = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query="Identify built-up infrastructure and water-covered regions using both optical and SAR images"
        )
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("cross_modal_fusion", res["models_used"])
        
        # Check tool calls
        fusion_calls = [tc for tc in res["tool_calls"] if tc["tool_name"] == "cross_modal_fusion"]
        self.assertEqual(len(fusion_calls), 1)
        self.assertIn("optical_contribution_pct", fusion_calls[0]["raw_result"])
        self.assertIn("sar_contribution_pct", fusion_calls[0]["raw_result"])

        # Check explainability trail
        trail = res["explainability_trail"]
        self.assertGreaterEqual(len(trail), 3)
        step_actions = [step["action"] for step in trail]
        self.assertTrue(any("Sensor Selection" in a for a in step_actions))
        self.assertTrue(any("Task Classification: FUSION" in a for a in step_actions))
        self.assertTrue(any("cross_modal_fusion" in a for a in step_actions))

        # Check citations in answer text
        self.assertIn("Optical–SAR Fusion Engine", res["answer_text"])

    def test_fusion_api_endpoint(self):
        """Test POST /api/fusion REST endpoint"""
        response = self.client.post('/api/fusion', json={
            "scenario": "mumbai-port",
            "query": "Joint optical-SAR extraction"
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["fusion_mode"], "optical_sar_cross_modal")
        self.assertIn("optical_contribution_pct", data)
        self.assertIn("sar_contribution_pct", data)
        self.assertIn("geojson", data)

if __name__ == '__main__':
    unittest.main()
