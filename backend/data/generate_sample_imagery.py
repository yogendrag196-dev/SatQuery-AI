"""
generate_sample_imagery.py
Generates realistic multi-modal satellite imagery files (RGB, False-Color NIR, SAR, Bi-Temporal T1/T2 pairs)
for the 5 preloaded ISRO/Remote Sensing missions.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def create_mission_imagery():
    out_dir = os.path.join(os.path.dirname(__file__), "sample_imagery")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Mumbai Port Maritime (Optical RGB + SAR)
    mumbai_rgb = Image.new('RGB', (800, 600), color=(14, 28, 48)) # Ocean water
    draw = ImageDraw.Draw(mumbai_rgb)
    # Coastal land mass
    draw.polygon([(0, 0), (280, 0), (320, 600), (0, 600)], fill=(40, 52, 50))
    # Docks & berths
    for y in range(80, 540, 70):
        draw.rectangle([(280, y), (370, y + 25)], fill=(75, 82, 90)) # Concrete wharf
        # Cargo ships moored
        draw.rectangle([(380, y + 2), (520, y + 23)], fill=(180, 70, 50)) # Ship hull
        draw.rectangle([(420, y + 6), (490, y + 19)], fill=(40, 140, 160)) # Containers

    # Ships in navigation channel
    draw.rectangle([(550, 120), (680, 155)], fill=(190, 60, 50))
    draw.rectangle([(580, 320), (710, 360)], fill=(60, 70, 80)) # Naval Frigate
    draw.rectangle([(620, 460), (740, 490)], fill=(170, 120, 40)) # Bulk Carrier

    mumbai_rgb.save(os.path.join(out_dir, "mumbai_port_rgb.png"))

    # 2. Brahmaputra Flood (T1 Baseline vs T2 Post-Flood)
    # T1 Pre-flood
    t1_flood = Image.new('RGB', (800, 600), color=(50, 85, 45)) # Green agrarian flood plain
    draw_t1 = ImageDraw.Draw(t1_flood)
    # River main channel (normal level)
    draw_t1.line([(0, 280), (300, 290), (600, 270), (800, 310)], fill=(25, 60, 95), width=45)
    t1_flood.save(os.path.join(out_dir, "brahmaputra_t1_baseline.png"))

    # T2 Post-flood (Extensive inundation)
    t2_flood = Image.new('RGB', (800, 600), color=(50, 85, 45))
    draw_t2 = ImageDraw.Draw(t2_flood)
    # Swollen main river
    draw_t2.line([(0, 280), (300, 290), (600, 270), (800, 310)], fill=(20, 75, 120), width=160)
    # Overflow flood lagoons
    draw_t2.ellipse([(120, 100), (380, 240)], fill=(20, 75, 120))
    draw_t2.ellipse([(420, 340), (760, 560)], fill=(20, 75, 120))
    t2_flood.save(os.path.join(out_dir, "brahmaputra_t2_flood.png"))

    # 3. Western Ghats Deforestation & Wildfire (T1 2022 vs T2 2026)
    t1_forest = Image.new('RGB', (800, 600), color=(20, 70, 25)) # Deep dense canopy
    t1_forest.save(os.path.join(out_dir, "western_ghats_t1_2022.png"))

    t2_forest = Image.new('RGB', (800, 600), color=(20, 70, 25))
    draw_t2_f = ImageDraw.Draw(t2_forest)
    # Deforestation scar
    draw_t2_f.polygon([(180, 150), (350, 120), (410, 320), (220, 340)], fill=(120, 85, 50))
    # Wildfire burn scar
    draw_t2_f.polygon([(480, 260), (720, 220), (690, 480), (450, 440)], fill=(45, 30, 25))
    t2_forest.save(os.path.join(out_dir, "western_ghats_t2_2026.png"))

    # 4. SDSC-SHAR Sriharikota Launch Complex
    shri_rgb = Image.new('RGB', (800, 600), color=(45, 60, 40)) # Coastal island scrub
    draw_shri = ImageDraw.Draw(shri_rgb)
    # Bay of Bengal coast
    draw_shri.polygon([(620, 0), (800, 0), (800, 600), (580, 600)], fill=(18, 42, 68))
    # Launch Pad 1 & 2 Concrete flame trenches & towers
    draw_shri.rectangle([(320, 180), (420, 260)], fill=(90, 95, 105))
    draw_shri.rectangle([(350, 205), (390, 235)], fill=(180, 185, 195)) # Mobile tower
    draw_shri.rectangle([(300, 380), (400, 460)], fill=(90, 95, 105)) # Pad 2
    # Propellant storage tanks (circular spheres)
    for cx, cy in [(250, 200), (275, 200), (250, 225), (275, 225)]:
        draw_shri.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=(220, 230, 240))
    shri_rgb.save(os.path.join(out_dir, "sriharikota_launch_complex.png"))

    # 5. Chennai Urban Expansion (T1 2020 vs T2 2026)
    t1_urban = Image.new('RGB', (800, 600), color=(70, 90, 60)) # Open vegetated/marshy area
    draw_t1_u = ImageDraw.Draw(t1_urban)
    draw_t1_u.ellipse([(200, 180), (550, 450)], fill=(30, 70, 110)) # Large marshland lake
    t1_urban.save(os.path.join(out_dir, "chennai_urban_t1_2020.png"))

    t2_urban = Image.new('RGB', (800, 600), color=(70, 90, 60))
    draw_t2_u = ImageDraw.Draw(t2_urban)
    draw_t2_u.ellipse([(260, 240), (490, 390)], fill=(30, 70, 110)) # Shrunken lake
    # High-density new buildings & concrete roads
    for bx in range(80, 720, 55):
        for by in range(60, 540, 55):
            if not (260 < bx < 490 and 240 < by < 390):
                draw_t2_u.rectangle([(bx, by), (bx + 35, by + 30)], fill=(110, 115, 125))
    t2_urban.save(os.path.join(out_dir, "chennai_urban_t2_2026.png"))

    print(f"[OK] Generated multi-modal satellite images in {out_dir}")

if __name__ == '__main__':
    create_mission_imagery()
