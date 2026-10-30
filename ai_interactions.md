# AI Interactions Log

> This log covers the stretch features built with an AI coding agent (Claude Code): advanced song attributes, multiple ranking modes, diversity and fairness logic, and table-formatted output.

---

## Agentic Workflow (SF8)

**What task did you give the agent?**

The work was split into four multi-step tasks. Each was one prompt, and the agent read the repository, made the changes, ran the code and reported back.

1. Expand `data/songs.csv` to at least 20 songs across diverse genres and add 5 advanced attributes, then show the schema before touching any Python.
2. Implement `src/recommender.py`: CSV loading, scoring with multiple ranking modes, and diversity-aware ranking, without breaking the existing tests.
3. Update `src/main.py` to run three listener profiles and a mode comparison, and print ASCII tables.
4. Write the README, model card and this log.

**Prompts used (summarized):**

- *Step 1:* "Read data/songs.csv to see the exact existing columns... Expand data/songs.csv so it has at least 20 total songs across diverse genres (hip-hop, indie rock, lofi, EDM, R&B, acoustic, jazz, pop)... add 5 new meaningful columns... popularity, release_decade, danceability, acousticness, detailed_mood_tag... Show me the updated CSV schema and a summary of the 20 songs before we touch any Python code."
- *Step 2:* "Now let's implement src/recommender.py. Keep all existing function signatures intact... Define a WEIGHT_STRATEGIES dictionary supporting at least 3 modes... apply a repetition penalty (-0.75 for same artist..., -0.35 if the same genre appears more than twice)... explain how the Strategy Pattern and Diversity Penalty work."
- *Step 3:* "Update src/main.py to verify our recommender and run the Phase 4 multi-profile experiments... Format the terminal output using clean ASCII table formatting... Run `python -m src.main`... show me the exact CLI output."
- *Step 4:* "Complete all documentation files to hit every rubric requirement..."

**What did the agent generate or change?**

| Step | Files changed | Summary |
|---|---|---|
| 1 | `data/songs.csv` | Added 10 songs (now 20 across 12 genres) and 5 columns: `popularity`, `release_decade`, `detailed_mood_tag`, `instrumentalness`, `speechiness`. |
| 2 | `src/recommender.py`, `tests/test_scoring.py` | Implemented `load_songs` (with `csv.DictReader` and numeric casting), `WEIGHT_STRATEGIES`, `score_song`, `recommend_songs` and the greedy diversity re-ranker. Wired the `Recommender` class to the same logic. Added 15 tests. |
| 3 | `src/main.py`, `src/recommender.py`, `tests/test_scoring.py` | Added three profiles, the mode comparison and an ASCII table formatter. Made the import work with both `python -m src.main` and `python src/main.py`. Let preferences accept a list of genres. Added 1 test. |
| 4 | `README.md`, `model_card.md`, `ai_interactions.md` | Wrote the documentation with real CLI output. |

Commands the agent ran included `python -m pytest`, `python -m src.main` and a CSV range-check script.

**What did you verify or fix manually?**

- **A conflict in the prompt.** Step 1 asked for 5 "new" columns, but `danceability` and `acousticness` already existed in the starter CSV. The agent flagged this before writing any Python. It added `instrumentalness` and `speechiness` instead, so there are still 5 genuinely new columns.
- **An ambiguous rule.** "Same genre appears more than twice" could mean penalizing the 3rd song or the 4th. The agent chose the 3rd (`>= 2` already picked) and called it out so it could be changed.
- **Profiles that did not fit the data.** The profiles listed two genres ("lofi/acoustic") and two moods ("energetic/aggressive"). The agent added list support for genres and split the two moods into `mood` and `detailed_mood_tag`.
- **Data checks.** A script confirmed 20 rows, 15 columns per row, no empty cells, and every 0–1 value and 0–100 popularity in range.
- **Tests and CLI run.** All 18 tests passed after each step. `python -m src.main` exited with code 0 and no errors.
- **Hand-checked scores.** For example, Focus Flow: genre 2.0 + mood tag 1.0 + energy 1.27 + acousticness 0.93 = 5.21, minus 0.75 and 0.35 = 4.11, which matches the CLI output.

<!-- TODO: Add anything you personally reviewed, changed or disagreed with in the agent's output. -->

---

## Design Pattern (SF10)

**Which design pattern did you use?**

The **Strategy pattern**, for multiple ranking modes.

**How did AI help you brainstorm or implement it?**

The prompt asked for a `WEIGHT_STRATEGIES` dictionary with at least three modes. The agent implemented each strategy as a *weight table*, not as a separate class or function. Every mode uses the same features and only the weights differ, so a table is the simplest form of the pattern (KISS):

- The scoring algorithm is written once.
- The "strategy" is the data that configures it.
- Adding a new mode is a one-dictionary change with no new code paths.

The agent also added a test that every mode defines every weight, so a new mode cannot silently miss a feature.

**How does the pattern appear in your final code?**

- `WEIGHT_STRATEGIES` in `src/recommender.py` holds the three strategies: `balanced`, `genre_first` and `vibe_and_energy`.
- `_weights_for(mode)` selects a strategy and raises a clear `ValueError` for an unknown mode.
- `score_song(user_prefs, song, mode)` is the "context". It passes the chosen weights to `_categorical_points`, `_proximity_points` and `_bonus_points` and never checks which mode is active.
- `recommend_songs(..., mode=...)` and `run_mode_comparison()` in `src/main.py` switch strategies at runtime.

**Effect:** for the hip-hop workout profile, `genre_first` kept hip-hop at #1 and #2, while `vibe_and_energy` pushed the best hip-hop song to #5. The code was identical; only the strategy changed.

---

## Diversity & Fairness Logic

**The problem:** content-based scoring rewards songs that resemble what the user already likes. That creates a filter bubble: the same genre, and often the same artist, over and over.

**How the penalty works** (`_rerank_with_diversity` and `_apply_diversity_penalty` in `src/recommender.py`):

1. Score and sort all songs with `sorted()`.
2. Build the top-*k* list one pick at a time.
3. Before each pick, re-score every remaining song against the songs already chosen:
   - **-0.75** if its artist is already on the list.
   - **-0.35** if its genre already appears twice.
4. Re-sort the penalized candidates, pick the best, and repeat.
5. Each penalty is added to the song's reasons, so the user can see it.

The penalty depends on what has already been picked, so it has to be applied step by step. A single pass and sort would not work.

**Why it helps prevent filter bubbles:**

- **Artist fairness:** one artist cannot fill the list. LoRoom's second song lost 0.75 points for the lofi listener.
- **Genre fairness:** after two songs from one genre, other genres get a better chance. The lofi listener's top 5 included acoustic and ambient songs.
- **Transparency:** the penalty is visible, so the listener knows the system made a deliberate trade-off.
- **Not a hard ban:** a very strong match can still make the list after a penalty. Focus Flow stayed at #4. Relevance still matters most.
- **Can be turned off:** `apply_diversity=False` disables it for comparison.
