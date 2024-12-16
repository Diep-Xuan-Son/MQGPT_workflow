import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
import requests

class BingParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.top_n = 10
        self.channel = "Webpages"
        self.api_key = "YOUR_ACCESS_KEY"
        self.country = "CN"
        self.language = "en"

    def check(self,):
        self.check_positive_integer(self.top_n, "Top N")
        self.check_valid_value(self.channel, "Bing Web Search or Bing News", ["Webpages", "News"])
        self.check_empty(self.api_key, "Bing subscription key")
        self.check_valid_value(self.country, "Bing Country",
                               ['AR', 'AU', 'AT', 'BE', 'BR', 'CA', 'CL', 'DK', 'FI', 'FR', 'DE', 'HK', 'IN', 'ID',
                                'IT', 'JP', 'KR', 'MY', 'MX', 'NL', 'NZ', 'NO', 'CN', 'PL', 'PT', 'PH', 'RU', 'SA',
                                'ZA', 'ES', 'SE', 'CH', 'TW', 'TR', 'GB', 'US'])
        self.check_valid_value(self.language, "Bing Languages",
                               ['ar', 'eu', 'bn', 'bg', 'ca', 'ns', 'nt', 'hr', 'cs', 'da', 'nl', 'en', 'gb', 'et',
                                'fi', 'fr', 'gl', 'de', 'gu', 'he', 'hi', 'hu', 'is', 'it', 'jp', 'kn', 'ko', 'lv',
                                'lt', 'ms', 'ml', 'mr', 'nb', 'pl', 'br', 'pt', 'pa', 'ro', 'ru', 'sr', 'sk', 'sl',
                                'es', 'sv', 'ta', 'te', 'th', 'tr', 'uk', 'vi'])

class Bing(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- BING ---")
        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            headers = {"Ocp-Apim-Subscription-Key": self._param.api_key, 'Accept-Language': self._param.language}
            params = {"q": state[inputs[i]], "textDecorations": True, "textFormat": "HTML", "cc": self._param.country,
                      "answerCount": 1, "promote": self._param.channel}
            if self._param.channel == "Webpages":
                response = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params)
                response.raise_for_status()
                search_results = response.json()
                bing_res = ['<a href="' + i["url"] + '">' + i["name"] + '</a>    ' + i["snippet"] for i in
                            search_results["webPages"]["value"]]
            elif self._param.channel == "News":
                response = requests.get("https://api.bing.microsoft.com/v7.0/news/search", headers=headers,
                                        params=params)
                response.raise_for_status()
                search_results = response.json()
                bing_res = ['<a href="' + i["url"] + '">' + i["name"] + '</a>    ' + i["description"] for i
                            in search_results['news']['value']]
            ret[out] = bing_res
            if not bing_res:
                ret[out] = ""
        return ret

if __name__=="__main__":
    param = BingParam()
    bing = Bing(0,param)
    output = bing(["question"], ["output"], {"question": "yolov8"})
    print(output)
