# this file will be used to record the cars state and enter it into a csv file for analysis later on

# importing libraries
import csv
from datetime import datetime
from pathlib import Path

# creating a new class called SessionRecorder to record data which is produced from the F1 25 game during a game session
class SessionRecorder:

    # create the class???
    def __init__(self, output_dir="data/sessions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.file_path = self.output_dir / f"session_{timestamp}.csv"

        self.file = None
        self.writer = None

        self.initial_lap = None
        self.recording_started = False

    # activate the SessionRecorder class
    def start(self):
        self.file = open(self.file_path, "w", newline="")

        fieldnames = [
            "timestamp",
            "lap",
            "lap_distance",
            "world_x",
            "world_y",
            "world_z",
            "speed",
            "throttle",
            "brake",
            "steering",
            "gear",
            "rpm",
            "drs",
            "tyre_compound",
            "tyre_age",
        ]

        self.writer = csv.DictWriter(
            self.file,
            fieldnames=fieldnames
        )

        self.writer.writeheader()

        # telling the user where the csv file is being recorded to
        print(f"Recording session to: {self.file_path}")

    # function to actually record the data being produced by the game
    def record(self, state):
        if self.writer is None:
            return

        # im assuming this means if there is no game session going on then dont record anything
        if state.world_x is None or state.lap is None:
            return

        # Remember which lap we were on when telemetry started.
        if self.initial_lap is None:
            self.initial_lap = state.lap
            print(
                f"Waiting for start/finish line "
                f"(currently lap {self.initial_lap})..."
            )
            return

        # Ignore everything until the lap number changes.
        if not self.recording_started:
            if state.lap == self.initial_lap:
                return

            self.recording_started = True
            print(
                f"Start/finish crossed - recording from lap {state.lap}!"
            )

        # this is all the data that the recorder will collect during game session
        self.writer.writerow({
            "timestamp": datetime.now().isoformat(),
            "lap": state.lap,
            "lap_distance": state.lap_distance,
            "world_x": state.world_x,
            "world_y": state.world_y,
            "world_z": state.world_z,
            "speed": state.speed,
            "throttle": state.throttle,
            "brake": state.brake,
            "steering": state.steering,
            "gear": state.gear,
            "rpm": state.rpm,
            "drs": state.drs,
            "tyre_compound": state.tyre_compound,
            "tyre_age": state.tyre_age,
        })

    # this function stops the recorder when there is no game session going on
    def stop(self):
        if self.file is not None:
            self.file.close()
            self.file = None
            self.writer = None

            # confirmation message telling user that file saved correctly
            print(f"Session saved to: {self.file_path}")