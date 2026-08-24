# imported libraries
import pandas as pd
import matplotlib.pyplot as plt

# csv file path we want to use data from
CSV_FILE = "/home/christopher/f1-telemetry/data/sessions/session_2026-08-22_20-15-18.csv"

# store contents of csv file in variable 'df'
df = pd.read_csv(CSV_FILE)

# Remove rows where motion data is unavailable
df = df.dropna(
    subset=["world_x", "world_y", "world_z"]
)

# Remove repeated coordinates
df = df.drop_duplicates(
    subset=["lap", "world_x", "world_y", "world_z"]
)

# printing the number of telemetry points gathered from a session
print(f"Telemetry points: {len(df)}")

# prints the number of laps completed in game
print(f"Laps found: {sorted(df['lap'].dropna().unique())}")


# --------------------------------
# TOP-DOWN TRACK VIEW
# --------------------------------

# create and specify dimensions of a blank figure
plt.figure(figsize=(10, 8))

# plot all of the 2D relevant data points onto the figure
plt.plot(
    df["world_x"],
    df["world_z"],
    linewidth=1 # setting line width
)

# graph labels/titels
plt.xlabel("World X (m)")
plt.ylabel("World Z (m)")
plt.title("F1 25 Telemetry - Track Position")

plt.axis("equal")
plt.grid(True)

# saving the figure as a png file
plt.savefig(
    "analysis/track_2d_center_line.png",
    dpi=200,
    bbox_inches="tight"
)

# removing figures contents and reverting back to blank figure state
plt.close()

# confirm graph file was saved correctly
print("Saved 2D track plot to analysis/track_2d_fast.png")


# --------------------------------
# 3D TRACK VIEW
# --------------------------------

# creating a variable to store the figure used for the 3D map of the track
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection="3d")

# plotting all of the data onto the graph to make a 3D version
ax.plot(
    df["world_x"],
    df["world_z"],
    df["world_y"],
    linewidth=1
)

# graph's labels
ax.set_xlabel("World X (m)")
ax.set_ylabel("World Z (m)")
ax.set_zlabel("Elevation (m)")

ax.set_title("F1 25 Telemetry - 3D Track Position")

# save the 3D version to a png file
plt.savefig(
    "analysis/track_3d_center_line.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Saved 3D track plot to analysis/track_3d.png")