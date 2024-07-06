import re
import json
import os
from typing import List

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

from .prompts import (
    assistant_response_prompt_template1,
    personal_question_check_prompt_template,
    personal_question_check_prompt_template_2,
    personal_question_check_prompt_template_3,
    output_format,
    example_output,
    enrich_usery_query_prompt
)
from collections import defaultdict
from pathlib import Path

def return_list():
    return []

class Conversation:
    def __init__(self, config) -> None:
        self.config = config          

        self.history = assistant_response_prompt_template1
        if os.path.exists(os.path.join(config['logs'], 'llm_conv.json') ):
            with open(os.path.join(config['logs'], 'llm_conv.json'), 'r') as f:
                self.conv_log = json.load(f)
        else:
            self.conv_log = self.history.copy()

        self.curr_conv = []

        if not os.path.exists(os.path.join(config['logs'], 'personal_info')):
            os.makedirs(os.path.join(config['logs'], 'personal_info'))
        files = [*Path(os.path.join(config['logs'], 'personal_info')).glob('*')]
        self.personal_info_files = files

        # RAG model settings
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")
        Settings.llm = Ollama(model="llama3", request_timeout=360.0)


    def get_history(self, query, img_url=None):
        self.history.append({
            "role": "user",
            "content": '{"message": ' + f'"{query}"' + "}"
        })
        self.conv_log.append(
            {
                "role": "user",
                "content": '{"message": ' + f'"{query}"' + "}",
                "img_url": img_url
            }
        )

        self.curr_conv.append(
            {
                "role": "user",
                "content": '{"message": ' + f'"{query}"' + "}"
            }
        )
        return self.history

    def decode_response(self, output, response_img_url=None):
        pattern = r'\{\s*\"message\":\s*"([^"]*)",\s*\"task\":\s*"([^"]*)",\s*\"prompt\":\s*"([^"]*)",\s*\"question\":\s*"([^"]*)"\s*}'
        match = re.search(pattern, output, re.DOTALL)
        res = {
            "message": match.group(1),
            "task":  match.group(2),
            "prompt":  match.group(3),
            "question":  match.group(4)
        }
        self.history.append(
            {
                "role": "assistant",
                "content": json.dumps(res)
            }
        )
        self.conv_log.append(
            {
                "role": "assistant",
                "content": json.dumps(res),
                "img_url": response_img_url if res["task"] != "null" else None
            }
        )

        self.curr_conv.append(
            {
                "role": "assistant",
                "content": json.dumps(res)
            }
        )

        return res
    
    def get_context_str(self):
        context_str = ""
        for i in range(len(self.curr_conv) - 1):
            message = self.curr_conv[i]
            if message['role'] == 'assistant':
                assistant_message = json.loads(message['content'])
                context_str += f"Assistant: {assistant_message['message']}\n"
            else:
                user_message = json.loads(message['content'])
                context_str += f"User: {user_message['message']}\n"
        return context_str

    def get_check_personal_question_prompt(self, user_response):
        if len(self.curr_conv) == 0:
            return None, None
        assistant_prev_response = self.curr_conv[-1]["content"]
        assistant_prev_response = json.loads(assistant_prev_response)
        question = assistant_prev_response["question"]
        if question == "null":
            return None, None
        context_str = self.get_context_str()
        prompt: List[str] = personal_question_check_prompt_template_3.copy()
        prompt[-1]["content"] = prompt[-1]["content"].format(context_str=context_str, question=question, user_response=user_response)
        # prompt = personal_question_check_prompt_template_2.format(output_format=output_format, example_output=example_output, context_str=context_str, question=question, user_response=user_response)

        return prompt, question

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

    def enrich_user_query_prompt(self, user_query):
        documents = SimpleDirectoryReader(os.path.join(self.config['logs'], 'personal_info')).load_data()
        index = VectorStoreIndex.from_documents(documents)
        
        query_engine = index.as_query_engine()
        response = query_engine.retrieve(user_query)
        score = response[0].score
        with open(response[0].metadata['file_path'], 'r') as f:
            relevant_information = f.read()
        
        if score >= 0.5:
            prompt = [
                # *kb_search_prompt,
                *enrich_usery_query_prompt,
                {
                    "role": "user",
                    "content": '{"Relevant Information": ' + relevant_information + ', \n"User Query": "' + user_query + '"}'
                }
            ]

            return prompt, response[0].metadata['file_path'], score
        else:
            return user_query, response[0].metadata['file_path'], score
    
    def decode_enriched_query(self, output_string, doc, score):
        pattern = r'"enriched_query":\s*"([^"]*)"\s*'

        match = re.search(pattern, output_string)
        if match:
            enriched_query = match.group(1)
            
            img_url = None
            img_doc_name = f"{doc.split(".")[0]}_img_url.txt"
            if os.path.exists(img_doc_name):
                with open(img_doc_name, 'r') as f:
                    img_url = f.read()

            return enriched_query, img_url
        return None, None

    def add_personal_info(self, entity, summary, img_url=None, question=None, complete_answer=None):
        file_path = os.path.join(self.config['logs'], 'personal_info', f"{entity}.txt")
        with open(file_path, "w") as f:
            f.write(summary)
        self.personal_info_files.append(file_path)

        if img_url is not None:
            file_path = os.path.join(self.config['logs'], 'personal_info', f"{entity}_img_url.txt")
            with open(file_path, "w") as f:
                f.write(img_url)