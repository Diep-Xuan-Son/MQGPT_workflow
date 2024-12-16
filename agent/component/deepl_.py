import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
import re
import deepl

class DeepLParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.auth_key = "xxx"
        self.source_lang = 'ZH'
        self.target_lang = 'EN-GB'

    def check(self,):
        self.check_empty(self.auth_key, "Deepl authentication key")
        self.check_valid_value(self.source_lang, "Source language",
                               ['AR', 'BG', 'CS', 'DA', 'DE', 'EL', 'EN', 'ES', 'ET', 'FI', 'FR', 'HU', 'ID', 'IT',
                                'JA', 'KO', 'LT', 'LV', 'NB', 'NL', 'PL', 'PT', 'RO', 'RU', 'SK', 'SL', 'SV', 'TR',
                                'UK', 'ZH'])
        self.check_valid_value(self.target_lang, "Target language",
                               ['AR', 'BG', 'CS', 'DA', 'DE', 'EL', 'EN-GB', 'EN-US', 'ES', 'ET', 'FI', 'FR', 'HU',
                                'ID', 'IT', 'JA', 'KO', 'LT', 'LV', 'NB', 'NL', 'PL', 'PT-BR', 'PT-PT', 'RO', 'RU',
                                'SK', 'SL', 'SV', 'TR', 'UK', 'ZH'])

class DeepL(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- BING ---")
        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            try:
                if not state[inputs[i]]:
                    ret[out] = ""
                translator = deepl.Translator(self._param.auth_key)
                result = translator.translate_text(ans, source_lang=self._param.source_lang,
                                                   target_lang=self._param.target_lang)
                ret[out] = result.text
            except Exception as e:
                ret[out] = "**Error**:" + str(e)
        return ret

if __name__=="__main__":
    param = DeepLParam()
    deepl = DeepL(0,param)
    output = deepl(["question"], ["output"], {"question": "yolov8"})
    print(output)