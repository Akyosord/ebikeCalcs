# E-Bike Acceleration Simulator

A browser-based tool to compare acceleration curves of different electric bikes based on their motor/battery/controller specs.

## Features

- **Speed vs Time** and **Acceleration (g's) vs Time** charts for multiple bikes
- **Constraint visualization**: line style shows which physical limit is active (phase current, battery current, or voltage)
- **Excel-like grid** for entering/editing bike parameters
- **Voltage slider** to simulate state-of-charge effects (+15% to -20%)
- **Auto-save/load** bike data to JSON
- **Full equation derivation** section explaining the physics at a high school level

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

## How It Works

The simulator uses the BLDC motor voltage equation and three constraint regions:

1. **Phase current limit** (constant torque) — dominates at low speed
2. **Battery current limit** (constant power) — dominates at mid speed  
3. **Voltage limit** (back-EMF) — dominates near top speed

See the "How It Works" section in the app for full derivations.

## Tech Stack

- Single HTML file with vanilla JS
- Plotly.js for interactive charts
- Python `http.server` for save/load API
- No build step, no frameworks, no dependencies to install (except Python for persistence)
