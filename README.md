# Medicare Advantage Quality Metrics Dashboard

A HEDIS / Star Ratings quality-improvement tracking project, built to support this resume line:

> Built real-time Tableau dashboard tracking HEDIS measures and Star Ratings performance, supporting quality improvement initiatives that improved overall rating from 3.5 to 4.2 stars

**One thing to flag before you use this:** the simulated trajectory below lands at **3.52 → 4.21 stars**, which is close but not exact to "3.5 to 4.2." I'd round it in your resume/talking points to whatever the data actually shows rather than force an exact match — "improved overall weighted rating from 3.5 to 4.2 stars over a 3-year measurement window" is accurate and defensible if asked to walk through the numbers in an interview.

---

## What's in this project

| File | Purpose |
|---|---|
| `hedis_measures_quarterly.csv` | Measure-level interim rates — 25 measures × 12 quarters (MY2021 Q1 – MY2023 Q4) |
| `star_cut_points.csv` | Illustrative 1–5 star thresholds per measure |
| `star_ratings_summary.csv` | Domain-level and overall weighted star ratings, by quarter |
| `measure_reference.csv` | Measure metadata: domain, CMS weight (1×/3×), improvement direction |
| `dashboard_data.json` | Same data, pre-aggregated for the HTML dashboard |
| `ma_quality_dashboard.html` | **Runnable dashboard** — opens in any browser, no install needed |
| `generate_data.py` | The script that generated the synthetic data (fully reproducible/auditable) |

## Run it on your Mac (30 seconds, no install)

The HTML file is fully self-contained — double-click `ma_quality_dashboard.html` in Finder, or:

```bash
open ma_quality_dashboard.html
```

It needs an internet connection once, to pull Chart.js from a CDN for the trend chart. Everything else (data, styling, logic) is embedded in the file.

This gives you something to screenshot for a portfolio site or LinkedIn today, while you build the actual Tableau version below.

---

## Building the real Tableau version (Tableau Public, free, runs on Mac)

Since the resume line specifically says Tableau, here's how to build it in **Tableau Public Desktop** (free download, works on macOS — [publictableau.com/en-us/s/download](https://public.tableau.com/en-us/s/download)). Tableau Desktop (paid) works identically if you have a license.

### 1. Connect your data
- Open Tableau Public Desktop → **Connect → Text File** → select `hedis_measures_quarterly.csv`
- Add `star_ratings_summary.csv` as a second connection (you'll use it for the overall-trend sheet)
- Optionally join `measure_reference.csv` on `measure` if you want direction/weight metadata without recomputing it

### 2. Key calculated fields (create these on the `hedis_measures_quarterly` data source)

**Star Rating Color (for conditional formatting)**
```
IF [Measure Star] >= 4 THEN "Meets/Exceeds 4-Star Threshold"
ELSEIF [Measure Star] = 3 THEN "At 3-Star Benchmark"
ELSE "Below 3-Star Threshold — Priority"
END
```

**Weighted Star Contribution**
```
[Measure Star] * [Weight]
```
(Use this as the numerator in a weighted-average calc: `SUM([Weighted Star Contribution]) / SUM([Weight])`, computed at whatever level you're rolling up — domain, or overall.)

**QoQ Rate Change**
```
[Rate] - LOOKUP(AVG([Rate]), -1)
```
(Table calc — set "Compute Using" to `Quarter`, partitioned by `Measure`.)

**Star Gap to Next Threshold** *(useful for a QI-prioritization view)*
```
IIF([Measure Star] < 5, 
    "Needs " + STR(ROUND([Rate to next cut point], 1)) + " pts", 
    "At ceiling")
```
*(You'll need the relevant `star_X_max` column from `star_cut_points.csv` blended in for this one — optional, nice-to-have for a "what would move the needle" view.)*

### 3. Sheets to build
1. **Overall Trend** — line chart, `Quarter` on Columns, `Weighted Star Rating` (from `star_ratings_summary`, filtered to `level = overall`) on Rows. Add a reference line at Star = 4 for context.
2. **Domain Breakdown** — bar or bump chart, one bar per domain, current quarter vs. baseline quarter (dual bars or a slope chart).
3. **Measure Detail Table** — `Measure`, `Domain`, `Weight`, `Rate`, `Measure Star`, colored by the `Star Rating Color` calc above. Sort by domain, then by star ascending so lowest-performing measures surface first.
4. **KPI Summary** — a few big-number text tiles: current overall rating, baseline rating, delta, count of measures ≥4★.

### 4. Assemble the dashboard
- New Dashboard, size **1200×800 (Desktop Browser)**
- Layout: KPI tiles across the top → Overall Trend (left, ~60% width) + Domain Breakdown (right, ~40% width) → Measure Detail Table across the bottom
- Add a **domain filter action**: click a bar in Domain Breakdown → filters the Measure Detail Table below it (Dashboard → Actions → Filter)
- Add a **Quarter parameter/filter** so a reviewer can scrub through the 12-quarter history

### 5. Publish
- **Server → Tableau Public → Save to Tableau Public As...** — this gives you a shareable public URL to put in your resume/portfolio/LinkedIn (this is what most healthcare analysts actually link to for portfolio pieces, since employers can't install your local `.twbx`)
- Rename the workbook `MA_Quality_Metrics_Dashboard` before publishing

---

## Data dictionary

**`hedis_measures_quarterly.csv`**
| Column | Description |
|---|---|
| `plan_id`, `plan_name` | Synthetic single-plan identifier |
| `quarter` | e.g. `2021Q1` — rolling 12-month interim measurement period |
| `measure` | HEDIS/CAHPS/HOS measure name (modeled on real CMS Part C measure set) |
| `domain` | One of 5 CMS Star Ratings domains |
| `weight` | CMS measure weight: 1× standard, 3× for select outcome measures |
| `eligible_denominator` / `numerator` | Simulated eligible population and compliant count |
| `rate` | Numerator/denominator, as a percentage |
| `measure_star` | 1–5 star value derived from `rate` via `star_cut_points.csv` |

**Domains modeled:** Staying Healthy · Managing Chronic Conditions · Member Experience (CAHPS) · Complaints & Access Problems · Health Plan Customer Service

## Honest methodology notes (say this if asked in an interview)

- **All data is synthetic**, generated with a documented, reproducible Python script (`generate_data.py`) — not real plan or member data.
- **Star cut points are simplified/static** across the 3-year window for clarity. In reality, CMS re-clusters cut points annually using a hierarchical clustering algorithm published in the Star Ratings Technical Notes — real cut points shift year to year.
- **"Real-time"** here means quarterly rolling-rate tracking, which is how MA plans commonly monitor HEDIS performance between the annual retrospective HEDIS submission (HEDIS itself is not literally real-time — it's calculated from the prior measurement year's claims/chart-review data). If you use "real-time" in an interview, be ready to clarify you mean the dashboard refreshes on a defined cadence against rolling interim rates, not that HEDIS itself streams live.
- **Only Part C measures are modeled** here (no Part D drug measures), and this is a single hypothetical plan, not a multi-contract book of business.
