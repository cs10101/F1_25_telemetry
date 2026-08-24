import socket
import struct

from telemetry.state import TelemetryState
from telemetry.recorder import SessionRecorder

UDP_IP = "0.0.0.0" # IP address to listen on
UDP_PORT = 20777 # UDP port which F1 25 telemetry is broadcasted on. This is the default port used by the game.

# these are the packet IDs used by the game to identify the type of data being sent. these IDs are used to determine how to parse the data being sent by the game
MOTION_PACKET_ID = 0
LAP_DATA_PACKET_ID = 2
CAR_TELEMETRY_PACKET_ID = 6
CAR_STATUS_PACKET_ID = 7

# these are the sizes of the data packets being sent by the game. these sizes are used to determine how much data to read from the UDP socket when receiving the data.
LAP_DATA_SIZE = 57
CAR_TELEMETRY_DATA_SIZE = 60
CAR_STATUS_DATA_SIZE = 55
MOTION_DATA_SIZE = 60

# Some telemetry versions use a 24-byte header while others use a 29-byte one.
# We accept both layouts so the parser remains compatible with common F1 packet formats.
HEADER_CANDIDATES = (
    (24, 5, 22),
    (29, 6, 27),
)

# these are the variables used to store the latest data being recived by the game. these variables are used to update the dashboard being printed to the console
latest_lap = {}
latest_car = {}
latest_status = {}
state = TelemetryState() # the state of the car being driven by the player
recorder = SessionRecorder() # 

# the format_ms function is used to format the time in milliseconds into a string format of minutes:seconds.milliseconds
def format_ms(ms):
    if ms == 0:
        return "--:--.---"
    minutes = ms // 60000
    seconds = (ms % 60000) / 1000
    return f"{minutes}:{seconds:06.3f}"

# the format_gap function is used to format the gap between the player and the car ahead in milliseconds into a string format of +seconds.milliseconds
def format_gap(minutes, ms):
    total_ms = (minutes * 60000) + ms
    if total_ms == 0:
        return "--"
    return f"+{total_ms / 1000:.3f}s"

# the format_steering function is used to format the steering angle into a string format of degrees.
# if the steering angle is less than 0.001 degrees, it will return "0" instead of a number with many decimal places
def format_steering(steering):
    if abs(steering) < 1e-3:
        return "0"
    formatted = f"{steering:.3f}".rstrip("0").rstrip(".")
    return formatted

# the tyre_name function is used to convert the tyre compound ID into a string format of the tyre compound name
# if the tyre compound ID is not recognised, it will return "Unknown (ID)" where ID is the tyre compound ID
def tyre_name(compound):
    return {
        16: "Soft",
        17: "Medium",
        18: "Hard",
        7: "Intermediate",
        8: "Wet",
    }.get(compound, f"Unknown ({compound})")

# this function is used to create and print the layout for the dashboard the user will see in the console
def print_dashboard():
    print("\033c", end="")
    print("LIVE F1 25 PIT WALL")
    print("-" * 40)

    print("LAP DATA:")
    print(f"Position:     P{latest_lap.get('position', '--')}") # the latest_lap.get() function is used to get the value of the key 'position' from the latest_lap dictionary. if the key does not exist, it will return '--' instead of throwing an error
    print(f"Lap:          {latest_lap.get('lap', '--')}")
    print(f"Sector:       S{latest_lap.get('sector', '--')}")
    print(f"Current Time: {latest_lap.get('current_time', '--')}")
    print(f"Last Lap:     {latest_lap.get('last_lap', '--')}")
    print(f"Gap Ahead:    {latest_lap.get('gap_ahead', '--')}")

    # the for loop is used to iterate through the list of cars behind the player and print their position and gap to the players car.
    # if there are no cars behind the player, it will print "No cars behind"
    print("Behind:")
    for item in latest_lap.get("behind", []):
        print(f"  {item}")

    print(f"Gap Leader:   {latest_lap.get('gap_leader', '--')}")
    print("-" * 40)
    print()

    # this is the section of the dashboard that displays information about the players car
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

# this function is used to parse the packet header of the data being sent by the game
# it will return the header size, packet ID, and player car index if the packet is valid. if the packet is not valid then "None" will be returned
def parse_packet_header(data):

    # this for loop is used to iterate through the HEADER_CANDIDATES list and check if the packet is valid
    for header_size, packet_id_offset, player_car_index_offset in HEADER_CANDIDATES:

        # if the length of the data is less than the header size, then the packet is not valid and it will continue to the next iteration of the for loop
        if len(data) < header_size:
            continue

        # the packet ID is extracted from the data using the struct.unpack_from() function. 
        # this function is used to unpack the data from the byte string into a python object
        packet_id = data[packet_id_offset]

        # if the packet ID is not one of the valid packet IDs, then the packet is not valid and it will continue to the next iteration of the for loop
        if packet_id not in {MOTION_PACKET_ID, LAP_DATA_PACKET_ID, CAR_TELEMETRY_PACKET_ID, CAR_STATUS_PACKET_ID}:
            continue

        player_car_index = data[player_car_index_offset]

        # the required size of the packet is calculated based on the header size, packetID, and the player car index
        # if the packet ID is MOTION_PACKET_ID, then the required size is calculated as the header size plus the player car index multiplied by the MOTION_DATA_SIZE plus the
        # MOTION_DATA_SIZE. this is because the MOTION_PACKET_ID contains data for all cars in the game, so the size of the packet will be larger than the other packet IDs which only contain data for the player car
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

# this fucntion is used to update the dashboard with the latest data being sent by the game.
# it will parse the data being sent by the game and update the latest_lap, latest_car, and the latest_status dictionaries with the latest data as well as the state of the players car
def update_dashboard_from_packet(data):
    header = parse_packet_header(data)
    if header is None:
        return False

    header_size, packet_id, player_car_index = header

    # this if statement is used to check if the packet ID is MOTION_PACKET_ID. if it is, then the world position of the players car is extracted from the data and stored in the state object.
    # afterwards the state object is recorded by the recorder object
    if packet_id == MOTION_PACKET_ID:
        offset = header_size + (player_car_index * MOTION_DATA_SIZE)

        # this code extracts the world position of the players car from the data being sent by the game
        # struct.unpack() is used to unpack the data from the byte string into a python object
        world_x = struct.unpack_from("<f", data, offset)[0]
        world_y = struct.unpack_from("<f", data, offset + 4)[0]
        world_z = struct.unpack_from("<f", data, offset + 8)[0]

        # this is the code which updates the state object with the latest world position of the players car
        state.world_x = world_x
        state.world_y = world_y
        state.world_z = world_z

        # Record one snapshot per Motion packet
        recorder.record(state)

        return True

    # if the packet_id is equal to LAP_DATA_PACKET_ID, then the latest lap data is extracted from the data being sent by the game and stored in the latest_lap dictionary as well as the state of the players car.
    if packet_id == LAP_DATA_PACKET_ID:

        # the offset is calculated based on the header size and the player car index. this is used to determine where in the data the lap data for the players car is located
        offset = header_size + (player_car_index * LAP_DATA_SIZE)

        # the last lap time and current lap time are extracted from the data being sent by the game. these values are in the milliseconds format and are converted into a string format
        # that is easer to read
        last_lap_ms = struct.unpack_from("<I", data, offset)[0]
        current_lap_ms = struct.unpack_from("<I", data, offset + 4)[0]

        gap_ahead_ms = struct.unpack_from("<H", data, offset + 14)[0]
        gap_ahead_min = data[offset + 16]

        gap_leader_ms = struct.unpack_from("<H", data, offset + 17)[0]
        gap_leader_min = data[offset + 19]

        position = data[offset + 32]
        lap = data[offset + 33]
        sector = data[offset + 36]

        # latest_lap dictionary is updated with the latest lap data being sent by the game.
        # this includes the position of the players car, the current lap time, the last lap time, the gap to the car ahead and the gap to the leader of the race
        latest_lap.update({
            "position": position,
            "lap": lap,
            "sector": sector + 1,
            "current_time": format_ms(current_lap_ms),
            "last_lap": format_ms(last_lap_ms),
            "gap_ahead": format_gap(gap_ahead_min, gap_ahead_ms),
            "gap_leader": format_gap(gap_leader_min, gap_leader_ms),
        })

        # the code below is used to update the state object with the latest lap data being sent by the game. 
        # this includes the position of the players car, the current lap time, the last lap time, and the lap distance of the players car
        state.position = position
        state.lap = lap
        state.sector = sector + 1
        state.current_lap_ms = current_lap_ms
        state.last_lap_ms = last_lap_ms
        state.lap_distance = struct.unpack_from("<f", data, offset + 24)[0]

        # the list below is to store the data of the cars behind the players car. this is used to display the gap between the players car and the cars behind them in the dashboard
        all_cars = []

        # the for loop below is used to iterate through all of the cars in the race and extract their position and total distance from the data being sent by the game.
        # this data is then stored in the all_cars list as a dictionary with the keys "index", "position", and "total_distance"
        # the range is 22 to account for the maximum number of cars in the race. 
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

# this is the main function which is used to start the UDP socket and listen for data being sent by the game. it will call the update_dashboard_from_packet() function to update the dashboard
# it will also call the recorder.record() function to record the state of the players car throughout the session.
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((UDP_IP, UDP_PORT))

        print("Listening for live F1 25 telemetry...")

        recorder.start()

        # the try and except block is used to handle the KeyboardInterrupt exception which is raised when the user presses Ctrl+c to stop the program
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
            recorder.stop() # recorder is also stopped in the event of a KeyboardInterrupt
            print("\nTelemetry listener stopped.")

# this is the entry point of the program. it will call the main() function to start the UDP socket and listen for data being sent by the game
if __name__ == "__main__":
    main()
