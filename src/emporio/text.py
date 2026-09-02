"""Text helpers shared by the policy index and the product search."""

import re
import unicodedata

STOPWORDS = {
    "a", "à", "ao", "aos", "as", "às", "com", "como", "da", "das", "de", "do",
    "dos", "e", "em", "na", "nas", "no", "nos", "o", "os", "ou", "para", "pela",
    "pelo", "por", "que", "se", "sem", "ser", "sobre", "um", "uma", "eu", "meu",
    "minha", "posso", "quero", "qual", "quais", "quanto", "tem", "voces", "loja",
    "ate", "mais", "menos", "reais",
}

PLURAL_ENDINGS = [("oes", "ao"), ("aes", "ao"), ("eis", "el"), ("ns", "m"),
                  ("res", "r"), ("zes", "z"), ("ses", "s")]


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def singular(word: str) -> str:
    """Rough singular form, enough to make "violões" find "violão"."""
    for plural, base in PLURAL_ENDINGS:
        if word.endswith(plural) and len(word) > len(plural) + 1:
            return word[: -len(plural)] + base
    if word.endswith("s") and len(word) > 3:
        return word[:-1]
    return word


def stem(text: str) -> list[str]:
    """Words cut to a five letter prefix, for the policy index.

    Portuguese inflects heavily and the customer never uses the wording of the
    manual: they write "me arrependi", the manual says "arrependimento". A prefix
    is a blunt stemmer, but at this corpus size it buys the recall that matters
    without pulling in a stemming dependency.
    """
    words = re.findall(r"[a-z0-9]+", normalize(text))
    return [word[:5] for word in words if word not in STOPWORDS and len(word) > 1]


def search_terms(query: str) -> list[str]:
    """Meaningful singular words of a product query, numbers dropped.

    Amounts belong in the min_price and max_price arguments; matching "1000"
    against product text would only produce noise.
    """
    words = re.findall(r"[a-z0-9]+", normalize(query))
    terms = []
    for word in words:
        if word.isdigit() or word in STOPWORDS or len(word) < 3:
            continue
        terms.append(singular(word))
    return terms


def searchable(text: str) -> str:
    """Product text reduced to the same shape as the query terms."""
    return " ".join(singular(word) for word in re.findall(r"[a-z0-9]+", normalize(text)))
