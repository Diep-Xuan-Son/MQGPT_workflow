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

class TransformQueryParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.temperature = 0
        self.groq_api_key = GROQ_API_KEY
        self.model_name = LLM_MODEL_NAME
        self.prompt = "Here is the initial question: \n\n {question} \n Formulate an improved question."

    def check(self,):
        self.check_nonnegative_number(self.temperature, "[TransformQuery] temperature")
        self.check_string(self.groq_api_key, "[TransformQuery] groq_api_key")
        self.check_string(self.model_name, "[TransformQuery] model_name")
        self.check_string(self.prompt, "[TransformQuery] prompt")

class TransformQuery(ComponentBase, ABC):
    def __init__(self, id, param):
        super().__init__(id, param)
        self.llm = ChatGroq(temperature=self._param.temperature, groq_api_key=self._param.groq_api_key, model_name=self._param.model_name)
        # Prompt
        system = """You a question re-writer that converts an input question to a better version that is optimized \n 
             for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", self._param.prompt),
            ]
        )
        self.question_rewriter = re_write_prompt | self.llm | StrOutputParser()

    def __call__(self, inputs, outputs, state):
        """
        Transform the query to produce a better question.
        Args:
            state (dict): The current graph state
        Returns:
            state (dict): Updates question key with a re-phrased question
        """

        print("---TRANSFORM QUERY---")
        ret = {}
        if len(inputs)>len(outputs):
            inputs = inputs[:len(outputs)]
        for i, out in enumerate(outputs):
            if i>len(inputs)-1:
                ret[out] = "Don't have enough input"
                continue
            # Re-write question
            better_question = self.question_rewriter.invoke(state[inputs[i]])
            ret[out] = better_question

        return ret
