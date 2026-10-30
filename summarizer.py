import re
from collections import Counter


def summarize_text(text, max_sentences=3):
    """
    Generate a simple extractive summary by selecting
    sentences containing the most frequent meaningful words.
    """

    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return "No article text was available to summarize."

    sentences = re.split(r"(?<=[.!?])\s+", text)

    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip().split()) >= 5
    ]

    if not sentences:
        return text[:500]

    stop_words = {
        "the", "is", "a", "an", "and", "or", "but",
        "in", "on", "at", "to", "of", "for", "with",
        "by", "from", "as", "are", "was", "were",
        "be", "been", "being", "it", "its", "this",
        "that", "these", "those", "they", "their",
        "he", "she", "we", "you", "i", "has", "have",
        "had", "will", "would", "can", "could", "not",
        "about", "into", "after", "before", "than"
    }

    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

    meaningful_words = [
        word for word in words
        if word not in stop_words
    ]

    frequencies = Counter(meaningful_words)

    if not frequencies:
        return " ".join(sentences[:max_sentences])

    scored_sentences = []

    for index, sentence in enumerate(sentences):
        sentence_words = re.findall(
            r"\b[a-zA-Z]{3,}\b",
            sentence.lower()
        )

        sentence_words = [
            word for word in sentence_words
            if word not in stop_words
        ]

        score = sum(
            frequencies[word]
            for word in sentence_words
        )

        scored_sentences.append((index, score, sentence))

    best_sentences = sorted(
        scored_sentences,
        key=lambda item: item[1],
        reverse=True
    )[:max_sentences]

    best_sentences.sort(key=lambda item: item[0])

    return " ".join(
        sentence for _, _, sentence in best_sentences
    )