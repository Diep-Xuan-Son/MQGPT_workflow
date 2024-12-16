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
import pandas as pd
from peewee import MySQLDatabase, PostgresqlDatabase

class ExeSQLParam(ComponentParamBase):
    def __init__(self):
        super().__init__()
        self.db_type = "postgresql"
        self.database = "data-recall-system"
        self.username = "postgres"
        self.password = "admin123"
        self.host = "192.168.6.163"
        self.port = 5412
        self.loop = 3
        self.top_n = 3

    def check(self,):
        self.check_valid_value(self.db_type, "Choose DB type", ['mysql', 'postgresql', 'mariadb'])
        self.check_empty(self.database, "Database name")
        self.check_empty(self.username, "database username")
        self.check_empty(self.host, "IP Address")
        self.check_positive_integer(self.port, "IP Port")
        self.check_empty(self.password, "Database password")
        self.check_positive_integer(self.top_n, "Number of records")

class ExeSQL(ComponentBase, ABC):

    def __call__(self, inputs, outputs, state):
        print("--- EXESQL ---")
        if self._param.db_type in ["mysql", "mariadb"]:
            db = MySQLDatabase(self._param.database, user=self._param.username, host=self._param.host,
                               port=self._param.port, password=self._param.password)
        elif self._param.db_type == 'postgresql':
            db = PostgresqlDatabase(self._param.database, user=self._param.username, host=self._param.host,
                                    port=self._param.port, password=self._param.password)
        try:
            db.connect()
        except Exception as e:
            raise Exception("Database Connection Failed! \n" + str(e))

        ret = {}
        for i, out in enumerate(outputs):
            if not state[inputs[i]]:
                ret[out] = ""
                continue
            # try:
            ans = re.sub(r'^.*?SELECT ', 'SELECT ', state[inputs[i]], flags=re.IGNORECASE)
            ans = re.sub(r';.*?SELECT ', '; SELECT ', ans, flags=re.IGNORECASE)
            ans = re.sub(r';[^;]*$', r';', ans)
            # print(ans)
            # exit()
            sql_res = []
            for single_sql in re.split(r';', ans.replace(r"\n", " ")):
                if not single_sql:
                    continue
                try:
                    query = db.execute_sql(single_sql)
                    if query.rowcount == 0:
                        sql_res.append("\nTotal: " + str(query.rowcount) + "\n No record in the database!")
                        continue
                    single_res = pd.DataFrame([i for i in query.fetchmany(size=self._param.top_n)])
                    single_res.columns = [i[0] for i in query.description]
                    sql_res.append("\nTotal: " + str(query.rowcount) + "\n" + single_res.to_markdown())
                except Exception as e:
                    sql_res.append("**Error**:" + str(e) + "\nError SQL Statement:" + single_sql)
                    pass
            db.close()
            ret[out] = sql_res
            if not sql_res:
                ret[out] = ""
            # except Exception as e:
            #     ret[out] = "**Error**:" + str(e)
        return ret

if __name__=="__main__":
    param = ExeSQLParam()
    exesql = ExeSQL(0,param)
    output = exesql(["question"], ["output"], {"question": "SELECT * from label"})
    print(output)