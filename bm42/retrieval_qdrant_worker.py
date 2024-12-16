from pathlib import Path 
import sys
FILE = Path(__file__).resolve()
DIR = FILE.parents[0]
ROOT = FILE.parents[1]
if str(ROOT) not in sys.path:
	sys.path.append(str(ROOT))
if str(DIR) not in sys.path:
	sys.path.append(str(DIR))

from qdrant_client import QdrantClient, models as qmodels
from fastembed import SparseTextEmbedding, TextEmbedding
from datetime import datetime
import time
import json 
import os 
from unstructured.partition.auto import partition
import uuid
import threading
from loguru import logger
from minio import Minio
from io import BytesIO
from tqdm import tqdm

logger_retrieval = logger.bind(name="logger_retrieval")
# logger_retrieval.add(os.path.join(PATH_DEFAULT.LOGDIR, f"retrieval_worker.{datetime.date.today()}.log"), mode='w')

import tiktoken
encoder_tiktoken = tiktoken.encoding_for_model("gpt-3.5-turbo")
def naive_merge(sections, chunk_token_num=128, delimiter="\n.;!?"):
	if not sections:
		return []
	if isinstance(sections[0], type("")):
		sections = [(s, "") for s in sections]
	cks = [""]
	tk_nums = [0]

	def num_tokens_from_string(string: str) -> int:
		"""Returns the number of tokens in a text string."""
		try:
			num_tokens = len(encoder_tiktoken.encode(string))
			return num_tokens
		except Exception as e:
			pass
		return 0

	def add_chunk(t, pos):
		nonlocal cks, tk_nums, delimiter
		tnum = num_tokens_from_string(t)
		if not pos: pos = ""
		if tnum < 8:
			pos = ""
		# Ensure that the length of the merged chunk does not exceed chunk_token_num  
		if tk_nums[-1] > chunk_token_num:

			if t.find(pos) < 0:
				t += pos
			cks.append(t)
			tk_nums.append(tnum)
		else:
			if cks[-1].find(pos) < 0:
				t += pos
			cks[-1] += t
			tk_nums[-1] += tnum

	for sec, pos in sections:
		add_chunk(sec, pos)
		continue
		s, e = 0, 1
		while e < len(sec):
			if sec[e] in delimiter:
				add_chunk(sec[s: e + 1], pos)
				s = e + 1
				e = s + 1
			else:
				e += 1
		if s < e:
			add_chunk(sec[s: e], pos)

	return cks

def pdf_chunk(pdf_file):
	elements = partition(file=pdf_file, strategy="fast")
	sections = [(str(el),"") for el in elements]
	#---------------------------------------
	parser_config = {"chunk_token_num": 256, "delimiter": "\n.;!?"}
	chunks = naive_merge(sections, int(parser_config.get(
			"chunk_token_num", 128)), parser_config.get(
			"delimiter", "\n.;!?"))
	return chunks

# def pdf_chunk(pdf_file):
# 	elements = partition(file=pdf_file, strategy="fast")
# 	text = "\n".join([str(el) for el in elements])
# 	text = " ".join(text.split())
# 	#---------------------------------------
# 	text_tokens = text.split()
# 	sentences = []
# 	for i in range(0, len(text_tokens), 50):
# 		window = text_tokens[i : i + 128]
# 		if len(window) < 128:
# 			break
# 		sentences.append(window)
# 	chunks = [" ".join(s) for s in sentences]
# 	return chunks

def check_qdrant_alive(worker_object, time_check):
	while True:
		status_qdrant = worker_object.get_list_collection()
		if not status_qdrant["success"]:
			logger_retrieval.error(status_qdrant["error"])
		else:
			logger_retrieval.info("Connected qdrant server")
		time.sleep(time_check)

def check_minio_alive(worker_object, time_check):
	while True:
		status_minio = worker_object.get_list_bucket()
		if not status_minio["success"]:
			logger_retrieval.error(status_minio["error"])
		else:
			logger_retrieval.info("Connected minio server")
		time.sleep(time_check)

class RetrievalWorker:
	def __init__(self, qdrant_url="http://192.168.6.163:6333", minio_url="192.168.6.163:9100", sparse_model_path=f"{DIR}/weights/all_miniLM_L6_v2_with_attentions", dense_model_path=f"{DIR}/weights/paraphrase-multilingual-mpnet-base-v2", check_connection=False):
		self.qdrant_client = QdrantClient(qdrant_url, https=True, timeout=60,)
		self.model_bm42 = SparseTextEmbedding(model_name=sparse_model_path, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
		self.model_text = TextEmbedding(model_name=dense_model_path, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
		model_dir = self.model_text.model_name
		with open(os.path.join(model_dir, "config.json")) as f:
			data_config = json.load(f)
		self.embed_dims = data_config['hidden_size']
		self.minio_client = Minio(
								endpoint=minio_url,
								access_key="minio_access_key",
								secret_key="minio_secret_key",
								secure=False,
							)
		self.qdrant_connect_status = True
		self.minio_connect_status = True
		time_check = 60
		if check_connection:
			check_qdrant = threading.Thread(target=check_qdrant_alive, args=(self,time_check))
			check_minio = threading.Thread(target=check_minio_alive, args=(self,time_check))
			check_qdrant.start()
			check_minio.start()

	def get_list_bucket(self):
		try:
			list_buckets = self.minio_client.list_buckets()
			self.minio_connect_status = True
			return {"success": True, "data": list_buckets}
		except:
			self.minio_connect_status = False
			return {"success": False, "error": "Could not connect to Minio server"}

	def create_bucket(self, bucket_name: str):
		bucket_name = bucket_name.replace("_", "-")
		found = self.minio_client.bucket_exists(bucket_name=bucket_name)
		if found:
			return {"success": False, "error": f"Bucket {bucket_name} already exists, skip creating!"}
		self.minio_client.make_bucket(bucket_name=bucket_name)
		return {"success": True}      	

	def upload_file2bucket(self, bucket_name: str, folder_name: str, list_file_path: list):
		bucket_name = bucket_name.replace("_", "-")
		found = self.minio_client.bucket_exists(bucket_name=bucket_name)
		if not found:
			return {"success": False, "error": f"Bucket {bucket_name} does not exist!"}
		objects_exist = self.get_file_name_bucket(bucket_name, folder_name)["data"]
		objects_exist = [os.path.basename(x.object_name) for x in objects_exist]
		for i, fp in enumerate(list_file_path):
			fn = os.path.basename(fp)
			if fn in objects_exist:
				logger_retrieval.info(f"File {fn} exists!")
				continue
			self.minio_client.fput_object(
				bucket_name=bucket_name, object_name=os.path.join(folder_name, fn), file_path=fp,
			)
		return {"success": True}

	def delete_file_bucket(self, bucket_name: str, folder_name: str, list_file_name: list):
		bucket_name = bucket_name.replace("_", "-")
		found = self.minio_client.bucket_exists(bucket_name=bucket_name)
		if not found:
			return {"success": False, "error": f"Bucket {bucket_name} does not exist!"}
		for i, fn in enumerate(list_file_name):
			self.minio_client.remove_object(bucket_name=bucket_name, object_name=os.path.join(folder_name, os.path.basename(fn)))
		return {"success": True}

	def delete_folder_bucket(self, bucket_name: str, folder_name: str):
		bucket_name = bucket_name.replace("_", "-")
		objects_to_delete = self.get_file_name_bucket(bucket_name, folder_name)["data"]
		for obj in objects_to_delete:
			self.minio_client.remove_object(bucket_name=bucket_name, object_name=obj.object_name)
		return {"success": True}

	def get_file_name_bucket(self, bucket_name: str, folder_name: str):
		bucket_name = bucket_name.replace("_", "-")
		found = self.minio_client.bucket_exists(bucket_name=bucket_name)
		if not found:
			return {"success": False, "error": f"Bucket {bucket_name} does not exist!"}
		return {"success": True, "data": self.minio_client.list_objects(bucket_name, prefix=folder_name, recursive=True)}

	def add_collection(self, collection_name: str):
		if self.qdrant_client.collection_exists(collection_name=collection_name):
			return {"success": False, "error": f"Collection {collection_name} already exists"}
		self.qdrant_client.create_collection(
			collection_name=collection_name,
			vectors_config={
				"text": qmodels.VectorParams(
					size=self.embed_dims,
					distance=qmodels.Distance.COSINE,
				)
			},
			sparse_vectors_config={
				"bm42": qmodels.SparseVectorParams(
					modifier=qmodels.Modifier.IDF,
				)
			},
			# optimizers_config=models.OptimizersConfigDiff(indexing_threshold=0),
			shard_number=2, # 2-4 is a reasonable number
		)
		return {"success": True}

	def delete_collection(self, collection_name: str):
		if not self.qdrant_client.collection_exists(collection_name=collection_name):
			return {"success": False, "error": f"Collection {collection_name} has not been registered yet"}
		self.qdrant_client.delete_collection(collection_name=collection_name)
		return {"success": True}

	def update_collection(self, collection_name: str, **kwargs):
		if not self.qdrant_client.collection_exists(collection_name=collection_name):
			return {"success": False, "error": f"Collection {collection_name} has not been registered yet"}
		self.qdrant_client.update_collection(
			collection_name="{collection_name}",
			**kwargs
		)
		return {"success": True}

	def get_status_collection(self, collection_name: str):
		if not self.qdrant_client.collection_exists(collection_name=collection_name):
			return {"success": False, "error": f"Collection {collection_name} has not been registered yet"}
		return {"success": True, "data": self.qdrant_client.get_collection(collection_name=collection_name)}

	def get_list_collection(self):
		try:
			list_collections = self.qdrant_client.get_collections()
			self.qdrant_connect_status = True
			return {"success": True, "data": list_collections}
		except:
			self.qdrant_connect_status = False
			return {"success": False, "error": "Could not connect to Qdrant server"}

	def add_list_file(self, collection_name: str, list_file_name: list, bucket_name: str):
		bucket_name = bucket_name.replace("_", "-")
		if not self.qdrant_client.collection_exists(collection_name=collection_name):
			return {"success": False, "error": f"Collection {collection_name} has not been registered yet"}
		for i, file_name in enumerate(tqdm(list_file_name)):
			filter_points = self.qdrant_client.scroll(
								collection_name=collection_name,
								scroll_filter=qmodels.Filter(
									must=[
										qmodels.FieldCondition(
											key="name",
											match=qmodels.MatchValue(value=file_name),
										),
									]
								),
							)
			if len(filter_points[0]) != 0:
				logger_retrieval.info(f"File {file_name} has been embedded!")
				continue
			response = self.minio_client.get_object(bucket_name=bucket_name, object_name=os.path.join(collection_name, os.path.basename(file_name)))
			file = BytesIO(response.data)
			documents = pdf_chunk(file)
			self.qdrant_client.upload_points(
				collection_name=collection_name,
				points=[
					qmodels.PointStruct(
						id=uuid.uuid4().hex,
						vector={
							"text": list(self.model_text.query_embed(doc))[0].tolist(),
							"bm42": list(self.model_bm42.query_embed(doc))[0].as_object(),
						},
						payload={
							"index": idx,
							"name": file_name,
							"description": doc,
							"category": "",
							"datetime": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
						},
					)
					for idx, doc in enumerate(tqdm(documents))
				], 
				batch_size=64,
				parallel=4,
				max_retries=3,
			)
		return {"success": True}

	def delete_list_file(self, collection_name: str, list_file_name: list):   
		if not self.qdrant_client.collection_exists(collection_name=collection_name):
			return {"success": False, "error": f"Collection {collection_name} has not been registered yet"}
		self.qdrant_client.delete(
			collection_name=collection_name,
			points_selector=qmodels.FilterSelector(
				filter=qmodels.Filter(
					must=[
						qmodels.FieldCondition(
							key="name",
							match=qmodels.MatchAny(any=list_file_name),
						),
					],
				)
			),
		)
		return {"success": True}

	def get_list_file_name(self, collection_name: str):
		records = self.qdrant_client.scroll(
								collection_name=collection_name,
								with_payload=True,
								with_vectors=False,
							)[0]
		list_file_name = sorted(list(set(map(lambda x: x.payload["name"], records))))
		return list_file_name

	def query(self, collection_names, text_querys, n_result=10, similarity_threshold=0.4):
		results = []
		scores = []
		sparse_embedding = list(self.model_bm42.query_embed(text_querys))
		dense_embedding = list(self.model_text.query_embed(text_querys))
		for i in range(len(text_querys)):
			result = []
			score = []
			for collection_name in collection_names:
				query_results = self.qdrant_client.query_points(
					collection_name=collection_name,
					prefetch=[
					  qmodels.Prefetch(query=sparse_embedding[i].as_object(), using="bm42", limit=20),
					  qmodels.Prefetch(query=dense_embedding[i].tolist(),  using="text", limit=20),
					],
					query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF), # <--- Combine the scores
					limit=n_result
				).points
				[(result.append(hit.payload), score.append(hit.score)) for hit in query_results if hit.score>similarity_threshold]
				#--------------add extension for result------------
				for i, r in enumerate(result):
					new_description = [r['description']]
					ext_results = self.qdrant_client.scroll(
						collection_name=collection_name,
						scroll_filter=qmodels.Filter(
							should=[
								qmodels.FieldCondition(
									key="index",
									match=qmodels.MatchAny(any=[int(r["index"]-2),int(r["index"]-1),int(r["index"]+1),int(r["index"]+2)]),
								)
							]
						),
					)[0]
					ext_results_sort = sorted(ext_results, key=lambda x: abs(x.payload['index']-r["index"]+1e-3))
					# print(ext_results_sort)
					[new_description.insert(0,extr.payload['description']) if i%2==0 else new_description.append(extr.payload['description']) for i, extr in enumerate(ext_results_sort)]
					# print(new_description)
					result[i]["description"] = " ".join(new_description)
					#///////////////////////////////////////////////
			results.append(result)
			scores.append(score)
		print("----scores: ", scores)
		use_ctx = True
		if len(results[0])==0:
			use_ctx = False
		return results, use_ctx

if __name__=="__main__":
	retw = RetrievalWorker()
	collection_name = "test2"
	ret = retw.add_collection(collection_name)
	list_file_path = ["./Anninhmang.pdf"]
	list_file_name = [os.path.basename(fp) for fp in list_file_path]
	list_file = [open(fp,mode='rb') for fp in list_file_path]
	# ret = retw.add_list_file(collection_name, list_file_name, config_minio["bucket_name"])
	# print(ret)
	# ret = retw.delete_list_file(collection_name, list_file_name)
	# print(ret)
	# ret = retw.delete_collection(collection_name)
	# print(ret)
	# exit()
	ret = retw.query([collection_name], ["Các hành vi bị nghiêm cấm về an ninh mạng"])
	print(ret)

	#---------minio--------
	config_minio = {
		"endpoint": "http://192.168.6.163:9100",
		"bucket_name": "data_bot",
		"folder_name": collection_name,
		"access_key": "minio_access_key",
		"secret_key": "minio_secret_key"
	}
	# ret = retw.create_bucket(config_minio["bucket_name"])
	# print(ret)

	# ret = retw.upload_file2bucket(config_minio["bucket_name"], config_minio["folder_name"], list_file_path)
	# print(ret)

	# ret = retw.delete_folder_bucket(config_minio["bucket_name"], "test2")
	# print(ret)

	# ret = retw.add_list_file(collection_name, list_file_name, config_minio["bucket_name"])
	# print(ret)

	
