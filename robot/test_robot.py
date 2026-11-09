import unittest
from robot import service

class RobotTests(unittest.TestCase):
    def test_correct_arm(self):
        self.assertEqual(service.react(True)['action'], 'arm_wave')
        self.assertTrue(service.react(True)['simulated'])
    def test_wrong_head(self):
        self.assertEqual(service.react(False)['action'], 'head_wave')
    def test_absent_stops(self):
        self.assertEqual(service.react(True, False)['action'], 'stop')
    def test_reject_implicit_truth(self):
        with self.assertRaises(ValueError): service.react('false')
    def test_sensor_context(self):
        self.assertFalse(service.sensor_context(False)['present'])
        self.assertEqual(service.sensor_context(True)['learning_mode'], 'guided')
    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError): service.Gateway(mode='serial')
    def test_gateway_default_simulated(self):
        self.assertTrue(service.Gateway().react(True)['simulated'])

if __name__ == '__main__': unittest.main()
