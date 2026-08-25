# EasyMesh AI Steering

An AI-powered client steering system for Wi-Fi EasyMesh networks, built as a personal research project.

## Goal
Replace fixed-threshold client steering (RSSI-based) with a machine learning model that considers multiple network signals (RSSI, throughput, AP load, mobility patterns) to make smarter steering decisions.

## Status
🚧 Work in progress — currently setting up simulation environment (Mininet-WiFi)

## Structure
- `simulation/` — Mininet-WiFi topology and scenario scripts
- `models/` — ML model training and evaluation code
- `data/` — Collected network metrics (gitignored, generated locally)
- `docs/` — Notes, references, architecture diagrams

## Background
This project explores integrating AI into the IEEE 1905.1 / Wi-Fi EasyMesh stack, specifically targeting the "sticky client" problem in mesh networks.

## Related Writing
Following this project's progress in a Medium series — link TBD.
