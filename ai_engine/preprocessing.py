import re
import string
from typing import List, Tuple
import numpy as np


# Common English stop words
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}


def clean_text(text: str) -> str:
    """
    Normalizes text for NLP processing by removing irregular whitespace,
    URLs, emails, and special characters while preserving domain acronyms (e.g. C++, .NET).
    """
    if not isinstance(text, str):
        return ""

    # Replace newlines and tabs
    text = re.sub(r"[\r\n\t]+", " ", text)

    # Protect key programming language terms
    text = re.sub(r"\bC\+\+\b", "CPP_TOKEN", text, flags=re.IGNORECASE)
    text = re.sub(r"\bC#\b", "CSHARP_TOKEN", text, flags=re.IGNORECASE)
    text = re.sub(r"\.NET\b", "DOTNET_TOKEN", text, flags=re.IGNORECASE)

    # Remove URLs and email addresses
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)

    # Strip symbols but retain alphanumeric and protected tokens
    text = re.sub(r"[^\w\s]", " ", text)

    # Restore protected tokens
    text = text.replace("CPP_TOKEN", "C++")
    text = text.replace("CSHARP_TOKEN", "C#")
    text = text.replace("DOTNET_TOKEN", ".NET")

    # Lowercase and normalize whitespace
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize_words(text: str, remove_stopwords: bool = True) -> List[str]:
    """Tokenizes text into words with optional stopword filtering."""
    cleaned = clean_text(text)
    tokens = [token for token in cleaned.split() if len(token) > 1]
    if remove_stopwords:
        tokens = [token for token in tokens if token not in STOP_WORDS]
    return tokens


def cosine_similarity_score(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Computes cosine similarity between two 1D or 2D vectors."""
    v1 = np.ravel(vec1)
    v2 = np.ravel(vec2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))
