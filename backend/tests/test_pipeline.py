"""
test_pipeline.py
Automated test suite for SatQuery AI CV Models, Orchestrator Agent, and REST API.
"""

import unittest
import json
import os
import sys

# Ensure backend directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from services.yolo_detector import YOLODetector
from services.spectral_segmenter import SpectralSegmenter
from services.change_detector import ChangeDetector
from services.orchestrator import OrchestratorAgent

class TestSatQueryAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.yolo = YOLODetector()
        cls.spectral = SpectralSegmenter()
        cls.change = ChangeDetector()
        cls.orchestrator = OrchestratorAgent()

    def test_01_health_endpoint(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get('status'), 'SYS_NOMINAL')

    def test_02_missions_catalog(self):
        res = self.client.get('/api/missions')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        missions = data.get('missions', {})
        self.assertIn('mumbai-port', missions)
        self.assertIn('brahmaputra-flood', missions)
        self.assertIn('western-ghats', missions)

    def test_03_yolo_detection(self):
        res = self.yolo.detect_objects(None, scenario="mumbai-port")
        self.assertIn('detections', res)
        self.assertGreater(len(res['detections']), 0)
        self.assertIn('lat', res['detections'][0])
        self.assertIn('lon', res['detections'][0])

    def test_04_spectral_flood_segmentation(self):
        res = self.spectral.segment_flood()
        self.assertIn('geojson', res)
        self.assertIn('area_km2', res)
        self.assertGreater(res['area_km2'], 100)

    def test_05_spectral_canopy_segmentation(self):
        res = self.spectral.segment_canopy_loss()
        self.assertIn('geojson', res)
        self.assertIn('area_km2', res)

    def test_06_change_detection(self):
        res = self.change.compute_bitemporal_change(scenario="chennai-urban")
        self.assertIn('change_percentage', res)
        self.assertGreater(res['change_percentage'], 0)

    def test_07_orchestrator_maritime_query(self):
        res = self.orchestrator.analyze_mission_query(
            "mumbai-port",
            "Count all cargo and naval ships in this harbor area"
        )
        self.assertIn('summary', res)
        self.assertIn('detections', res)
        self.assertIn('total_targets', res)
        self.assertGreaterEqual(res['total_targets'], 10)

    def test_08_orchestrator_flood_query(self):
        res = self.orchestrator.analyze_mission_query(
            "brahmaputra-flood",
            "Show flooded areas near this river vs pre-monsoon baseline"
        )
        self.assertIn('summary', res)
        self.assertIn('geojson', res)
        self.assertIn('area_km2', res)

    def test_09_api_analyze_endpoint(self):
        payload = {
            "mission_id": "mumbai-port",
            "query": "Identify large container vessels"
        }
        res = self.client.post('/api/analyze', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('summary', data)
        self.assertIn('detections', data)

if __name__ == '__main__':
    unittest.main()
