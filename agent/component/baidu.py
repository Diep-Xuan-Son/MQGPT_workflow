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
import re

class BaiduParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.top_n = 2

    def check(self,):
        self.check_positive_integer(self.top_n, "Top N")

class Baidu(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- BAIDU ---")
        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            url = 'https://www.baidu.com/s?wd=' + state[inputs[i]] + '&rn=' + str(self._param.top_n)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'}
            response = requests.get(url=url, headers=headers)

            url_res = re.findall(r"'url': \\\"(.*?)\\\"}", response.text)
            title_res = re.findall(r"'title': \\\"(.*?)\\\",\\n", response.text)
            body_res = re.findall(r"\"contentText\":\"(.*?)\"", response.text)
            baidu_res = [re.sub('<em>|</em>', '', '<a href="' + url + '">' + title + '</a>    ' + body) for
                         url, title, body in zip(url_res, title_res, body_res)]
            del body_res, url_res, title_res
            ret[out] = baidu_res
            if not baidu_res:
                ret[out] = ""
        return ret

if __name__=="__main__":
    param = BaiduParam()
    baidu = Baidu(0,param)
    output = baidu(["question"], ["output"], {"question": "yolov8"})
    print(output)
