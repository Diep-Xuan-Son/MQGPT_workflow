# import sys
# from pathlib import Path
# FILE = Path(__file__).resolve()
# DIR = FILE.parents[0]
# if str(DIR) not in sys.path:
# 	sys.path.append(str(DIR))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase

class ConditionParam(ComponentParamBase):
    def __init__(self):
        super().__init__()

    def check(self,):
        self.check_positive_number(self.message_history_window_size, "History window size")

class Condition(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- ASSESS GRADED DOCUMENTS ---")
        filtered_documents = state[inputs[0]]
        # filtered_documents = state["grade_documents_0_filtered_docs"]

        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            print(
                "DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY"
            )
            return "transform_query_0"
        # We have relevant documents, so generate answer
        print("DECISION: GENERATE")
        return "generate_0"
