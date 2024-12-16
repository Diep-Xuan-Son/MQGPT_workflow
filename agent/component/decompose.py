import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
import time
from typing import Literal, Optional, Tuple, List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from component.base_comp import ComponentBase, ComponentParamBase
from settings import GROQ_API_KEY, LLM_MODEL_NAME

class SubQuery(BaseModel):
    """Given a user question, break it down into distinct sub questions that \
    you need to answer in order to answer the original question. Sub questions write in Vietnamese"""
    questions: List[str] = Field(description="The list of sub questions")

class DecomposeParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.temperature = 0
        self.groq_api_key = GROQ_API_KEY
        self.model_name = LLM_MODEL_NAME

    def check(self,):
        self.check_nonnegative_number(self.temperature, "[Decompose] temperature")
        self.check_string(self.groq_api_key, "[Decompose] groq_api_key")
        self.check_string(self.model_name, "[Decompose] model_name")

class Decompose(ComponentBase, ABC):
    def __init__(self, id, param):
        super().__init__(id, param)
        self.llm = ChatGroq(temperature=self._param.temperature, groq_api_key=self._param.groq_api_key, model_name=self._param.model_name)
        self.sub_question_generator = self.llm.with_structured_output(SubQuery)

    def __call__(self, inputs, outputs, state):
        """
        Retrieve documents
        Args:
            state (dict): The current graph state
        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        print("--- QUERY DECOMPOSITION ---")
        st_time = time.time()
        ret = {}
        if len(inputs)>len(outputs):
            inputs = inputs[:len(outputs)]
        for i, out in enumerate(outputs):
            if i>len(inputs)-1:
                ret[out] = "Don't have enough input"
                continue
            # Reranking
            ret[out] = self.sub_question_generator.invoke(state[inputs[i]]).questions
        print(f"----Duration: {time.time()-st_time}")
        return ret
