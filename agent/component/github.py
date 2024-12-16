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

class GitHubParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.top_n = 10

    def check(self,):
        self.check_positive_integer(self.top_n, "Top N")

class GitHub(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- GITHUB ---")
        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            try:
                url = 'https://api.github.com/search/repositories?q=' + state[inputs[i]] + '&sort=stars&order=desc&per_page=' + str(
                    self._param.top_n)
                headers = {"Content-Type": "application/vnd.github+json", "X-GitHub-Api-Version": '2022-11-28'}
                response = requests.get(url=url, headers=headers).json()

                github_res = ['<a href="' + i["html_url"] + '">' + i["name"] + '</a>' + str(
                    i["description"]) + '\n stars:' + str(i['watchers']) for i in response['items']]
                ret[out] = github_res
                if not github_res:
                    ret[out] = ""
            except Exception as e:
                ret[out] = "**Error**:" + str(e)
        return ret

if __name__=="__main__":
    param = GitHubParam()
    github = GitHub(0,param)
    output = github(["question"], ["output"], {"question": "yolov8"})
    print(output)
