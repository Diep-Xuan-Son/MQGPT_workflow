import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
import pandas as pd
from scholarly import scholarly

class GoogleScholarParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.top_n = 6
        self.sort_by = 'relevance'
        self.year_low = None
        self.year_high = None
        self.patents = True

    def check(self,):
        self.check_positive_integer(self.top_n, "Top N")
        self.check_valid_value(self.sort_by, "GoogleScholar Sort_by", ['date', 'relevance'])
        self.check_boolean(self.patents, "Whether or not to include patents, defaults to True")

class GoogleScholar(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- GoogleScholar ---")

        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            # try:
            scholar_client = scholarly.search_pubs(state[inputs[i]], patents=self._param.patents, year_low=self._param.year_low,
                                               year_high=self._param.year_high, sort_by=self._param.sort_by)
            scholar_res = []
            for i in range(self._param.top_n):
                try:
                    pub = next(scholar_client)
                    scholar_res.append('Title: ' + pub['bib']['title'] + '\n_Url: <a href="' + pub[
                        'pub_url'] + '"></a> ' + "\n author: " + ",".join(pub['bib']['author']) + '\n Abstract: ' + pub[
                                                       'bib'].get('abstract', 'no abstract'))

                except StopIteration or Exception as e:
                    scholar_res.append("**ERROR** " + str(e))
                    break
            ret[out] = scholar_res
            if not scholar_res:
                ret[out] = ""
            # except Exception as e:
            #     ret[out] = "**Error**:" + str(e)
        return ret

if __name__=="__main__":
    param = GoogleScholarParam()
    googlescholar = GoogleScholar(0,param)
    output = googlescholar(["question"], ["output"], {"question": "yolov8"})
    print(output)