import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
from Bio import Entrez
import xml.etree.ElementTree as ET

class PubMedParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.top_n = 5
        self.email = "A.N.Other@example.com"

    def check(self,):
        self.check_positive_integer(self.top_n, "Top N")

class PubMed(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- PubMed ---")

        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            try:
                Entrez.email = self._param.email
                pubmedids = Entrez.read(Entrez.esearch(db='pubmed', retmax=self._param.top_n, term=state[inputs[i]]))['IdList']
                pubmedcnt = ET.fromstring(
                    Entrez.efetch(db='pubmed', id=",".join(pubmedids), retmode="xml").read().decode("utf-8"))
                pubmed_res = ['Title:' + child.find("MedlineCitation").find("Article").find(
                    "ArticleTitle").text + '\nUrl:<a href=" https://pubmed.ncbi.nlm.nih.gov/' + child.find(
                    "MedlineCitation").find("PMID").text + '">' + '</a>\n' + 'Abstract:' + child.find(
                    "MedlineCitation").find("Article").find("Abstract").find("AbstractText").text for child in
                              pubmedcnt.findall("PubmedArticle")]
                ret[out] = pubmed_res
                if not pubmed_res:
                    ret[out] = ""
            except Exception as e:
                ret[out] = "**Error**:" + str(e)
        return ret

if __name__=="__main__":
    param = PubMedParam()
    pubmed = PubMed(0,param)
    output = pubmed(["question"], ["output"], {"question": "yolov8"})
    print(output)