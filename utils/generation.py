import torch
from PIL import Image

from diffusers import AutoPipelineForImage2Image, AutoPipelineForText2Image
from transformers import pipeline

from .conv import Conversation

class Assistant:
    def __init__(self, config) -> None:
        # LLM interface
        self.pipe = pipeline("text-generation", model="meta-llama/Meta-Llama-3-8B-Instruct", device="cuda", max_new_tokens=1024, top_p=1, temperature=0.7, )
        # self.pipe = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.3", device="cuda", torch_dtype=torch.float16, do_sample=False, max_new_tokens=1024)

        # Text to Image
        self.t2i = AutoPipelineForText2Image.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16).to("cuda")
        
        # Image to Image
        self.i2i = AutoPipelineForImage2Image.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True
        ).to("cuda")

        self.conversation = Conversation(config)


    def detect_personal_information(self, query, img_url=None):
        print('Entering detect_personal_information')
        llm_prompt_pq_check, prev_question = self.conversation.get_check_personal_question_prompt(query)
        if llm_prompt_pq_check is not None:
            print('llm_pq_prompt: ', llm_prompt_pq_check)
            output = self.pipe(llm_prompt_pq_check)[-1]['generated_text'][-1]['content']
            print('pq check: ', output)
            answered_personal_question_flag, entity, summary = self.conversation.decode_pq_check(output)
            if answered_personal_question_flag:
                self.conversation.add_personal_info(entity, summary, img_url, prev_question, query)
        
        print('Exiting detect_personal_information')

    def enrich_user_query(self, query):
        print('Entering enrich_user_query')
        kb_img_url = None
        if len(self.conversation.personal_info_files) > 0:
            llm_prompt_enrich_query, doc, score = self.conversation.enrich_user_query_prompt(query)
            print('llm_prompt_enrich_query: ', llm_prompt_enrich_query)
            if score >= 0.5:
                output = self.pipe(llm_prompt_enrich_query)[-1]['generated_text'][-1]['content']
                print('enriched output: ', output)
                enriched_query, kb_img_url = self.conversation.decode_enriched_query(output, doc, score)
                print('enriched query: ', enriched_query)
                query = enriched_query
        
        print('Exiting enrich_user_query')
        return query, kb_img_url

    def llm_response(self, query, img_url=None, response_img_url=None):
        # Get knowledge from KB and enrich user query.
        new_query, kb_img_url = self.enrich_user_query(query)

        # Check if the user answered LLM's personal questions.
        self.detect_personal_information(query, img_url)

        # Generate response for the user query
        print('query: ', new_query)
        messages = self.conversation.get_history(new_query.strip())
        # print('messages: ', messages)
        outputs = self.pipe(messages)
        output = outputs[-1]['generated_text'][-1]['content']
        print('output: ', output)
        res = self.conversation.decode_response(output)

        return res, kb_img_url
    
    def text2image(self, prompt):
        print('Inside text2image')
        image = self.t2i(prompt=prompt).images[0]
        image = image.resize((768, 768))
        return image
    
    def image2image(self, init_image, prompt):
        print('Inside image2image')
        image = self.i2i(prompt, image=init_image, strength=0.8, guidance_scale=10.5).images[0]
        image = image.resize((768, 768))
        return image

    def generate(self, query, image_url=None, response_image_url=None):
        output, kb_img_url = self.llm_response(query, image_url, response_image_url)
        response = output['message']
        img_flag = None if output['task'] == "null" else output['task']
        prompt = output['prompt']
        follow_up_question = output['question']

        image = None
        if image_url is not None:
            image = Image.open(image_url).convert('RGB')
            image = image.resize((768, 768))
        elif kb_img_url is not None:
            image = Image.open(image_url).convert('RGB')
            image = image.resize((768, 768))

        if image is not None:
            assert type(image) != type(None), "Input Image is not provided"
            image = self.image2image(image, prompt)
        elif img_flag is not None:
            # if img_flag == 'Generation':
            image = self.text2image(prompt)
                
        torch.cuda.empty_cache()
        return response, follow_up_question, image

if __name__ == "__main__":
    model = Assistant()
    # url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/sdxl-text2img.png"
    # init_image = load_image(url)
    img = Image.open('../../test_images/test3.png')
    response, image = model.generate('Remove the tail of the cat', img)
    image.save('output.png')