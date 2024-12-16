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

class OpenWeatherParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.web_apikey = "c73551a3c8ce8360ff1001fac33f3193"
        self.lang = "vi"
        self.type = "weather"
        self.limit = 3
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
        self.check_valid_value(self.type, "Type", ["weather", "air_pollution"])
        self.check_valid_value(self.lang, "Use language",
                               ['zh', 'zh-hant', 'en', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'ru', 'hi', 'th', 'ar', 'pt',
                                'bn', 'ms', 'nl', 'el', 'la', 'sv', 'id', 'pl', 'tr', 'cs', 'et', 'vi', 'fil', 'fi',
                                'he', 'is', 'nb'])
        self.check_valid_value(self.time_period, "Time period", ['now', '3d', '7d', '10d', '15d', '30d'])

class OpenWeather(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- OPENWEATHER ---")

        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            try:
                response = requests.get(
                    url=f"http://api.openweathermap.org/geo/1.0/direct?q={state[inputs[i]]}&limit={self._param.limit}&appid={self._param.web_apikey}").json()
                print(response)
                if not response:
                    ret[out] = "Don't have information about this place"
                    continue
                if "cod" not in response:
                    location = response[0]["name"]
                    lat = response[0]["lat"]
                    lon = response[0]["lon"]
                else:
                    ret[out] = "**Error**" + self._param.error_code[response["cod"]]
                    continue

                base_url = "https://api.openweathermap.org/data/2.5"

                if self._param.type == "weather":
                    url = f"{base_url}/weather?lat={lat}&lon={lon}&appid={self._param.web_apikey}"
                    response = requests.get(url=url).json()
                    # print(response)
                    if response["cod"] == 200:
                        qweather_res = {"location_name":location, "main":response["weather"][0]["main"], "description":response["weather"][0]["description"], 
                                        "temperature":float(response["main"]["temp"])-273.15, "max_temperature":float(response["main"]["temp_max"])-273.15, 
                                        "min_temperature":float(response["main"]["temp_min"])-273.15, "pressure":response["main"]["pressure"], "humidity":response["main"]["humidity"], 
                                        "sea_level":response["main"]["sea_level"], "ground_level":response["main"]["grnd_level"], "visibility":response["visibility"], 
                                        "wind_speed":response["wind"]["speed"], "wind_direction":response["wind"]["deg"], "wind_gust":response["wind"].get("gust","")
                                        }
                        ret[out] = qweather_res
                        if not qweather_res:
                            ret[out] = ""
                    else:
                        ret[out] = "**Error**" + self._param.error_code[str(response["cod"])]

                elif self._param.type == "air_pollution":
                    category = ["Good", "Fair", "Moderate", "Poor", "Very Poo"]
                    url = f"{base_url}/air_pollution?lat={lat}&lon={lon}&appid={self._param.web_apikey}"
                    response = requests.get(url=url).json()
                    if "cod" not in response:
                        air_res = {"location_name":location, "level":response["list"][0]["main"]["aqi"], "category":category[response["list"][0]["main"]["aqi"]]}
                        air_res.update(response["list"][0]["components"])
                        ret[out] = air_res
                    else:
                        ret[out] = "**Error**" + self._param.error_code[response["code"]]

            except Exception as e:
                ret[out] = "**Error**:" + str(e)
        return ret

if __name__=="__main__":
    param = OpenWeatherParam()
    openweather = OpenWeather(0,param)
    output = openweather(["question"], ["output"], {"question": "hà nội"})
    print(output)