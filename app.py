import gradio as gr
import os
import uuid
from PIL import Image

from utils.generation import Assistant


config = {}
upload_folder = os.path.join(os.getcwd(), 'uploads')
os.makedirs(upload_folder, exist_ok=True)
user_upload_folder = f"{upload_folder}/user"
bot_upload_folder = f"{upload_folder}/bot"
os.makedirs(user_upload_folder, exist_ok=True)
os.makedirs(bot_upload_folder, exist_ok=True)
config['ALLOWED_EXTENSION'] = {'png', 'jpg', 'jpeg', 'gif'}
config['USER_UPLOAD_FOLDER'] = user_upload_folder
config['BOT_UPLOAD_FOLDER'] = bot_upload_folder
logs_path = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_path, exist_ok=True)
config['logs'] = logs_path

assistant = Assistant(config)

def respond(message, chat_history):
    unique_id = uuid.uuid4()
    user_message = message['text']
    user_img_url = None
    if len(message['files']) > 0:
        img = Image.open(message['files'][0]).resize((768, 768))
        filename = f'user_{unique_id}.png'
        user_img_url = os.path.join(config['USER_UPLOAD_FOLDER'], filename)
        img.save(user_img_url)

    filename = f'assistant_{unique_id}.png'
    bot_img_url = os.path.join(config['BOT_UPLOAD_FOLDER'], filename)

    bot_message, bot_question, bot_image = assistant.generate(user_message, user_img_url, bot_img_url)
    if bot_image is not None:
        bot_image.save(bot_img_url)

    chat_history.append((user_message, None))
    if user_img_url is not None:
        chat_history.append(((user_img_url,), None))

    chat_history.append((None, bot_message))
    if bot_image is not None:
        chat_history.append((None, (bot_img_url,)))
    
    # if bot_question is not None:
    #     chat_history.append((None, bot_question))

    return gr.MultimodalTextbox(value=None, show_label=False), chat_history


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(
        value=[(None, "Hello! How can I assist you today?\n 1. Would you like to view images of famous personalities?\n 2. Are you interested in seeing pictures of your favorite foods?\n 3. Would you like to explore images of your favorite places?\n Please let me know how I can help!")], 
        avatar_images=["./assets/default_user.png", "./assets/ai_bot.jpeg"],
        height=500
    )
    msg = gr.MultimodalTextbox(show_label=False)

    msg.submit(respond, [msg, chatbot], [msg, chatbot])

demo.launch(share=True)