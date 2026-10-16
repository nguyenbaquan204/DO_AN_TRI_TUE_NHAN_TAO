from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TfidfMatcher:
    @staticmethod
    def score(cv_text: str, jd_text: str) -> float:
        if not cv_text or not jd_text:
            return 0.0
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([cv_text, jd_text])
        similarity = cosine_similarity(matrix[0], matrix[1])[0][0]
        return float(similarity)
