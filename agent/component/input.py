import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase

class InputGraphParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.prologue = "Hi there!"
        self.key_input = "question"

    def check(self,):
        self.check_positive_number(self.message_history_window_size, "History window size")
        self.check_string(self.prologue, "[InputGraph] prologue")

class InputGraph(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- INPUT ---")
        ret = {}
        for i, out in enumerate(outputs):
            ret[out] = state[out]
        return ret
