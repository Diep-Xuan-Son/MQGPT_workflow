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
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from component.base_comp import ComponentBase, ComponentParamBase
from settings import GROQ_API_KEY, LLM_MODEL_NAME

class RetrievalGrader(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

class GradeDocumentsParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.temperature = 0
        self.groq_api_key = GROQ_API_KEY
        self.model_name = LLM_MODEL_NAME
        self.prompt = "Retrieved document: \n\n {retrieve_0_documents} \n\n User question: {input_0_question}"

    def check(self,):
        self.check_nonnegative_number(self.temperature, "[GradeDocuments] temperature")
        self.check_string(self.groq_api_key, "[GradeDocuments] groq_api_key")
        self.check_string(self.model_name, "[GradeDocuments] model_name")
        self.check_string(self.prompt, "[GradeDocuments] prompt")

class GradeDocuments(ComponentBase, ABC):
    def __init__(self, id, param):
        super().__init__(id, param)
        self.llm = ChatGroq(temperature=self._param.temperature, groq_api_key=self._param.groq_api_key, model_name=self._param.model_name)
        retrieval_grader = self.llm.with_structured_output(RetrievalGrader)
        # Prompt
        system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
            It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
            If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
        grade_prompt = ChatPromptTemplate.from_messages(
            [
             
                ("system", system),
                ("human", self._param.prompt),
            ]
        )
        self.retrieval_grader = grade_prompt | retrieval_grader

    def __call__(self, inputs, outputs, state):
        """
        Determines whether the retrieved documents are relevant to the question.
        Args:
            state (dict): The current graph state
        Returns:
            state (dict): Updates documents key with only filtered relevant documents
        """
        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        st_time = time.time()
        # question = state["question"]
        # documents = state["documents"]
        ret = {}
        for i, out in enumerate(outputs):
            data_inp = {}
            docs_id = ""
            for inp in inputs:
                if not isinstance(state[inp], list):
                    data_inp[inp] = state[inp]
                else:
                    docs_id = inp
            # Score each doc
            filtered_docs = []
            for d in state[docs_id]:
                data_inp[docs_id] = d
                score = self.retrieval_grader.invoke(data_inp)
                grade = score.binary_score
                if grade == "yes":
                    print("GRADE: DOCUMENT RELEVANT")
                    filtered_docs.append(d)
                else:
                    print("GRADE: DOCUMENT NOT RELEVANT")
                    continue
            ret[out] = filtered_docs
        print(f"----Duration: {time.time()-st_time}")
        return ret
