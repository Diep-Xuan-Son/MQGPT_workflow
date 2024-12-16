import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
# from langchain_community.tools import WikipediaQueryRun
# from langchain_community.utilities import WikipediaAPIWrapper
import wikipedia

class WikipediaParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.top_n = 1
        self.language = "vi"
        # self.wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

    def check(self,):
        self.check_positive_integer(self.top_n, "Top N")
        self.check_valid_value(self.language, "Wikipedia languages",
                               ['af', 'pl', 'ar', 'ast', 'az', 'bg', 'nan', 'bn', 'be', 'ca', 'cs', 'cy', 'da', 'de',
                                'et', 'el', 'en', 'es', 'eo', 'eu', 'fa', 'fr', 'gl', 'ko', 'hy', 'hi', 'hr', 'id',
                                'it', 'he', 'ka', 'lld', 'la', 'lv', 'lt', 'hu', 'mk', 'arz', 'ms', 'min', 'my', 'nl',
                                'ja', 'nb', 'nn', 'ce', 'uz', 'pt', 'kk', 'ro', 'ru', 'ceb', 'sk', 'sl', 'sr', 'sh',
                                'fi', 'sv', 'ta', 'tt', 'th', 'tg', 'azb', 'tr', 'uk', 'ur', 'vi', 'war', 'zh', 'yue'])

class Wikipedia(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- WIKIPEDIA ---")
        # ret = {}
        # for i, out in enumerate(outputs):
        #     ret[out] = self._param.wikipedia.run(state[inputs[i]])
        # return ret
        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            wiki_res = []
            wikipedia.set_lang(self._param.language)
            wiki_engine = wikipedia
            for wiki_key in wiki_engine.search(state[inputs[i]], results=self._param.top_n):
                page = wiki_engine.page(title=wiki_key, auto_suggest=False)
                wiki_res.append('<a href="' + page.url + '">' + page.title + '</a> ' + page.summary)
            ret[out] = wiki_res
            if not wiki_res:
                ret[out] = ""
        return ret

if __name__=="__main__":
    param = WikipediaParam()
    wiki = Wikipedia(0,param)
    output = wiki(["question"], ["output"], {"question": "Ai là chủ tịch nước của việt nam"})
    print(output)