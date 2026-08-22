# this file will be used to record the cars state and enter it into a csv file for analysis later on

import csv
from datetime import datetime
from pathlib import Path


class SessionRecorder:
    def __init__(self, output_dir="data/sessions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.file_path = self.output_dir / f"session_{timestamp}.csv"

        self.file = None
        self.writer = None

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

        print(f"Recording session to: {self.file_path}")

    def record(self, state):
        if self.writer is None:
            return

        # Don't record until motion data exists
        if state.world_x is None:
            return

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

    def stop(self):
        if self.file is not None:
            self.file.close()
            self.file = None
            self.writer = None

            print(f"Session saved to: {self.file_path}")