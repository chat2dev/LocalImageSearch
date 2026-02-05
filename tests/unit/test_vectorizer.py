"""
Text vector化服务单元测试
"""
import pytest
import numpy as np
from src.services.text_vectorizer import SentenceBERTVectorizer
from src.config.settings import settings


class TestSentenceBERTVectorizer:
    """Test Sentence-BERT vectorizer"""

    @pytest.fixture(scope="class")
    def vectorizer(self):
        """创建向量化器实例"""
        return SentenceBERTVectorizer()

    def test_initialization(self, vectorizer):
        """测试向量化器初始化"""
        assert vectorizer is not None
        assert vectorizer.model is not None
        assert vectorizer.model_name == settings.VECTORIZER_MODEL

    def test_vectorize_text_basic(self, vectorizer):
        """测试基本Text vector化功能"""
        text = "风景,山脉,天空"
        vector = vectorizer.vectorize_text(text)

        assert isinstance(vector, np.ndarray)
        assert vector.shape == (settings.FAISS_DIMENSION,)
        assert not np.all(vector == 0)

    def test_vectorize_text_empty(self, vectorizer):
        """测试空Text vector化"""
        vector = vectorizer.vectorize_text("")
        assert isinstance(vector, np.ndarray)
        assert vector.shape == (settings.FAISS_DIMENSION,)
        assert np.all(vector == 0)

    def test_vectorize_text_whitespace(self, vectorizer):
        """测试纯空白Text vector化"""
        vector = vectorizer.vectorize_text("   ")
        assert isinstance(vector, np.ndarray)
        assert vector.shape == (settings.FAISS_DIMENSION,)
        assert np.all(vector == 0)

    def test_vectorize_tags_basic(self, vectorizer):
        """测试List of tags向量化"""
        tags = ["风景", "山脉", "天空"]
        vector = vectorizer.vectorize_tags(tags)

        assert isinstance(vector, np.ndarray)
        assert vector.shape == (settings.FAISS_DIMENSION,)
        assert not np.all(vector == 0)

    def test_vectorize_tags_empty(self, vectorizer):
        """测试空List of tags向量化"""
        vector = vectorizer.vectorize_tags([])
        assert isinstance(vector, np.ndarray)
        assert vector.shape == (settings.FAISS_DIMENSION,)
        assert np.all(vector == 0)

    def test_vectorize_tags_single(self, vectorizer):
        """测试单个Tag vector化"""
        tags = ["风景"]
        vector = vectorizer.vectorize_tags(tags)

        assert isinstance(vector, np.ndarray)
        assert vector.shape == (settings.FAISS_DIMENSION,)
        assert not np.all(vector == 0)

    def test_vectorize_texts_batch(self, vectorizer):
        """测试批量Text vector化"""
        texts = ["风景,山脉", "动物,狗", "建筑,高楼"]
        vectors = vectorizer.vectorize_texts(texts)

        assert isinstance(vectors, np.ndarray)
        assert vectors.shape == (3, settings.FAISS_DIMENSION)

        for i, vector in enumerate(vectors):
            assert not np.all(vector == 0), f"Vector {i} is all zeros"

    def test_vectorize_texts_with_empty(self, vectorizer):
        """Test batch vectorization with empty texts"""
        texts = ["风景,山脉", "", "动物,狗"]
        vectors = vectorizer.vectorize_texts(texts)

        assert isinstance(vectors, np.ndarray)
        assert vectors.shape == (3, settings.FAISS_DIMENSION)

        # 第一个和第三个向量应该非零，第二个向量应该全零
        assert not np.all(vectors[0] == 0)
        assert np.all(vectors[1] == 0)
        assert not np.all(vectors[2] == 0)

    def test_similar_texts_similar_vectors(self, vectorizer):
        """Test vector similarity for similar texts"""
        text1 = "风景,山脉,天空"
        text2 = "山脉,风景,蓝天"
        text3 = "动物,狗,猫"

        vector1 = vectorizer.vectorize_text(text1)
        vector2 = vectorizer.vectorize_text(text2)
        vector3 = vectorizer.vectorize_text(text3)

        # 计算余弦相似度
        def cosine_similarity(v1, v2):
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

        sim12 = cosine_similarity(vector1, vector2)
        sim13 = cosine_similarity(vector1, vector3)
        sim23 = cosine_similarity(vector2, vector3)

        assert sim12 > sim13
        assert sim12 > sim23
        assert sim13 > 0  # 即使不同类别的文本也会有一定的相似度
