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

Apps like Spotify, YouTube and TikTok predict what you will enjoy next. They mostly combine two ideas:

- **Collaborative filtering** uses *other people's behavior*. If many listeners who liked song A also liked song B, the app recommends B to you after you play A. It needs no knowledge of the songs themselves, only a huge log of plays, likes, skips and follows. Its weakness is the *cold-start* problem: a brand-new song or user has no history to learn from.
- **Content-based filtering** uses *the item's own attributes*. If you like high-energy hip-hop, it finds other songs that are high-energy hip-hop. It works for new songs on day one, and every recommendation is easy to explain. Its weakness is that it only finds "more of the same", so it can trap users in a filter bubble.

Real platforms blend both. On the content side they use features like **tempo, mood and genre**. On the user side they use **listening history**: likes, skips, playlists you build, and songs you replay. They also use signals such as watch time, time of day and device. TikTok and YouTube lean heavily on implicit feedback (how long you watch and what you finish), while Spotify mixes collaborative signals with audio features of each track.

**This project is purely content-based.** It has no listening history, so it relies on song attributes and an explicit user profile. It uses tempo, mood and genre, but not likes, skips, playlists or replays.

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
- **Exact-label matching.** "indie" does not match "indie rock", and "hip-hop" does not match "rap". Users whose words differ from the catalog's labels lose points silently. A listener who asks for "classical" or "sad" gets no genre or mood points at all, because the catalog has no such songs.
- **Catalog imbalance.** Lofi has 3 songs. Pop, hip-hop, EDM, R&B, jazz and indie rock have 2 each. Rock, ambient, synthwave, indie pop and acoustic have only 1 each. Fans of smaller genres run out of genre matches quickly, and the rest of their list is filled by energy closeness alone.
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

The suite has 23 tests. `tests/test_recommender.py` covers the `Recommender` class. `tests/test_scoring.py` covers loading, scoring, the ranking modes and the diversity penalties.

---

## Sample Recommendation Output & Multi-Profile Experiments

`python -m src.main` prints `Loaded songs: 20`, then runs three experiments:

1. Five listener profiles, all in `balanced` mode with diversity on.
2. The hip-hop profile under all three ranking modes.
3. The lofi profile with the diversity penalty off and on.

All tables below are copied directly from the program output.

### Sample output: Default Pop / Happy Listener

```
=== Default Pop / Happy Listener | mode: balanced | diversity: on ===
Profile: genre=pop, mood=happy, energy=0.8
+------+---------------------+---------------+------------+-------+--------------------------------+
| Rank | Song Title          | Artist        | Genre      | Score | Reasons                        |
+======+=====================+===============+============+=======+================================+
|    1 | Sunrise City        | Neon Echo     | pop        |  4.97 | Genre match: pop (+2.0)        |
|      |                     |               |            |       | Mood match: happy (+1.5)       |
|      |                     |               |            |       | Energy proximity: 0.98 (+1.47) |
+------+---------------------+---------------+------------+-------+--------------------------------+
|    2 | Gym Hero            | Max Pulse     | pop        |  3.30 | Genre match: pop (+2.0)        |
|      |                     |               |            |       | Energy proximity: 0.87 (+1.3)  |
+------+---------------------+---------------+------------+-------+--------------------------------+
|    3 | Rooftop Lights      | Indigo Parade | indie pop  |  2.94 | Mood match: happy (+1.5)       |
|      |                     |               |            |       | Energy proximity: 0.96 (+1.44) |
+------+---------------------+---------------+------------+-------+--------------------------------+
|    4 | Ferris Wheel Summer | Cardigan Club | indie rock |  2.82 | Mood match: happy (+1.5)       |
|      |                     |               |            |       | Energy proximity: 0.88 (+1.32) |
+------+---------------------+---------------+------------+-------+--------------------------------+
|    5 | Blue Note Taxi      | The Late Set  | jazz       |  2.62 | Mood match: happy (+1.5)       |
|      |                     |               |            |       | Energy proximity: 0.75 (+1.12) |
+------+---------------------+---------------+------------+-------+--------------------------------+
```

Sunrise City wins because it matches all three signals in this profile: genre (pop), mood (happy) and energy (0.82 against a target of 0.8). Gym Hero is #2 with only two of them. It is pop and its energy is close (0.93 against 0.8), but its mood is intense, not happy, so it earns no mood points.

### The five listener profiles (`balanced`)

**Profile 1: High-Energy Hip-Hop / Workout Listener.** The two hip-hop songs are #1 and #2 because they match genre. The rest of the list is high-energy songs from other genres.

```
=== High-Energy Hip-Hop / Workout Listener | mode: balanced | diversity: on ===
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

**Profile 2: Chill Lofi / Late-Night Study Listener.** Three lofi songs and an acoustic song lead the list, with an ambient song at #5. Focus Flow is penalized by the diversity rule (see Experiment 3 below).

```
=== Chill Lofi / Late-Night Study Listener | mode: balanced | diversity: on ===
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

**Profile 3: Upbeat Indie / Nostalgic Roadtrip Listener.** Ferris Wheel Summer matches genre, mood, decade, nostalgic tag and energy, so it scores highest.

```
=== Upbeat Indie / Nostalgic Roadtrip Listener | mode: balanced | diversity: on ===
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

**Profile 4: Default Pop / Happy Listener.** This is the sample shown above.

**Profile 5: Edge Case: Sad but High-Energy Classical Fan.** The catalog has no classical songs and no sad songs, so this profile earns no genre or mood points. Every point comes from energy, tempo and popularity. The top five is mostly loud rock, EDM and pop songs. This shows what happens when a listener's taste is outside the catalog.

```
=== Edge Case: Sad but High-Energy Classical Fan | mode: balanced | diversity: on ===
Profile: genre=classical, mood=sad, energy=0.9, tempo_bpm=170, prefers_popular=True
+------+--------------+---------------+-------+-------+--------------------------------+
| Rank | Song Title   | Artist        | Genre | Score | Reasons                        |
+======+==============+===============+=======+=======+================================+
|    1 | Storm Runner | Voltline      | rock  |  2.25 | Energy proximity: 0.99 (+1.48) |
|      |              |               |       |       | Tempo proximity: 0.82 (+0.41)  |
|      |              |               |       |       | Popularity bonus: 71 (+0.35)   |
+------+--------------+---------------+-------+-------+--------------------------------+
|    2 | Gym Hero     | Max Pulse     | pop   |  2.16 | Energy proximity: 0.97 (+1.46) |
|      |              |               |       |       | Tempo proximity: 0.62 (+0.31)  |
|      |              |               |       |       | Popularity bonus: 79 (+0.4)    |
+------+--------------+---------------+-------+-------+--------------------------------+
|    3 | Laser Tide   | Pulse Theory  | edm   |  2.13 | Energy proximity: 0.95 (+1.43) |
|      |              |               |       |       | Tempo proximity: 0.58 (+0.29)  |
|      |              |               |       |       | Popularity bonus: 83 (+0.41)   |
+------+--------------+---------------+-------+-------+--------------------------------+
|    4 | Drop Zone    | Kilowatt Kids | edm   |  2.13 | Energy proximity: 0.93 (+1.4)  |
|      |              |               |       |       | Tempo proximity: 0.70 (+0.35)  |
|      |              |               |       |       | Popularity bonus: 77 (+0.39)   |
+------+--------------+---------------+-------+-------+--------------------------------+
|    5 | Sunrise City | Neon Echo     | pop   |  2.04 | Energy proximity: 0.92 (+1.38) |
|      |              |               |       |       | Tempo proximity: 0.48 (+0.24)  |
|      |              |               |       |       | Popularity bonus: 85 (+0.42)   |
+------+--------------+---------------+-------+-------+--------------------------------+
```

### Experiment 2: ranking modes for the hip-hop profile

The same songs and the same scoring code, with three different weight tables.

```
=== High-Energy Hip-Hop / Workout Listener | mode: balanced | diversity: on ===
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

With `genre_first` (genre worth 4.0), the top two are still the hip-hop songs and the gap widens. Laser Tide drops to 2.34 at #3.

```
=== High-Energy Hip-Hop / Workout Listener | mode: genre_first | diversity: on ===
Profile: genre=hip-hop, mood=energetic, detailed_mood_tag=aggressive, energy=0.85, danceability=0.8
+------+------------------+--------------+---------+-------+--------------------------------------+
| Rank | Song Title       | Artist       | Genre   | Score | Reasons                              |
+======+==================+==============+=========+=======+======================================+
|    1 | Concrete Crown   | Blockline    | hip-hop |  5.41 | Genre match: hip-hop (+4.0)          |
|      |                  |              |         |       | Energy proximity: 0.93 (+0.93)       |
|      |                  |              |         |       | Danceability proximity: 0.95 (+0.48) |
+------+------------------+--------------+---------+-------+--------------------------------------+
|    2 | Paper Cuts Verse | Mic Theory   | hip-hop |  5.26 | Genre match: hip-hop (+4.0)          |
|      |                  |              |         |       | Energy proximity: 0.79 (+0.79)       |
|      |                  |              |         |       | Danceability proximity: 0.94 (+0.47) |
+------+------------------+--------------+---------+-------+--------------------------------------+
|    3 | Laser Tide       | Pulse Theory | edm     |  2.34 | Mood match: energetic (+1.0)         |
|      |                  |              |         |       | Energy proximity: 0.90 (+0.9)        |
|      |                  |              |         |       | Danceability proximity: 0.88 (+0.44) |
+------+------------------+--------------+---------+-------+--------------------------------------+
|    4 | Gym Hero         | Max Pulse    | pop     |  1.88 | Mood tag match: aggressive (+0.5)    |
|      |                  |              |         |       | Energy proximity: 0.92 (+0.92)       |
|      |                  |              |         |       | Danceability proximity: 0.92 (+0.46) |
+------+------------------+--------------+---------+-------+--------------------------------------+
|    5 | Storm Runner     | Voltline     | rock    |  1.87 | Mood tag match: aggressive (+0.5)    |
|      |                  |              |         |       | Energy proximity: 0.94 (+0.94)       |
|      |                  |              |         |       | Danceability proximity: 0.86 (+0.43) |
+------+------------------+--------------+---------+-------+--------------------------------------+
```

With `vibe_and_energy` (energy 3.0, mood 2.0, genre 0.75), aggressive pop, rock and EDM songs fill the top four and the best hip-hop song drops to #5.

```
=== High-Energy Hip-Hop / Workout Listener | mode: vibe_and_energy | diversity: on ===
Profile: genre=hip-hop, mood=energetic, detailed_mood_tag=aggressive, energy=0.85, danceability=0.8
+------+----------------+---------------+---------+-------+--------------------------------------+
| Rank | Song Title     | Artist        | Genre   | Score | Reasons                              |
+======+================+===============+=========+=======+======================================+
|    1 | Gym Hero       | Max Pulse     | pop     |  6.14 | Mood tag match: aggressive (+2.0)    |
|      |                |               |         |       | Energy proximity: 0.92 (+2.76)       |
|      |                |               |         |       | Danceability proximity: 0.92 (+1.38) |
+------+----------------+---------------+---------+-------+--------------------------------------+
|    2 | Storm Runner   | Voltline      | rock    |  6.11 | Mood tag match: aggressive (+2.0)    |
|      |                |               |         |       | Energy proximity: 0.94 (+2.82)       |
|      |                |               |         |       | Danceability proximity: 0.86 (+1.29) |
+------+----------------+---------------+---------+-------+--------------------------------------+
|    3 | Drop Zone      | Kilowatt Kids | edm     |  6.05 | Mood tag match: aggressive (+2.0)    |
|      |                |               |         |       | Energy proximity: 0.88 (+2.64)       |
|      |                |               |         |       | Danceability proximity: 0.94 (+1.41) |
+------+----------------+---------------+---------+-------+--------------------------------------+
|    4 | Laser Tide     | Pulse Theory  | edm     |  6.02 | Mood match: energetic (+2.0)         |
|      |                |               |         |       | Energy proximity: 0.90 (+2.7)        |
|      |                |               |         |       | Danceability proximity: 0.88 (+1.32) |
+------+----------------+---------------+---------+-------+--------------------------------------+
|    5 | Concrete Crown | Blockline     | hip-hop |  4.96 | Genre match: hip-hop (+0.75)         |
|      |                |               |         |       | Energy proximity: 0.93 (+2.79)       |
|      |                |               |         |       | Danceability proximity: 0.95 (+1.43) |
+------+----------------+---------------+---------+-------+--------------------------------------+
```

### Experiment 3: diversity penalty off vs on (lofi profile)

```
=== Chill Lofi / Late-Night Study Listener | mode: balanced | diversity: off ===
Profile: genre=lofi/acoustic, mood=chill, detailed_mood_tag=focused, energy=0.25, acousticness=0.85
+------+---------------------+----------------+----------+-------+--------------------------------------+
| Rank | Song Title          | Artist         | Genre    | Score | Reasons                              |
+======+=====================+================+==========+=======+======================================+
|    1 | Midnight Coding     | LoRoom         | lofi     |  6.61 | Genre match: lofi (+2.0)             |
|      |                     |                |          |       | Mood match: chill (+1.5)             |
|      |                     |                |          |       | Mood tag match: focused (+1.0)       |
|      |                     |                |          |       | Energy proximity: 0.83 (+1.25)       |
|      |                     |                |          |       | Acousticness proximity: 0.86 (+0.86) |
+------+---------------------+----------------+----------+-------+--------------------------------------+
|    2 | Library Rain        | Paper Lanterns | lofi     |  5.84 | Genre match: lofi (+2.0)             |
|      |                     |                |          |       | Mood match: chill (+1.5)             |
|      |                     |                |          |       | Energy proximity: 0.90 (+1.35)       |
|      |                     |                |          |       | Acousticness proximity: 0.99 (+0.99) |
+------+---------------------+----------------+----------+-------+--------------------------------------+
|    3 | Focus Flow          | LoRoom         | lofi     |  5.21 | Genre match: lofi (+2.0)             |
|      |                     |                |          |       | Mood tag match: focused (+1.0)       |
|      |                     |                |          |       | Energy proximity: 0.85 (+1.27)       |
|      |                     |                |          |       | Acousticness proximity: 0.93 (+0.93) |
+------+---------------------+----------------+----------+-------+--------------------------------------+
|    4 | Porch Light Letters | Willow & Pine  | acoustic |  4.33 | Genre match: acoustic (+2.0)         |
|      |                     |                |          |       | Energy proximity: 0.95 (+1.42)       |
|      |                     |                |          |       | Acousticness proximity: 0.91 (+0.91) |
+------+---------------------+----------------+----------+-------+--------------------------------------+
|    5 | Spacewalk Thoughts  | Orbit Bloom    | ambient  |  3.88 | Mood match: chill (+1.5)             |
|      |                     |                |          |       | Energy proximity: 0.97 (+1.46)       |
|      |                     |                |          |       | Acousticness proximity: 0.93 (+0.93) |
+------+---------------------+----------------+----------+-------+--------------------------------------+
```

```
=== Chill Lofi / Late-Night Study Listener | mode: balanced | diversity: on ===
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

With the penalty off, Focus Flow is #3. It is the second LoRoom song and the third lofi song. With the penalty on, the top five is the same set of five songs, but Focus Flow drops to #4 and Porch Light Letters (acoustic) moves up to #3. The penalty changed the order, not the membership of the top five.

### Pairwise comparisons

Each pair below uses the `balanced` results shown above.

- **Hip-Hop vs Lofi.** Lofi scores much higher (top score 6.61 vs 4.34), and the two lists share no songs. Lofi's top song matches genre, mood and mood tag. No hip-hop song in the catalog is labeled energetic or aggressive, so hip-hop's list is built from genre and energy alone. This makes sense because the two profiles want opposite energy (0.85 vs 0.25).
- **Hip-Hop vs Indie.** They share one song, Gym Hero, which is #4 in both lists. Gym Hero is pop with very high energy, so it earns energy points for both and mood-tag points for the hip-hop listener. The rest of each list follows its own genres.
- **Lofi vs Indie.** No songs are shared. The lofi listener wants calm, low-energy acoustic music (energy 0.25), while the indie listener wants brighter, happy music (energy 0.7). Both top scores are close (6.61 and 6.47) because both genres are well covered in the catalog.
- **Pop/Happy vs Indie.** Four of the five songs are shared (Sunrise City, Gym Hero, Rooftop Lights and Ferris Wheel Summer). The indie profile adds a 2010s decade preference and a nostalgic tag, which lifts Ferris Wheel Summer from 2.82 to 6.47 and makes it #1. Its indie rock genre also brings Basement Static in at #5, where the pop profile has the jazz song Blue Note Taxi.
- **Pop/Happy vs Edge Case.** They share Gym Hero and Sunrise City. The pop profile's top score is 4.97, and the edge case's top score is 2.25. The edge case matches no genre or mood, so its list is driven only by energy and tempo. Sunrise City stays on top for the pop profile because it wins on genre and mood.
- **Hip-Hop vs Edge Case.** They share three songs (Laser Tide, Gym Hero and Storm Runner). Both profiles want loud music. Hip-hop's top two stay at the top because of genre points, while Storm Runner moves to #1 for the edge case because it is the closest match to its energy and tempo.

### Ranking-mode and diversity findings

- Changing the weights changed which songs appear and in what order. The hip-hop songs stay on top in `balanced` and `genre_first`, and `vibe_and_energy` pushes them down.
- Turning the diversity penalty on did not add new songs to the lofi top five. It only swapped two positions.

---

## Experiments You Tried

- **Five contrasting profiles** in `balanced` mode (workout, study, roadtrip, default pop and a deliberate edge case). Four got a top 5 that matched their intent. The edge case showed that a genre and mood missing from the catalog leaves only energy to decide the list.
- **Three ranking modes** on the same profile. Raising genre's weight to 4.0 kept the top 2 on hip-hop. Dropping it to 0.75 pushed hip-hop to #5, behind songs that match the aggressive tag and high energy.
- **Diversity on vs. off** on the lofi profile. The penalty is visible in the reasons, but the same five songs are in the top five either way. It only reorders them. This does not show that the list became more accurate.
- **Multi-genre preferences.** Letting a profile like a list of genres (`["lofi", "acoustic"]`) fixed the problem of "lofi/acoustic" fans missing acoustic songs.

**Did the experiments make the results more accurate, or just different?** Mostly just different. The project has no listener ratings or ground-truth "correct" playlist, so accuracy cannot be measured here. Changing the weights changed the results in the direction the weights asked for, which is expected. Whether that is "more accurate" depends on what the listener wants. The diversity penalty changed the order but not the set of songs, so it made the list look more varied, not more relevant.

---

## Limitations and Risks

- The catalog has only 20 hand-made songs, so some genres have only 1–3 options. Classical and sad music are missing completely.
- Matching is by exact label, so "indie" does not match "indie rock", and a profile that asks for a genre the catalog lacks gets no genre points.
- It does not understand lyrics, language, or how a song actually sounds.
- It has no listening history, so it cannot learn and must be told your taste up front (cold start for users).
- The default weights favor genre, which can create a filter bubble. The diversity penalty reduces but does not remove this. In the lofi example, LoRoom still appears twice in the top five.

See the [model card](model_card.md) for a deeper discussion.

---

## Reflection

Read the full write-up in the [**Model Card**](model_card.md).

Building this showed that a recommender is just a scoring rule plus a ranking rule. The scoring rule turns a song's data into a number, and the ranking rule decides which numbers win. Every choice in between, such as how much a genre match is worth or whether energy matters more than mood, is a human value judgment that quietly shapes what the listener sees.

Bias showed up in places that were easy to miss. A small catalog meant hip-hop fans could never get a "perfect" match. Exact labels meant a slightly different word could hide a great song. The default weights kept recommending more of the same genre. The diversity penalty and the switchable modes help, but they also showed that "fair" depends on what the listener wants, and real apps make that choice for millions of people at once.
