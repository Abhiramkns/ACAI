import gradio as gr
import os
import signal
import sys
import shutil
import uuid
from PIL import Image

from utils.generation import Assistant


config = {}
upload_folder = os.path.join(os.getcwd(), "uploads")
os.makedirs(upload_folder, exist_ok=True)
user_upload_folder = f"{upload_folder}/user"
bot_upload_folder = f"{upload_folder}/bot"
os.makedirs(user_upload_folder, exist_ok=True)
os.makedirs(bot_upload_folder, exist_ok=True)
config["ALLOWED_EXTENSION"] = {"png", "jpg", "jpeg", "gif"}
config["USER_UPLOAD_FOLDER"] = user_upload_folder
config["BOT_UPLOAD_FOLDER"] = bot_upload_folder
logs_path = os.path.join(os.getcwd(), "logs")
os.makedirs(logs_path, exist_ok=True)
config["logs"] = logs_path


def delete_folder(folder_path):
    try:
        # Delete the folder and all its contents
        shutil.rmtree(folder_path)
        print(f"Deleted folder {folder_path}")
    except Exception as e:
        print(f"Failed to delete folder {folder_path}. Reason: {e}")


def signal_handler(sig, frame):
    print("Signal received. Deleting all files in the folder...")
    delete_folder(upload_folder)
    delete_folder(logs_path)
    sys.exit(0)


# Register the signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

assistant = Assistant(config)


def respond(message, audio, chat_history):
    unique_id = uuid.uuid4()
    user_message = message["text"]
    user_img_url = None
    if len(message["files"]) > 0:
        img = Image.open(message["files"][0]).resize((768, 768))
        filename = f"user_{unique_id}.png"
        user_img_url = os.path.join(config["USER_UPLOAD_FOLDER"], filename)
        img.save(user_img_url)

    filename = f"assistant_{unique_id}.png"
    bot_img_url = os.path.join(config["BOT_UPLOAD_FOLDER"], filename)

    bot_message, bot_image, user_message = assistant.generate(
        user_message, user_img_url, bot_img_url, audio
    )
    if bot_image is not None:
        bot_image.save(bot_img_url)

    chat_history.append((user_message, None))
    if user_img_url is not None:
        chat_history.append(((user_img_url,), None))

    chat_history.append((None, bot_message))
    if bot_image is not None:
        chat_history.append((None, (bot_img_url,)))

    return (
        gr.MultimodalTextbox(value=None, show_label=False),
        gr.update(value=None),
        chat_history,
    )


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(
        avatar_images=["./assets/default_user.png", "./assets/ai_bot.jpeg"],
        height=580,
    )
    with gr.Row():
        audio = gr.Audio(sources=["microphone"], scale=1)
        msg = gr.MultimodalTextbox(show_label=False, scale=3)

    msg.submit(respond, [msg, audio, chatbot], [msg, audio, chatbot])

demo.launch(share=True)
