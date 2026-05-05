import re
import unicodedata
from datetime import datetime
from typing import List, Tuple

WEEKDAYS_RO = [
    "luni", "marți", "miercuri", "joi", "vineri", "sâmbătă", "duminică",
]
MONTHS_RO = [
    "ianuarie", "februarie", "martie", "aprilie", "mai", "iunie",
    "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie",
]
UNITS_RO = [
    "", "unu", "doi", "trei", "patru", "cinci", "șase", "șapte", "opt", "nouă",
    "zece", "unsprezece", "doisprezece", "treisprezece", "paisprezece",
    "cincisprezece", "șaisprezece", "șaptesprezece", "optsprezece", "nouăsprezece",
]
TENS_RO = [
    "", "", "douăzeci", "treizeci", "patruzeci", "cincizeci",
    "șaizeci", "șaptezeci", "optzeci", "nouăzeci",
]


def format_date_ro(dt: datetime) -> str:
    return f"{WEEKDAYS_RO[dt.weekday()]}, {dt.day} {MONTHS_RO[dt.month - 1]}"


def _two_digits_to_words_ro(n: int) -> str:
    if n == 0:
        return ""
    if n < 20:
        return UNITS_RO[n]
    tens, unit = divmod(n, 10)
    if unit == 0:
        return TENS_RO[tens]
    return f"{TENS_RO[tens]} și {UNITS_RO[unit]}"


def year_to_words_ro(year: int) -> str:
    if year < 2000 or year >= 3000:
        raise ValueError(f"Only years 2000-2999 supported, got {year}")
    remainder = year - 2000
    if remainder == 0:
        return "două mii"
    rest = _two_digits_to_words_ro(remainder)
    return f"două mii {rest}"


# ---------------------------------------------------------------------------
# Foreign-word → Romanian phonetic substitution table.
# Used as a deterministic safety-net AFTER LLM generation to catch any
# foreign terms the model forgot to transliterate per the system prompt.
# Multi-word phrases must come before their component single words so the
# longest match wins.
# ---------------------------------------------------------------------------
_PHONETICS_RAW: List[Tuple[str, str]] = [
    # --- English Premier League clubs ---
    ("Manchester City",         "Mencester Siti"),
    ("Manchester United",       "Mencester Iunaitid"),
    ("Liverpool",               "Liverpul"),
    ("Chelsea",                 "Celsi"),
    ("Arsenal",                 "Arsnăl"),
    ("Tottenham Hotspur",       "Totnăm Hotspur"),
    ("Tottenham",               "Totnăm"),
    ("Leicester City",          "Lestăr Siti"),
    ("Leicester",               "Lestăr"),
    ("Newcastle United",        "Niucasăl Iunaitid"),
    ("Newcastle",               "Niucasăl"),
    ("Nottingham Forest",       "Notingăm Forest"),
    ("Nottingham",              "Notingăm"),
    ("Crystal Palace",          "Cristăl Palăs"),
    ("Bournemouth",             "Bornmăth"),
    ("Wolverhampton Wanderers", "Ulverhampton Uondererz"),
    ("Wolverhampton",           "Ulverhampton"),
    ("West Ham United",         "Uest Ham Iunaitid"),
    ("West Ham",                "Uest Ham"),
    ("Sheffield United",        "Șefild Iunaitid"),
    ("Sheffield Wednesday",     "Șefild Uenzdei"),
    ("Sheffield",               "Șefild"),
    ("Fulham",                  "Fulăm"),
    ("Luton Town",              "Luton Taun"),
    ("Aston Villa",             "Aston Vila"),
    ("Brighton",                "Braiton"),
    ("Everton",                 "Everton"),
    ("Brentford",               "Brentford"),
    # --- Other European clubs ---
    ("Bayern München",          "Baiărn Miunhen"),
    ("Bayern Munich",           "Baiărn Miunhen"),
    ("Bayern",                  "Baiărn"),
    ("Borussia Dortmund",       "Borusia Dortmund"),
    ("Paris Saint-Germain",     "Paris Sengermen"),
    ("Atlético Madrid",         "Atletico Madrid"),
    ("Real Madrid",             "Rial Madrid"),
    ("Juventus",                "Iuventus"),
    ("Celtic",                  "Seltik"),
    ("Rangers",                 "Reingers"),
    ("PSG",                     "Pe-Se-Je"),
    # --- Competitions ---
    ("Champions League",        "Ceampions Lig"),
    ("Europa League",           "Europa Lig"),
    ("Conference League",       "Conferens Lig"),
    ("Premier League",          "Premier Lig"),
    # --- Players ---
    ("Haaland",                 "Holand"),
    ("Mbappé",                  "Mbape"),
    ("Mbappe",                  "Mbape"),
    ("Bellingham",              "Belingăm"),
    ("Foden",                   "Fodăn"),
    ("Rashford",                "Rașford"),
    ("De Bruyne",               "De Bruin"),
    ("Vinicius",                "Vinicitus"),
    ("Rodrygo",                 "Rodrigo"),
    ("Salah",                   "Salah"),
    ("Saka",                    "Saka"),
    # --- Politicians / world leaders ---
    ("Netanyahu",               "Netaniahu"),
    ("Zelenskyy",               "Zelenski"),
    ("Zelensky",                "Zelenski"),
    ("Biden",                   "Baidăn"),
    ("Trump",                   "Tramp"),
    ("Macron",                  "Macron"),
    # --- Cities (English form → Romanian form) ---
    ("New York",                "Niu Iork"),
    ("Washington",              "Uașington"),
    ("Los Angeles",             "Los Angeleș"),
    ("Chicago",                 "Șicago"),
    ("London",                  "Londra"),
    ("Moscow",                  "Moscova"),
    ("Brussels",                "Bruxelles"),
    ("Beijing",                 "Beidjing"),
    # --- AI / Tech ---
    ("ChatGPT",                 "Cet-Ji-Pi-Ti"),
    ("OpenAI",                  "Open-AI"),
    ("DeepSeek",                "Dip-Sik"),
    ("GitHub",                  "Ghit-Hab"),
    ("LinkedIn",                "Linkt-In"),
    ("Gemini",                  "Jemini"),
    ("Copilot",                 "Copailot"),
]

# Pre-compile patterns sorted by descending phrase length (longest match wins).
_PHONETICS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(foreign) + r"\b", re.IGNORECASE), phonetic)
    for foreign, phonetic in sorted(
        _PHONETICS_RAW, key=lambda p: len(p[0]), reverse=True
    )
]


def romanize_for_tts(text: str) -> str:
    """Replace known foreign words with Romanian phonetic equivalents.

    Deterministic safety-net applied after LLM generation, for terms the
    model failed to transliterate per the system prompt instructions.
    """
    for pattern, phonetic in _PHONETICS:
        text = pattern.sub(phonetic, text)
    return text


def normalize_title_for_dedup(title: str) -> str:
    # Strip diacritics, lowercase, remove punctuation, collapse whitespace.
    nfkd = unicodedata.normalize("NFKD", title)
    no_diacritics = "".join(c for c in nfkd if not unicodedata.combining(c))
    lowered = no_diacritics.lower()
    no_punct = re.sub(r"[^\w\s]", " ", lowered)
    collapsed = re.sub(r"\s+", " ", no_punct).strip()
    return collapsed
