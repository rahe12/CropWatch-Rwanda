# CropWatch Rwanda — Proposal & Roadmap Alignment

This document details how the CropWatch Rwanda platform implements the national strategic roadmap aligned with MINAGRI, RAB, NISR, and Rwanda's Second National Strategy for Transformation (NST2 2024–2029). NASA POWER telemetry is integrated for the four pilot districts, complemented by Sentinel-2 vegetation indices and nationwide CHIRPS agrometeorological modeling.

## Six Core Modules

| Strategic Module | Platform Implementation |
|---|---|
| 1. Integrated agricultural data | NISR SAS 2018–2025 plot microdata; 2026 published tables; CHIRPS; Open-Meteo archive + 7-day; Sentinel NDRE; WFP market prices; UN Comtrade maize flows |
| 2. Climate & agricultural monitoring | 30-district interactive GIS map, rainfall deviation vs usual baselines, 7-day rain forecast, air temperature, ET₀, NDRE vegetation layer |
| 3. Predictive climate risk & crop water | FAO-56 maize ETc = ET₀ × Kc; agroclimatic risk classification; Ridge regression & Random Forest yield models validated out of sample |
| 4. Irrigation & soil conservation | Irrigation-gap and soil-erosion trigger rules from Season A plot microdata and Rwanda Water Portal erosion assessments |
| 5. Explainable decision support | Six-part agrometeorological intelligence card, water balance accounting, and Markdown/HTML executive brief export on each district board |
| 6. Bilingual access | Fully synchronized English and Kinyarwanda interface, AI agronomic copilot, and 160-character mobile USSD/SMS dispatch protocol |

## Climate-Risk Classes (§4.3)

- **Normal monitoring**: Adequate soil moisture and normal rainfall onset.
- **Rainfall watch**: Moderate precipitation deficit detected; monitor phenology.
- **Potential water stress**: Negative 7-day water balance (Pe − ETc < −10 mm) combined with dry season start and low irrigation.
- **Excess rainfall watch**: Heavy localized storms threatening hillside erosion or waterlogging.
- **Agronomist assessment required**: Complex compound risks (acidity + slope + deficit) requiring field ground-truthing.

## FAO-56 Agrometeorological Parameters

- **ET₀**: Open-Meteo FAO-56 reference evapotranspiration at NISR district centroids.
- **Kc**: FAO-56 Table 12 grain maize crop coefficients (0.30 initial / 1.20 mid-season / 0.60 late season).
- **Stage lengths**: FAO-56 Table 11 tropical crop stages (20 / 35 / 40 / 30 days).
- **Planting date**: Synchronized to 15 September 2026 (mid FAO GIEWS Season A window).
- **Effective rainfall (Pe)**: 60% of daily precipitation if ≤5 mm, 80% if >5 mm.
- **Root-zone water balance**: Pe − ETc. Negative values indicate soil moisture depletion.

## Strategic Pilot Districts

Bugesera, Nyagatare, Musanze, Nyaruguru. The platform actively computes and visualizes risk indicators across all 30 districts of Rwanda.
