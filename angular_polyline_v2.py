"""
Polyline Angle Calculator V2.0
Copyright (c) 2026 Muhammad Gufran Nurendrawan Bangsa
Licensed under the MIT License.
See LICENSE file di root directory untuk full license text.
"""

# SPDX-License-Identifier: MIT

import numpy as np
import pandas as pd
import math
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import logging
import tkinter as tk
from tkinter import filedialog

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class PolylineAngleCalculator:
    """
    Kelas untuk menghitung sudut belokan pada polyline dari koordinat GPS.
    """
    def __init__(self, earth_radius: float = 6371000.0):
        self.earth_radius = earth_radius
        
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
        dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return self.earth_radius * c
    
    def calculate_initial_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
        dlon = lon2_rad - lon1_rad
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        return (math.degrees(math.atan2(y, x)) + 360) % 360
    
    def calculate_vector_angle(self, point1: Tuple[float, float], point2: Tuple[float, float], point3: Tuple[float, float]) -> float:
        def to_cartesian(lat, lon):
            lat_rad, lon_rad = math.radians(lat), math.radians(lon)
            return np.array([math.cos(lat_rad) * math.cos(lon_rad), math.cos(lat_rad) * math.sin(lon_rad), math.sin(lat_rad)])
        
        v1, v2, v3 = to_cartesian(*point1), to_cartesian(*point2), to_cartesian(*point3)
        vec_a, vec_b = v1 - v2, v3 - v2
        norm_a, norm_b = np.linalg.norm(vec_a), np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0: return 0.0
        cos_angle = np.clip(np.dot(vec_a, vec_b) / (norm_a * norm_b), -1.0, 1.0)
        return math.degrees(math.acos(cos_angle))

    def calculate_additional_metrics(self, coordinates: List[Tuple[float, float]]) -> pd.DataFrame:
        n_points = len(coordinates)
        data = {'latitude': [], 'longitude': [], 'turn_angle_deg': [], 'segment_length_m': [], 'cumulative_distance_m': [], 'bearing_deg': []}
        cum_distance = 0.0
        for i in range(n_points):
            lat, lon = coordinates[i]
            data['latitude'].append(lat)
            data['longitude'].append(lon)
            data['turn_angle_deg'].append(round(self.calculate_vector_angle(coordinates[i-1], coordinates[i], coordinates[i+1]), 2) if 0 < i < n_points - 1 else None)
            if i < n_points - 1:
                dist = self.haversine_distance(lat, lon, *coordinates[i+1])
                data['segment_length_m'].append(round(dist, 2))
                data['bearing_deg'].append(round(self.calculate_initial_bearing(lat, lon, *coordinates[i+1]), 2))
            else:
                data['segment_length_m'].append(None)
                data['bearing_deg'].append(None)
            data['cumulative_distance_m'].append(round(cum_distance, 2))
            if i < n_points - 1: cum_distance += self.haversine_distance(lat, lon, *coordinates[i+1])
        return pd.DataFrame(data)

    def process_csv_file(self, input_path: str) -> pd.DataFrame:
        df = pd.read_csv(input_path)
        col_map = {col.lower(): col for col in df.columns}
        if 'latitude' not in col_map or 'longitude' not in col_map:
            raise ValueError("Kolom latitude/longitude tidak ditemukan!")
        df['latitude'] = df[col_map['latitude']].astype(float)
        df['longitude'] = df[col_map['longitude']].astype(float)
        coords = list(zip(df['latitude'], df['longitude']))
        res_df = self.calculate_additional_metrics(coords)
        out_path = str(Path(input_path).with_name(f"{Path(input_path).stem}_with_angles.csv"))
        res_df.to_csv(out_path, index=False)
        logger.info(f"💾 Tersimpan di: {out_path}")
        return res_df

def get_file_path_gui():
    """Menggunakan GUI untuk memilih file."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(title="Pilih File CSV", filetypes=[("CSV Files", "*.csv")])
    root.destroy()
    return file_path if file_path else None

def main():
    while True:
        print("\n" + "="*30 + "\n1. Pilih File (GUI)\n2. Buat Contoh\n3. Keluar\n" + "="*30)
        choice = input("Pilih (1-3): ").strip()
        if choice == '1':
            path = get_file_path_gui()
            if path:
                try:
                    calc = PolylineAngleCalculator()
                    result = calc.process_csv_file(path)
                    print("\nSelesai! 10 baris pertama:\n", result.head(10))
                except Exception as e: print(f"Error: {e}")
            else: print("Pemilihan dibatalkan.")
        elif choice == '2':
            pd.DataFrame({'latitude': [-6.20, -6.21, -6.22], 'longitude': [106.81, 106.82, 106.81]}).to_csv("sample.csv", index=False)
            print("File sample.csv dibuat.")
        elif choice == '3': break

if __name__ == "__main__":
    main()