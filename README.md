# 🎵 Music Recommender Simulation

## Project Summary

This project is a small, explainable, content-based music recommender written in Python.

It loads a 20-song catalog from `data/songs.csv`, compares every song to a listener's taste profile, and returns the top 5 songs with a score and a plain-language reason for every point awarded.

Highlights:

- 20 songs across 12 genres, each with 14 attributes (including 5 advanced ones: popularity, release decade, detailed mood tag, instrumentalness, speechiness).
- Three swappable ranking modes (`balanced`, `genre_first`, `vibe_and_energy`) built with the Strategy pattern.
- A diversity re-ranker that penalizes repeated artists and over-represented genres.
- A CLI that prints results as ASCII tables and runs multi-profile experiments.

---

## How The System Works

### How real-world recommenders work

Apps like Spotify and TikTok predict what you will enjoy next. They mostly combine two ideas:

- **Collaborative filtering** uses *other people's behavior*. If many listeners who liked song A also liked song B, the app recommends B to you after you play A. It needs no knowledge of the songs themselves, only a huge log of plays, likes, skips and follows. Its weakness is the *cold-start* problem: a brand-new song or user has no history to learn from.
- **Content-based filtering** uses *the item's own attributes*. If you like high-energy hip-hop, it finds other songs that are high-energy hip-hop. It works for new songs on day one, and every recommendation is easy to explain. Its weakness is that it only finds "more of the same", so it can trap users in a filter bubble.

Real platforms blend both, plus signals such as watch time, skips, time of day and device. TikTok leans heavily on implicit feedback (how long you watch), while Spotify mixes collaborative signals with audio features of each track.

**This project is purely content-based.** It has no listening history, so it relies on song attributes and an explicit user profile.

### The four building blocks

| Building block | What it is in this project |
|---|---|
| **Input features** (describe each song) | `genre`, `mood`, `energy`, `tempo_bpm`, `valence`, `danceability`, `acousticness`, plus advanced features `popularity`, `release_decade`, `detailed_mood_tag`, `instrumentalness`, `speechiness` |
| **User preferences** (describe the listener) | Any subset of: favorite `genre` (one or a list), `mood`, `detailed_mood_tag`, `release_decade`, target `energy`, `danceability`, `acousticness`, `tempo_bpm`, and a `prefers_popular` flag. The `UserProfile` class stores genre, mood, target energy and `likes_acoustic` |
| **Scoring rule** (judges *one* song) | `score_song()` gives a single song points for each preference it satisfies and returns `(score, reasons)` |
| **Ranking rule** (orders the *catalog*) | `recommend_songs()` scores every song, sorts highest first with `sorted()`, then re-ranks greedily with diversity penalties and returns the top *k* |

The scoring rule never looks at other songs. The ranking rule is the only place where songs are compared to each other, which is why the diversity penalty lives there.

```
songs.csv ──> load_songs() ──> score_song() for every song ──> sorted() ──> diversity re-rank ──> top k + reasons
                                   ▲
                    user profile + ranking mode (weights)
```

### Algorithm recipe

**1. Categorical match points.** For each of `genre`, `mood`, `release_decade`, `detailed_mood_tag` the user specified:

```
points = weight[feature]   if the song's value matches (case-insensitive, or any value in a list)
points = 0                 otherwise
```

**2. Continuous proximity points.** For each of `energy`, `danceability`, `acousticness` the user specified:

```
similarity = max(0, 1.0 - |target - song_value|)
points     = similarity × weight[feature]
```

If the user gives `likes_acoustic` but no acousticness target, the target becomes 0.8 (likes) or 0.2 (dislikes).

**3. Optional bonuses** (only when the user asks for them):

```
tempo:      max(0, 1 - |target_bpm - song_bpm| / 100) × weight[tempo_bpm]
popularity: (popularity / 100) × weight[popularity]          # only if prefers_popular=True
```

**4. Song score** = sum of all points above, rounded to 2 decimals.

**5. Ranking with diversity.** Build the top-*k* list one pick at a time. Before each pick, every remaining song is re-scored against the songs already chosen:

```
-0.75  if the song's artist is already in the list
-0.35  if the song's genre already appears 2 or more times in the list
```

The candidates are re-sorted and the highest is picked. Each penalty is added to that song's reasons.

**Weights per ranking mode** (`WEIGHT_STRATEGIES` in `src/recommender.py`):

| Feature | `balanced` (default) | `genre_first` | `vibe_and_energy` |
|---|---:|---:|---:|
| genre | 2.0 | **4.0** | 0.75 |
| mood | 1.5 | 1.0 | **2.0** |
| release_decade | 0.5 | 0.5 | 0.25 |
| detailed_mood_tag | 1.0 | 0.5 | **2.0** |
| energy | 1.5 | 1.0 | **3.0** |
| danceability | 1.0 | 0.5 | 1.5 |
| acousticness | 1.0 | 0.5 | 1.0 |
| tempo_bpm | 0.5 | 0.25 | 0.75 |
| popularity | 0.5 | 0.25 | 0.25 |

### Potential algorithmic biases

- **Genre over-weighting.** In `balanced` mode a genre match is a guaranteed +2.0, while a continuous feature can earn at most 1.5. A song in the right genre but the wrong vibe can beat a perfect-vibe song in a neighboring genre.
- **Filter bubbles.** Content-based scoring rewards sameness. Without the diversity penalty, a lofi fan would get three lofi songs in the top four, two of them by the same artist.
- **Exact-label matching.** "indie" does not match "indie rock", and "hip-hop" does not match "rap". Users whose words differ from the catalog's labels lose points silently.
- **Catalog imbalance.** Lofi has 3 songs while hip-hop, EDM and R&B have only 2 each, and five genres have just 1. Fans of smaller genres run out of genre matches quickly, and the rest of their list is filled by energy closeness alone.
- **Popularity bias (opt-in).** If `prefers_popular` is on, already-popular songs get a boost, which makes them even more visible.
- **Subjective labels.** Mood and mood tags were assigned by hand (with AI help). Someone else might call "Gym Hero" energetic instead of intense.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app from the project root:

   ```bash
   python -m src.main
   ```

### Running Tests

```bash
pytest
```

`tests/test_recommender.py` covers the `Recommender` class. `tests/test_scoring.py` covers loading, scoring, the ranking modes and the diversity penalties.

---

## Sample Recommendation Output & Multi-Profile Experiments

`python -m src.main` prints `Loaded songs: 20`, then runs two experiments:

1. Three listener profiles, all in `balanced` mode.
2. The hip-hop profile under all three ranking modes.

### Profile 1: High-Energy Hip-Hop / Workout Listener (`balanced`)

```
=== High-Energy Hip-Hop / Workout Listener | mode: balanced ===
Profile: genre=hip-hop, mood=energetic, detailed_mood_tag=aggressive, energy=0.85, danceability=0.8
+------+------------------+--------------+---------+-------+--------------------------------------+
| Rank | Song Title       | Artist       | Genre   | Score | Reasons                              |
+======+==================+==============+=========+=======+======================================+
|    1 | Concrete Crown   | Blockline    | hip-hop |  4.34 | Genre match: hip-hop (+2.0)          |
|      |                  |              |         |       | Energy proximity: 0.93 (+1.4)        |
|      |                  |              |         |       | Danceability proximity: 0.95 (+0.95) |
+------+------------------+--------------+---------+-------+--------------------------------------+
|    2 | Paper Cuts Verse | Mic Theory   | hip-hop |  4.12 | Genre match: hip-hop (+2.0)          |
|      |                  |              |         |       | Energy proximity: 0.79 (+1.19)       |
|      |                  |              |         |       | Danceability proximity: 0.94 (+0.94) |
+------+------------------+--------------+---------+-------+--------------------------------------+
|    3 | Laser Tide       | Pulse Theory | edm     |  3.73 | Mood match: energetic (+1.5)         |
|      |                  |              |         |       | Energy proximity: 0.90 (+1.35)       |
|      |                  |              |         |       | Danceability proximity: 0.88 (+0.88) |
+------+------------------+--------------+---------+-------+--------------------------------------+
|    4 | Gym Hero         | Max Pulse    | pop     |  3.30 | Mood tag match: aggressive (+1.0)    |
|      |                  |              |         |       | Energy proximity: 0.92 (+1.38)       |
|      |                  |              |         |       | Danceability proximity: 0.92 (+0.92) |
+------+------------------+--------------+---------+-------+--------------------------------------+
|    5 | Storm Runner     | Voltline     | rock    |  3.27 | Mood tag match: aggressive (+1.0)    |
|      |                  |              |         |       | Energy proximity: 0.94 (+1.41)       |
|      |                  |              |         |       | Danceability proximity: 0.86 (+0.86) |
+------+------------------+--------------+---------+-------+--------------------------------------+
```

### Profile 2: Chill Lofi / Late-Night Study Listener (`balanced`)

```
=== Chill Lofi / Late-Night Study Listener | mode: balanced ===
Profile: genre=lofi/acoustic, mood=chill, detailed_mood_tag=focused, energy=0.25, acousticness=0.85
+------+---------------------+----------------+----------+-------+--------------------------------------------------------------+
| Rank | Song Title          | Artist         | Genre    | Score | Reasons                                                      |
+======+=====================+================+==========+=======+==============================================================+
|    1 | Midnight Coding     | LoRoom         | lofi     |  6.61 | Genre match: lofi (+2.0)                                     |
|      |                     |                |          |       | Mood match: chill (+1.5)                                     |
|      |                     |                |          |       | Mood tag match: focused (+1.0)                               |
|      |                     |                |          |       | Energy proximity: 0.83 (+1.25)                               |
|      |                     |                |          |       | Acousticness proximity: 0.86 (+0.86)                         |
+------+---------------------+----------------+----------+-------+--------------------------------------------------------------+
|    2 | Library Rain        | Paper Lanterns | lofi     |  5.84 | Genre match: lofi (+2.0)                                     |
|      |                     |                |          |       | Mood match: chill (+1.5)                                     |
|      |                     |                |          |       | Energy proximity: 0.90 (+1.35)                               |
|      |                     |                |          |       | Acousticness proximity: 0.99 (+0.99)                         |
+------+---------------------+----------------+----------+-------+--------------------------------------------------------------+
|    3 | Porch Light Letters | Willow & Pine  | acoustic |  4.33 | Genre match: acoustic (+2.0)                                 |
|      |                     |                |          |       | Energy proximity: 0.95 (+1.42)                               |
|      |                     |                |          |       | Acousticness proximity: 0.91 (+0.91)                         |
+------+---------------------+----------------+----------+-------+--------------------------------------------------------------+
|    4 | Focus Flow          | LoRoom         | lofi     |  4.11 | Genre match: lofi (+2.0)                                     |
|      |                     |                |          |       | Mood tag match: focused (+1.0)                               |
|      |                     |                |          |       | Energy proximity: 0.85 (+1.27)                               |
|      |                     |                |          |       | Acousticness proximity: 0.93 (+0.93)                         |
|      |                     |                |          |       | Diversity penalty: artist LoRoom already recommended (-0.75) |
|      |                     |                |          |       | Diversity penalty: genre lofi already appears 2x (-0.35)     |
+------+---------------------+----------------+----------+-------+--------------------------------------------------------------+
|    5 | Spacewalk Thoughts  | Orbit Bloom    | ambient  |  3.88 | Mood match: chill (+1.5)                                     |
|      |                     |                |          |       | Energy proximity: 0.97 (+1.46)                               |
|      |                     |                |          |       | Acousticness proximity: 0.93 (+0.93)                         |
+------+---------------------+----------------+----------+-------+--------------------------------------------------------------+
```

### Profile 3: Upbeat Indie / Nostalgic Roadtrip Listener (`balanced`)

```
=== Upbeat Indie / Nostalgic Roadtrip Listener | mode: balanced ===
Profile: genre=indie rock/indie pop/pop, mood=happy, detailed_mood_tag=nostalgic, energy=0.7, release_decade=2010s
+------+---------------------+-----------------+------------+-------+----------------------------------+
| Rank | Song Title          | Artist          | Genre      | Score | Reasons                          |
+======+=====================+=================+============+=======+==================================+
|    1 | Ferris Wheel Summer | Cardigan Club   | indie rock |  6.47 | Genre match: indie rock (+2.0)   |
|      |                     |                 |            |       | Mood match: happy (+1.5)         |
|      |                     |                 |            |       | Decade match: 2010s (+0.5)       |
|      |                     |                 |            |       | Mood tag match: nostalgic (+1.0) |
|      |                     |                 |            |       | Energy proximity: 0.98 (+1.47)   |
+------+---------------------+-----------------+------------+-------+----------------------------------+
|    2 | Rooftop Lights      | Indigo Parade   | indie pop  |  5.41 | Genre match: indie pop (+2.0)    |
|      |                     |                 |            |       | Mood match: happy (+1.5)         |
|      |                     |                 |            |       | Decade match: 2010s (+0.5)       |
|      |                     |                 |            |       | Energy proximity: 0.94 (+1.41)   |
+------+---------------------+-----------------+------------+-------+----------------------------------+
|    3 | Sunrise City        | Neon Echo       | pop        |  4.82 | Genre match: pop (+2.0)          |
|      |                     |                 |            |       | Mood match: happy (+1.5)         |
|      |                     |                 |            |       | Energy proximity: 0.88 (+1.32)   |
+------+---------------------+-----------------+------------+-------+----------------------------------+
|    4 | Gym Hero            | Max Pulse       | pop        |  3.65 | Genre match: pop (+2.0)          |
|      |                     |                 |            |       | Decade match: 2010s (+0.5)       |
|      |                     |                 |            |       | Energy proximity: 0.77 (+1.15)   |
+------+---------------------+-----------------+------------+-------+----------------------------------+
|    5 | Basement Static     | The Loose Fuses | indie rock |  3.47 | Genre match: indie rock (+2.0)   |
|      |                     |                 |            |       | Energy proximity: 0.98 (+1.47)   |
+------+---------------------+-----------------+------------+-------+----------------------------------+
```

### Ranking-mode comparison (Profile 1)

The full tables are printed by `python -m src.main`. Summary of the top 5 in each mode:

| Rank | `balanced` | `genre_first` | `vibe_and_energy` |
|---:|---|---|---|
| 1 | Concrete Crown (hip-hop) 4.34 | Concrete Crown (hip-hop) 5.41 | Gym Hero (pop) 6.14 |
| 2 | Paper Cuts Verse (hip-hop) 4.12 | Paper Cuts Verse (hip-hop) 5.26 | Storm Runner (rock) 6.11 |
| 3 | Laser Tide (edm) 3.73 | Laser Tide (edm) 2.34 | Drop Zone (edm) 6.05 |
| 4 | Gym Hero (pop) 3.30 | Gym Hero (pop) 1.88 | Laser Tide (edm) 6.02 |
| 5 | Storm Runner (rock) 3.27 | Storm Runner (rock) 1.87 | Concrete Crown (hip-hop) 4.96 |

### Comparative analysis

**Across profiles:**

- **Profile 2 and Profile 3 get the strongest matches** (6.61 and 6.47) because the catalog has songs that hit genre, mood, mood tag and energy all at once.
- **Profile 1 tops out at 4.34.** No hip-hop song in the catalog is labeled `energetic` or `aggressive`, so the hip-hop songs only earn genre and proximity points. The mood and mood-tag points go to EDM, pop and rock songs instead. This shows how a small catalog limits what any profile can achieve.
- **The diversity penalty only fires for Profile 2.** Focus Flow would have scored 5.21, but it repeats the artist LoRoom (-0.75) and would be the third lofi song (-0.35). It drops to 4.11 and stays at #4 because its base score is still strong. Without the penalty the top 4 would be three lofi songs, two by the same artist.
- **Profile 3 benefits from accepting a list of genres.** Indie rock, indie pop and pop songs all earn the genre bonus, and the 2010s decade match breaks the tie between similar songs.

**Across ranking modes (Profile 1):**

- **`balanced`** puts the two hip-hop songs first, then fills the list with high-energy songs from other genres.
- **`genre_first`** keeps the same order but widens the gap. The two hip-hop songs score above 5.2 and the next song scores 2.34. If the catalog had five hip-hop songs, this mode would return only hip-hop.
- **`vibe_and_energy`** flips the list. With energy weighted 3.0 and genre only 0.75, aggressive pop, rock and EDM songs fill the top four. The best hip-hop song drops to #5. This mode suits a listener who cares about "workout energy" more than genre.

The same songs and the same scoring code produce very different lists. Only the weight table changes, which is the point of the Strategy pattern.

---

## Experiments You Tried

- **Three contrasting profiles** (workout, study, roadtrip) in `balanced` mode. Each got a top 5 that matched its intent.
- **Three ranking modes** on the same profile. Raising genre's weight to 4.0 locked the top 2 to hip-hop; dropping it to 0.75 pushed hip-hop down to #5.
- **Diversity on vs. off.** With `apply_diversity=False`, the lofi listener's top 4 would include three lofi songs, two by LoRoom. With it on, Focus Flow is penalized and labeled, and an acoustic song and an ambient song still make the top 5.
- **Multi-genre preferences.** Letting a profile like a list of genres (`["lofi", "acoustic"]`) fixed the problem of "lofi/acoustic" fans missing acoustic songs.

---

## Limitations and Risks

- The catalog has only 20 hand-made songs, so some genres have only 1–3 options.
- Matching is by exact label, so "indie" does not match "indie rock".
- It does not understand lyrics, language, or how a song actually sounds.
- It has no listening history, so it cannot learn and must be told your taste up front (cold start for users).
- The default weights favor genre, which can create a filter bubble. The diversity penalty reduces but does not remove this.

See the [model card](model_card.md) for a deeper discussion.

---

## Reflection

Read the full write-up in the [**Model Card**](model_card.md).

Building this showed that a recommender is just a scoring rule plus a ranking rule. The scoring rule turns a song's data into a number, and the ranking rule decides which numbers win. Every choice in between, such as how much a genre match is worth or whether energy matters more than mood, is a human value judgment that quietly shapes what the listener sees.

Bias showed up in places that were easy to miss. A small catalog meant hip-hop fans could never get a "perfect" match. Exact labels meant a slightly different word could hide a great song. The default weights kept recommending more of the same genre. The diversity penalty and the switchable modes help, but they also showed that "fair" depends on what the listener wants, and real apps make that choice for millions of people at once.
