# import sys
# from pathlib import Path
# FILE = Path(__file__).resolve()
# DIR = FILE.parents[0]
# if str(DIR) not in sys.path:
# 	sys.path.append(str(DIR))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase

class OutputGraphParam(ComponentParamBase):
    def __init__(self):
        super().__init__()

    def check(self,):
        self.check_positive_number(self.message_history_window_size, "History window size")

class OutputGraph(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- OUTPUT ---")
        ret = {}
        for i, inp in enumerate(inputs):
            ret[inp] = state[inp]
        return ret
