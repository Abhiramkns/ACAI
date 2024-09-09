import torch
from PIL import Image
import numpy as np
import json
import requests
import time

from diffusers import AutoPipelineForImage2Image, AutoPipelineForText2Image
from transformers import (
    AutoTokenizer,
    pipeline,
    TextIteratorStreamer,
    AutoModelForCausalLM,
)

from .conv import Conversation
from .stop_thread_util import thread_with_trace


def pipe_thread(pipe, prompt):
    pipe(prompt)


class Assistant:
    def __init__(self, config) -> None:
        # Automatic speech recognition.
        self.transcriber = pipeline(
            "automatic-speech-recognition", model="openai/whisper-base.en"
        )

        # LLM interface
        self.tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Meta-Llama-3.1-8B-Instruct"
        )
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Meta-Llama-3.1-8B-Instruct"
        ).to("cuda")

        # Text to Image
        self.t2i = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0"
        )

        # Image to Image
        self.i2i = AutoPipelineForImage2Image.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            variant="fp16",
            use_safetensors=True,
        )

        self.conversation = Conversation(config)

        self.retry = 2

    def run_llm(self, prompt, response_decoder=None):
        inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")
        streamer = TextIteratorStreamer(
            self.tokenizer, timeout=10.0, skip_prompt=True, skip_special_tokens=True
        )
        generation_kwargs = dict(
            inputs,
            streamer=streamer,
            max_new_tokens=1024,
            top_p=1,
            temperature=0.7,
            return_dict_in_generate=True,
        )
        t = thread_with_trace(target=self.llm_model.generate, kwargs=generation_kwargs)
        t.start()
        response = ""
        for new_text in streamer:
            response += new_text
            if response_decoder is None:
                res = response
                continue
            res = response_decoder(response)
            if res is not None:
                t.kill()
                t.join()
                break
        return res

    def detect_personal_information(self, query, img_url=None, bot_image=None):
        print("Entering detect_personal_information")
        llm_prompt_pq_check = self.conversation.get_check_personal_question_prompt(
            query
        )
        if llm_prompt_pq_check is not None:
            print("llm_pq_prompt: ", llm_prompt_pq_check)
            output = self.run_llm(
                llm_prompt_pq_check, self.conversation.decode_pq_check
            )
            print("pq check: ", output)
            answered_personal_question_flag, entity, summary = output
            if answered_personal_question_flag:
                self.conversation.add_personal_info(entity, summary, img_url, bot_image)

        print("Exiting detect_personal_information")

    def get_relevant_info(self, query):  # , queue):
        print("get relevant info")
        kb_img_url = None
        relevant_info = ""
        if len(self.conversation.personal_info_files) > 0:
            relevant_info, kb_img_url = self.conversation.get_relevant_info(query)
        # queue.put(("get_relevant_info", relevant_info, kb_img_url))
        return relevant_info, kb_img_url

    def response_to_user(self, relevant_info, user_message, internet_info, img_url):
        res = {
            "message": "Error while processing the message. Please try again later",
            "prompt": "",
            "reasoning": "",
        }
        for _ in range(self.retry):
            try:
                prompt = self.conversation.get_llm_prompt(
                    relevant_info, user_message, internet_info, img_url
                )
                print("prompt: ", prompt)
                res = self.run_llm(prompt, self.conversation.decode_llm_response)
                if res is None:
                    raise
                print("res: ", res)
                return res, json.dumps(res)
            except:
                pass
        return res, ""

    def get_relevant_information_from_internet(self, query):  # , queue):
        prompt = self.conversation.get_internet_info_prompt(query)
        print("internet info prompt: ", prompt)
        question = self.run_llm(prompt, self.conversation.decode_get_info_result)
        if question is None or question == "":
            return ""

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": "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",
            "query": question,
            "search_depth": "basic",
            "include_answer": True,
            "include_images": False,
            "include_raw_content": False,
            "max_results": 1,
            "include_domains": [],
            "exclude_domains": [],
        }
        result = json.loads(requests.post(url, json=payload).content)
        with open("internet_response", "w") as f:
            json.dump(result, f)
        print("internet result: ", result["answer"])
        return result["answer"]

    def process_message(self, query, img_url=None, response_img_url=None):
        start_time = time.time()
        relevant_info, kb_img_url = self.get_relevant_info(query)
        internet_info = self.get_relevant_information_from_internet(query)

        mid_time = time.time()
        print(f"Time taken to retrieve information: {mid_time - start_time} seconds")

        # Get response from llm
        bot_image_url = None
        res, output = self.response_to_user(
            relevant_info, query.strip(), internet_info, img_url
        )
        if res["prompt"] != "":
            bot_image_url = response_img_url

        response = res["message"]
        prompt: str = res["prompt"]

        # Check if the user answered LLM's personal questions.
        t = thread_with_trace(
            target=self.detect_personal_information, args=(query, img_url, bot_image_url)
        )
        t.start()

        # Generate Image
        image = None
        if img_url is not None:
            image = Image.open(img_url).convert("RGB")
            image = image.resize((768, 768))
        elif kb_img_url is not None:
            image = Image.open(kb_img_url).convert("RGB")
            image = image.resize((768, 768))

        bot_image = None
        if prompt != "":
            if image is not None:
                assert type(image) != type(None), "Input Image is not provided"
                bot_image = self.image2image(image, prompt)
            else:
                bot_image = self.text2image(prompt)

        end_time = time.time()
        time_difference = end_time - start_time
        print(f"Time taken to process the message: {time_difference} seconds")

        # Add user query to history.
        self.conversation.add_to_conv(query.strip())

        # Add llm resposne to the history
        self.conversation.add_to_conv(output, bot_image_url, role="assistant")

        return response, bot_image, query

    def text2image(self, prompt):
        print("Inside text2image")
        self.t2i.to("cuda")
        image = self.t2i(prompt=prompt, num_inference_steps=10).images[0]
        self.t2i.to("cpu")
        image = image.resize((768, 768))
        return image

    def image2image(self, init_image, prompt):
        print("Inside image2image")
        self.i2i.to("cuda")
        image = self.i2i(
            prompt,
            image=init_image,
            strength=0.8,
            guidance_scale=10.5,
            num_inference_steps=10,
        ).images[0]
        self.i2i.to("cpu")
        image = image.resize((768, 768))
        return image

    def generate(self, query, image_url=None, response_image_url=None, audio=None):
        if audio is not None:
            sr, y = audio
            y = y.astype(np.float32)
            y /= np.max(np.abs(y))
            query = self.transcriber({"sampling_rate": sr, "raw": y})["text"]
        response, image, query = self.process_message(
            query, image_url, response_image_url
        )

        torch.cuda.empty_cache()
        return response, image, query


if __name__ == "__main__":
    model = Assistant()
    # url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/sdxl-text2img.png"
    # init_image = load_image(url)
    img = Image.open("../../test_images/test3.png")
    response, image = model.generate("Remove the tail of the cat", img)
    image.save("output.png")
