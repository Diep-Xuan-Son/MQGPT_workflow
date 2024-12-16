#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# Logger
import sys
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
if ROOT not in sys.path:
    sys.path.append(str(ROOT))

import datetime
import os

from base.constants import PATH_DEFAULT, logger

DEBUG = 0
logger_flow = logger.bind(name="logger_workflow")
logger_flow.add(
    os.path.join(PATH_DEFAULT.PATH_LOG, f"workflow.{datetime.date.today()}.log"),
    mode="w",
)

GROQ_API_KEY = "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"
LLM_MODEL_NAME = "mixtral-8x7b-32768"

# database_logger = getLogger("database")
# FLOAT_ZERO = 1e-8
# PARAM_MAXDEPTH = 5
