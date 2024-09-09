import gradio as gr
import signal
import shutil
import sys
from src.user import User


def respond(student, message, audio, chat_history):
    bot_message, bot_img_url, user_message, user_img_url = student.chat(message, audio)

    chat_history.append((user_message, None))
    if user_img_url is not None:
        chat_history.append(((user_img_url,), None))

    chat_history.append((None, bot_message))
    if bot_img_url is not None:
        chat_history.append((None, (bot_img_url,)))

    return (
        gr.MultimodalTextbox(value=None, show_label=False),
        gr.update(value=None),
        chat_history,
    )


with gr.Blocks() as demo:
    student = gr.State(User())
    chatbot = gr.Chatbot(
        avatar_images=["./assets/default_user.png", "./assets/ai_bot.jpeg"],
        height=580,
    )
    with gr.Row():
        audio = gr.Audio(sources=["microphone"], scale=1)
        msg = gr.MultimodalTextbox(show_label=False, scale=3)

    msg.submit(respond, [student, msg, audio, chatbot], [msg, audio, chatbot])

    # def delete_folder(folder_path):
    #     try:
    #         # Delete the folder and all its contents
    #         shutil.rmtree(folder_path)
    #         print(f"Deleted folder {folder_path}")
    #     except Exception as e:
    #         print(f"Failed to delete folder {folder_path}. Reason: {e}")

    # def signal_handler(sig, frame):
    #     print("Signal received. Deleting all files in the folder...")
        
    #     sys.exit(0)


    # # Register the signal handler for SIGINT (Ctrl+C)
    # signal.signal(signal.SIGINT, signal_handler)

demo.launch(share=True)
