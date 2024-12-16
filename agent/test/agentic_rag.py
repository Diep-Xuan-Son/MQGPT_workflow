import sys
from pathlib import Path
FILE = Path(__file__).resolve()
ROOT1 = FILE.parents[1]
if str(ROOT1) not in sys.path:
	sys.path.append(str(ROOT1))
ROOT2 = FILE.parents[2]
if str(ROOT2) not in sys.path:
	sys.path.append(str(ROOT2))

import pandas as pd
from itertools import zip_longest
from functools import partial
from typing import Literal, Optional, Tuple, List, Dict
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain_nvidia_ai_endpoints import ChatNVIDIA
from bm42.retrieval_qdrant_worker import RetrievalWorker
from langgraph.graph import END, StateGraph, START

import time
import json
from component import component_class
# DATA_GRAPH = {
# 	"components": {
# 			"input_0": {
# 				"component_name": "InputGraph",
# 				"params": {
# 					"prologue": "Hi there!",
# 					"key_input": "user_question"
# 				},
# 				"downstream": ["decompose_0"],
# 				"upstream": [],
# 				"input": [],
# 				"output":["user_question"],
# 				"type_data": "str"
# 			},
# 			"decompose_0": {
# 				"component_name": "Decompose",
# 				"params": {
# 				  "temperature": 0,
# 				  "model_name": "mixtral-8x7b-32768"
# 				},
# 				"downstream": ["retrieve_0"],
# 				"upstream": ["input_0"],
# 				"input": ["input_0_user_question"],
# 				"output":["sub_questions"],
# 				"type_data": "List[str]"
# 			},
# 			"retrieve_0": {
# 				"component_name": "Retrieve",
# 				"params": {
# 					"similarity_threshold": 0.4,
# 					"top_k": 10,
# 					"collection_names": ["test2"],
# 					"qdrant_url": "http://192.168.6.163:6333",
# 					"minio_url": "192.168.6.163:9100"
# 				},
# 				"downstream": ["grade_documents_0"],
# 				"upstream": ["decompose_0"],
# 				"input": ["decompose_0_sub_questions"],
# 				"output":["documents"],
# 				"type_data": "List[str]"
# 			},
# 			"grade_documents_0": {
# 				"component_name": "GradeDocuments",
# 				"params": {
# 					"temperature": 0,
# 					"model_name": "mixtral-8x7b-32768",
# 					"prompt": "Retrieved document: \n\n {retrieve_0_documents} \n\n User question: {input_0_user_question}"
# 				},
# 				"downstream": ["condition_0"],
# 				"upstream": ["retrieve_0"],
# 				"input": ["retrieve_0_documents", "input_0_user_question"],
# 				"output":["filtered_docs"],
# 				"type_data": "List[str]"
# 			},
# 			"condition_0": {
# 				"component_name": "Condition",
# 				"params": {},
# 				"downstream": ["generate_0", "transform_query_0"],
# 				"upstream": ["grade_documents_0"],
# 				"input": ["grade_documents_0_filtered_docs"],
# 				"output":[]
# 			},
# 			"transform_query_0": {
# 				"component_name": "TransformQuery",
# 				"params": {
# 					"temperature": 0,
# 					"model_name": "mixtral-8x7b-32768",
# 					"prompt": "Here is the initial question: \n\n {question} \n Formulate an improved question."
# 				},
# 				"downstream": ["retrieve_0"],
# 				"upstream": ["condition_0"],
# 				"input": ["input_0_user_question"],
# 				"output":["better_question"],
# 				"type_data": "str"
# 			},
# 			"generate_0": {
# 				"component_name": "Generate",
# 				"params": {
# 					"temperature": 0,
# 					"model_name": "mixtral-8x7b-32768",
# 					"prompt": "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. The answer write in Vietnamese.\nQuestion: {input_0_user_question} \nContext: {grade_documents_0_filtered_docs} \nAnswer:"
# 				},
# 				"downstream": ["output_0"],
# 				"upstream": ["condition_0"],
# 				"input": ["input_0_user_question", "grade_documents_0_filtered_docs"],
# 				"output":["generation"],
# 				"type_data": "str"
# 			},
# 			# "generate_1": {
# 			# 	"component_name": "Generate",
# 			# 	"params": {
# 			# 		"temperature": 0,
# 			# 	  	"model_name": "mixtral-8x7b-32768",
# 			# 	  	"prompt": "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. The answer write in Vietnamese.\nQuestion: {input_0_user_question} \nContext: {retrieve_0_documents} \nAnswer:"
# 			# },
# 			# 	"downstream": ["output_0"],
# 			# 	"upstream": ["retrieve_0"],
# 			# 	"input": ["input_0_user_question", "retrieve_0_documents"],
# 			# 	"output":["generation"],
# 			# 	"type_data": "str"
# 			# },
# 			"output_0": {
# 				"component_name": "OutputGraph",
# 				"params": {
# 					"key_output": "generate_0_generation"
# 				},
# 				"downstream": [],
# 				"upstream": ["transform_query_0", "generate_0"],
# 				"input": ["generate_0_generation"],
# 				"output":[]
# 			},
# 	},
# 	"history": [],
# 	"messages": [],
# 	"reference": {},
# 	"path": [],
# 	"answer": []
# }
DATA_GRAPH = open(str(ROOT1/"templates/agentic_rag_test.json"), "r").read()

class GraphState(TypedDict):
	"""
	Represents the state of our graph.
	Attributes:
		question: question
		generation: LLM generation
		documents: list of documents
	"""
	inputs: List[str]
	outputs: List[str]
	question: str
	sub_questions:  List[str]
	generation: str
	documents: List[str]

class SubQuery(BaseModel):
	"""Given a user question, break it down into distinct sub questions that \
	you need to answer in order to answer the original question. Sub questions write in Vietnamese. The maximum number of sub questions is three"""
	questions: List[str] = Field(description="The list of sub questions")

class RetrievalGrader(BaseModel):
	"""Binary score for relevance check on retrieved documents."""
	binary_score: str = Field(
		description="Documents are relevant to the question, 'yes' or 'no'"
	)

class NodeGraph():
	def __init__(self,):
		self.llm = ChatGroq(temperature=0, groq_api_key="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", model_name="mixtral-8x7b-32768")
		# self.llm = ChatNVIDIA(model="meta/llama-3.1-8b-instruct", nvidia_api_key="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", temperature=0)
		# llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3", huggingfacehub_api_token="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", temperature=0, max_tokens=1024)
		# self.llm = ChatHuggingFace(llm=llm)
		self.sub_question_generator = self.llm.with_structured_output(SubQuery)

		prompt_rag = ChatPromptTemplate.from_messages(
			[
				("human", "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. The answer write in Vietnamese.\nQuestion: {input_0_user_question} \nContext: {grade_documents_0_filtered_docs} \nAnswer:"),
			]
		)
		self.rag_chain = prompt_rag | self.llm | StrOutputParser()
		self.retw = RetrievalWorker()
		self.collection_names = ["test2"]

		retrieval_grader = self.llm.with_structured_output(RetrievalGrader)
		# Prompt
		system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
			It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
			If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
			Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
		grade_prompt = ChatPromptTemplate.from_messages(
			[
			 
				("system", system),
				("human", "Retrieved document: \n\n {retrieve_0_documents} \n\n User question: {input_0_user_question}"),
			]
		)
		self.retrieval_grader = grade_prompt | retrieval_grader

		### Question Re-writer
		# Prompt
		system = """You a question re-writer that converts an input question to a better version that is optimized \n 
			 for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
		re_write_prompt = ChatPromptTemplate.from_messages(
			[
				("system", system),
				(
					"human",
					"Here is the initial question: \n\n {question} \n Formulate an improved question.",
				),
			]
		)
		self.question_rewriter = re_write_prompt | self.llm | StrOutputParser()


	def InputGraph(self, inputs, outputs, state):
		print("--- INPUT ---")
		ret = {}
		for i, out in enumerate(outputs):
			ret[out] = state[out]
		return ret

	def OutputGraph(self, inputs, outputs, state):
		print("--- OUTPUT ---")
		ret = {}
		for i, inp in enumerate(inputs):
			ret[inp] = state[inp]
		return ret

	def Decompose(self, inputs, outputs, state):
		"""
		Retrieve documents
		Args:
			state (dict): The current graph state
		Returns:
			state (dict): New key added to state, documents, that contains retrieved documents
		"""
		print("--- QUERY DECOMPOSITION ---")
		st_time = time.time()
		# question = state["question"]
		ret = {}
		if len(inputs)>len(outputs):
			inputs = inputs[:len(outputs)]
		for i, out in enumerate(outputs):
			if i>len(inputs)-1:
				ret[out] = "Don't have enough input"
				continue
			ret[out] = self.sub_question_generator.invoke(state[inputs[i]]).questions
		print(f"----Duration: {time.time()-st_time}")
		# Reranking
		# sub_queries = self.sub_question_generator.invoke(question)
		return ret


	def Retrieve(self, inputs, outputs, state):
		"""
		Retrieve documents
		Args:
			state (dict): The current graph state
		Returns:
			state (dict): New key added to state, documents, that contains retrieved documents
		"""
		print("---RETRIEVE---")
		st_time = time.time()
		# sub_questions = state["sub_questions"]
		ret = {}
		if len(inputs)>len(outputs):
			inputs = inputs[:len(outputs)]
		for i, out in enumerate(outputs):
			if i>len(inputs)-1:
				ret[out] = "Don't have enough input"
				continue
			# Retrieval
			dt_retws, use_ctx = self.retw.query(self.collection_names, state[inputs[i]])
			if not dt_retws[0]:
				documents = ["There's no knowledge fit with your question"]

			dfs = pd.DataFrame([])
			for i, dt in enumerate(dt_retws):
				df = pd.DataFrame(dt)
				df["ID"] = i
				dfs = pd.concat([dfs, df], ignore_index=True)
			# dfs = dfs.groupby('ID')['description'].agg('\n\t'.join).reset_index()
			documents = list(dfs.to_dict()['description'].values())
			ret[out] = documents
		print(f"----Duration: {time.time()-st_time}")
		return ret

	def Generate(self, inputs, outputs, state):
		"""
		Generate answer
		Args:
			state (dict): The current graph state
		Returns:
			state (dict): New key added to state, generation, that contains LLM generation
		"""
		print("---GENERATE---")
		st_time = time.time()
		# question = state["question"]
		# documents = state["documents"]
		ret = {}
		for i, out in enumerate(outputs):
			data_inp = {}
			for inp in inputs:
				data_inp[inp] = state[inp]
			# RAG generation
			generation = self.rag_chain.invoke(data_inp)
			ret[out] = generation
		print(f"----Duration: {time.time()-st_time}")
		return ret

	def GradeDocuments(self, inputs, outputs, state):
		"""
		Determines whether the retrieved documents are relevant to the question.
		Args:
			state (dict): The current graph state
		Returns:
			state (dict): Updates documents key with only filtered relevant documents
		"""
		print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
		st_time = time.time()
		# question = state["question"]
		# documents = state["documents"]
		ret = {}
		for i, out in enumerate(outputs):
			data_inp = {}
			docs_id = ""
			for inp in inputs:
				if not isinstance(state[inp], list):
					data_inp[inp] = state[inp]
				else:
					docs_id = inp
			# Score each doc
			filtered_docs = []
			for d in state[docs_id]:
				data_inp[docs_id] = d
				score = self.retrieval_grader.invoke(data_inp)
				grade = score.binary_score
				if grade == "yes":
					print("---GRADE: DOCUMENT RELEVANT---")
					filtered_docs.append(d)
				else:
					print("---GRADE: DOCUMENT NOT RELEVANT---")
					continue
			ret[out] = filtered_docs
		print(f"----Duration: {time.time()-st_time}")
		return ret

	def TransformQuery(self, inputs, outputs, state):
		"""
		Transform the query to produce a better question.
		Args:
			state (dict): The current graph state
		Returns:
			state (dict): Updates question key with a re-phrased question
		"""

		print("---TRANSFORM QUERY---")
		# question = state["question"]\
		ret = {}
		if len(inputs)>len(outputs):
			inputs = inputs[:len(outputs)]
		for i, out in enumerate(outputs):
			if i>len(inputs)-1:
				ret[out] = "Don't have enough input"
				continue
			# Re-write question
			better_question = self.question_rewriter.invoke(state[inputs[i]])
			ret[out] = better_question

		return ret

	### Edges
	# @classmethod
	def Condition(self, inputs, outputs, state):
		"""
		Determines whether to generate an answer, or re-generate a question.
		Args:
			state (dict): The current graph state
		Returns:
			str: Binary decision for next node to call
		"""
		print("---ASSESS GRADED DOCUMENTS---")
		# filtered_documents = state["documents"]
		filtered_documents = state[inputs[0]]
		# filtered_documents = state["grade_documents_0_filtered_docs"]

		if not filtered_documents:
			# All documents have been filtered check_relevance
			# We will re-generate a new query
			print(
				"---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
			)
			return "transform_query_0"
		# We have relevant documents, so generate answer
		print("---DECISION: GENERATE---")
		return "generate_0"

def create_graph(InitState):
	# dsl = json.dumps(DATA_GRAPH)
	dsl = json.loads(DATA_GRAPH)
	comp = dsl["components"]

	# st_time = time.time()
	state_scheme = {}
	for comp_id, inf in comp.items():
		if len(inf["output"])==0: continue
		for o in inf["output"]:
			state_scheme[f"{comp_id}_{o}"] = eval(inf["type_data"])

	print(state_scheme)
	# print(f"duration: {time.time() - st_time}")
	# exit()
	InitState = TypedDict("InitState", state_scheme)
	workflow = StateGraph(InitState)

	NODEGRAPH = NodeGraph()
	# Define the nodes
	for comp_id, inf in comp.items():
		if "Condition" in inf["component_name"]:
			continue
		print(comp_id)
		node = getattr(NODEGRAPH, inf["component_name"])
		# if "Input" in inf["component_name"]:
		workflow.add_node(comp_id, partial(node, inf["input"], list(map((comp_id+"_").__add__,inf['output']))) )
		# else:
		# 	workflow.add_node(comp_id, node)

	# Build graph
	for s, inf in comp.items():
		for t in inf["downstream"]:
			if not inf["upstream"]:
				workflow.add_edge(START, s)
				workflow.add_edge(s, t)
			elif not inf["downstream"]:
				workflow.add_edge(s, END)
			elif "Condition" in comp[t]["component_name"]:
				condition_define = {}
				for c_id in comp[t]["downstream"]:
					condition_define[c_id] = c_id
				node = getattr(NODEGRAPH, comp[t]["component_name"])
				workflow.add_conditional_edges(
					s, 
					partial(node, comp[t]["input"], list(map((t+"_").__add__,comp[t]['output']))),
					condition_define,
				)
			elif "Condition" in inf["component_name"]:
				continue
			else:
				workflow.add_edge(s, t)

	# Compile
	app = workflow.compile()
	return app

text_inputs = []
file_inputs = []
path = {}
def create_graph2(comp):
	state_scheme = {}
	for i, (comp_id, inf) in enumerate(comp.items()):
		param = component_class(inf["component_name"] + "Param")()
		param.update(inf["params"])
		param.check()
		inf["obj"] = component_class(inf["component_name"])(i, param)
		if "Input" in inf["component_name"]:
			text_inputs.append(f"{comp_id}_{inf['params']['key_input']}")
		if "File" in inf["component_name"]:
			file_inputs.append(f"{comp_id}_{inf['params']['key_input']}")
		if len(inf["output"])==0: continue
		for o in inf["output"]:
			state_scheme[f"{comp_id}_{o}"] = eval(inf["type_data"])
		#---- init path ----
		if len(inf["input"])==0: path[comp_id] = inf["upstream"]
		for dst in inf["downstream"]:
			if dst not in path:
				path[dst] = [comp_id]
			else:
				path[dst].append(comp_id)

	print(state_scheme)
	InitState = TypedDict("InitState", state_scheme)
	workflow = StateGraph(InitState)

	# NODEGRAPH = NodeGraph()
	# Define the nodes
	compid_loop = []
	for comp_id, inf in comp.items():
		for dst in inf["downstream"]:
			path[dst].extend(path[comp_id])
			path[dst] = list(set(path[dst]))
			if dst in path[dst]:
				compid_loop.append(dst)
		if "Condition" in inf["component_name"]:
			continue
		print(comp_id)
		# node = getattr(NODEGRAPH, inf["component_name"])
		workflow.add_node(comp_id, partial(inf["obj"], inf["input"], list(map((comp_id+"_").__add__,inf['output']))) )

	# Build graph
	# for s, inf in comp.items():
	# 	for t in inf["downstream"]:
	# 		if not inf["upstream"]:
	# 			workflow.add_edge(START, s)
	# 			workflow.add_edge(s, t)
	# 		elif not inf["downstream"]:
	# 			workflow.add_edge(s, END)
	# 		elif "Condition" in comp[t]["component_name"]:
	# 			condition_define = {}
	# 			for c_id in comp[t]["downstream"]:
	# 				condition_define[c_id] = c_id
	# 			# node = getattr(NODEGRAPH, comp[t]["component_name"])
	# 			workflow.add_conditional_edges(
	# 				s, 
	# 				partial(comp[t]["obj"], comp[t]["input"], list(map((t+"_").__add__,comp[t]['output']))),
	# 				condition_define,
	# 			)
	# 		elif "Condition" in inf["component_name"]:
	# 			continue
	# 		else:
	# 			workflow.add_edge(s, t)
	comp_id_pass = []
	for t, inf in comp.items():
		if t in compid_loop:
			inf["upstream"] = [ust for ust in inf["upstream"] if ust not in compid_loop]
			for dst in inf["downstream"]:
				workflow.add_edge(t, dst)
		if not inf["upstream"]:
			workflow.add_edge(START, t)
		elif not inf["downstream"]:
			workflow.add_edge(inf["upstream"], t)
			workflow.add_edge(t, END)
		elif "Condition" in inf["component_name"]:
			workflow.add_conditional_edges(
				inf["upstream"], 
				partial(inf["obj"], inf["input"], list(map((t+"_").__add__,inf['output']))),
				dict(zip(inf["downstream"])),
			)
			comp_id_pass.extend(inf["downstream"])
		elif t in comp_id_pass:
			continue
		else:
			workflow.add_edge(inf["upstream"], t)

	# Compile
	app = workflow.compile()
	print("----Load workflow done!")
	return app

from abc import ABC
import json
class Canvas(ABC):
	def __init__(self, dsl: str, tenant_id=None):
		self.roles = ["User", "Assistant"]
		self.path = {}
		self.messages = []
		self.file = None
		self.dsl = json.loads(dsl)
		self.comps = self.dsl["components"]
		self._tenant_id = tenant_id
		self.text_inputs = []
		self.file_inputs = []
		self.prologue = ""
		self.app = None
		# try:
		self.load()
		# except Exception as error:
		# 	print(f'Error: {error}')

	def load(self):
		# Define the nodes
		state_scheme = {}
		for i, (comp_id, inf) in enumerate(self.comps.items()):
			param = component_class(inf["component_name"] + "Param")()
			param.update(inf["params"])
			param.check()
			inf["obj"] = component_class(inf["component_name"])(i, param)
			if "Input" in inf["component_name"]:
				self.text_inputs.append(f"{comp_id}_{inf['params']['key_input']}")
				self.prologue = inf['params']['prologue']
			if "File" in inf["component_name"]:
				self.file_inputs.append(f"{comp_id}_{inf['params']['key_input']}")
			if len(inf["output"])==0: continue
			for o in inf["output"]:
				state_scheme[f"{comp_id}_{o}"] = eval(inf["type_data"])
			#---- init path ----
			if len(inf["input"])==0: self.path[comp_id] = inf["upstream"]
			for dst in inf["downstream"]:
				if dst not in self.path:
					self.path[dst] = [comp_id]
				else:
					self.path[dst].append(comp_id)

		print("----state_scheme: ", state_scheme)
		InitState = TypedDict("InitState", state_scheme)
		workflow = StateGraph(InitState)

		# NODEGRAPH = NodeGraph()
		# Define the nodes
		compid_loop = []
		for comp_id, inf in self.comps.items():
			for dst in inf["downstream"]:
				self.path[dst].extend(self.path[comp_id])
				self.path[dst] = list(set(self.path[dst]))
				if dst in self.path[dst]:
					compid_loop.append(dst)
			if "Condition" in inf["component_name"]:
				continue
			print(comp_id)
			# node = getattr(NODEGRAPH, inf["component_name"])
			workflow.add_node(comp_id, partial(inf["obj"], inf["input"], list(map((comp_id+"_").__add__,inf['output']))) )
		# print(self.path)
		# print(compid_loop)
		# exit()

		# Build graph
		compid_pass = []
		for t, inf in self.comps.items():
			if t in compid_loop:
				inf["upstream"] = [ust for ust in inf["upstream"] if ust not in compid_loop]
				for dst in inf["downstream"]:
					workflow.add_edge(t, dst)
			if not inf["upstream"]:
				workflow.add_edge(START, t)
			elif not inf["downstream"]:
				workflow.add_edge(inf["upstream"], t)
				workflow.add_edge(t, END)
			elif "Condition" in inf["component_name"]:
				workflow.add_conditional_edges(
					inf["upstream"][0], 
					partial(inf["obj"], inf["input"], list(map((t+"_").__add__,inf['output']))),
					dict(zip(inf["downstream"],inf["downstream"])),
				)
				compid_pass.extend(inf["downstream"])
			elif t in compid_pass:
				# for dst in inf["downstream"]:
				# 	workflow.add_edge(t, dst)
				continue
			else:
				workflow.add_edge(inf["upstream"], t)

		# checkpointer = MemorySaver()
		# Compile
		self.app = workflow.compile()
		print("----Load workflow done!")

	def run(self,):
		if not self.messages:
			return self.prologue
		ques = self.messages[-1][self.roles[0]]
		inputs = dict(zip_longest(self.text_inputs,[ques],fillvalue=ques))
		ifiles = dict(zip_longest(self.file_inputs,[[self.file]],fillvalue=self.file)) if self.file is not None else {}
		inputs.update(ifiles)
		for output in self.app.stream(inputs):
			print(output)
			print("---------\n")
		k_ans, v_ans = output.popitem()
		ans = v_ans[self.comps[k_ans]['params']['key_output']]
		self.messages[-1][self.roles[1]] = ans
		return ans

	def add_user_input(self, question="", file=None):
		self.messages.append({self.roles[0]: str(question), self.roles[1]: ""})
		self.file = file

if __name__=="__main__":
	# state = GraphState(inputs=["abs"])
	# print(state)
	# exit()
	# state = {"question": "Các hành vi bị nghiêm cấm về an ninh mạng", 
	#         "sub_questions": ["Các hành vi bị nghiêm cấm về an ninh mạng"], 
	#         "input": "abcd"}
	# retrieve(state)
	# a = getattr()
	# paths = [["decompose:0"], ["retrieve:0"], ["grade_documents:0"], ["condition:0"], ["generate:0"], ["transform_query:0"]]
	# paths = {
	# 			"input:0": ["decompose:0"],
	# 			"decompose:0": ["retrieve:0"], 
	# 			"retrieve:0": ["grade_documents:0"], 
	# 			"grade_documents:0": ["condition:0"], 
	# 			"condition:0": ["generate:0", "transform_query:0"], 
	# 			"transform_query:0":["retrieve:0"],
	# 			"generate:0":["output:0"], 
	# 			"output:0":[], 
	# 		}

	# Run
	# inputs = {"input_0_user_question": "Các hành vi bị nghiêm cấm về an ninh mạng"}
	# ragflow = create_graph(GraphState)
	# for output in ragflow.stream(inputs):
	# 	print(output)
	# 	print("---------\n")

	# NODEGRAPH = NodeGraph()
	# output = getattr(NODEGRAPH, "Decompose")
	# print(output(state))

	# from component import component_class
	# state = {"user_question": "Các hành vi bị nghiêm cấm về an ninh mạng", }
	# param = component_class("InputGraph" + "Param")()
	# node = component_class("InputGraph")(1, param)
	# state.update(node(["user_question"], ["question"], state))
	# print(state)

	DATA_GRAPH = open(str(ROOT1/"templates/face_recognition_pipeline.json"), "r").read()
	dsl = json.loads(DATA_GRAPH)
	comp = dsl["components"]
	ragflow = create_graph2(comp)
	ques = "who is this person?"
	file = open("hieu.jpg", "rb")
	inputs = dict(zip_longest(text_inputs,[ques],fillvalue=ques))
	ifiles = dict(zip_longest(file_inputs,[[file]],fillvalue=[file]))
	inputs.update(ifiles)
	for output in ragflow.stream(inputs):
		if list(output.keys())[0]=="input_0":
			continue
		print(output)
		print("---------\n")

	# DATA_GRAPH = open(str(ROOT1/"templates/agentic_rag_test.json"), "r").read()
	# canvas = Canvas(DATA_GRAPH)
	# while True:
	# 	ans = canvas.run()
	# 	print("==================== Bot =====================\n>    ", end='')
	# 	print(ans)

	# 	question = input("\n\t\t\t|\t  |\t   | ==================== User =====================\n\t\t\t|\t  |\t   | > ")
	# 	canvas.add_user_input(question=question)



"""
note build graph: 
	- if you want to create a loop, need a condition in that loop
	- if a node with upstream is condition, the next node 
"""