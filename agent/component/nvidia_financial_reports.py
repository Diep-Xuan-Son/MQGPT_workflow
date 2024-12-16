import sys
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
    sys.path.append(str(ROOT1))

from bs4 import BeautifulSoup
import markdownify
import requests

urls_content = []

url_template1 = "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-{quarter}-quarter-fiscal-{year}"
url_template2 = "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-{quarter}-quarter-and-fiscal-{year}"

for quarter in ["first"]:
    for year in range(2024,2025):
        args = {"quarter":quarter, "year": str(year)}
        if quarter == "fourth":
            urls_content.append(requests.get(url_template2.format(**args)).content)
        else:
            urls_content.append(requests.get(url_template1.format(**args)).content)
# print(urls_content)
# exit()

def extract_url_title_time(soup):
    url = ""
    title = ""
    revised_time = ""
    tables = []
    try:
        if soup.find("title"):
            title = str(soup.find("title").string)

        og_url_meta = soup.find("meta", property="og:url")
        if og_url_meta:
            url = og_url_meta.get("content", "")

        for table in soup.find_all("table"):
            tables.append(markdownify.markdownify(str(table)))
            table.decompose()

        text_content = soup.get_text(separator=' ', strip=True)
        print(text_content)
        exit()
        text_content = ' '.join(text_content.split())

        return url, title,text_content, tables
    except:
        print("parse error")
        return "", "", "", "", []

parsed_htmls = []
for url_content in urls_content:
    soup = BeautifulSoup(url_content, 'html.parser')
    url, title, content, tables = extract_url_title_time(soup)
    
    for idx, table in enumerate(tables):
        print(f"parsing tables in {title}...")
        table = get_table_summary(table, title, llm)
        tables[idx] = table
    parsed_htmls.append({"url":url, "title":title, "content":content, "tables":tables})

# summarize tables
def get_table_summary(table, title, llm):
    res = ""
    try:
        #table = markdownify.markdownify(table)
        prompt = f"""
                    [INST] You are a virtual assistant.  Your task is to understand the content of TABLE in the markdown format.
                    TABLE is from "{title}".  Summarize the information in TABLE into SUMMARY. SUMMARY MUST be concise. Return SUMMARY only and nothing else.
                    TABLE: ```{table}```
                    Summary:
                    [/INST]
                """
        result = llm.invoke(prompt)
        res = result.content
    except Exception as e:
        print(f"Error: {e} while getting table summary from LLM")
        if not os.getenv("NVIDIA_API_KEY", False):
            print("NVIDIA_API_KEY not set")
        pass
    finally:
        return res


# for parsed_item in parsed_htmls:
#     title = parsed_item['title']
#     for idx, table in enumerate(parsed_item['tables']):
#         print(f"parsing tables in {title}...")
#         table = get_table_summary(table, title, llm)
#         parsed_item['tables'][idx] = table