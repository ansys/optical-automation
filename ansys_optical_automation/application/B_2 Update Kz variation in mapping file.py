import os

# ==== Parameters ====
K_Z_1 = 0.5  # Value applied at the minimum X (start of the range)
K_Z_2 = 0.1  # Value applied at the maximum X (end of the range)

# File paths
base_dir = (
    r"C:\Users\amarin\OneDrive - ANSYS, Inc\Articules and Trainings ACE" r"\3D Texture - Light Guide\#3. Variable Kz"
)
input_path = os.path.join(base_dir, "TL L.3D Texture.2.OPT3DMapping")
output_path = os.path.join(base_dir, "K-Z Variation.OPT3DMapping")
# ==== Read the file ====
# Read all lines from the mapping file
with open(input_path, "r") as f:
    lines = f.readlines()

# Ignore first line (header or point count); keep for re-writing later
header = lines[0].strip()
# Keep only non-empty lines from the data section
data_lines = [line.strip() for line in lines[1:] if line.strip()]

# Split each line into a list of floats (assumes numeric, tab/space-separated)
data = [list(map(float, line.split())) for line in data_lines]

# ==== Find min and max X ====
# Extract the X-coordinate (first column) for range computation
x_values = [row[0] for row in data]
x_min = min(x_values)
x_max = max(x_values)

# Avoid division by zero if all X values are identical
if x_max == x_min:
    raise ValueError("All X values are identical. Cannot interpolate.")

# ==== Apply linear interpolation to last column ====
# For each row, compute a normalized position t in [0,1] across X range
# and linearly interpolate the last-column value between K_Z_1 and K_Z_2
for row in data:
    x = row[0]
    # Normalize distance between 0 and 1 along the X span
    t = (x - x_min) / (x_max - x_min)
    # Interpolated K-Z value at this X
    new_value = K_Z_1 + (K_Z_2 - K_Z_1) * t
    row[-1] = round(new_value, 6)  # overwrite last column; keep reasonable precision

# ==== Write the updated file ====
# Re-write the first line as originally read, then all updated data rows
with open(output_path, "w") as f:
    # First line: same header (e.g., point count)
    f.write(f"{header}\n")
    # Write data lines with tab separators
    for row in data:
        f.write("\t".join(map(str, row)) + "\n")

# Final console output with useful info
print(f"File saved to: {output_path}")
print(f"X range: {x_min} to {x_max}")
