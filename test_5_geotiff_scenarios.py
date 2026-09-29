"""
test_5_geotiff_scenarios.py
Runs through all 3 user scenarios with the 5 exact GeoTIFF files:
Scenario 1: Single Image Mode with satquery_demo_satellite_geotiff.tif
Scenario 2: Bi-Temporal Mode with satellite_scene_A.tif (T1) and satellite_scene_B.tif (T2)
Scenario 3: Cross-Modal Mode with cross_modal_scene_A.tif (Optical) and cross_modal_scene_B.tif (SAR)
"""

import os
import sys
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from backend.services.imagery_validator import ImageryValidator
from backend.services.orchestrator import OrchestratorAgent
from backend.app import create_app

app = create_app()

class TestRealGeoTIFFScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.validator = ImageryValidator()
        cls.orchestrator = OrchestratorAgent()
        cls.fixtures_dir = os.path.join(os.path.dirname(__file__), "test_fixtures")

    def test_scenario_1_single_image(self):
        print("\n=== RUNNING SCENARIO 1: Single Image Mode (satquery_demo_satellite_geotiff.tif) ===")
        file_path = os.path.join(self.fixtures_dir, "satquery_demo_satellite_geotiff.tif")
        self.assertTrue(os.path.exists(file_path), "File 1 exists")
        
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Step 1: Validate ingestion
        val_result = self.validator.validate_ingestion(
            mode="single",
            primary_file={"filename": "satquery_demo_satellite_geotiff.tif", "bytes": file_bytes},
            user_opts={"is_benchmark": True}
        )
        print(f"Validation status: {val_result['status']} (Passed: {val_result['passed']})")
        for c in val_result['checks']:
            print(f"  [{c['status'].upper()}] {c['name']}: {c['message']}")
        self.assertTrue(val_result["passed"], "Scenario 1 validation should pass")
        self.assertEqual(val_result["metadata_primary"]["width"], 1366)
        self.assertEqual(val_result["metadata_primary"]["height"], 1152)

        # Step 2: Session Ingestion API
        ingest_res = self.client.post("/api/ingest_imagery_session", json={
            "mode": "single",
            "metadata_primary": val_result["metadata_primary"],
            "metadata_secondary": None
        })
        self.assertEqual(ingest_res.status_code, 200)
        ingest_data = ingest_res.get_json()
        session_id = ingest_data["session_id"]
        print(f"Session Created: {session_id} | AOI Bounds: {ingest_data['bounds']}")
        self.assertIsNotNone(ingest_data["bounds"], "Bounds must not be null")

        # Step 3: Dispatch VQA Query
        vqa_res = self.client.post("/ask", json={
            "query": "Count all cargo and naval ships in this harbor area",
            "mission_id": session_id,
            "session_id": session_id,
            "history": []
        })
        self.assertEqual(vqa_res.status_code, 200)
        vqa_data = vqa_res.get_json()
        print(f"VQA Answer: {vqa_data.get('answer_text')[:100]}...")
        print(f"Confidence: {vqa_data.get('confidence')} | Targets: {vqa_data.get('total_targets')}")
        self.assertIn("answer_text", vqa_data)
        conf = float(vqa_data.get("confidence", 0))
        self.assertTrue(conf > 0.5 or conf > 50, f"Confidence {conf} should be > 0.5")
        self.assertGreater(len(vqa_data.get("explainability_trail", [])), 0)

        # Step 4: Describe Scene Query
        desc_res = self.client.post("/ask", json={
            "query": "Describe this image in detail: identify geography, terrain features, prominent structures, and land use.",
            "mission_id": session_id,
            "session_id": session_id,
            "history": [{"query": "Count ships", "answer": vqa_data.get("answer_text")}]
        })
        self.assertEqual(desc_res.status_code, 200)
        desc_data = desc_res.get_json()
        print(f"Describe Answer: {desc_data.get('answer_text')[:100]}...")
        self.assertIn("answer_text", desc_data)
        print("[SCENARIO 1 COMPLETE] All checkpoints passed.\n")

    def test_scenario_2_bitemporal(self):
        print("\n=== RUNNING SCENARIO 2: Bi-Temporal Mode (satellite_scene_A.tif + B.tif) ===")
        f1_path = os.path.join(self.fixtures_dir, "satellite_scene_A.tif")
        f2_path = os.path.join(self.fixtures_dir, "satellite_scene_B.tif")
        
        with open(f1_path, "rb") as f1, open(f2_path, "rb") as f2:
            f1_bytes = f1.read()
            f2_bytes = f2.read()

        # Step 1: Validate Bi-temporal
        val_result = self.validator.validate_ingestion(
            mode="bitemporal",
            primary_file={"filename": "satellite_scene_A.tif", "bytes": f1_bytes},
            secondary_file={"filename": "satellite_scene_B.tif", "bytes": f2_bytes},
            user_opts={}
        )
        print(f"Validation status: {val_result['status']} (Passed: {val_result['passed']})")
        for c in val_result['checks']:
            print(f"  [{c['status'].upper()}] {c['name']}: {c['message']}")
        self.assertTrue(val_result["passed"], "Scenario 2 validation should pass")

        # Step 2: Session Ingestion API
        ingest_res = self.client.post("/api/ingest_imagery_session", json={
            "mode": "bitemporal",
            "metadata_primary": val_result["metadata_primary"],
            "metadata_secondary": val_result["metadata_secondary"]
        })
        self.assertEqual(ingest_res.status_code, 200)
        ingest_data = ingest_res.get_json()
        session_id = ingest_data["session_id"]
        print(f"Session Created: {session_id} | Temporal delta: T1={ingest_data.get('metadata_primary', {}).get('acquisition_date')} vs T2={ingest_data.get('metadata_secondary', {}).get('acquisition_date')}")

        # Step 3: Dispatch Change Query
        change_res = self.client.post("/ask", json={
            "query": "What changed between these two dates, and where?",
            "mission_id": session_id,
            "session_id": session_id,
            "history": []
        })
        self.assertEqual(change_res.status_code, 200)
        change_data = change_res.get_json()
        print(f"Change Answer: {change_data.get('answer_text')[:100]}...")
        print(f"Delta Pct: {change_data.get('change_percentage')}% | Area: {change_data.get('area_km2')} km2")
        self.assertIn("answer_text", change_data)
        self.assertIsNotNone(change_data.get("change_percentage"))
        self.assertGreater(len(change_data.get("explainability_trail", [])), 0)

        # Step 4: Dispatch Change-VQA
        vqa_change_res = self.client.post("/ask", json={
            "query": "Has the built-up area increased, decreased, or remained unchanged?",
            "mission_id": session_id,
            "session_id": session_id,
            "history": []
        })
        self.assertEqual(vqa_change_res.status_code, 200)
        vqa_change_data = vqa_change_res.get_json()
        print(f"Change VQA Answer: {vqa_change_data.get('answer_text')[:100]}...")
        self.assertIn("answer_text", vqa_change_data)
        print("[SCENARIO 2 COMPLETE] All checkpoints passed.\n")

    def test_scenario_3_cross_modal(self):
        print("\n=== RUNNING SCENARIO 3: Cross-Modal Mode (cross_modal_scene_A.tif + B.tif) ===")
        f1_path = os.path.join(self.fixtures_dir, "cross_modal_scene_A.tif")
        f2_path = os.path.join(self.fixtures_dir, "cross_modal_scene_B.tif")
        
        with open(f1_path, "rb") as f1, open(f2_path, "rb") as f2:
            f1_bytes = f1.read()
            f2_bytes = f2.read()

        # Step 1: Validate Cross-Modal
        val_result = self.validator.validate_ingestion(
            mode="cross_modal",
            primary_file={"filename": "cross_modal_scene_A.tif", "bytes": f1_bytes},
            secondary_file={"filename": "cross_modal_scene_B.tif", "bytes": f2_bytes},
            user_opts={"sensor_type_p": "Optical Multispectral (6-Band)", "sensor_type_s": "Polarimetric SAR Radar (6-Band)"}
        )
        print(f"Validation status: {val_result['status']} (Passed: {val_result['passed']})")
        for c in val_result['checks']:
            print(f"  [{c['status'].upper()}] {c['name']}: {c['message']}")
        self.assertTrue(val_result["passed"], "Scenario 3 validation should pass")

        # Step 2: Session Ingestion API
        ingest_res = self.client.post("/api/ingest_imagery_session", json={
            "mode": "cross_modal",
            "metadata_primary": val_result["metadata_primary"],
            "metadata_secondary": val_result["metadata_secondary"]
        })
        self.assertEqual(ingest_res.status_code, 200)
        ingest_data = ingest_res.get_json()
        session_id = ingest_data["session_id"]
        print(f"Session Created: {session_id} | Primary: {ingest_data.get('metadata_primary', {}).get('sensor_type')} | Secondary: {ingest_data.get('metadata_secondary', {}).get('sensor_type')}")

        # Step 3: Dispatch Cross-Modal Joint Extraction Query
        fusion_res = self.client.post("/ask", json={
            "query": "Identify built-up infrastructure and water-covered regions using both optical and SAR images",
            "mission_id": session_id,
            "session_id": session_id,
            "history": []
        })
        self.assertEqual(fusion_res.status_code, 200)
        fusion_data = fusion_res.get_json()
        print(f"Fusion Answer: {fusion_data.get('answer_text')[:100]}...")
        print(f"Task Type: {fusion_data.get('task_type')} | Tools: {fusion_data.get('models_used')}")
        self.assertIn("answer_text", fusion_data)
        self.assertGreater(len(fusion_data.get("explainability_trail", [])), 0)
        print("[SCENARIO 3 COMPLETE] All checkpoints passed.\n")

if __name__ == "__main__":
    unittest.main()
