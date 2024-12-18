from typing import Any, Dict, Iterable, List, Optional, Sequence, Type, Union

import numpy as np
from pathlib import Path

from fastembed.common import OnnxProvider
from fastembed.common.onnx_model import OnnxOutputContext
from fastembed.common.utils import define_cache_dir, normalize
from fastembed.text.onnx_text_model import OnnxTextModel, TextEmbeddingWorker
from fastembed.text.text_embedding_base import TextEmbeddingBase

supported_onnx_models = [
    {
        "model": "BAAI/bge-base-en",
        "dim": 768,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: necessary, 2023 year",
        "size_in_GB": 0.42,
        "sources": {
            "url": "https://storage.googleapis.com/qdrant-fastembed/fast-bge-base-en.tar.gz",
        },
        "model_file": "model_optimized.onnx",
    },
    {
        "model": "BAAI/bge-base-en-v1.5",
        "dim": 768,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: not so necessary, 2023 year",
        "size_in_GB": 0.21,
        "sources": {
            "url": "https://storage.googleapis.com/qdrant-fastembed/fast-bge-base-en-v1.5.tar.gz",
            "hf": "qdrant/bge-base-en-v1.5-onnx-q",
        },
        "model_file": "model_optimized.onnx",
    },
    {
        "model": "BAAI/bge-large-en-v1.5",
        "dim": 1024,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: not so necessary, 2023 year",
        "size_in_GB": 1.20,
        "sources": {
            "hf": "qdrant/bge-large-en-v1.5-onnx",
        },
        "model_file": "model.onnx",
    },
    {
        "model": "BAAI/bge-small-en",
        "dim": 384,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: necessary, 2023 year",
        "size_in_GB": 0.13,
        "sources": {
            "url": "https://storage.googleapis.com/qdrant-fastembed/BAAI-bge-small-en.tar.gz",
        },
        "model_file": "model_optimized.onnx",
    },
    {
        "model": "BAAI/bge-small-en-v1.5",
        "dim": 384,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: not so necessary, 2023 year",
        "size_in_GB": 0.067,
        "sources": {
            "hf": "qdrant/bge-small-en-v1.5-onnx-q",
        },
        "model_file": "model_optimized.onnx",
    },
    {
        "model": "BAAI/bge-small-zh-v1.5",
        "dim": 512,
        "description": "Text embeddings, Unimodal (text), Chinese, 512 input tokens truncation, Prefixes for queries/documents: not so necessary, 2023 year",
        "size_in_GB": 0.09,
        "sources": {
            "url": "https://storage.googleapis.com/qdrant-fastembed/fast-bge-small-zh-v1.5.tar.gz",
        },
        "model_file": "model_optimized.onnx",
    },
    {
        "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "dim": 384,
        "description": "Text embeddings, Unimodal (text), Multilingual (~50 languages), 512 input tokens truncation, Prefixes for queries/documents: not necessary, 2019 year",
        "size_in_GB": 0.22,
        "sources": {
            "hf": "qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q",
        },
        "model_file": "model_optimized.onnx",
    },
    {
        "model": "thenlper/gte-large",
        "dim": 1024,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: not necessary, 2023 year",
        "size_in_GB": 1.20,
        "sources": {
            "hf": "qdrant/gte-large-onnx",
        },
        "model_file": "model.onnx",
    },
    {
        "model": "mixedbread-ai/mxbai-embed-large-v1",
        "dim": 1024,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: necessary, 2024 year",
        "size_in_GB": 0.64,
        "sources": {
            "hf": "mixedbread-ai/mxbai-embed-large-v1",
        },
        "model_file": "onnx/model.onnx",
    },
    {
        "model": "snowflake/snowflake-arctic-embed-xs",
        "dim": 384,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: necessary, 2024 year",
        "size_in_GB": 0.09,
        "sources": {
            "hf": "snowflake/snowflake-arctic-embed-xs",
        },
        "model_file": "onnx/model.onnx",
    },
    {
        "model": "snowflake/snowflake-arctic-embed-s",
        "dim": 384,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: necessary, 2024 year",
        "size_in_GB": 0.13,
        "sources": {
            "hf": "snowflake/snowflake-arctic-embed-s",
        },
        "model_file": "onnx/model.onnx",
    },
    {
        "model": "snowflake/snowflake-arctic-embed-m",
        "dim": 768,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: necessary, 2024 year",
        "size_in_GB": 0.43,
        "sources": {
            "hf": "Snowflake/snowflake-arctic-embed-m",
        },
        "model_file": "onnx/model.onnx",
    },
    {
        "model": "snowflake/snowflake-arctic-embed-m-long",
        "dim": 768,
        "description": "Text embeddings, Unimodal (text), English, 2048 input tokens truncation, Prefixes for queries/documents: necessary, 2024 year",
        "size_in_GB": 0.54,
        "sources": {
            "hf": "snowflake/snowflake-arctic-embed-m-long",
        },
        "model_file": "onnx/model.onnx",
    },
    {
        "model": "snowflake/snowflake-arctic-embed-l",
        "dim": 1024,
        "description": "Text embeddings, Unimodal (text), English, 512 input tokens truncation, Prefixes for queries/documents: necessary, 2024 year",
        "size_in_GB": 1.02,
        "sources": {
            "hf": "snowflake/snowflake-arctic-embed-l",
        },
        "model_file": "onnx/model.onnx",
    },
]


class OnnxTextEmbedding(TextEmbeddingBase, OnnxTextModel[np.ndarray]):
    """Implementation of the Flag Embedding model."""

    @classmethod
    def list_supported_models(cls) -> List[Dict[str, Any]]:
        """
        Lists the supported models.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the model information.
        """
        return supported_onnx_models

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        cache_dir: Optional[str] = None,
        threads: Optional[int] = None,
        providers: Optional[Sequence[OnnxProvider]] = None,
        **kwargs,
    ):
        """
        Args:
            model_name (str): The name of the model to use.
            cache_dir (str, optional): The path to the cache directory.
                                       Can be set using the `FASTEMBED_CACHE_PATH` env variable.
                                       Defaults to `fastembed_cache` in the system's temp directory.
            threads (int, optional): The number of threads single onnxruntime session can use. Defaults to None.

        Raises:
            ValueError: If the model_name is not in the format <org>/<model> e.g. BAAI/bge-base-en.
        """

        super().__init__(model_name, cache_dir, threads, **kwargs)

        model_description = self._get_model_description(model_name)
        self.cache_dir = define_cache_dir(cache_dir)
        # model_dir = self.download_model(
        #     model_description, self.cache_dir, local_files_only=self._local_files_only
        # )
        # print(model_dir)
        # print(type(model_dir))
        # exit()
        model_dir = Path(model_description["model"])

        self.load_onnx_model(
            model_dir=model_dir,
            model_file=model_description["model_file"],
            threads=threads,
            providers=providers,
        )

    def embed(
        self,
        documents: Union[str, Iterable[str]],
        batch_size: int = 256,
        parallel: Optional[int] = None,
        **kwargs,
    ) -> Iterable[np.ndarray]:
        """
        Encode a list of documents into list of embeddings.
        We use mean pooling with attention so that the model can handle variable-length inputs.

        Args:
            documents: Iterator of documents or single document to embed
            batch_size: Batch size for encoding -- higher values will use more memory, but be faster
            parallel:
                If > 1, data-parallel encoding will be used, recommended for offline encoding of large datasets.
                If 0, use all available cores.
                If None, don't use data-parallel processing, use default onnxruntime threading instead.

        Returns:
            List of embeddings, one per document
        """
        yield from self._embed_documents(
            model_name=self.model_name,
            cache_dir=str(self.cache_dir),
            documents=documents,
            batch_size=batch_size,
            parallel=parallel,
            **kwargs,
        )

    @classmethod
    def _get_worker_class(cls) -> Type["TextEmbeddingWorker"]:
        return OnnxTextEmbeddingWorker

    def _preprocess_onnx_input(
        self, onnx_input: Dict[str, np.ndarray], **kwargs
    ) -> Dict[str, np.ndarray]:
        """
        Preprocess the onnx input.
        """
        return onnx_input

    def _post_process_onnx_output(self, output: OnnxOutputContext) -> Iterable[np.ndarray]:
        embeddings = output.model_output
        return normalize(embeddings[:, 0]).astype(np.float32)


class OnnxTextEmbeddingWorker(TextEmbeddingWorker):
    def init_embedding(
        self,
        model_name: str,
        cache_dir: str,
        **kwargs,
    ) -> OnnxTextEmbedding:
        return OnnxTextEmbedding(model_name=model_name, cache_dir=cache_dir, threads=1, **kwargs)
