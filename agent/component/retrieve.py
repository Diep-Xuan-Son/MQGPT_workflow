import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))
ROOT2 = FILE.parents[2]
if str(ROOT2) not in sys.path:
    sys.path.append(str(ROOT2))

from abc import ABC
import time
import pandas as pd
from component.base_comp import ComponentBase, ComponentParamBase
from bm42.retrieval_qdrant_worker import RetrievalWorker

class RetrieveParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.collection_names = ["test2"]
        self.n_result = 10
        self.similarity_threshold = 0.4
        self.qdrant_url = "http://192.168.6.146:6333"
        self.minio_url = "192.168.6.146:9100"

    def check(self,):
        self.check_empty(self.collection_names, "[Retrieve] collection_names")
        self.check_positive_number(self.n_result, "[Retrieve] n_result")
        self.check_decimal_float(self.similarity_threshold, "[Retrieve] similarity_threshold")
        self.check_string(self.qdrant_url, "[Retrieve] qdrant_url")
        self.check_string(self.minio_url, "[Retrieve] minio_url")

class Retrieve(ComponentBase, ABC):
    def __init__(self, id, param):
        super().__init__(id, param)
        self.retw = RetrievalWorker(qdrant_url=self._param.qdrant_url, minio_url=self._param.minio_url)

    def __call__(self, inputs, outputs, state):
        """
        Retrieve documents
        Args:
            state (dict): The current graph state
        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        print("---RETRIEVE---")
        st_time = time.time()
        # sub_questions = state["sub_questions"]
        ret = {}
        if len(inputs)>len(outputs):
            inputs = inputs[:len(outputs)]
        for i, out in enumerate(outputs):
            if i>len(inputs)-1:
                ret[out] = "Don't have enough input"
                continue
            # Retrieval
            dt_retws, use_ctx = self.retw.query(collection_names=self._param.collection_names, \
                                                text_querys=state[inputs[i]], \
                                                n_result=self._param.n_result, \
                                                similarity_threshold=self._param.similarity_threshold)
            if not dt_retws[0]:
                documents = ["There's no knowledge fit with your question"]

            dfs = pd.DataFrame([])
            for i, dt in enumerate(dt_retws):
                df = pd.DataFrame(dt)
                df["ID"] = i
                dfs = pd.concat([dfs, df], ignore_index=True)
            # dfs = dfs.groupby('ID')['description'].agg('\n\t'.join).reset_index()
            documents = list(dfs.to_dict()['description'].values())
            ret[out] = documents
        print(f"----Duration: {time.time()-st_time}")
        return ret
