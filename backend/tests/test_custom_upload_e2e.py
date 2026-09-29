"""
test_custom_upload_e2e.py
End-to-End Test for Imagery Ingestion, Validation, and Custom Session Query Execution
"""

import unittest
import io
import os
from PIL import Image
import sys

# Ensure backend root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import create_app

class TestCustomUploadE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Create dummy GeoTIFF in memory
        img = Image.new("RGB", (512, 512), color=(40, 80, 120))
        buf = io.BytesIO()
        img.save(buf, format="TIFF")
        cls.img_bytes = buf.getvalue()

    def test_01_upload_and_validate(self):
        """Step 1: Validate uploaded GeoTIFF raster file"""
        response = self.client.post('/upload/validate', data={
            'mode': 'single',
            'is_benchmark': 'false',
            'file_primary': (io.BytesIO(self.img_bytes), 'satellite_scene_0.tif')
        }, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['passed'])
        self.assertIn('metadata_primary', data)
        self.assertEqual(data['metadata_primary']['format'], 'TIF')
        self.assertIsNotNone(data['metadata_primary']['preview_base64'])

    def test_02_ingest_and_anchor_session(self):
        """Step 2: Ingest and register session for map anchoring"""
        response = self.client.post('/upload/ingest', data={
            'mode': 'single',
            'is_benchmark': 'false',
            'file_primary': (io.BytesIO(self.img_bytes), 'satellite_scene_0.tif')
        }, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'INGESTED')
        self.assertTrue(data['session_id'].startswith('custom_session_'))
        self.assertIsNotNone(data['preview_primary'])
        self.assertIsNotNone(data['bounds'])

        # Store session_id for next step
        self.__class__.session_id = data['session_id']
        self.__class__.bounds = data['bounds']

    def test_03_query_custom_ingested_session(self):
        """Step 3: Execute query against ingested custom imagery session"""
        query_text = "Count all discrete objects and structures in this uploaded imagery"
        response = self.client.post('/ask', json={
            'mission_id': self.__class__.session_id,
            'query': query_text,
            'bounds': self.__class__.bounds
        })

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertTrue(len(result['answer_text']) > 30)
        self.assertGreater(result['confidence_summary']['overall_confidence'], 0.90)
        self.assertGreater(result['metrics']['total_targets'], 0)
        self.assertTrue(len(result['explainability_trail']) >= 4)
        self.assertTrue(len(result['tool_calls']) >= 1)

if __name__ == '__main__':
    unittest.main()
