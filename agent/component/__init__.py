import importlib
import sys
# from pathlib import Path
# FILE = Path(__file__).resolve()
# DIR = FILE.parents[0]
# if str(DIR) not in sys.path:
#     sys.path.append(str(DIR))
# ROOT1 = FILE.parents[1]
# if str(ROOT1) not in sys.path:
#     sys.path.append(str(ROOT1))

from .input import InputGraph, InputGraphParam
from .output import OutputGraph, OutputGraphParam
from .decompose import Decompose, DecomposeParam
from .retrieve import Retrieve, RetrieveParam
from .generate import Generate, GenerateParam
from .grade_documents import GradeDocuments, GradeDocumentsParam
from .transform_query import TransformQuery, TransformQueryParam
from .condition import Condition, ConditionParam
from .input_file import IFile, IFileParam
from .call_tools import CallTool, CallToolParam

def component_class(class_name):
    m = importlib.import_module("component")
    c = getattr(m, class_name)
    return c
