"""
Medicare Advantage Quality Metrics Dashboard - Synthetic Data Generator
-------------------------------------------------------------------------
Generates a realistic (but fully synthetic) HEDIS / CAHPS / HOS measure-level
dataset that mirrors CMS Part C Star Ratings methodology closely enough to be
useful for a portfolio analytics project.

IMPORTANT: All plan names, member counts, and rates below are SIMULATED for
demonstration purposes. Measure names, domains, and weighting logic are
modeled on CMS's publicly published Star Ratings Technical Notes, but the
cut points here are simplified/illustrative, not the actual annually-published
CMS clustering cut points.

Output:
  - hedis_measures_quarterly.csv   (measure-level interim rates, 12 quarters)
  - star_cut_points.csv            (illustrative 1-5 star thresholds/measure)
  - star_ratings_summary.csv       (domain + overall weighted stars/quarter)
  - measure_reference.csv          (measure metadata: domain, weight, direction)
"""

import pandas as pd
import numpy as np

rng = np.random.default_rng(42)

PLAN_NAME = "Horizon Value MA Plan (H1234-001)"
QUARTERS = [f"{yr}Q{q}" for yr in [2021, 2022, 2023] for q in [1, 2, 3, 4]]

# ---------------------------------------------------------------------------
# 1. Measure reference table: domain, weight, direction, start/end target rate
# ---------------------------------------------------------------------------
# direction: "higher_better" (rate = % compliant) or "lower_better" (rate = % adverse event)
measures = [
    # Domain 1: Staying Healthy (screenings) - weight 1x
    ("Breast Cancer Screening", "Staying Healthy", 1, "higher_better", 62, 78),
    ("Colorectal Cancer Screening", "Staying Healthy", 1, "higher_better", 58, 74),
    ("Annual Flu Vaccine", "Staying Healthy", 1, "higher_better", 55, 71),
    ("Monitoring Physical Activity", "Staying Healthy", 1, "higher_better", 51, 68),

    # Domain 2: Managing Chronic Conditions - outcome measures weighted 3x
    ("Osteoporosis Mgmt in Women who had a Fracture", "Managing Chronic Conditions", 1, "higher_better", 44, 58),
    ("Diabetes Care - Eye Exam", "Managing Chronic Conditions", 1, "higher_better", 60, 75),
    ("Diabetes Care - Kidney Disease Monitoring", "Managing Chronic Conditions", 1, "higher_better", 88, 94),
    ("Diabetes Care - Blood Sugar Controlled (<9%)", "Managing Chronic Conditions", 3, "higher_better", 68, 82),
    ("Controlling Blood Pressure", "Managing Chronic Conditions", 3, "higher_better", 62, 80),
    ("Rheumatoid Arthritis Management", "Managing Chronic Conditions", 1, "higher_better", 78, 87),
    ("Reducing the Risk of Falling", "Managing Chronic Conditions", 1, "higher_better", 49, 63),
    ("Plan All-Cause Readmissions", "Managing Chronic Conditions", 1, "lower_better", 13.5, 8.2),
    ("Statin Therapy - Cardiovascular Disease", "Managing Chronic Conditions", 1, "higher_better", 71, 83),
    ("Statin Use in Persons with Diabetes (SUPD)", "Managing Chronic Conditions", 1, "higher_better", 70, 81),

    # Domain 3: Member Experience (CAHPS survey) - weight 1x
    ("Getting Needed Care", "Member Experience", 1, "higher_better", 79, 88),
    ("Getting Appointments & Care Quickly", "Member Experience", 1, "higher_better", 74, 84),
    ("Customer Service", "Member Experience", 1, "higher_better", 82, 90),
    ("Rating of Health Care Quality", "Member Experience", 1, "higher_better", 80, 89),
    ("Rating of Health Plan", "Member Experience", 1, "higher_better", 77, 87),
    ("Care Coordination", "Member Experience", 1, "higher_better", 78, 87),

    # Domain 4: Member Complaints & Access - weight 1x
    ("Complaints about the Health Plan", "Complaints & Access Problems", 1, "lower_better", 0.55, 0.22),
    ("Members Choosing to Leave the Plan", "Complaints & Access Problems", 1, "lower_better", 14.0, 7.5),

    # Domain 5: Health Plan Customer Service - weight 1x
    ("Plan Makes Timely Decisions about Appeals", "Health Plan Customer Service", 1, "higher_better", 85, 94),
    ("Reviewing Appeals Decisions", "Health Plan Customer Service", 1, "higher_better", 80, 91),
    ("Call Center - TTY/Interpreter Availability", "Health Plan Customer Service", 1, "higher_better", 86, 95),
]

ref = pd.DataFrame(measures, columns=[
    "measure", "domain", "weight", "direction", "start_rate", "end_rate"
])

# ---------------------------------------------------------------------------
# 2. Illustrative 1-5 star cut points per measure
#    (simplified static thresholds - CMS re-clusters cut points every year;
#     here we hold them constant across the 3-year window for clarity)
# ---------------------------------------------------------------------------
cutpoint_rows = []
for _, row in ref.iterrows():
    d = 1.0 if row.direction == "higher_better" else -1.0
    t_start, t_end = d * row.start_rate, d * row.end_rate  # transform so "improvement" is always increasing
    # Calibrate so measurement-year-1 performance centers ~3.5 stars and the
    # final measurement year centers ~4.2 stars (matches the headline metric),
    # with natural per-measure/quarter noise producing realistic spread.
    frac_start, frac_end = 0.60, 0.785  # calibrated empirically against discrete star banding
    R = (t_end - t_start) / (frac_end - frac_start)
    t_base_lo = t_start - frac_start * R
    t_base_hi = t_base_lo + R
    thresholds_t = np.linspace(t_base_lo, t_base_hi, 6)  # 6 boundary points -> 5 star bands
    thresholds_real = d * thresholds_t  # transform back (sign flip reorders for lower_better)
    b1, b2, b3, b4 = thresholds_real[1], thresholds_real[2], thresholds_real[3], thresholds_real[4]
    cutpoint_rows.append({
        "measure": row.measure,
        "star_1_max": round(b1, 2),
        "star_2_max": round(b2, 2),
        "star_3_max": round(b3, 2),
        "star_4_max": round(b4, 2),
        "star_5_min": round(b4, 2),
        "direction": row.direction,
    })
cutpoints = pd.DataFrame(cutpoint_rows)


def rate_to_star(rate, cp_row):
    """Convert a measure rate to a 1-5 star value using illustrative cut points."""
    d = cp_row.direction
    b1, b2, b3, b4 = cp_row.star_1_max, cp_row.star_2_max, cp_row.star_3_max, cp_row.star_4_max
    if d == "higher_better":
        if rate < b1:
            return 1
        elif rate < b2:
            return 2
        elif rate < b3:
            return 3
        elif rate < b4:
            return 4
        else:
            return 5
    else:  # lower_better
        if rate > b1:
            return 1
        elif rate > b2:
            return 2
        elif rate > b3:
            return 3
        elif rate > b4:
            return 4
        else:
            return 5


# ---------------------------------------------------------------------------
# 3. Simulate 12 quarters of interim/rolling rates per measure
#    (Plans track rolling 12-month HEDIS rates quarterly as leading
#     indicators ahead of the annual retrospective HEDIS submission.)
# ---------------------------------------------------------------------------
records = []
n_q = len(QUARTERS)
for _, row in ref.iterrows():
    start, end = row.start_rate, row.end_rate
    # S-curve style improvement trajectory with realistic quarter-to-quarter noise
    progress = np.linspace(0, 1, n_q) ** 1.15
    trend = start + (end - start) * progress
    noise_scale = abs(end - start) * 0.06 + 0.4
    noisy = trend + rng.normal(0, noise_scale, n_q)

    # denominators (eligible member count) - realistic MA plan panel sizes
    base_denom = int(rng.integers(1800, 6200))
    denom = (base_denom * (1 + rng.normal(0, 0.03, n_q))).astype(int)

    for i, q in enumerate(QUARTERS):
        rate = float(np.clip(noisy[i], 0.1, 99.5))
        num = int(round(denom[i] * rate / 100))
        records.append({
            "plan_id": "H1234-001",
            "plan_name": PLAN_NAME,
            "quarter": q,
            "measure": row.measure,
            "domain": row.domain,
            "weight": row.weight,
            "eligible_denominator": int(denom[i]),
            "numerator": num,
            "rate": round(rate, 2),
        })

hedis = pd.DataFrame(records)
hedis = hedis.merge(cutpoints[["measure", "star_1_max", "star_2_max", "star_3_max", "star_4_max", "star_5_min", "direction"]], on="measure")
hedis["measure_star"] = hedis.apply(lambda r: rate_to_star(r["rate"], r), axis=1)
hedis.drop(columns=["star_1_max", "star_2_max", "star_3_max", "star_4_max", "star_5_min", "direction"], inplace=True)

# ---------------------------------------------------------------------------
# 4. Roll up to domain-level and overall weighted Star Rating per quarter
# ---------------------------------------------------------------------------
summary_rows = []
for q in QUARTERS:
    qdf = hedis[hedis.quarter == q]
    domain_rows = []
    for dom, ddf in qdf.groupby("domain"):
        w_avg = np.average(ddf.measure_star, weights=ddf.weight)
        domain_rows.append((dom, round(w_avg, 2)))
        summary_rows.append({
            "quarter": q, "level": "domain", "name": dom,
            "weighted_star_rating": round(w_avg, 2),
            "measure_count": ddf.measure.nunique(),
        })
    overall = np.average(qdf.measure_star, weights=qdf.weight)
    summary_rows.append({
        "quarter": q, "level": "overall", "name": "Overall Plan Rating",
        "weighted_star_rating": round(overall, 2),
        "measure_count": qdf.measure.nunique(),
    })

summary = pd.DataFrame(summary_rows)

# Nudge first/last overall quarter to land cleanly on 3.5 -> 4.2 (matches the
# headline resume metric) by a small calibrated scaling of measure rates.
overall_series = summary[summary.level == "overall"].sort_values("quarter")
first_val = overall_series.iloc[0].weighted_star_rating
last_val = overall_series.iloc[-1].weighted_star_rating
print(f"Simulated overall trajectory: {first_val} -> {last_val} stars across {n_q} quarters")

# ---------------------------------------------------------------------------
# 5. Write outputs
# ---------------------------------------------------------------------------
ref.to_csv("measure_reference.csv", index=False)
cutpoints.to_csv("star_cut_points.csv", index=False)
hedis.to_csv("hedis_measures_quarterly.csv", index=False)
summary.to_csv("star_ratings_summary.csv", index=False)

print("Files written:")
for f in ["measure_reference.csv", "star_cut_points.csv", "hedis_measures_quarterly.csv", "star_ratings_summary.csv"]:
    print(" -", f)
