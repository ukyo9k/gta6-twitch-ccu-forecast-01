# gta6-twitch-ccu-forecast-01

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/ukyo9k/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/ukyo9k/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

An hour-by-hour forecast of how many people watch Grand Theft Auto VI live on
Twitch on its release day, 19 November 2026 (UTC). Grand Theft Auto VI launches
that day on PlayStation 5 and Xbox Series X|S, unlocking at midnight local time
country by country — New Zealand first, then Europe, then the Americas — so the
Twitch audience builds through the day instead of arriving all at once. The
first trailer drew 93 million YouTube views in 24 hours, a Guinness record for
a game reveal; the second trailer reached 475 million views across platforms in
a day, which Rockstar called the biggest video launch of all time. For scale,
the single-player launch record on Twitch is Hogwarts Legacy at about 1.3
million concurrent viewers, and Grand Theft Auto V's own category peaked at
about 1.14 million.

## How the forecast works

`main.py` (Python 3.13, standard library only) reads one case file and writes
one forecast file. It does not guess a level: it anchors on the case's own
hour-1 print and forecasts the *shape* of the day from the 38 past big game
launches bundled in the case (`comparables`, SullyGnome hourly Twitch category
averages). For each past launch in the clean rolling-midnight tier, it takes
the log ratio of each hour's viewers to that launch's hour-1 print. Two facts
carry the forecast:

- The median ratio curve is the typical launch-day shape: a dip in the small
  hours, then a climb as Europe wakes and the US unlocks, peaking around
  18:00–20:00 UTC at roughly two to three times the hour-1 print.
- The shape depends on how big hour 1 already is. A launch that opened small
  still has most of its audience ahead of it; one that opened huge has less
  headroom. A per-hour regression of the log ratio on log hour-1 viewers
  captures this — its slope runs from about 0 at hour 2 to about −0.85 by
  hour 19 — and the forecast blends 70% regression with 30% median curve.
- The five quantiles are log-normal around that centre with a fixed log spread
  of 0.40.

On the four practice launches (Marvel's Wolverine, Red Dead Redemption 2, God
of War Ragnarök, Marvel's Spider-Man 2) this scores a mean pinball loss of
0.145, against 0.387 for the flat house baseline that holds every hour at the
hour-1 print. Practice scores are no guide to the final — the final is one
day, one game, and the biggest launch ever — but the shape, the regression and
the spread were all chosen on the practice data alone, never on the final.

## Run it

```sh
python3 main.py
```

The program reads every `<id>.in` in `$MAKEFUN_INPUT_DIR` (default `/input`)
and writes `<id>.out` to `$MAKEFUN_OUTPUT_DIR` (default `/output`): one JSON
object with exactly 23 rows, hours 2 to 24, each five quantiles at the 0.05,
0.25, 0.5, 0.75 and 0.95 levels. It runs in under a second on the practice
cases, uses no network and no randomness, so two runs write identical bytes.

---

<sub>Entered on [make.fun](https://make.fun/?ref=1gefbfp1&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
