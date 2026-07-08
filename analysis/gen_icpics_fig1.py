#!/usr/bin/env python3
"""Generate a simplified Fig. 1 system architecture diagram for the ICPICS paper.

Removes non-essential elements (SpO2, battery, Android, LED, ring buffers) and fixes
text/border overlaps from the previous version. Three columns: sensors → ESP32 dual-core → host.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D
from pathlib import Path

OUT = Path(__file__).parent.parent / "papers/icpics_figures/fig_system_architecture.png"


def box(ax, x, y, w, h, lines, face="#e8eef9", edge="#3552a3", lw=1.4, fontsize=10, weight="normal"):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=lw, edgecolor=edge, facecolor=face,
    )
    ax.add_patch(p)
    text = "\n".join(lines)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight)


def label_above(ax, x, y, w, text, fontsize=10, weight="bold", color="#222"):
    ax.text(x + w / 2, y, text, ha="center", va="bottom",
            fontsize=fontsize, fontweight=weight, color=color)


def arrow(ax, x0, y0, x1, y1, label="", label_offset_y=0.06, label_offset_x=0.0, color="#444"):
    a = FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle="-|>", mutation_scale=14,
        linewidth=1.3, color=color,
    )
    ax.add_patch(a)
    if label:
        ax.text((x0 + x1) / 2 + label_offset_x, (y0 + y1) / 2 + label_offset_y, label,
                ha="center", va="bottom", fontsize=9, color=color)


def main():
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.6)
    ax.set_aspect("equal")
    ax.axis("off")

    # Title
    ax.text(6, 5.35, "System Architecture", ha="center", va="center",
            fontsize=14, fontweight="bold")

    # ----- Sensors (left column) -----
    box(ax, 0.2, 3.4, 2.0, 1.2,
        ["MyoWare 2.0", "EMG (ENV + RAW)", "2000 Hz"],
        face="#fde2c5", edge="#c97a2b")
    box(ax, 0.2, 1.6, 2.0, 1.2,
        ["ICM-20948", "6-axis IMU", "200 Hz"],
        face="#cfe5f7", edge="#3a78c0")

    # ----- ESP32 outer box -----
    esp_x, esp_y, esp_w, esp_h = 3.3, 0.9, 6.4, 4.0
    p = FancyBboxPatch(
        (esp_x, esp_y), esp_w, esp_h,
        boxstyle="round,pad=0.03,rounding_size=0.10",
        linewidth=1.8, edgecolor="#1f3a76", facecolor="#f5f8ff",
    )
    ax.add_patch(p)
    ax.text(esp_x + esp_w / 2, esp_y + esp_h - 0.32,
            "ESP32 WROOM-32E (240 MHz, dual-core)",
            ha="center", va="center", fontsize=11, fontweight="bold", color="#1f3a76")

    # Core 1 (sensor CPU) — left half
    c1_x, c1_y, c1_w, c1_h = esp_x + 0.25, esp_y + 0.55, 2.35, 2.7
    label_above(ax, c1_x, c1_y + c1_h + 0.05, c1_w, "Core 1 — Sensor CPU", fontsize=10)
    box(ax, c1_x, c1_y + c1_h - 1.05, c1_w, 1.0,
        ["emgDrainTask", "ADC DMA 40 kHz → 2 kHz"],
        face="#cfe5f7", edge="#3a78c0", fontsize=9)
    box(ax, c1_x, c1_y + c1_h - 2.25, c1_w, 1.0,
        ["imuTask", "200 Hz timer"],
        face="#cfe5f7", edge="#3a78c0", fontsize=9)

    # Core 0 (BLE CPU) — right half
    c0_x, c0_y, c0_w, c0_h = esp_x + 3.8, esp_y + 0.55, 2.35, 2.7
    label_above(ax, c0_x, c0_y + c0_h + 0.05, c0_w, "Core 0 — BLE CPU", fontsize=10)
    box(ax, c0_x, c0_y + c0_h - 1.05, c0_w, 1.0,
        ["BLE TX", "NUS notify"],
        face="#fde2c5", edge="#c97a2b", fontsize=9)
    box(ax, c0_x, c0_y + c0_h - 2.25, c0_w, 1.0,
        ["Host watchdog", "PING / PONG"],
        face="#fde2c5", edge="#c97a2b", fontsize=9)

    # ----- Host (right column) -----
    box(ax, 11.2, 2.4, 2.2, 1.2,
        ["PC host", "btCentral.py", "CSV + UDP mirror"],
        face="#dceedb", edge="#3a8a4a")

    # ----- Arrows (kept clear of borders) -----
    # MyoWare → emgDrainTask (ADC DMA)
    arrow(ax, 2.2, 4.0, c1_x, c1_y + c1_h - 0.55, label="ADC DMA", label_offset_y=0.18, label_offset_x=0.0)
    # ICM → imuTask (I2C)
    arrow(ax, 2.2, 2.2, c1_x, c1_y + c1_h - 1.75, label="I²C 400 kHz", label_offset_y=0.14, label_offset_x=-0.1)
    # emgDrainTask → BLE TX (ring buf label above arrow, in the gap)
    arrow(ax, c1_x + c1_w, c1_y + c1_h - 0.55, c0_x, c0_y + c0_h - 0.55,
          label="ring buf", label_offset_y=0.10)
    # imuTask → BLE TX
    arrow(ax, c1_x + c1_w, c1_y + c1_h - 1.75, c0_x, c0_y + c0_h - 0.65, label="")
    # BLE TX → PC host
    arrow(ax, c0_x + c0_w, c0_y + c0_h - 0.55, 11.2, 3.0, label="BLE NUS", label_offset_y=0.18)
    # Host watchdog ← PC (PING)
    arrow(ax, 11.2, 2.7, c0_x + c0_w, c0_y + c0_h - 1.75, label="PING", color="#c97a2b")

    plt.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
