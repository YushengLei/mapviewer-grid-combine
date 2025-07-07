import os
import re
from PIL import Image
from collections import defaultdict

def parse_filename(filename):
    """Extract direction and value from filename (e.g. N09E092.png -> ('N', 9, 'E', 92))"""
    match = re.match(r'^([NS])(\d+)([EW])(\d+)\.png$', filename, re.IGNORECASE)
    if not match:
        return None
    lat_dir, lat_val, lon_dir, lon_val = match.groups()
    return lat_dir.upper(), int(lat_val), lon_dir.upper(), int(lon_val)

# Scan directory for PNG files only
files = [f for f in os.listdir() if f.lower().endswith('.png')]
if not files:
    print("No PNG files found in directory!")
    exit()

# Parse all coordinates
coordinates = []
valid_files = []
print("Found PNG files:")
for f in sorted(files):
    parsed = parse_filename(f)
    if not parsed:
        print(f"  Skipping invalid filename: {f}")
        continue
    coordinates.append(parsed)
    valid_files.append(f)
    print(f"  {f}")

# Determine min/max values for each direction
lat_values = {'N': [], 'S': []}
lon_values = {'E': [], 'W': []}

for lat_dir, lat_val, lon_dir, lon_val in coordinates:
    lat_values[lat_dir].append(lat_val)
    lon_values[lon_dir].append(lon_val)

# Create complete ranges (including missing numbers)
def create_range(values, reverse=False):
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    return list(range(max_val, min_val - 1, -1)) if reverse else list(range(min_val, max_val + 1))

north_lats = create_range(lat_values['N'], reverse=True)  # North at top
south_lats = create_range(lat_values['S'])  # South at bottom
east_lons = create_range(lon_values['E'])  # East at right
west_lons = create_range(lon_values['W'], reverse=True)  # West at left

# Combine all coordinates in proper order
all_lats = [(lat, 'N') for lat in north_lats] + [(lat, 'S') for lat in south_lats]
all_lons = [(lon, 'W') for lon in west_lons] + [(lon, 'E') for lon in east_lons]

# Get all image sizes
image_sizes = {}
for f, coord in zip(valid_files, coordinates):
    try:
        with Image.open(f) as img:
            image_sizes[coord] = img.size
            print(f"  Loaded {f} ({img.size[0]}x{img.size[1]})")
    except Exception as e:
        print(f"Error reading {f}: {str(e)}")
        continue

# Determine row heights and column widths
row_heights = {}
for lat, lat_dir in all_lats:
    row_heights[(lat, lat_dir)] = max(
        image_sizes.get((lat_dir, lat, lon_dir, lon), (0, 0))[1]
        for lon, lon_dir in all_lons
    )

col_widths = {}
for lon, lon_dir in all_lons:
    col_widths[(lon, lon_dir)] = max(
        image_sizes.get((lat_dir, lat, lon_dir, lon), (0, 0))[0]
        for lat, lat_dir in all_lats
    )

# Calculate total image size
total_width = sum(col_widths.values())
total_height = sum(row_heights.values())

# Create output image
output = Image.new('RGB', (total_width, total_height), (255, 255, 255))

# Paste images in correct positions
current_y = 0
for lat, lat_dir in all_lats:
    row_height = row_heights[(lat, lat_dir)]
    current_x = 0
    for lon, lon_dir in all_lons:
        col_width = col_widths[(lon, lon_dir)]
        filename = f"{lat_dir}{lat:02d}{lon_dir}{lon:03d}.png"
        
        if os.path.exists(filename):
            try:
                with Image.open(filename) as img:
                    # Center image in its cell
                    x_offset = (col_width - img.width) // 2
                    y_offset = (row_height - img.height) // 2
                    output.paste(img, (current_x + x_offset, current_y + y_offset))
                    print(f"  Placed {filename} at ({current_x + x_offset}, {current_y + y_offset})")
            except Exception as e:
                print(f"Error pasting {filename}: {str(e)}")
                blank = Image.new('RGB', (col_width, row_height), (200, 200, 200))
                output.paste(blank, (current_x, current_y))
        else:
            # Create blank cell
            blank = Image.new('RGB', (col_width, row_height), (200, 200, 200))
            output.paste(blank, (current_x, current_y))
            print(f"  Missing {filename}, created placeholder")
        
        current_x += col_width
    current_y += row_height

# Save output as PNG
output.save('combined_grid.png')
print(f"\nSuccessfully created combined_grid.png ({total_width}x{total_height})")
print(f"Grid layout: {len(all_lats)} rows x {len(all_lons)} columns")

# Print missing files
missing_files = [
    f"{lat_dir}{lat:02d}{lon_dir}{lon:03d}.png"
    for lat, lat_dir in all_lats
    for lon, lon_dir in all_lons
    if not os.path.exists(f"{lat_dir}{lat:02d}{lon_dir}{lon:03d}.png")
]

if missing_files:
    print("\nMissing PNG files in grid:")
    for f in sorted(missing_files)[:20]:  # Show first 20 missing files
        print(f"  {f}")
    if len(missing_files) > 20:
        print(f"  ...and {len(missing_files)-20} more")
else:
    print("\nAll grid positions filled with PNG files!")