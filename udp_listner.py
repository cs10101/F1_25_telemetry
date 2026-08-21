import socket
import struct
from collections import Counter

UDP_IP = "0.0.0.0"
UDP_PORT = 20777

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

packet_counts = Counter()

print(f"Listening for F1 25 telemetry on UDP port {UDP_PORT}...")

while True:
    data, addr = sock.recvfrom(4096)

    if len(data) < 7:
        continue

    packet_format = struct.unpack_from("<H", data, 0)[0]
    game_year = data[2]
    major_version = data[3]
    minor_version = data[4]
    packet_version = data[5]
    packet_id = data[6]
    packet_size = len(data)

    packet_counts[(packet_id, packet_size)] += 1

    print("\033c", end="")
    print("F1 25 Telemetry Packets Detected")
    print("-" * 45)
    print(f"From: {addr}")
    print(f"Packet Format: {packet_format}")
    print(f"Game Year: {game_year}")
    print(f"Version: {major_version}.{minor_version}")
    print()
    print("Packet ID | Size | Count")
    print("-" * 45)

    for (pid, size), count in sorted(packet_counts.items()):
        print(f"{pid:9} | {size:4} | {count}")