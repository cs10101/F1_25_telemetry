import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "live_telemetry.py"
SPEC = importlib.util.spec_from_file_location("live_telemetry", MODULE_PATH)
live_telemetry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(live_telemetry)


class ParsePacketHeaderTests(unittest.TestCase):
    def _build_packet(self, header_size, packet_id_offset, player_car_index_offset, packet_id, player_car_index):
        data = bytearray(header_size + 256)
        data[packet_id_offset] = packet_id
        data[player_car_index_offset] = player_car_index
        return bytes(data)

    def test_detects_24_byte_header_layout(self):
        data = self._build_packet(24, 5, 22, 2, 0)
        self.assertEqual(live_telemetry.parse_packet_header(data), (24, 2, 0))

    def test_detects_29_byte_header_layout(self):
        data = self._build_packet(29, 6, 27, 6, 1)
        self.assertEqual(live_telemetry.parse_packet_header(data), (29, 6, 1))

    def test_detects_car_status_packet(self):
        data = self._build_packet(29, 6, 27, 7, 0)
        self.assertEqual(live_telemetry.parse_packet_header(data), (29, 7, 0))


class FormatSteeringTests(unittest.TestCase):
    def test_format_steering_zero(self):
        self.assertEqual(live_telemetry.format_steering(0.0), "0")
        self.assertEqual(live_telemetry.format_steering(0.0005), "0")

    def test_format_steering_left(self):
        self.assertEqual(live_telemetry.format_steering(-1.0), "-1")
        self.assertEqual(live_telemetry.format_steering(-0.5), "-0.5")

    def test_format_steering_right(self):
        self.assertEqual(live_telemetry.format_steering(1.0), "1")
        self.assertEqual(live_telemetry.format_steering(0.75), "0.75")


if __name__ == "__main__":
    unittest.main()
