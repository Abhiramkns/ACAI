import re
import json
import os
from typing import List

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

from .prompts import (
    assistant_response_prompt_template1,
    personal_question_check_prompt_template_3,
    llm_response_output_format,
    assistant_get_info_prompt,
    get_info_output_format,
    get_info_examples,
)
from collections import defaultdict
from pathlib import Path


def return_list():
    return []


class Conversation:
    def __init__(self, config) -> None:
        self.config = config

        self.history = []
        if os.path.exists(os.path.join(config["logs"], "llm_conv.json")):
            with open(os.path.join(config["logs"], "llm_conv.json"), "r") as f:
                self.conv_log = json.load(f)
        else:
            self.conv_log = self.history.copy()

        self.curr_conv = []

        if not os.path.exists(os.path.join(config["logs"], "personal_info")):
            os.makedirs(os.path.join(config["logs"], "personal_info"))
        files = [*Path(os.path.join(config["logs"], "personal_info")).glob("*")]
        self.personal_info_files = files

        # RAG model settings
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")
        Settings.llm = Ollama(model="llama3", request_timeout=360.0)

    def get_internet_info_prompt(self, query):
        conversation_str = self.get_conversation_str()
        conversation_str += f"User: {query.strip()}\n"
        if conversation_str == "":
            return None
        prompt = assistant_get_info_prompt.format(
            get_info_output_format, get_info_examples, conversation_str
        )
        return prompt

    def get_llm_prompt(self, relevant_info, user_message, internet_info):
        conversation_str = self.get_conversation_str()
        if conversation_str != "":
            conversation_str = f"Conversation: {conversation_str}"
        if relevant_info != "":
            relevant_info = f"User Personal Context Str: {relevant_info}"
        if internet_info != "":
            internet_info = f"Internet Information: {internet_info}"
        prompt = assistant_response_prompt_template1.format(
            llm_response_output_format,
            relevant_info,
            internet_info,
            conversation_str,
            user_message,
        )
        return prompt

    def add_to_conv(self, content, img_url=None, role="user"):
        if role == "user":
            content = '{"message": ' + f'"{content}"' + "}"
        self.history.append({"role": role, "content": content})
        self.conv_log.append({"role": role, "content": content, "img_url": img_url})

        self.curr_conv.append({"role": role, "content": content})
        return self.history

    def decode_get_info_result(self, output):
        pattern = (
            r'\{\s*\"reasoning\":\s*"([^"]*)",\s*\"search prompt\":\s*"([^"]*)"\s*}'
        )
        match = re.search(pattern, output, re.DOTALL)
        res = {"reasoning": match.group(1), "question": match.group(2)}
        return res["question"]

    def decode_llm_response(self, output):
        pattern = r'\{\s*\"reasoning\":\s*"([^"]*)",\s*\"message\":\s*"([^"]*)"\s*,\s*\"prompt\":\s*"([^"]*)"\s*}'
        match = re.search(pattern, output, re.DOTALL)
        res = {
            "reasoning": match.group(1),
            "message": match.group(2),
            "prompt": match.group(3),
        }
        return res

    def get_conversation_str(self):
        context_str = ""
        for i in range(len(self.curr_conv)):
            message = self.curr_conv[i]
            if message["role"] == "assistant":
                assistant_message = json.loads(message["content"])
                context_str += f"Assistant: {assistant_message['message']}\n"
            else:
                user_message = json.loads(message["content"])
                context_str += f"User: {user_message['message']}\n"
        return context_str

    def get_check_personal_question_prompt(self, user_response):
        if len(self.curr_conv) == 0:
            return None
        context_str = self.get_conversation_str()
        prompt: List[str] = personal_question_check_prompt_template_3.copy()
        prompt[-1]["content"] = prompt[-1]["content"].format(
            context_str=context_str, user_response=user_response
        )

        return prompt

    def decode_pq_check(self, output_string):
        pattern = r'"entity":\s*"([^"]*)",\s*"summary":\s*"([^"]*)"'
        match = re.search(pattern, output_string)
        if match:
            entity, summary = match.groups()
            if entity == "null":
                return False, None, None
            return True, entity, summary
        else:
            return False, None, None

    def get_relevant_info(self, user_query):
        documents = SimpleDirectoryReader(
            os.path.join(self.config["logs"], "personal_info"), recursive=True
        ).load_data()
        index = VectorStoreIndex.from_documents(documents)

        query_engine = index.as_query_engine()
        response = query_engine.retrieve(user_query)
        if len(response) == 0:
            return ""
        score = response[0].score
        with open(response[0].metadata["file_path"], "r") as f:
            relevant_information = f.read()

        if score >= 0.5:
            img_url = None
            img_doc_name = (
                f"{response[0].metadata['file_path'].split(".")[0]}_img_url.txt"
            )
            if os.path.exists(img_doc_name):
                with open(img_doc_name, "r") as f:
                    img_url = f.read()
            return relevant_information, img_url
        return "", None

    def decode_enriched_query(self, output_string, doc, score):
        pattern = r'"enriched_query":\s*"([^"]*)"\s*'

        match = re.search(pattern, output_string)
        if match:
            enriched_query = match.group(1)

            img_url = None
            img_doc_name = f"{doc.split(".")[0]}_img_url.txt"
            if os.path.exists(img_doc_name):
                with open(img_doc_name, "r") as f:
                    img_url = f.read()

            return enriched_query, img_url
        return None, None

    def add_personal_info(self, entity, summary, img_url=None):
        file_path = os.path.join(self.config["logs"], "personal_info", f"{entity}.txt")
        directory_path = os.path.dirname(file_path)
        os.makedirs(directory_path, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(summary)
        self.personal_info_files.append(file_path)

        if img_url is not None:
            file_path = os.path.join(
                self.config["logs"], "personal_info", f"{entity}_img_url.txt"
            )
            with open(file_path, "w") as f:
                f.write(img_url)
