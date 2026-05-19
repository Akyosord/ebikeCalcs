# E-Bike Acceleration Simulator

A browser-based tool to compare acceleration curves of different electric bikes based on their motor/battery/controller specs.

## Features

- **Speed vs Time** and **Acceleration (g's) vs Time** charts for multiple bikes
- **Constraint visualization**: line style shows which physical limit is active (phase current, battery current, or voltage)
- **Excel-like grid** for entering/editing bike parameters
- **Voltage slider** to simulate state-of-charge effects (+15% to -20%)
- **Auto-save/load** bike data to JSON
- **Full equation derivation** section explaining the physics

## Quick Start

```bash
python server.py
```

Opens `http://localhost:8080` in your browser.

## Parameters

| Type | Fields |
|------|--------|
| **Input** | Top Speed (mph), Motor Peak Power (W), Battery Max Current (A), Controller Phase Current (A) |
| **Assumption** | Battery Voltage, Internal Resistances, Gear Ratio, Wheel Size, Mass, Aero Drag, Rolling Resistance |
| **Calculated** | Kt (torque constant), Ke (back-EMF constant) |

## Tech Stack

- Single HTML file with vanilla JS
- Plotly.js for interactive charts
- KaTeX for LaTeX equation rendering
- Python `http.server` for save/load API
- No build step, no frameworks

---

## Physics & Derivation

The full derivation (with LaTeX-rendered equations) lives in the app itself — open `http://localhost:8080` and scroll to the **"How It Works — Full Derivation"** section.

This is the single source of truth. Topics covered:

1. Motor constants ($K_t = K_e$) and what they mean physically
2. The voltage budget equation
3. Deriving $K_t$ from top speed (why it works)
4. Three constraint zones & transition points (phase current → battery current → voltage limit)
5. From torque to acceleration (Euler integration)
6. Why higher wattage ≠ faster launch
7. DC vs BLDC equivalence — why the "DC motor" equations are exact for e-bike hub motors
8. Voltage slider & state of charge effects
