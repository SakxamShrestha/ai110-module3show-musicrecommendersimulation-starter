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
- Genres are uneven. Lofi has 3 songs. Pop, jazz, hip-hop, EDM, R&B and indie rock have 2 each. Rock, ambient, synthwave, indie pop and acoustic have only 1 each.
- Large parts of music are missing, including classical, country, Latin, K-pop, metal and non-English music. The catalog also has no song labeled sad.
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

## 5. Observed Behavior

**What works well:**

- Listeners with a clear, well-covered taste get strong, sensible results. The lofi study listener and the indie roadtrip listener both got top matches that hit 4 or 5 preferences at once. The default pop listener's #1 song hit all 3 of its preferences.
- Every result explains itself, so it is easy to see why a song ranked where it did.

**Mitigation: the diversity penalty.** For the lofi listener, Focus Flow scores 5.21 before any penalty. It shares an artist with #1 (LoRoom) and is the third lofi song, so it drops to 4.11 and is labeled with both penalties.

Experiment 3 ran the same profile with the penalty off and on, and the evidence is less strong than the rule suggests. The top five contained the same five songs both times. The only change was the order: Focus Flow moved from #3 to #4, and Porch Light Letters (acoustic) moved from #4 to #3. The acoustic and ambient songs were already in the top five without the penalty, so they should not be credited to it. The penalty is a nudge, not a fix: LoRoom still has two songs in the top five.

---

## 6. Limitations and Bias

**Biases and weaknesses:**

- **Filter bubbles.** The scoring rewards sameness. In `balanced` mode a genre match is worth more than any single other feature, so a listener keeps hearing their favorite genre.
- **Genre over-weighting.** In `genre_first` mode, the two hip-hop songs scored over 5.2 and the next song scored 2.34. With a bigger catalog this mode would return only one genre.
- **Small-genre unfairness.** Hip-hop fans had only 2 songs to choose from, and neither was labeled energetic or aggressive. Their best score was 4.34, compared with 6.61 for the lofi listener. The system serves well-covered tastes better.
- **Cold start.** There is no listening history. A new user must describe their taste in the catalog's exact words, and the system cannot learn from what they play or skip.
- **Exact-label matching.** "indie" does not match "indie rock", so a small wording difference can hide a perfect song.
- **Popularity bias (opt-in).** Turning on `prefers_popular` boosts songs that are already popular.

**Weakness found by the edge-case profile.** The edge-case listener wants classical music in a sad mood, but the catalog has no classical songs and no sad songs, so the system gives zero genre and mood points. Nothing gives partial credit for related labels, so the ranking is decided by energy, tempo and popularity alone. The top five is mostly loud rock, EDM and pop (Storm Runner, Gym Hero, Laser Tide, Drop Zone and Sunrise City), and the output never tells the listener that nothing in the catalog is close to their taste. This is unfair to listeners whose taste falls outside the catalog. A fairer version would give partial credit for related labels, such as indie and indie rock, and warn the user when the catalog has no matches.

---

## 7. Evaluation Process

**Five listener profiles** were run in `balanced` mode with diversity on:

- **High-Energy Hip-Hop / Workout.** Top result: Concrete Crown (hip-hop), 4.34. Mostly yes. Genre matched, but no hip-hop song had the energetic or aggressive label.
- **Chill Lofi / Late-Night Study.** Top result: Midnight Coding (lofi), 6.61. Yes. The penalty moved Focus Flow from #3 to #4.
- **Upbeat Indie / Nostalgic Roadtrip.** Top result: Ferris Wheel Summer (indie rock), 6.47. Yes, matching 5 preferences.
- **Default Pop / Happy.** Top result: Sunrise City (pop), 4.97. Yes, matching all 3 preferences (genre, mood, energy).
- **Edge Case: Sad but High-Energy Classical Fan.** Top result: Storm Runner (rock), 2.25. No, and the catalog cannot match this listener. Every point came from energy, tempo and popularity, which is the failure described in Section 6.

**Mode comparison.** The hip-hop profile was run in all three modes.

- `balanced` and `genre_first` kept hip-hop at #1 and #2.
- `vibe_and_energy` pushed hip-hop down to #5, behind aggressive pop, rock and EDM songs.

This confirmed that the weights, not the code, control what the user sees.

**Diversity comparison.** The lofi profile was run with the penalty off and on. The top five was the same set of songs in both runs, so the penalty changed the order and not the membership of the list.

**Pairwise comparisons:**

- **Hip-Hop vs Lofi.** Lofi scores much higher, and the lists share no songs. Lofi matches genre, mood and tag. Hip-hop has no energetic or aggressive songs, so it earns only genre and energy points.
- **Hip-Hop vs Indie.** They share only Gym Hero (#4 in both). Each list is driven by its own genres.
- **Lofi vs Indie.** No shared songs, and the top scores are close (6.61 and 6.47). Both genres are well covered.
- **Pop/Happy vs Indie.** Four of five songs are shared. The indie profile's decade and nostalgic preferences lift Ferris Wheel Summer to #1.
- **Pop/Happy vs Edge Case.** They share Gym Hero and Sunrise City. The edge case has no genre or mood matches, so its scores are much lower (2.25 vs 4.97).
- **Hip-Hop vs Edge Case.** They share Laser Tide, Gym Hero and Storm Runner. Hip-hop keeps its genre-matched songs on top, while the edge case is ranked only by energy and tempo.

**Why "Gym Hero" keeps showing up.** Gym Hero appears in four of the five lists: #4 for the hip-hop listener, #2 for the default pop listener, #2 for the edge-case listener and #4 for the indie listener. In plain terms, it is a loud, fast workout song with a pop label. The scoring rule does not ask whether a song fits the listener overall. It adds up separate points for each thing the song shares with the profile. Gym Hero is pop, so pop listeners get genre points. Its energy is 0.93, near the top of the scale, so anyone who wants high energy gets energy points. Its tag is aggressive, so the hip-hop listener gets tag points as well. Its mood is intense, which matches none of these profiles, so it earns no mood points. A mismatch only means zero points, so a song can rank high on genre or energy even when its mood is wrong.

**Automated tests.** 23 pytest tests check:

- CSV loading and type casting.
- Clear errors for a missing file, a bad number (including the line it is on), an unknown mode or a negative `k`.
- Exact point values for each scoring rule.
- Case-insensitive and multi-genre matching, and an unknown genre or mood falling back to numeric features.
- Both diversity penalties.
- Duplicate song entries are kept by the ranking and the diversity re-rank.
- Songs missing a feature are skipped instead of raising a `KeyError`.
- That the input song list is never modified.

**What was surprising:** the "hip-hop workout" listener's #1 song in `vibe_and_energy` mode was a pop song. Reading the reasons made it clear why: the pop song matched the "aggressive" tag and the energy target, and genre was worth very little in that mode.

---

## 8. Intended vs. Non-Intended Use

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

## 9. Ideas for Improvement

- **Collaborative filtering:** learn from what similar listeners enjoyed, so the system can find songs a user would not have described themselves.
- **Learned embeddings:** represent songs and users as vectors learned from audio or listening data, instead of hand-picked weights and exact labels. Related genres like "indie" and "indie rock" would then land close together.
- **Implicit feedback:** use skip rates, replays and listening time to update a profile automatically, which addresses cold start over time.
- **Use the unused features:** add valence, instrumentalness and speechiness to scoring. Instrumentalness is a natural fit for a study playlist.
- **Fuzzy genre matching:** treat related genres as partial matches, and handle moods the catalog does not contain (such as "sad") by mapping them to close labels.
- **Smarter diversity:** reward novelty, such as a new decade or mood, not only penalize repeats.
- **A bigger, balanced catalog** so every genre has enough songs to compete fairly, including classical and sad-mood songs.

---

## 10. Personal Reflection

<!-- Draft written with AI help. Rewrite in your own words before submitting. -->

The biggest lesson was that a recommender is mostly a set of value judgments written as numbers. Deciding that a genre match is worth 2.0 and a mood match is worth 1.5 felt like a small coding detail, but it decided which songs every listener saw. Switching to `vibe_and_energy` mode turned a hip-hop listener's playlist into a pop, rock and EDM playlist without changing a single line of logic.

I was also surprised by how much the data limited fairness. The hip-hop profile could never score as high as the lofi profile, not because the algorithm favored lofi, but because the catalog had fewer hip-hop songs and none of them matched the requested mood. This changed how I see apps like Spotify. When a recommendation feels repetitive or misses my taste, the cause may be the catalog, the labels or the weights, and not "the algorithm" knowing me poorly. Adding a simple diversity penalty showed that fairness can be designed in, but it also showed that every fix involves a trade-off between giving users what they asked for and showing them something new.

I expected a weighted sum of a few numbers to feel mechanical. Instead, the top lists felt like real recommendations, because each song's reasons told a short story: this one matches the genre, that one matches the energy. Seeing a 2.25 score for the edge-case listener made it obvious that a score only means "close to this profile" and says nothing about whether the song is good.

AI tools helped me build this faster, and I had to check their work several times. An audit pass with separate agents for code and documentation found real problems that I had missed. The diversity re-rank removed songs by value, so a duplicate song entry could be dropped, and I changed it to remove by identity. `score_song` raised a `KeyError` on songs with missing features, and a bad numeric preference gave an unhelpful error. The same audit pointed out that I had no profile for a listener outside the catalog, so I added the edge case. I also could not trust the AI's pasted tables. I regenerated every table from the program's real output, and I checked a hand calculation (Focus Flow) against the code.

Next, I would like to try partial credit for related genres and moods, and use the unused features (instrumentalness especially) for a study profile. I would also like to test the recommendations with real listeners, to see whether the ranking matches what people actually want, instead of only checking that the arithmetic is right.
