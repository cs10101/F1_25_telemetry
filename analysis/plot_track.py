import pandas as pd
import matplotlib.pyplot as plt


CSV_FILE = "/home/christopher/f1-telemetry/data/sessions/session_2026-08-22_18-58-52.csv"

df = pd.read_csv(CSV_FILE)

# Remove rows where motion data is unavailable
df = df.dropna(
    subset=["world_x", "world_y", "world_z"]
)

# Remove repeated coordinates
df = df.drop_duplicates(
    subset=["lap", "world_x", "world_y", "world_z"]
)

print(f"Telemetry points: {len(df)}")
print(f"Laps found: {sorted(df['lap'].dropna().unique())}")


# --------------------------------
# TOP-DOWN TRACK VIEW
# --------------------------------

plt.figure(figsize=(10, 8))

plt.plot(
    df["world_x"],
    df["world_z"],
    linewidth=1
)

plt.xlabel("World X (m)")
plt.ylabel("World Z (m)")
plt.title("F1 25 Telemetry - Track Position")

plt.axis("equal")
plt.grid(True)

plt.savefig(
    "analysis/track_2d_fast.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Saved 2D track plot to analysis/track_2d.png")


# --------------------------------
# 3D TRACK VIEW
# --------------------------------

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection="3d")

ax.plot(
    df["world_x"],
    df["world_z"],
    df["world_y"],
    linewidth=1
)

ax.set_xlabel("World X (m)")
ax.set_ylabel("World Z (m)")
ax.set_zlabel("Elevation (m)")

ax.set_title("F1 25 Telemetry - 3D Track Position")

plt.savefig(
    "analysis/track_3d_fast.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Saved 3D track plot to analysis/track_3d.png")