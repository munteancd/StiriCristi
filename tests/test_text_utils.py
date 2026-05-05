from datetime import datetime

from generator.text_utils import (
    format_date_ro,
    year_to_words_ro,
    normalize_title_for_dedup,
    romanize_for_tts,
)


def test_format_date_ro_weekend():
    # 2026-04-19 is a Sunday
    assert format_date_ro(datetime(2026, 4, 19)) == "duminică, 19 aprilie"


def test_format_date_ro_weekday():
    # 2026-04-20 is a Monday
    assert format_date_ro(datetime(2026, 4, 20)) == "luni, 20 aprilie"


def test_year_to_words_ro_2026():
    assert year_to_words_ro(2026) == "două mii douăzeci și șase"


def test_year_to_words_ro_2000():
    assert year_to_words_ro(2000) == "două mii"


def test_year_to_words_ro_2010():
    assert year_to_words_ro(2010) == "două mii zece"


def test_normalize_title_strips_punctuation_and_lowercases():
    assert normalize_title_for_dedup("  Guvernul, adoptă Măsuri! ") == "guvernul adopta masuri"


def test_normalize_title_dedups_despite_diacritic_difference():
    a = normalize_title_for_dedup("Președintele Iohannis a declarat")
    b = normalize_title_for_dedup("Presedintele Iohannis a declarat")
    assert a == b


# ---------------------------------------------------------------------------
# romanize_for_tts
# ---------------------------------------------------------------------------

def test_romanize_football_clubs():
    assert romanize_for_tts("Manchester City a câștigat") == "Mencester Siti a câștigat"
    assert romanize_for_tts("Liverpool și Chelsea") == "Liverpul și Celsi"
    assert romanize_for_tts("Tottenham Hotspur") == "Totnăm Hotspur"


def test_romanize_prefers_longer_match():
    # "Manchester City" should not become "Mencester City" (wrong split)
    result = romanize_for_tts("Manchester City joacă")
    assert result == "Mencester Siti joacă"


def test_romanize_competitions():
    assert romanize_for_tts("Champions League și Premier League") == \
        "Ceampions Lig și Premier Lig"


def test_romanize_players():
    assert romanize_for_tts("Haaland a marcat") == "Holand a marcat"
    assert romanize_for_tts("Mbappé a dat gol") == "Mbape a dat gol"


def test_romanize_politicians():
    assert romanize_for_tts("Trump și Biden") == "Tramp și Baidăn"
    assert romanize_for_tts("Zelensky a declarat") == "Zelenski a declarat"


def test_romanize_cities():
    assert romanize_for_tts("la Washington") == "la Uașington"
    assert romanize_for_tts("în New York") == "în Niu Iork"
    assert romanize_for_tts("London") == "Londra"


def test_romanize_tech():
    assert romanize_for_tts("ChatGPT și OpenAI") == "Cet-Ji-Pi-Ti și Open-AI"
    assert romanize_for_tts("DeepSeek") == "Dip-Sik"
    assert romanize_for_tts("Gemini de la Google") == "Jemini de la Google"


def test_romanize_case_insensitive():
    # Input may have different casing if LLM doesn't capitalize properly.
    assert romanize_for_tts("liverpool") == "Liverpul"
    assert romanize_for_tts("LIVERPOOL") == "Liverpul"


def test_romanize_does_not_touch_pure_romanian():
    text = "Bună dimineața, Cristi. Astăzi este luni, cinci mai."
    assert romanize_for_tts(text) == text


def test_romanize_word_boundary_no_false_positive():
    # "Chelsey" is not "Chelsea" — should not be replaced.
    text = "Chelsey este un prenume."
    assert romanize_for_tts(text) == text
