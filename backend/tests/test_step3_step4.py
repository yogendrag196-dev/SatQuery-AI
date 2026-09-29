import unittest
import json
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from services.orchestrator import OrchestratorAgent

class TestStep3AndStep4Features(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.orchestrator = OrchestratorAgent()

    def test_step3_scene_description(self):
        """Test Step 3: Scene Captioning / Description returns qualitative assessment and confidence."""
        payload = {
            "mission_id": "mumbai-port",
            "query": "Describe this image in detail: identify geography, terrain features, prominent structures, and land use."
        }
        res = self.client.post("/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("summary", data)
        self.assertIn("confidence", data)
        self.assertGreater(data["confidence"], 0.8)
        self.assertTrue(any(t["tool_name"] in ["vlm_describe", "vlm_ask"] for t in data.get("tool_calls", [])))
        self.assertIn("models_used", data)
        print(f"[TEST PASS] Scene Description Confidence: {data['confidence']*100:.1f}%")

    def test_step3_text_guided_region_grounding_objects(self):
        """Test Step 3: Text-guided object grounding returns discrete bounding boxes and counts."""
        payload = {
            "mission_id": "mumbai-port",
            "query": "Highlight naval craft and vessels in sector Bravo"
        }
        res = self.client.post("/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("total_targets", data)
        self.assertGreater(data["total_targets"], 0)
        self.assertIn("detections", data)
        self.assertGreater(len(data["detections"]), 0)
        # Verify bounding box / coordinate fields
        det = data["detections"][0]
        self.assertIn("lat", det)
        self.assertIn("lon", det)
        self.assertIn("label", det)
        print(f"[TEST PASS] Grounded {len(data['detections'])} objects with labels: {[d['label'] for d in data['detections'][:2]]}")

    def test_step3_text_guided_region_grounding_masks(self):
        """Test Step 3: Text-guided region grounding returns spatial polygon masks (GeoJSON)."""
        payload = {
            "mission_id": "brahmaputra-flood",
            "query": "Highlight the water body & flood zone across this scene"
        }
        res = self.client.post("/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("geojson", data)
        self.assertIsNotNone(data["geojson"])
        self.assertIn("features", data["geojson"])
        self.assertGreater(len(data["geojson"]["features"]), 0)
        self.assertGreater(data.get("area_km2", 0), 0)
        print(f"[TEST PASS] Grounded surface polygon mask: {data.get('area_km2')} km²")

    def test_step4_bitemporal_change_description(self):
        """Test Step 4: Bi-temporal change description returns variance analysis and change percentage."""
        payload = {
            "mission_id": "chennai-urban",
            "query": "What changed between these two dates, and where?"
        }
        res = self.client.post("/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("summary", data)
        self.assertIn("change_percentage", data)
        self.assertNotEqual(data["change_percentage"], 0)
        self.assertTrue(any(t["tool_name"] == "change_detect" for t in data.get("tool_calls", [])))
        print(f"[TEST PASS] Bi-temporal Change Delta: {data['change_percentage']}%")

    def test_step4_bitemporal_change_vqa(self):
        """Test Step 4: Change-based VQA answering specific temporal shift questions."""
        payload = {
            "mission_id": "chennai-urban",
            "query": "Has the built-up area increased, decreased, or remained unchanged?"
        }
        res = self.client.post("/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        summary_lower = data.get("summary", "").lower()
        self.assertTrue("increased" in summary_lower or "expansion" in summary_lower or "growth" in summary_lower)
        self.assertIn("change_percentage", data)
        print(f"[TEST PASS] Change VQA Answered: {data['summary'][:120]}...")

    def test_step4_spatial_change_map_overlay(self):
        """Test Step 4: Change analysis generates GeoJSON spatial change polygons."""
        payload = {
            "mission_id": "western-ghats",
            "query": "Analyze deforestation and burn scar extent in km²"
        }
        res = self.client.post("/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("geojson", data)
        self.assertIsNotNone(data["geojson"])
        self.assertIn("features", data["geojson"])
        self.assertGreater(len(data["geojson"]["features"]), 0)
        self.assertGreater(data.get("area_km2", 0), 0)
        print(f"[TEST PASS] Spatial change map features: {len(data['geojson']['features'])}, Area: {data.get('area_km2')} km²")

if __name__ == "__main__":
    unittest.main()
