import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))
ROOT2 = FILE.parents[2]
if str(ROOT2) not in sys.path:
    sys.path.append(str(ROOT2))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
import requests
import json
from base.constants import controller_url, get_worker_addr

# def get_file(file_type, filebs):
#     if file_type == "image":
#         files = [("image", image) for image in filebs]
#     return files

class CallToolParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.api = "http://192.168.6.178:8421/api/searchUserv2"
        self.payload = {}
        self.headers = {}
        self.filebs = []
        # self.file_type = "image"
        self.connection = {"input_file_0_image":"filebs"}
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

    def check(self,):
        self.check_empty(self.api, "CallTool api")
        # self.check_valid_value(self.file_type, "File type", ["image"])

class CallTool(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- CALLTOOL ---")
        # ret = {}
        ret = {}
        for i, out in enumerate(outputs):
            connection = self._param.connection
            if connection:
                for i, inp in enumerate(inputs):
                    setattr(self._param, connection[inp], state[inp])
                    # self._param.api = state[inp]

            api_skill = self._param.api
            if not api_skill.startswith(("http", "https")):
                api_skill = get_worker_addr(controller_url, api_skill)
                if api_skill == -1:
                    ret[out] = f"Tool cannot return the answer because this tool has not been registered"
                api_skill += "/worker_generate"
            payload = self._param.payload
            if isinstance(payload, (str)):
                payload = json.loads(payload)

            try:
                tool_res = requests.request("POST", url=api_skill, headers=self._param.headers, data=payload, files=self._param.filebs)
                # print(tool_res.__dict__)
                if tool_res.status_code != 200:
                    ret[out] = self._param.error_code[str(tool_res.status_code)]
                    continue
                tool_res = tool_res.json()
                if not tool_res["success"]:
                    ret[out] = tool_res["error"]
                else:
                    ret[out] = tool_res["information"]
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
                ret[out] =  f"Tool cannot return the answer because Unable to establish connection with tool {api_skill}."

        return ret

if __name__=="__main__":
    # from PIL import Image
    # from io import BytesIO
    # image = Image.open("hieu.jpg")
    # buffered = BytesIO()
    # image.save(buffered, format="PNG")
    # image = buffered.getvalue()

    param = CallToolParam()
    calltool = CallTool(0,param)
    output = calltool(["input_file_0_image"], ["output"], {"input_file_0_image": [("image", open("hieu.jpg", "rb"))]})
    print(output)