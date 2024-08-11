import torch
from PIL import Image
import numpy as np
import json
import requests

from diffusers import AutoPipelineForImage2Image, AutoPipelineForText2Image
from transformers import pipeline

from .conv import Conversation


class Assistant:
    def __init__(self, config) -> None:
        # Automatic speech recognition.
        self.transcriber = pipeline(
            "automatic-speech-recognition", model="openai/whisper-base.en"
        )

        # LLM interface
        self.pipe = pipeline(
            "text-generation",
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            device="cuda",
            max_new_tokens=1024,
            top_p=1,
            temperature=0.7,
            return_full_text=False,
        )

        # Text to Image
        self.t2i = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16
        ).to("cuda")

        # Image to Image
        self.i2i = AutoPipelineForImage2Image.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
        ).to("cuda")

        self.conversation = Conversation(config)

        self.retry = 2

    def detect_personal_information(self, query, img_url=None):
        print("Entering detect_personal_information")
        llm_prompt_pq_check = self.conversation.get_check_personal_question_prompt(
            query
        )
        if llm_prompt_pq_check is not None:
            print("llm_pq_prompt: ", llm_prompt_pq_check)
            output = self.pipe(llm_prompt_pq_check)[-1]["generated_text"]
            print("pq check: ", output)
            answered_personal_question_flag, entity, summary = (
                self.conversation.decode_pq_check(output)
            )
            if answered_personal_question_flag:
                self.conversation.add_personal_info(entity, summary, img_url)

        print("Exiting detect_personal_information")

    def get_relevant_info(self, query):
        print("get relevant info")
        kb_img_url = None
        relevant_info = ""
        if len(self.conversation.personal_info_files) > 0:
            relevant_info, kb_img_url = self.conversation.get_relevant_info(query)
        return relevant_info, kb_img_url

    def response_to_user(self, relevant_info, user_message, internet_info):
        res = {
            "message": "Error while processing the message. Please try again later",
            "prompt": "",
            "reasoning": "",
        }
        for _ in range(self.retry):
            try:
                prompt = self.conversation.get_llm_prompt(
                    relevant_info, user_message, internet_info
                )
                print("prompt: ", prompt)
                outputs = self.pipe(prompt)
                output = outputs[0]["generated_text"]
                res = self.conversation.decode_llm_response(output)
                print("res: ", res)
                return res, json.dumps(res)
            except:
                return res, ""
        return res, ""

    def get_relevant_information_from_internet(self, query):
        prompt = self.conversation.get_internet_info_prompt(query)
        print("internet info prompt: ", prompt)
        output = self.pipe(prompt)[0]["generated_text"]
        question = self.conversation.decode_get_info_result(output)
        if question == "":
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
            json.dump({"question": question, "result": result}, f)
        print("internet result: ", result)
        return result

    def process_message(self, query, img_url=None, response_img_url=None):
        # Get relevant information from user personal details
        relevant_info, kb_img_url = self.get_relevant_info(query)

        # Check if the user answered LLM's personal questions.
        self.detect_personal_information(query, img_url)

        # Get relevant information from the internet.
        internet_info = self.get_relevant_information_from_internet(query)

        # Get response from llm
        bot_image_url = None
        res, output = self.response_to_user(relevant_info, query.strip(), internet_info)
        if res["prompt"] != "":
            bot_image_url = response_img_url

        # Add user query to history.
        self.conversation.add_to_conv(query.strip())

        # Add llm resposne to the history
        self.conversation.add_to_conv(output, bot_image_url, role="assistant")

        return res, kb_img_url

    def text2image(self, prompt):
        print("Inside text2image")
        image = self.t2i(prompt=prompt).images[0]
        image = image.resize((768, 768))
        return image

    def image2image(self, init_image, prompt):
        print("Inside image2image")
        image = self.i2i(
            prompt, image=init_image, strength=0.8, guidance_scale=10.5
        ).images[0]
        image = image.resize((768, 768))
        return image

    def generate(self, query, image_url=None, response_image_url=None, audio=None):
        if audio is not None:
            sr, y = audio
            y = y.astype(np.float32)
            y /= np.max(np.abs(y))
            query = self.transcriber({"sampling_rate": sr, "raw": y})["text"]
        output, kb_img_url = self.process_message(query, image_url, response_image_url)

        response = output["message"]
        prompt: str = output["prompt"]

        image = None
        if image_url is not None:
            image = Image.open(image_url).convert("RGB")
            image = image.resize((768, 768))
        elif kb_img_url is not None:
            image = Image.open(kb_img_url).convert("RGB")
            image = image.resize((768, 768))

        if prompt != "":
            if image is not None:
                assert type(image) != type(None), "Input Image is not provided"
                image = self.image2image(image, prompt)
            else:
                image = self.text2image(prompt)

        torch.cuda.empty_cache()
        return response, image, query


if __name__ == "__main__":
    model = Assistant()
    # url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/sdxl-text2img.png"
    # init_image = load_image(url)
    img = Image.open("../../test_images/test3.png")
    response, image = model.generate("Remove the tail of the cat", img)
    image.save("output.png")
