from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton model between tests."""
    import autoapply.ai.utils.Embedder as embedder_module
    embedder_module._singleton_model = None
    yield
    embedder_module._singleton_model = None


def _make_mock_model(dim: int = 384) -> MagicMock:
    import numpy as np
    mock_model = MagicMock()
    mock_model.encode.side_effect = lambda texts, **kwargs: np.array(
        [[0.1] * dim for _ in texts]
    )
    return mock_model


@patch("autoapply.ai.utils.Embedder.SentenceTransformer")
def test_embed_text_returns_list_of_floats(mock_st):
    mock_st.return_value = _make_mock_model()
    from autoapply.ai.utils.Embedder import Embedder

    result = Embedder.embed_text("hello world")

    assert isinstance(result, list)
    assert len(result) == 384
    assert all(isinstance(v, float) for v in result)


@patch("autoapply.ai.utils.Embedder.SentenceTransformer")
def test_embed_texts_returns_one_vector_per_input(mock_st):
    mock_st.return_value = _make_mock_model()
    from autoapply.ai.utils.Embedder import Embedder

    texts = ["first", "second", "third"]
    results = Embedder.embed_texts(texts)

    assert len(results) == 3
    assert all(len(v) == 384 for v in results)


@patch("autoapply.ai.utils.Embedder.SentenceTransformer")
def test_model_loaded_only_once(mock_st):
    mock_st.return_value = _make_mock_model()
    from autoapply.ai.utils.Embedder import Embedder

    Embedder.embed_text("first call")
    Embedder.embed_text("second call")

    mock_st.assert_called_once()
