import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from abc import ABC
from component.base_comp import ComponentBase, ComponentParamBase
from io import BytesIO
from PIL import Image

class IFileParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.file_type = "image"
        self.key_input = "face_image"

    def check(self,):
        self.check_positive_number(self.message_history_window_size, "History window size")
        self.check_empty(self.file_type, "[InputFile] file_type")

class IFile(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- IFILE ---")
        ret = {}
        for i, out in enumerate(outputs):
            if self._param.file_type == "image":
                # print(state[out])
                ret[out] = [("image", image) for image in state[out]]
        return ret

if __name__=="__main__":
    image = Image.open("hieu.jpg")
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image = buffered.getvalue()

    param = InputFileParam()
    inpf = InputFile(0,param)
    output = inpf([], ["image"], {"image": [image]})
    print(output)