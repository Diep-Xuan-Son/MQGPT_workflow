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
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from component.base_comp import ComponentBase, ComponentParamBase
from settings import GROQ_API_KEY, LLM_MODEL_NAME

class GenerateParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.temperature = 0
        self.groq_api_key = GROQ_API_KEY
        self.model_name = LLM_MODEL_NAME
        self.prompt = "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. The answer write in Vietnamese.\nQuestion: {input_0_question} \nContext: {grade_documents_0_filtered_docs} \nAnswer:"

    def check(self,):
        self.check_nonnegative_number(self.temperature, "[Generate] temperature")
        self.check_string(self.groq_api_key, "[Generate] groq_api_key")
        self.check_string(self.model_name, "[Generate] model_name")
        self.check_string(self.prompt, "[Generate] prompt")

class Generate(ComponentBase, ABC):
    def __init__(self, id, param):
        super().__init__(id, param)
        self.llm = ChatGroq(temperature=self._param.temperature, groq_api_key=self._param.groq_api_key, model_name=self._param.model_name)
        prompt_rag = ChatPromptTemplate.from_messages(
            [
                ("human", self._param.prompt),
            ]
        )
        self.rag_chain = prompt_rag | self.llm | StrOutputParser()

    def __call__(self, inputs, outputs, state):
        """
        Generate answer
        Args:
            state (dict): The current graph state
        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        print("---GENERATE---")
        st_time = time.time()
        # question = state["question"]
        # documents = state["documents"]
        ret = {}
        for i, out in enumerate(outputs):
            data_inp = {}
            for inp in inputs:
                data_inp[inp] = state[inp]
            print(data_inp)
            # RAG generation
            generation = self.rag_chain.invoke(data_inp)
            ret[out] = generation
        print(f"----Duration: {time.time()-st_time}")
        return ret
