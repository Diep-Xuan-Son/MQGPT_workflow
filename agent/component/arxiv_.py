import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
import arxiv

class ArXivParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.top_n = 2
        self.sort_by = 'submittedDate'

    def check(self,):
        self.check_positive_integer(self.top_n, "Top N")
        self.check_valid_value(self.sort_by, "ArXiv Search Sort_by",
                               ['submittedDate', 'lastUpdatedDate', 'relevance'])

class ArXiv(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- ARXIV ---")
        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            sort_choices = {"relevance": arxiv.SortCriterion.Relevance,
                            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
                            'submittedDate': arxiv.SortCriterion.SubmittedDate}
            arxiv_client = arxiv.Client()
            search = arxiv.Search(
                query=state[inputs[i]],
                max_results=self._param.top_n,
                sort_by=sort_choices[self._param.sort_by]
            )

            arxiv_res = [
                'Title: ' + i.title + '\nPdf_Url: <a href="' + i.pdf_url + '"></a> \nSummary: ' + i.summary for
                i in list(arxiv_client.results(search))]
            ret[out] = arxiv_res
            if not arxiv_res:
                ret[out] = ""
        return ret

if __name__=="__main__":
    param = ArXivParam()
    arx = ArXiv(0,param)
    output = arx(["question"], ["output"], {"question": "yolov8"})
    print(output)
