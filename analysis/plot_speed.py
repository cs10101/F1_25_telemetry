import pandas as pd
import matplotlib.pyplot as plt


# Load telemetry data
df = pd.read_csv("/home/christopher/f1-telemetry/data/sessions/session_2026-08-26_15-35-11.csv")


# Group telemetry samples by lap
for lap_number, lap_data in df.groupby("lap"):

    plt.plot(
        lap_data["lap_distance"],
        lap_data["speed"],
        label=f"Lap {int(lap_number)}"
    )


# Configure graph
plt.xlabel("Lap Distance (m)")
plt.ylabel("Speed (km/h)")
plt.title("Multi-Lap Speed Comparison")

plt.legend()
plt.grid()

# saving the figure as a png file
plt.savefig(
    "analysis/speed_graph_4.png",
    dpi=200,
    bbox_inches="tight"
)