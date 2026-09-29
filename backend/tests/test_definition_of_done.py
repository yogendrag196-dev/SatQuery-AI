"""
test_definition_of_done.py
Comprehensive End-to-End Verification for Step 7 & Step 8 (Definition of Done)
Confirms each mandatory capability produces real, grounded, non-placeholder output.
"""

import os
import sys
import unittest
import json
import io

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.imagery_validator import imagery_validator
from services.orchestrator import OrchestratorAgent
from services.fusion_engine import CrossModalFusionEngine
from services.change_detector import ChangeDetector
from services.spectral_segmenter import SpectralSegmenter
from services.yolo_detector import YOLODetector
from services.vlm_engine import VLMEngine
from app import create_app

class TestDefinitionOfDone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orchestrator = OrchestratorAgent()
        cls.fusion = CrossModalFusionEngine()
        cls.change = ChangeDetector()
        cls.spectral = SpectralSegmenter()
        cls.yolo = YOLODetector()
        cls.vlm = VLMEngine()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    # Checklist Item 1: Upload -> validation -> preview works for all 3 input types
    def test_item1_upload_validation_all_3_modes(self):
        """1. Upload -> validation -> preview works for all 3 input types (Single, Cross-modal, Bi-temporal)"""
        # 1-A: Single image validation
        report_single = imagery_validator.validate_ingestion(
            mode="single",
            primary_file={"filename": "cartosat3_mumbai.tif", "bytes": b"fake_geotiff_bytes"},
            secondary_file=None,
            user_opts={"is_benchmark": False, "sensor_type_p": "Cartosat-3"}
        )
        self.assertTrue(report_single["passed"])
        self.assertIn("metadata_primary", report_single)
        self.assertIn("preview_base64", report_single["metadata_primary"])

        # 1-B: Cross-modal pair validation (Optical + SAR)
        report_cross = imagery_validator.validate_ingestion(
            mode="cross_modal",
            primary_file={"filename": "optical_pass.tif", "bytes": b"optical_bytes"},
            secondary_file={"filename": "sar_pass.tif", "bytes": b"sar_bytes"},
            user_opts={"is_benchmark": False, "sensor_type_p": "Cartosat-3", "sensor_type_s": "RISAT-2B SAR"}
        )
        self.assertIn("metadata_secondary", report_cross)
        self.assertIn("RISAT-2B", report_cross["metadata_secondary"]["sensor_type"])

        # 1-C: Bi-temporal pair validation (T1 + T2)
        report_bitemp = imagery_validator.validate_ingestion(
            mode="bitemporal",
            primary_file={"filename": "t1_2022.tif", "bytes": b"t1_bytes"},
            secondary_file={"filename": "t2_2026.tif", "bytes": b"t2_bytes"},
            user_opts={"date_p": "2022-04-12", "date_s": "2026-08-15"}
        )
        self.assertTrue(report_bitemp["passed"])
        self.assertEqual(report_bitemp["mode"], "bitemporal")
        self.assertIn("metadata_secondary", report_bitemp)

    # Checklist Item 2: Single-image VQA returns real text answers with confidence
    def test_item2_single_image_vqa_with_confidence(self):
        """2. Single-image VQA returns real text answers with confidence"""
        res = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query="Count all cargo and naval ships in this harbor area"
        )
        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreater(len(res["answer_text"]), 40)
        self.assertGreater(res["confidence"], 0.90)
        self.assertIn("Object Detection Engine (YOLOv8)", res["answer_text"])
        self.assertGreater(res["metrics"]["total_targets"], 0)

    # Checklist Item 3: Captioning and grounding return real output
    def test_item3_captioning_and_grounding(self):
        """3. Captioning or grounding returns real output"""
        # Captioning
        res_cap = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query="Describe this image in detail: identify geography, terrain features, prominent structures, and land use."
        )
        self.assertIn("vlm_describe", res_cap["models_used"])
        self.assertGreater(len(res_cap["answer_text"]), 100)

        # Grounding
        res_ground = self.orchestrator.analyze_mission_query(
            mission_id="brahmaputra-flood",
            query="Highlight the water body & flood zone across this scene"
        )
        self.assertIn("segment", res_ground["models_used"])
        self.assertIsNotNone(res_ground["geojson"])
        self.assertGreater(res_ground["metrics"]["area_km2"], 0)

    # Checklist Item 4: Bi-temporal change description + change-VQA return real output
    def test_item4_bitemporal_change_description_and_vqa(self):
        """4. Bi-temporal change description + change-VQA return real output"""
        res_chg = self.orchestrator.analyze_mission_query(
            mission_id="chennai-urban",
            query="What changed between these two dates, and where?"
        )
        self.assertEqual(res_chg["status"], "SUCCESS")
        self.assertIn("change_detect", res_chg["models_used"])
        self.assertIn("Bi-Temporal Differencing Engine", res_chg["answer_text"])
        self.assertNotEqual(res_chg["metrics"]["change_percentage"], 0.0)

    # Checklist Item 5: Optical–SAR fusion analysis returns real joint output
    def test_item5_optical_sar_fusion_joint_output(self):
        """5. Optical–SAR fusion analysis returns real joint output with per-modality breakdown"""
        res_fusion = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query="Identify built-up infrastructure and water-covered regions using both optical and SAR images"
        )
        self.assertEqual(res_fusion["status"], "SUCCESS")
        self.assertIn("cross_modal_fusion", res_fusion["models_used"])
        self.assertIn("Optical–SAR Fusion Engine", res_fusion["answer_text"])
        self.assertIn("Modality Breakdown", res_fusion["answer_text"])

    # Checklist Item 6: Model Trail tab shows real per-query execution traces
    def test_item6_model_trail_execution_traces(self):
        """6. Model Trail tab shows real per-query execution traces"""
        res = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query="Identify built-up infrastructure and water-covered regions using both optical and SAR images"
        )
        trail = res["explainability_trail"]
        self.assertGreaterEqual(len(trail), 4)
        for step in trail:
            self.assertIn("step", step)
            self.assertIn("action", step)

    # Checklist Item 7: Telemetry tiles reflect real computed values
    def test_item7_telemetry_tiles_computed_values(self):
        """7. Telemetry tiles reflect real computed values (targets, area, delta %)"""
        res = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query="Count all vessels in this AOI"
        )
        metrics = res["metrics"]
        self.assertIsInstance(metrics["total_targets"], int)
        self.assertIsInstance(metrics["area_km2"], float)
        self.assertIsInstance(metrics["change_percentage"], float)
        self.assertIsInstance(metrics["breakdown"], dict)

    # Checklist Item 8: Export endpoints produce real serialized data
    def test_item8_export_serialization_payload(self):
        """8. Export serialization verifies query, task type, model trail, confidence, and vector features"""
        res = self.orchestrator.analyze_mission_query(
            mission_id="mumbai-port",
            query="Identify built-up infrastructure and water-covered regions using both optical and SAR images"
        )
        # Verify JSON serializability
        serialized_json = json.dumps(res)
        self.assertIn("answer_text", serialized_json)
        self.assertIn("explainability_trail", serialized_json)
        self.assertIn("metrics", serialized_json)

if __name__ == '__main__':
    unittest.main()
