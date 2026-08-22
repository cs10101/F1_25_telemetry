import socket
import struct

from telemetry.state import TelemetryState
from telemetry.recorder import SessionRecorder

UDP_IP = "0.0.0.0"
UDP_PORT = 20777

LAP_DATA_PACKET_ID = 2
CAR_TELEMETRY_PACKET_ID = 6
CAR_STATUS_PACKET_ID = 7

LAP_DATA_SIZE = 57
CAR_TELEMETRY_DATA_SIZE = 60
CAR_STATUS_DATA_SIZE = 55

MOTION_PACKET_ID = 0
MOTION_DATA_SIZE = 60

# Some telemetry versions use a 24-byte header while others use a 29-byte one.
# We accept both layouts so the parser remains compatible with common F1 packet formats.
HEADER_CANDIDATES = (
    (24, 5, 22),
    (29, 6, 27),
)

latest_lap = {}
latest_car = {}
latest_status = {}
state = TelemetryState()
recorder = SessionRecorder()


def format_ms(ms):
    if ms == 0:
        return "--:--.---"
    minutes = ms // 60000
    seconds = (ms % 60000) / 1000
    return f"{minutes}:{seconds:06.3f}"


def format_gap(minutes, ms):
    total_ms = (minutes * 60000) + ms
    if total_ms == 0:
        return "--"
    return f"+{total_ms / 1000:.3f}s"


def format_steering(steering):
    if abs(steering) < 1e-3:
        return "0"
    formatted = f"{steering:.3f}".rstrip("0").rstrip(".")
    return formatted

def tyre_name(compound):
    return {
        16: "Soft",
        17: "Medium",
        18: "Hard",
        7: "Intermediate",
        8: "Wet",
    }.get(compound, f"Unknown ({compound})")


def print_dashboard():
    print("\033c", end="")
    print("LIVE F1 25 PIT WALL")
    print("-" * 40)

    print("LAP DATA:")
    print(f"Position:     P{latest_lap.get('position', '--')}")
    print(f"Lap:          {latest_lap.get('lap', '--')}")
    print(f"Sector:       S{latest_lap.get('sector', '--')}")
    print(f"Current Time: {latest_lap.get('current_time', '--')}")
    print(f"Last Lap:     {latest_lap.get('last_lap', '--')}")
    print(f"Gap Ahead:    {latest_lap.get('gap_ahead', '--')}")

    print("Behind:")
    for item in latest_lap.get("behind", []):
        print(f"  {item}")

    print(f"Gap Leader:   {latest_lap.get('gap_leader', '--')}")
    print("-" * 40)
    print()

    print("CAR DATA:")
    print(f"Speed:        {latest_car.get('speed', '--')} km/h")
    print(f"Gear:         {latest_car.get('gear', '--')}")
    print(f"RPM:          {latest_car.get('rpm', '--')}")
    print(f"Throttle:     {latest_car.get('throttle', '--')}")
    print(f"Steering:     {latest_car.get('steering', '--')}")
    print(f"Brake:        {latest_car.get('brake', '--')}")
    print(f"DRS:          {latest_car.get('drs', '--')}")
    print("-" * 40)
    print()

    print("CAR STATUS:")
    print(f"Tyre:         {latest_status.get('tyre', '--')}")
    print(f"Tyre Age:     {latest_status.get('tyre_age', '--')}")

def parse_packet_header(data):

    for header_size, packet_id_offset, player_car_index_offset in HEADER_CANDIDATES:

        if len(data) < header_size:
            continue

        packet_id = data[packet_id_offset]

        if packet_id not in {MOTION_PACKET_ID, LAP_DATA_PACKET_ID, CAR_TELEMETRY_PACKET_ID, CAR_STATUS_PACKET_ID}:
            continue

        player_car_index = data[player_car_index_offset]

        #required_size = header_size + (player_car_index * LAP_DATA_SIZE) + LAP_DATA_SIZE

        if packet_id == MOTION_PACKET_ID:
            required_size = (
                header_size
                + (player_car_index * MOTION_DATA_SIZE)
                + MOTION_DATA_SIZE
            )
        elif packet_id == LAP_DATA_PACKET_ID:
            required_size = header_size + (player_car_index * LAP_DATA_SIZE) + LAP_DATA_SIZE
        elif packet_id == CAR_TELEMETRY_PACKET_ID:
            required_size = header_size + (player_car_index * CAR_TELEMETRY_DATA_SIZE) + CAR_TELEMETRY_DATA_SIZE
        elif packet_id == CAR_STATUS_PACKET_ID:
            required_size = header_size + (player_car_index * CAR_STATUS_DATA_SIZE) + CAR_STATUS_DATA_SIZE

        if len(data) >= required_size:
            return header_size, packet_id, player_car_index

    return None


def update_dashboard_from_packet(data):
    header = parse_packet_header(data)
    if header is None:
        return False

    header_size, packet_id, player_car_index = header

    if packet_id == MOTION_PACKET_ID:
        offset = header_size + (player_car_index * MOTION_DATA_SIZE)

        world_x = struct.unpack_from("<f", data, offset)[0]
        world_y = struct.unpack_from("<f", data, offset + 4)[0]
        world_z = struct.unpack_from("<f", data, offset + 8)[0]

        state.world_x = world_x
        state.world_y = world_y
        state.world_z = world_z

        # Record one snapshot per Motion packet
        recorder.record(state)

        return True

    if packet_id == LAP_DATA_PACKET_ID:
        offset = header_size + (player_car_index * LAP_DATA_SIZE)

        last_lap_ms = struct.unpack_from("<I", data, offset)[0]
        current_lap_ms = struct.unpack_from("<I", data, offset + 4)[0]

        gap_ahead_ms = struct.unpack_from("<H", data, offset + 14)[0]
        gap_ahead_min = data[offset + 16]

        gap_leader_ms = struct.unpack_from("<H", data, offset + 17)[0]
        gap_leader_min = data[offset + 19]

        position = data[offset + 32]
        lap = data[offset + 33]
        sector = data[offset + 36]

        latest_lap.update({
            "position": position,
            "lap": lap,
            "sector": sector + 1,
            "current_time": format_ms(current_lap_ms),
            "last_lap": format_ms(last_lap_ms),
            "gap_ahead": format_gap(gap_ahead_min, gap_ahead_ms),
            "gap_leader": format_gap(gap_leader_min, gap_leader_ms),
        })

        state.position = position
        state.lap = lap
        state.sector = sector + 1
        state.current_lap_ms = current_lap_ms
        state.last_lap_ms = last_lap_ms
        state.lap_distance = struct.unpack_from("<f", data, offset + 24)[0]

        all_cars = []

        for car_index in range(22):
            car_offset = header_size + (car_index * LAP_DATA_SIZE)

            total_distance = struct.unpack_from("<f", data, car_offset + 24)[0]
            car_position = data[car_offset + 32]

            if car_position > 0:
                all_cars.append({
                    "index": car_index,
                    "position": car_position,
                    "total_distance": total_distance,
                })

        player_total_distance = struct.unpack_from("<f", data, offset + 24)[0]
        player_position = position

        cars_behind = [
            car for car in all_cars
            if car["position"] > player_position
        ]

        cars_behind = sorted(cars_behind, key=lambda car: car["position"])[:3]

        behind_display = []

        speed_mps = max((state.speed or 0) / 3.6, 1)

        for car in cars_behind:
            gap_metres = player_total_distance - car["total_distance"]
            gap_seconds = gap_metres / speed_mps

            behind_display.append(
                f"P{car['position']} Car {car['index']}: +{gap_seconds:.3f}s"
            )

        latest_lap["behind"] = behind_display

        print_dashboard()
        return True

    if packet_id == CAR_TELEMETRY_PACKET_ID:
        offset = header_size + (player_car_index * CAR_TELEMETRY_DATA_SIZE)

        speed = struct.unpack_from("<H", data, offset)[0]
        throttle = struct.unpack_from("<f", data, offset + 2)[0]
        steering = struct.unpack_from("<f", data, offset + 6)[0]
        brake = struct.unpack_from("<f", data, offset + 10)[0]
        gear = struct.unpack_from("<b", data, offset + 15)[0]
        rpm = struct.unpack_from("<H", data, offset + 16)[0]
        drs = data[offset + 18]

        latest_car.update({
            "speed": speed,
            "gear": gear,
            "rpm": rpm,
            "throttle": f"{throttle * 100:.0f}%",
            "brake": f"{brake * 100:.0f}%",
            "drs": "ON" if drs else "OFF",
            "steering": format_steering(steering),
        })

        state.speed = speed
        state.throttle = throttle
        state.steering = steering
        state.brake = brake
        state.gear = gear
        state.rpm = rpm
        state.drs = bool(drs)

        print_dashboard()
        return True

    if packet_id == CAR_STATUS_PACKET_ID:
        offset = header_size + (player_car_index * CAR_STATUS_DATA_SIZE)

        actual_tyre = data[offset + 25]
        visual_tyre = data[offset + 26]
        tyre_age = data[offset + 27]

        latest_status.update({
            "tyre": tyre_name(visual_tyre),
            "tyre_age": f"{tyre_age} laps",
        })

        state.tyre_compound = tyre_name(visual_tyre)
        state.tyre_age = tyre_age

        print_dashboard()
        return True

    return False


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((UDP_IP, UDP_PORT))

        print("Listening for live F1 25 telemetry...")

        recorder.start()

        try:
            while True:
                data, _ = sock.recvfrom(4096)
                update_dashboard_from_packet(data)

                #recorder.record(state)

                if state.world_x is not None:
                    print(
                        f"\nMOTION TEST | "
                        f"X: {state.world_x:.2f} | "
                        f"Y: {state.world_y:.2f} | "
                        f"Z: {state.world_z:.2f}"
                    )
        except KeyboardInterrupt:
            recorder.stop()
            print("\nTelemetry listener stopped.")


if __name__ == "__main__":
    main()
