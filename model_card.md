# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**, a content-based music recommender with switchable ranking modes and a diversity re-ranker.

---

## 2. Goal / Task

VibeMatch suggests the top 5 songs from a small catalog for one listener.

- It takes a taste profile, such as favorite genre, mood and target energy.
- It scores every song against that profile.
- It returns the best matches with a score and a reason for every point.

The goal is transparency. Every recommendation can be traced back to a specific rule.

---

## 3. Data Used

- **Size:** 20 songs in `data/songs.csv`. 10 came with the starter project and 10 were added.
- **Genres (12):** pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, indie rock, edm, r&b, acoustic.
- **Original features:** genre, mood, energy, tempo (BPM), valence, danceability, acousticness.
- **5 advanced features added:**
  - `popularity`: 0 to 100.
  - `release_decade`: 1960s to 2020s.
  - `detailed_mood_tag`: a finer mood label, such as euphoric, nostalgic or aggressive.
  - `instrumentalness`: 0 to 1, how much of the song has no vocals.
  - `speechiness`: 0 to 1, how much of the song is spoken word, such as rap verses.

**Limitations of the data:**

- The songs and artists are fictional. Their numbers were made up to look realistic, not measured from audio.
- Mood labels are subjective and were assigned by one person with AI help.
- Genres are uneven. Lofi has 3 songs; pop, hip-hop, EDM, R&B, jazz and indie rock have 2; rock, ambient, synthwave, indie pop and acoustic have only 1.
- Large parts of music are missing, including classical, country, Latin, K-pop, metal and non-English music.
- `valence`, `instrumentalness` and `speechiness` are stored but not used in scoring yet.

---

## 4. Algorithm Summary

Think of it as a judge with a scorecard.

1. **Matching labels earns fixed points.** If the song's genre is one you like, it gets points. The same goes for mood, mood tag and decade.
2. **Being close earns partial points.** If you want energy 0.8 and the song is 0.7, it is 90% close and earns 90% of the energy points. The same applies to danceability and acousticness.
3. **Optional bonuses.** Matching tempo, or being popular, earns a small bonus, but only if you ask for it.
4. **Add it all up.** The total is the song's score.
5. **Rank the catalog.** Sort all songs from highest to lowest score.
6. **Keep the list varied.** While picking the top 5, a song loses 0.75 points if its artist is already on the list, and 0.35 points if its genre already appears twice. The list is re-sorted after each pick.

**Ranking modes.** The same steps run with different point values:

- `balanced` is the default and weighs everything moderately.
- `genre_first` doubles the value of a genre match.
- `vibe_and_energy` cares most about energy and mood, and much less about genre.

---

## 5. Observed Behavior / Biases

**What works well:**

- Listeners with a clear, well-covered taste get strong, sensible results. The lofi study listener and the indie roadtrip listener both got top matches that hit 4 or 5 preferences at once.
- Every result explains itself, so it is easy to see why a song ranked where it did.

**Biases and weaknesses:**

- **Filter bubbles.** The scoring rewards sameness. In `balanced` mode a genre match is worth more than any single other feature, so a listener keeps hearing their favorite genre.
- **Genre over-weighting.** In `genre_first` mode, the two hip-hop songs scored over 5.2 and the next song scored 2.34. With a bigger catalog this mode would return only one genre.
- **Small-genre unfairness.** Hip-hop fans had only 2 songs to choose from, and neither was labeled energetic or aggressive. Their best score was 4.34, compared with 6.61 for the lofi listener. The system serves well-covered tastes better.
- **Cold start.** There is no listening history. A new user must describe their taste in the catalog's exact words, and the system cannot learn from what they play or skip.
- **Exact-label matching.** "indie" does not match "indie rock", so a small wording difference can hide a perfect song.
- **Popularity bias (opt-in).** Turning on `prefers_popular` boosts songs that are already popular.

**Mitigation: the diversity penalty.** For the lofi listener, Focus Flow would have scored 5.21. It was the same artist as #1 and the third lofi song, so it dropped to 4.11 and was labeled with both penalties. An acoustic song and an ambient song made the top 5. The penalty softens the bubble, but a very strong match can still survive it.

---

## 6. Evaluation Process

**Three listener profiles** were run in `balanced` mode:

| Profile | Top result | Score | Did it match intent? |
|---|---|---:|---|
| High-Energy Hip-Hop / Workout | Concrete Crown (hip-hop) | 4.34 | Yes, though no hip-hop song matched the mood |
| Chill Lofi / Late-Night Study | Midnight Coding (lofi) | 6.61 | Yes, and the diversity penalty kept the list varied |
| Upbeat Indie / Nostalgic Roadtrip | Ferris Wheel Summer (indie rock) | 6.47 | Yes, matching 5 preferences |

**Mode comparison.** The hip-hop profile was run in all three modes.

- `balanced` and `genre_first` kept hip-hop at #1 and #2.
- `vibe_and_energy` pushed hip-hop down to #5, behind aggressive pop, rock and EDM songs.

This confirmed that the weights, not the code, control what the user sees.

**Automated tests.** 18 pytest tests check:

- CSV loading and type casting.
- Clear errors for a missing file, a bad number, an unknown mode or a negative `k`.
- Exact point values for each scoring rule.
- Case-insensitive and multi-genre matching.
- Both diversity penalties.
- That the input song list is never modified.

**What was surprising:** the "hip-hop workout" listener's #1 song in `vibe_and_energy` mode was a pop song. Reading the reasons made it clear why: the pop song matched the "aggressive" tag and the energy target, and genre was worth very little in that mode.

---

## 7. Intended vs. Non-Intended Use

**Intended use:**

- Classroom exploration of how recommenders turn data into ranked lists.
- Experimenting with weights, modes and fairness ideas on a small, readable dataset.
- Demonstrating explainable scoring, where every point has a reason.

**Not intended for:**

- Real users or a real music service. The catalog is tiny and fictional.
- Making claims about real artists, genres or listeners.
- Any decision that matters, such as artist payouts, promotion or charts.
- Judging music quality. A high score means "close to this profile", not "a good song".

---

## 8. Ideas for Improvement

- **Collaborative filtering:** learn from what similar listeners enjoyed, so the system can find songs a user would not have described themselves.
- **Learned embeddings:** represent songs and users as vectors learned from audio or listening data, instead of hand-picked weights and exact labels. Related genres like "indie" and "indie rock" would then land close together.
- **Implicit feedback:** use skip rates, replays and listening time to update a profile automatically, which addresses cold start over time.
- **Use the unused features:** add valence, instrumentalness and speechiness to scoring. Instrumentalness is a natural fit for a study playlist.
- **Fuzzy genre matching:** treat related genres as partial matches.
- **Smarter diversity:** reward novelty, such as a new decade or mood, not only penalize repeats.
- **A bigger, balanced catalog** so every genre has enough songs to compete fairly.

---

## 9. Personal Reflection

<!-- Draft written with AI help. Rewrite in your own words before submitting. -->

The biggest lesson was that a recommender is mostly a set of value judgments written as numbers. Deciding that a genre match is worth 2.0 and a mood match is worth 1.5 felt like a small coding detail, but it decided which songs every listener saw. Switching to `vibe_and_energy` mode turned a hip-hop listener's playlist into a pop, rock and EDM playlist without changing a single line of logic.

I was also surprised by how much the data limited fairness. The hip-hop profile could never score as high as the lofi profile, not because the algorithm favored lofi, but because the catalog had fewer hip-hop songs and none of them matched the requested mood. This changed how I see apps like Spotify. When a recommendation feels repetitive or misses my taste, the cause may be the catalog, the labels or the weights, and not "the algorithm" knowing me poorly. Adding a simple diversity penalty showed that fairness can be designed in, but it also showed that every fix involves a trade-off between giving users what they asked for and showing them something new.
