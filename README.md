# EasyMesh AI Steering

An AI-powered client steering system for Wi-Fi EasyMesh networks, built as a personal research project.

## Goal
Replace fixed-threshold client steering (RSSI-based) with a machine learning model that considers multiple network signals (RSSI, throughput, AP load, mobility patterns) to make smarter steering decisions.

## Status
| Phase | What | State |
|---|---|---|
| 1 | Simulator + RSSI-threshold baseline (Mininet-WiFi) | ✅ Done |
| 2 | Data generator: many scenarios → per-second CSV features | ⏳ Next |
| 3 | Train a first steering model | — |
| 4 | Let the model steer in simulation, compare against the baseline | — |

## Structure
- `simulation/` — Mininet-WiFi topology and scenario scripts
- `models/` — ML model training and evaluation code
- `data/` — Collected network metrics (gitignored, generated locally)
- `docs/` — Notes, references, architecture diagrams, roaming dashboard

## Phase 1: the baseline scenario

`simulation/topology_2ap.py` builds a small EasyMesh-style network in Mininet-WiFi:

```
  ap1 (ch 1, x=30 m) ====== wired backhaul ====== ap2 (ch 6, x=90 m)
        sta1 walks from x=10 m to x=110 m in 30 s
```

- Both APs use the same SSID (`easymesh`) with WPA2, as in a real mesh.
- Signal strength comes from a log-distance propagation model (exponent 3.5), simulated by wmediumd.
- The station roams on its own, the way most clients do today: `wpa_supplicant` background scanning (`bgscan simple`) starts looking for a better AP below **−60 dBm** and only switches when the new AP is at least **5 dB** stronger. This is the RSSI-threshold behaviour the ML model has to beat.
- Scans are limited to the mesh channels (1 and 6), as an 802.11k neighbor report would do. Without this, the simulated radio sweeps every 2.4/5/6 GHz channel, a scan takes about 20 s, and the station never roams.

Run it (Mininet-WiFi needs root):

```bash
sudo ~/mininet-wifi-env/bin/python simulation/topology_2ap.py            # interactive CLI
sudo ~/mininet-wifi-env/bin/python simulation/topology_2ap.py --no-cli   # walk, log, exit
sudo ~/mininet-wifi-env/bin/python simulation/topology_2ap.py --no-cli --wpa-log /path/sta1_wpa.log
```

`--no-cli` prints, once per second: time, station position, the AP it is connected to, and its RSSI. `--wpa-log` also writes the `wpa_supplicant` debug log and prints the scan results every 5 s.

### Baseline result

ap2 becomes the stronger AP at x = 60 m (t ≈ 15 s). The station switches to ap2 only at x ≈ 75 m (t = 19 s): about **4 s / 15 m late**, because ap2 was not yet 5 dB stronger. That lag is the "sticky client" problem in miniature, and it is what the steering model should remove.

## Roaming dashboard

[`docs/roaming_dashboard.html`](docs/roaming_dashboard.html) is a self-contained page for checking simulation runs second by second. Download it and open it in a browser; no install or server is needed. It contains three runs:

| Run | Setup | Result |
|---|---|---|
| 1 | Open APs | Linked late (t = 7 s), never roamed |
| 2 | WPA2 APs | Same as run 1: scans took 7–20 s |
| 3 | WPA2 + scans limited to ch 1 and 6 | Linked at t = 0, roamed to ap2 at t = 19 s |

What it shows:

- **Run summaries.** For each run: when the station first connected, how many handovers it made, and how many seconds it spent *sticky* (on one AP while the other was at least the roam margin stronger), *weak* (below −60 dBm) or with no link.
- **Signal over time.** The station's RSSI for the two compared runs, the −60 dBm bgscan threshold, and the signal the station *would* get from each AP at its position. Those model curves use the log-distance model with its 1 m reference fitted from the measured samples; they match the measured ap1 signal within about 1 dB. A shaded band marks where ap2 is the better AP.
- **Corridor view.** The 0–120 m corridor with both APs, where the station is at the selected second, and a line to the AP it is connected to. A time slider and hover on the chart move it.
- **Second-by-second table.** Position, each run's AP and RSSI, the difference between runs, the modelled signal from ap1 and ap2, the better AP, and an OK / Weak / Sticky / No-link verdict per run. With `--wpa-log` runs, it also shows the scan results. Clicking a row moves the chart and corridor to that second.
- **Add a run.** Paste the output of `topology_2ap.py --no-cli` (or open the log file) to compare a new run. Added runs are kept in that browser only.

The roam margin used for the *sticky* verdict is adjustable (default 5 dB, the same as `wpa_supplicant`).

## Background
This project explores integrating AI into the IEEE 1905.1 / Wi-Fi EasyMesh stack, specifically targeting the "sticky client" problem in mesh networks.

## Related Writing
Following this project's progress in a Medium series — link TBD.
