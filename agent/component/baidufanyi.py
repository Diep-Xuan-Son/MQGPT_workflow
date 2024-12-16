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
import random
from hashlib import md5

class BaiduFanyiParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.appid = "xxx"
        self.secret_key = "xxx"
        self.trans_type = 'translate'
        self.source_lang = 'auto'
        self.target_lang = 'auto'
        self.domain = 'it'

    def check(self,):
        self.check_empty(self.appid, "BaiduFanyi APPID")
        self.check_empty(self.secret_key, "BaiduFanyi Secret Key")
        self.check_valid_value(self.trans_type, "Translate type", ['translate', 'fieldtranslate'])
        self.check_valid_value(self.source_lang, "Source language",
                               ['auto', 'zh', 'en', 'yue', 'wyw', 'jp', 'kor', 'fra', 'spa', 'th', 'ara', 'ru', 'pt',
                                'de', 'it', 'el', 'nl', 'pl', 'bul', 'est', 'dan', 'fin', 'cs', 'rom', 'slo', 'swe',
                                'hu', 'cht', 'vie'])
        self.check_valid_value(self.target_lang, "Target language",
                               ['auto', 'zh', 'en', 'yue', 'wyw', 'jp', 'kor', 'fra', 'spa', 'th', 'ara', 'ru', 'pt',
                                'de', 'it', 'el', 'nl', 'pl', 'bul', 'est', 'dan', 'fin', 'cs', 'rom', 'slo', 'swe',
                                'hu', 'cht', 'vie'])
        self.check_valid_value(self.domain, "Translate field",
                               ['it', 'finance', 'machinery', 'senimed', 'novel', 'academic', 'aerospace', 'wiki',
                                'news', 'law', 'contract'])

class BaiduFanyi(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- BAIDUFANYI ---")
        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            source_lang = self._param.source_lang
            target_lang = self._param.target_lang
            appid = self._param.appid
            salt = str(random.randint(32768, 65536))
            secret_key = self._param.secret_key

            if self._param.trans_type == 'translate':
                sign = md5((appid + state[inputs[i]] + salt + secret_key).encode('utf-8')).hexdigest()
                url = 'http://api.fanyi.baidu.com/api/trans/vip/translate?' + 'q=' + state[inputs[i]] + '&from=' + source_lang + '&to=' + target_lang + '&appid=' + appid + '&salt=' + salt + '&sign=' + sign
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                response = requests.post(url=url, headers=headers).json()
                if response.get('error_code'):
                    ret[out] = "**Error**:" + response['error_msg']
                else:
                    ret[out] = response['trans_result'][0]['dst']

            elif self._param.trans_type == 'fieldtranslate':
                domain = self._param.domain
                sign = md5((appid + state[inputs[i]] + salt + domain + secret_key).encode('utf-8')).hexdigest()
                url = 'http://api.fanyi.baidu.com/api/trans/vip/fieldtranslate?' + 'q=' + state[inputs[i]] + '&from=' + source_lang + '&to=' + target_lang + '&appid=' + appid + '&salt=' + salt + '&domain=' + domain + '&sign=' + sign
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                response = requests.post(url=url, headers=headers).json()
                if response.get('error_code'):
                    BaiduFanyi.be_output("**Error**:" + response['error_msg'])
                else:
                    ret[out] = response['trans_result'][0]['dst']
        return ret

if __name__=="__main__":
    param = BaiduFanyiParam()
    baidufanyi = BaiduFanyi(0,param)
    output = baidufanyi(["question"], ["output"], {"question": "yolov8"})
    print(output)
