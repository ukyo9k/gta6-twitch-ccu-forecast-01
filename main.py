"""Forecast Grand Theft Auto VI's launch-day Twitch concurrent viewers, hour by hour.

Method (in my own words). The contest hands the program one case: hour 1's print
of the release day, plus every past big game launch's hourly Twitch category counts
(`comparables`, SullyGnome hourly averages). A launch day is not flat: the game
unlocks at midnight local time, rolling westwards, so hour 1 (00:00-01:00 UTC) only
catches New Zealand, Australia and the first European timezones, and the audience
grows through the day as Europe wakes and the Americas unlock (US East 05:00 UTC,
US West 08:00 UTC). The program therefore forecasts a *shape*, not a level:

1. For each past launch in the `comparable` tier (big launches with a rolling
   midnight unlock, no early-access contamination), take its release-day hourly
   counts and divide by its own hour-1 print: the log-ratio curve log(v_h / v_1).
2. The median curve across those launches is the typical shape of a launch day.
3. The shape depends on how big hour 1 already is: a launch whose hour 1 is
   small still has most of its audience ahead of it, while one that opened huge
   has less headroom. Per hour, an ordinary-least-squares line of log-ratio on
   log(hour-1 viewers) across the comparables captures this (the fitted slope
   runs from ~0 at hour 2 to about -0.85 by hour 19). The centre for hour h blends
   30% median curve with 70% regression prediction at this case's hour-1 level.
4. The five quantiles are log-normal around that centre with a fixed log spread
   of 0.40, chosen because it scored best on the four practice launches (mean
   pinball loss ~0.14, against ~0.39 for the flat house baseline).

Everything is computed at run time from the case file, so the same program works
on the practice cases and on the final. No network, no randomness, no fitted
constants that depend on the case being scored: the only numbers fixed in advance
are the blend (0.7), the spread (0.40) and the tier rule. Standard library only.

Run by the grader as `python3 -P -s /bot/main.py` (Python 3.13), one case at a
time: it reads every <id>.in in the input directory and writes <id>.out to the
output directory. Outside the grader, MAKEFUN_INPUT_DIR and MAKEFUN_OUTPUT_DIR
stand in for /input and /output.
"""

import json
import math
import os
import sys
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first, so a helper
# module shipped beside this file would still import.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

# The quantile levels the contest scores, in the order each output row lists them.
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
# Standard normal quantiles at those levels.
Z_VALUES = [-1.6448536269514722, -0.6744897501960817, 0.0, 0.6744897501960817, 1.6448536269514722]

# How much of the centre comes from the per-hour regression on log(hour-1),
# the rest from the median shape across the comparables.
REGRESSION_BLEND = 0.7
# Log spread of the five quantiles around the centre.
LOG_SPREAD = 0.40
# A comparable only counts if its own hour-1 print clears this many viewers;
# a near-empty hour 1 makes its ratios meaningless.
MIN_HOUR_ONE = 500
# A regression needs at least this many launches with a point at the hour.
MIN_REGRESSION_POINTS = 8
# A median needs at least this many ratios at the hour.
MIN_MEDIAN_POINTS = 5


def round_half_up_2(x):
    """Round to 2 decimals, halves away from zero, returning an int when whole."""
    scaled = math.floor(x * 100 + 0.5)
    value = scaled / 100
    return int(value) if value == int(value) else value


def median(values):
    """The median of a non-empty list of numbers."""
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def comparable_tier(comp):
    """True when a comparable is a clean rolling-midnight launch.

    The kit marks the tier inside the `unlock` text ("Tier: comparable").
    Early-access launches, free-to-play launches and the target game's own
    pre-release history carry other tiers and are left out: their release-day
    shapes are contaminated or not a launch at all.
    """
    return "Tier: comparable" in (comp.get("unlock") or "")


def hourly_map(comp):
    """A comparable's hourly points as {hour-start datetime: viewers}."""
    from datetime import datetime

    out = {}
    for point in comp.get("hourly") or []:
        viewers = point.get("viewers")
        if viewers is not None and viewers > 0:
            start = datetime.fromisoformat(point["from"].replace("Z", "+00:00"))
            out[start] = viewers
    return out


def hour_one_print(case):
    """Hour 1's print, falling back to the last pre-checkpoint hour if needed."""
    for row in case.get("known") or []:
        if row.get("hour") == 1 and row.get("viewers"):
            return max(1.0, float(row["viewers"]))
    hourly = case.get("history_hourly") or []
    if hourly:
        last = hourly[-1].get("viewers")
        if last:
            return max(1.0, float(last))
    return 1.0


def log_ratio_curves(case):
    """Per-hour log-ratio lists and regression rows from the comparables.

    Returns (per_hour, rows) where per_hour[h - 2] holds log(v_h / v_1) over
    the comparables that have both hours, and rows holds (log v_1, [log-ratios])
    for the regression. Hours are located by ISO timestamp so sparse series
    (a small category sampled every ~12 h) simply skip the hours they lack.
    """
    from datetime import datetime, timedelta

    def at(text):
        return datetime.fromisoformat(text.replace("Z", "+00:00"))

    chosen = [c for c in (case.get("comparables") or []) if comparable_tier(c)]
    if len(chosen) < MIN_REGRESSION_POINTS:
        # Too few clean launches: fall back to every comparable except the
        # target game's own pre-release history.
        chosen = [c for c in (case.get("comparables") or [])
                  if "target-history" not in (c.get("unlock") or "")]
    per_hour = [[] for _ in range(23)]
    rows = []
    for comp in chosen:
        points = hourly_map(comp)
        day0 = at(comp["day_start"])
        first = points.get(day0)
        if not first or first < MIN_HOUR_ONE:
            continue
        ratios = []
        for h in range(2, 25):
            value = points.get(day0 + timedelta(hours=h - 1))
            if value is not None:
                ratio = math.log(value / first)
                ratios.append(ratio)
                per_hour[h - 2].append(ratio)
            else:
                ratios.append(None)
        if sum(r is not None for r in ratios) >= 20:
            rows.append((math.log(first), ratios))
    return per_hour, rows


def fit_line(xs, ys):
    """Ordinary least squares (intercept, slope) of ys on xs, or None."""
    n = len(xs)
    if n < MIN_REGRESSION_POINTS:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx <= 0:
        return None
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / sxx
    return mean_y - slope * mean_x, slope


def forecast_case(case, name):
    """The 23 forecast rows for one case."""
    p1 = hour_one_print(case)
    log_p1 = math.log(p1)
    per_hour, rows = log_ratio_curves(case)
    hours = []
    for index, hour in enumerate(range(2, 25)):
        ratios = per_hour[index]
        centre = 0.0
        if len(ratios) >= MIN_MEDIAN_POINTS:
            centre = median(ratios)
        xs = [r[0] for r in rows if r[1][index] is not None]
        ys = [r[1][index] for r in rows if r[1][index] is not None]
        line = fit_line(xs, ys)
        if line is not None:
            intercept, slope = line
            centre = (1.0 - REGRESSION_BLEND) * centre + REGRESSION_BLEND * (intercept + slope * log_p1)
        quantiles = []
        previous = 0.0
        for z in Z_VALUES:
            value = p1 * math.exp(centre + z * LOG_SPREAD)
            value = min(max(value, 1.0), 1e9)
            value = round_half_up_2(value)
            if value < previous:
                value = previous
            quantiles.append(value)
            previous = value
        hours.append({"hour": hour, "q": quantiles})
    return {"hours": hours}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        text = json.dumps(forecast, separators=(",", ":")) + "\n"
        (OUTPUT_DIR / (path.stem + ".out")).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
