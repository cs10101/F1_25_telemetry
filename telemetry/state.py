# this file will be used to keep track of the cars live state position in the game

from dataclasses import dataclass


@dataclass
class TelemetryState:
    # Lap data
    position: int | None = None
    lap: int | None = None
    sector: int | None = None
    current_lap_ms: int | None = None
    last_lap_ms: int | None = None
    lap_distance: float | None = None

    # Car telemetry
    speed: int | None = None
    throttle: float | None = None
    steering: float | None = None
    brake: float | None = None
    gear: int | None = None
    rpm: int | None = None
    drs: bool | None = None

    # Car status
    tyre_compound: str | None = None
    tyre_age: int | None = None

    # Motion data
    world_x: float | None = None
    world_y: float | None = None
    world_z: float | None = None