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

class QWeatherParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.web_apikey = "93d707a7681e4b7abf0cedb3741f3e54"
        self.lang = "vi"
        self.type = "weather"
        self.user_type = 'free'
        self.error_code = {
            "204": "The request was successful, but the region you are querying does not have the data you need at this time.",
            "400": "Request error, may contain incorrect request parameters or missing mandatory request parameters.",
            "401": "Authentication fails, possibly using the wrong KEY, wrong digital signature, wrong type of KEY (e.g. using the SDK's KEY to access the Web API).",
            "402": "Exceeded the number of accesses or the balance is not enough to support continued access to the service, you can recharge, upgrade the accesses or wait for the accesses to be reset.",
            "403": "No access, may be the binding PackageName, BundleID, domain IP address is inconsistent, or the data that requires additional payment.",
            "404": "The queried data or region does not exist.",
            "429": "Exceeded the limited QPM (number of accesses per minute), please refer to the QPM description",
            "500": "No response or timeout, interface service abnormality please contact us"
            }
        # Weather
        self.time_period = 'now'

    def check(self,):
        self.check_empty(self.web_apikey, "BaiduFanyi APPID")
        self.check_valid_value(self.type, "Type", ["weather", "indices", "airquality", "citylookup", "warning"])
        self.check_valid_value(self.user_type, "Free subscription or paid subscription", ["free", "paid"])
        self.check_valid_value(self.lang, "Use language",
                               ['zh', 'zh-hant', 'en', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'ru', 'hi', 'th', 'ar', 'pt',
                                'bn', 'ms', 'nl', 'el', 'la', 'sv', 'id', 'pl', 'tr', 'cs', 'et', 'vi', 'fil', 'fi',
                                'he', 'is', 'nb'])
        self.check_valid_value(self.time_period, "Time period", ['now', '3d', '7d', '10d', '15d', '30d'])

class QWeather(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- QWEATHER ---")

        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            try:
                response = requests.get(
                    url="https://geoapi.qweather.com/v2/city/lookup?location=" + state[inputs[i]] + "&key=" + self._param.web_apikey).json()
                if response["code"] == "200":
                    location_id = response["location"][0]["id"]
                    lat = response["location"][0]["lat"]
                    lon = response["location"][0]["lon"]
                else:
                    ret[out] = "**Error**" + self._param.error_code[response["code"]]
                    continue

                base_url = "https://api.qweather.com/v7/" if self._param.user_type == 'paid' else "https://devapi.qweather.com/v7/"

                if self._param.type == "weather":
                    url = base_url + "weather/" + self._param.time_period + "?location=" + location_id + "&key=" + self._param.web_apikey + "&lang=" + self._param.lang
                    response = requests.get(url=url).json()
                    if response["code"] == "200":
                        if self._param.time_period == "now":
                            ret[out] = str(response["now"])

                        else:
                            qweather_res = [str(i) + "\n" for i in response["daily"]]
                            ret[out] = qweather_res
                            if not qweather_res:
                                ret[out] = ""
                    else:
                        ret[out] = "**Error**" + self._param.error_code[response["code"]]

                elif self._param.type == "indices":
                    url = base_url + "indices/1d?type=0&location=" + location_id + "&key=" + self._param.web_apikey + "&lang=" + self._param.lang
                    response = requests.get(url=url).json()
                    if response["code"] == "200":
                        indices_res = response["daily"][0]["date"] + "\n" + "\n".join(
                            [i["name"] + ": " + i["category"] + ", " + i["text"] for i in response["daily"]])
                        ret[out] = indices_res

                    else:
                        ret[out] = "**Error**" + self._param.error_code[response["code"]]

                elif self._param.type == "airquality":
                    # url = base_url + "air/now?location=" + location_id + "&key=" + self._param.web_apikey + "&lang=" + self._param.lang
                    url = f"https://devapi.qweather.com/airquality/v1/current/{lat}/{lon}?key={self._param.web_apikey}&lang={self._param.lang}"
                    response = requests.get(url=url).json()
                    if response["code"] == "200":
                        ret[out] = str(response["now"])
                    else:
                        ret[out] = "**Error**" + self._param.error_code[response["code"]]

                elif self._param.type == "citylookup":
                    url = "https://geoapi.qweather.com/v2/city/lookup?location=" + location_id + "&key=" + self._param.web_apikey + "&lang=" + self._param.lang
                    response = requests.get(url=url).json()
                    if response["code"] == "200":
                        ret[out] = str(response["location"])
                    else:
                        ret[out] = "**Error**" + self._param.error_code[response["code"]]
                
                elif self._param.type == "warning":
                    url = f"{base_url}warning/now?location={location_id}&lang={self._param.lang}&key={self._param.web_apikey}"
                    response = requests.get(url=url).json()
                    if response["code"] == "200":
                        ret[out] = str(response["location"])
                    else:
                        ret[out] = "**Error**" + self._param.error_code[response["code"]]
            except Exception as e:
                ret[out] = "**Error**:" + str(e)
        return ret

if __name__=="__main__":
    param = QWeatherParam()
    qweather = QWeather(0,param)
    output = qweather(["question"], ["output"], {"question": "hanoi"})
    print(output)