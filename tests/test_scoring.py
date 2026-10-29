import pytest

from src.recommender import (
    WEIGHT_STRATEGIES,
    load_songs,
    recommend_songs,
    score_song,
)


def make_song(**overrides) -> dict:
    """Build a song dict with neutral defaults, overriding any given fields."""
    base = {
        "id": 1,
        "title": "Track",
        "artist": "Artist A",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "tempo_bpm": 120.0,
        "valence": 0.8,
        "danceability": 0.8,
        "acousticness": 0.2,
        "popularity": 50,
        "release_decade": "2010s",
        "detailed_mood_tag": "euphoric",
        "instrumentalness": 0.1,
        "speechiness": 0.05,
    }
    return {**base, **overrides}


def test_load_songs_casts_numeric_fields():
    songs = load_songs("data/songs.csv")

    assert len(songs) >= 20
    first = songs[0]
    assert isinstance(first["id"], int)
    assert isinstance(first["popularity"], int)
    assert isinstance(first["energy"], float)
    assert isinstance(first["tempo_bpm"], float)
    assert isinstance(first["release_decade"], str)


def test_load_songs_raises_clear_error_for_missing_file():
    with pytest.raises(FileNotFoundError, match="Songs file not found"):
        load_songs("data/does_not_exist.csv")


def test_load_songs_reports_line_of_bad_numeric_value(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("id,title,energy\n1,Ok,0.5\n2,Broken,loud\n")

    with pytest.raises(ValueError, match="line 3"):
        load_songs(str(bad_csv))


def test_score_song_awards_categorical_and_proximity_points_with_reasons():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    score, reasons = score_song(prefs, make_song())

    # balanced: genre 2.0 + mood 1.5 + perfect energy 1.5
    assert score == 5.0
    assert "Genre match: pop (+2.0)" in reasons
    assert "Mood match: happy (+1.5)" in reasons
    assert "Energy proximity: 1.00 (+1.5)" in reasons


def test_score_song_matches_decade_and_mood_tag_case_insensitively():
    prefs = {"release_decade": "2010S", "detailed_mood_tag": "Euphoric"}

    score, reasons = score_song(prefs, make_song())

    assert score == 1.5
    assert any(reason.startswith("Decade match") for reason in reasons)
    assert any(reason.startswith("Mood tag match") for reason in reasons)


def test_score_song_derives_acoustic_target_from_likes_acoustic():
    prefs = {"likes_acoustic": True}

    score, reasons = score_song(prefs, make_song(acousticness=0.8))

    assert score == 1.0
    assert reasons == ["Acousticness proximity: 1.00 (+1.0)"]


def test_score_song_adds_tempo_and_popularity_bonuses_only_when_requested():
    song = make_song(tempo_bpm=110.0, popularity=80)

    plain_score, _ = score_song({}, song)
    bonus_score, reasons = score_song({"tempo_bpm": 120, "prefers_popular": True}, song)

    assert plain_score == 0.0
    # tempo: (1 - 10/100) * 0.5 = 0.45; popularity: 0.8 * 0.5 = 0.4
    assert bonus_score == 0.85
    assert any(reason.startswith("Tempo proximity: 0.90") for reason in reasons)
    assert any(reason.startswith("Popularity bonus: 80") for reason in reasons)


def test_score_song_mode_changes_weights():
    prefs = {"genre": "pop"}

    balanced, _ = score_song(prefs, make_song(), mode="balanced")
    genre_first, _ = score_song(prefs, make_song(), mode="genre_first")

    assert balanced == WEIGHT_STRATEGIES["balanced"]["genre"]
    assert genre_first == WEIGHT_STRATEGIES["genre_first"]["genre"]
    assert genre_first > balanced


def test_score_song_rejects_unknown_mode():
    with pytest.raises(ValueError, match="Unknown scoring mode"):
        score_song({}, make_song(), mode="random")


def test_every_strategy_defines_every_weight():
    expected_keys = set(WEIGHT_STRATEGIES["balanced"])

    for mode, weights in WEIGHT_STRATEGIES.items():
        assert set(weights) == expected_keys, mode


def test_recommend_songs_returns_highest_scores_first_without_mutating_input():
    songs = [
        make_song(id=1, artist="A", genre="rock", energy=0.2),
        make_song(id=2, artist="B", genre="pop", energy=0.8),
    ]
    snapshot = [dict(song) for song in songs]

    results = recommend_songs({"genre": "pop", "energy": 0.8}, songs, k=2)

    assert [song["id"] for song, _, _ in results] == [2, 1]
    assert results[0][1] >= results[1][1]
    assert isinstance(results[0][2], str)
    assert songs == snapshot


def test_recommend_songs_penalizes_repeated_artist():
    songs = [
        make_song(id=1, artist="Same"),
        make_song(id=2, artist="Same"),
        make_song(id=3, artist="Other", energy=0.6),
    ]
    prefs = {"genre": "pop", "energy": 0.8}

    results = recommend_songs(prefs, songs, k=3)

    # Song 2 ties song 1 before penalty but loses 0.75 for the repeated artist.
    assert [song["id"] for song, _, _ in results] == [1, 3, 2]
    assert "Diversity penalty: artist Same" in results[2][2]


def test_recommend_songs_penalizes_third_song_of_same_genre():
    songs = [make_song(id=i, artist=f"Artist {i}") for i in range(1, 4)]

    results = recommend_songs({"genre": "pop"}, songs, k=3)

    assert results[2][1] == round(2.0 - 0.35, 2)
    assert "Diversity penalty: genre pop" in results[2][2]
    assert "Diversity penalty" not in results[1][2]


def test_recommend_songs_skips_penalties_when_diversity_disabled():
    songs = [make_song(id=1, artist="Same"), make_song(id=2, artist="Same")]

    results = recommend_songs({"genre": "pop"}, songs, k=2, apply_diversity=False)

    assert [score for _, score, _ in results] == [2.0, 2.0]


def test_recommend_songs_rejects_negative_k():
    with pytest.raises(ValueError, match="k must be non-negative"):
        recommend_songs({}, [make_song()], k=-1)
