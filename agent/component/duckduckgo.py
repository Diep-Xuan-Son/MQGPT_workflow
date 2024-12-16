import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
from duckduckgo_search import DDGS

class DuckDuckGoParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.top_n = 1
        self.channel = "text"

    def check(self,):
        self.check_positive_integer(self.top_n, "Top N")
        self.check_valid_value(self.channel, "Web Search or News", ["text", "news"])

class DuckDuckGo(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- DUCKDUCKGO ---")
        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            try:
                if self._param.channel == "text":
                    with DDGS() as ddgs:
                        # {'title': '', 'href': '', 'body': ''}
                        duck_res = ['<a href="' + i["href"] + '">' + i["title"] + '</a>    ' + i["body"] for i
                                    in ddgs.text(state[inputs[i]], max_results=self._param.top_n)]
                elif self._param.channel == "news":
                    with DDGS() as ddgs:
                        # {'date': '', 'title': '', 'body': '', 'url': '', 'image': '', 'source': ''}
                        duck_res = ['<a href="' + i["url"] + '">' + i["title"] + '</a>    ' + i["body"] for i
                                    in ddgs.news(state[inputs[i]], max_results=self._param.top_n)]
                ret[out] = duck_res
                if not duck_res:
                    ret[out] = ""
            except Exception as e:
                ret[out] = "**Error**:" + str(e)
        return ret

if __name__=="__main__":
    param = DuckDuckGoParam()
    duckduckgo = DuckDuckGo(0,param)
    output = duckduckgo(["question"], ["output"], {"question": "yolov8"})
    print(output)