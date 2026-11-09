import unittest
from vision import service

class VisionTests(unittest.TestCase):
    def test_status_has_readiness(self):
        self.assertIn("ready", service.status())
    def test_missing_model_fails_explicitly(self):
        with self.assertRaises(service.ModelUnavailable): service.predict(b"not an image")
    def test_classes_are_educational(self):
        self.assertEqual(len(service.LABELS), 12)
        self.assertEqual(service.LABELS["backpack"]["es"], "mochila")
