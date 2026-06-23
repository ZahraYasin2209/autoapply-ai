from sentence_transformers import SentenceTransformer

from config.settings.base import EMBEDDING_MODEL

_singleton_model: SentenceTransformer | None = None


class Embedder:
    @staticmethod
    def get_model() -> SentenceTransformer:
        global _singleton_model
        if _singleton_model is None:
            _singleton_model = SentenceTransformer(EMBEDDING_MODEL)
        return _singleton_model

    @staticmethod
    def embed_texts(texts: list[str]) -> list[list[float]]:
        sentence_model = Embedder.get_model()
        return sentence_model.encode(texts, convert_to_numpy=True).tolist()

    @staticmethod
    def embed_text(text: str) -> list[float]:
        return Embedder.embed_texts([text])[0]
