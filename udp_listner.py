# imported libraries
import socket
import struct
from collections import Counter

UDP_IP = "0.0.0.0" # listens on all available network interfaces
UDP_PORT = 20777 # UDP port used by F1 25 for telemetry data

# create a UDP socket and bind it to the specified IP address and port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# create a Counter object to keep track of the number of packets received for each packet ID and size
packet_counts = Counter()

print(f"Listening for F1 25 telemetry on UDP port {UDP_PORT}...")

# while loop to continuously listen for incoming UDP packets and process them
while True:
    data, addr = sock.recvfrom(4096)

    # check if the received data is at least 7 bytes long, which is the minimum size for a valid telemetry packet
    if len(data) < 7:
        continue

    # the code below is used to unpack the first 7 bytes of the received data to extract the packet format, game year, version, packet ID, and packet size.
    packet_format = struct.unpack_from("<H", data, 0)[0]
    game_year = data[2]
    major_version = data[3]
    minor_version = data[4]
    packet_version = data[5]
    packet_id = data[6]
    packet_size = len(data)

    packet_counts[(packet_id, packet_size)] += 1

    # the code below is used to clear the console and print the current telemetry packet information,
    # including the source address, packet format, game year, version, and a table of packet IDs, sizes, and counts.
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

    # this for loop is used to iterate through the sorted packet_counts dictionary and print the packet ID, size, and count for each unique packet received.
    for (pid, size), count in sorted(packet_counts.items()):
        print(f"{pid:9} | {size:4} | {count}")