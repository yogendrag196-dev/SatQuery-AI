"""
create_test_geotiffs.py
Generates the 5 exact GeoTIFF test files specified:
1. satquery_demo_satellite_geotiff.tif (1366x1152, RGB, 8-bit, unreferenced)
2. satellite_scene_A.tif (512x512, 4 bands, float32, WGS84 georeferenced, T1)
3. satellite_scene_B.tif (512x512, 4 bands, float32, WGS84 georeferenced, T2)
4. cross_modal_scene_A.tif (512x512, 6 bands, float32, WGS84 georeferenced, Optical)
5. cross_modal_scene_B.tif (512x512, 6 bands, float32, WGS84 georeferenced, SAR)
"""

import os
import numpy as np
from PIL import Image, TiffImagePlugin

def create_unreferenced_rgb_tiff(output_path, width=1366, height=1152):
    # Synthetic coastal port scene RGB 8-bit
    img_data = np.zeros((height, width, 3), dtype=np.uint8)
    # Ocean gradient
    img_data[:, :width//2, 0] = 12
    img_data[:, :width//2, 1] = 45
    img_data[:, :width//2, 2] = 85
    # Land mass
    img_data[:, width//2:, 0] = 70
    img_data[:, width//2:, 1] = 95
    img_data[:, width//2:, 2] = 50
    # Add port structure lines and ships
    img_data[400:460, width//2-100:width//2+200] = [180, 180, 190]
    img = Image.fromarray(img_data, mode="RGB")
    img.save(output_path, format="TIFF")
    print(f"Created {output_path} ({width}x{height}, RGB 8-bit, unreferenced)")

def create_georeferenced_float32_tiff(output_path, width=512, height=512, num_bands=4, date_str="2024:01:15 10:30:00", is_sar=False):
    # Generate multi-band float32 frames
    frames = []
    for b in range(num_bands):
        if is_sar:
            # Radar backscatter texture with speckle
            base = np.random.uniform(0.05 * (b + 1), 0.85, (height, width)).astype(np.float32)
        else:
            # Multispectral reflection values [0.0, 1.0] across bands
            base = np.linspace(0.1 * (b + 1), 0.9, width, dtype=np.float32).reshape(1, -1)
            base = np.repeat(base, height, axis=0) + (np.sin(np.linspace(0, 3.14, height)).reshape(-1, 1) * 0.05).astype(np.float32)
        frames.append(Image.fromarray(base, mode="F"))

    # Use PIL TiffImagePlugin.ImageFileDirectory_v2 for GeoTIFF tags
    ifdir = TiffImagePlugin.ImageFileDirectory_v2()
    
    # ModelPixelScaleTag (33550) -> [ScaleX, ScaleY, ScaleZ] (0.0005 deg ~ 50m GSD)
    ifdir[33550] = (0.0005, 0.0005, 0.0)
    
    # ModelTiepointTag (33922) -> [I, J, K, X, Y, Z] (Mumbai coordinates 72.82E, 18.96N)
    ifdir[33922] = (0.0, 0.0, 0.0, 72.8200, 18.9600, 0.0)
    
    # GeoKeyDirectoryTag (34735) -> EPSG:4326 WGS-84
    ifdir[34735] = (1, 1, 0, 1, 2048, 0, 1, 4326)
    
    # DateTime Tag (306)
    ifdir[306] = date_str

    if len(frames) > 1:
        frames[0].save(output_path, format="TIFF", save_all=True, append_images=frames[1:], tiffinfo=ifdir)
    else:
        frames[0].save(output_path, format="TIFF", tiffinfo=ifdir)

    print(f"Created {output_path} ({width}x{height}, {num_bands} bands float32, WGS84 georeferenced, date: {date_str})")

if __name__ == "__main__":
    fixtures_dir = os.path.join(os.path.dirname(__file__), "test_fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)

    # 1. Single image mode test GeoTIFF
    p1 = os.path.join(fixtures_dir, "satquery_demo_satellite_geotiff.tif")
    create_unreferenced_rgb_tiff(p1, 1366, 1152)

    # 2. Bi-Temporal T1 (Pre-event: 2024-01-10)
    p2 = os.path.join(fixtures_dir, "satellite_scene_A.tif")
    create_georeferenced_float32_tiff(p2, 512, 512, 4, date_str="2024:01:10 09:15:00", is_sar=False)

    # 3. Bi-Temporal T2 (Post-event: 2024-03-22)
    p3 = os.path.join(fixtures_dir, "satellite_scene_B.tif")
    create_georeferenced_float32_tiff(p3, 512, 512, 4, date_str="2024:03:22 09:30:00", is_sar=False)

    # 4. Cross-Modal Optical (6 bands float32)
    p4 = os.path.join(fixtures_dir, "cross_modal_scene_A.tif")
    create_georeferenced_float32_tiff(p4, 512, 512, 6, date_str="2024:02:14 10:00:00", is_sar=False)

    # 5. Cross-Modal SAR (6 bands float32 polarimetric)
    p5 = os.path.join(fixtures_dir, "cross_modal_scene_B.tif")
    create_georeferenced_float32_tiff(p5, 512, 512, 6, date_str="2024:02:14 10:05:00", is_sar=True)
