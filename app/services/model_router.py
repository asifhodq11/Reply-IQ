"""
app/services/model_router.py

Implements the Smart Model Router defined in Chapter 6.
Classifies review complexity and returns the exact model string to use.
"""

# Exact list from Chapter 6 of the Bible
CRISIS_WORDS = [
    "lawyer",
    "lawsuit",
    "health department",
    "food poisoning",
    "poison",
    "sick",
    "ill",
    "police",
    "illegal",
    "sue",
    "sued",
    "attorney",
    "court",
    "legal action",
    "report you",
    "shut down",
]


def classify_complexity(star_rating: int, review_text: str) -> str:
    """
    Returns one of: 'crisis', 'simple', 'standard'.
    """
    text = (review_text or "").lower()
    word_count = len(text.split())

    # Pass 1: Crisis check — supersedes everything else
    if star_rating <= 2 and any(w in text for w in CRISIS_WORDS):
        return "crisis"

    # Pass 2: Simple check (5 stars, short, practically no text)
    if star_rating == 5 and word_count < 30:
        return "simple"

    # Pass 3: Standard — everything else
    return "standard"


def get_model_for_complexity(complexity: str) -> str:
    """
    Maps the complexity string to the actual API model name.
    """
    mapping = {
        "crisis": "gpt-4o",  # OpenAI GPT-4o Full
        "simple": "gemini-2.0-flash-lite-preview-02-05",  # Google Gemini 2.0 Flash-Lite
        "standard": "gpt-4o-mini",  # OpenAI GPT-4o-mini (Quality Floor)
    }
    # Fallback safely to standard if unknown
    return mapping.get(complexity, "gpt-4o-mini")
