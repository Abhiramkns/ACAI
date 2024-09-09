import os
import uuid
from PIL import Image
import base64
import numpy as np
from flask import Flask, request, jsonify
from utils.generation import Assistant
from utils.user import User


os.environ["OPENAI_API_KEY"] = (
    "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"
)

assistant = Assistant()

app = Flask(__name__)

USERS = {}

# def delete_folder(folder_path):
#     try:
#         # Delete the folder and all its contents
#         shutil.rmtree(folder_path)
#         print(f"Deleted folder {folder_path}")
#     except Exception as e:
#         print(f"Failed to delete folder {folder_path}. Reason: {e}")

# def signal_handler(sig, frame):
#     print("Signal received. Deleting all files in the folder...")
#     delete_folder(upload_folder)
#     delete_folder(logs_path)
#     sys.exit(0)


# # Register the signal handler for SIGINT (Ctrl+C)
# signal.signal(signal.SIGINT, signal_handler)


def respond(user: User, message, audio):
    unique_id = uuid.uuid4()
    user_message = message["text"]
    user_img_url = None
    if len(message["files"]) > 0:
        img = Image.open(message["files"][0]).resize((768, 768))
        filename = f"user_{unique_id}.png"
        user_img_url = os.path.join(user.config["USER_UPLOAD_FOLDER"], filename)
        img.save(user_img_url)

    filename = f"assistant_{unique_id}.png"
    bot_img_url = os.path.join(user.config["BOT_UPLOAD_FOLDER"], filename)

    bot_message, bot_image, user_message = assistant.generate(
        user, user_message, user_img_url, bot_img_url, audio
    )
    if bot_image is not None:
        bot_image.save(bot_img_url)
    else:
        bot_img_url = None

    return jsonify(
        {
            "status_code": 200,
            "user_msg": user_message,
            "user_img_url": user_img_url,
            "bot_msg": bot_message,
            "bot_img_url": bot_img_url,
        }
    )


# Simple POST API
@app.route("/agent", methods=["POST"])
def handle_data():
    # Get JSON data from the request
    data = request.get_json()
    if data["id"] in USERS:
        user = USERS[data["id"]]
    else:
        user = User(data["id"])
        USERS[data["id"]] = user

    audio = None
    if "audio" in data:
        audio_data = np.frombuffer(base64.b64decode(data["audio"]), dtype=np.int16)
        sample_rate = data["sample_rate"]
        audio = (sample_rate, audio_data)

    return respond(user, data["message"], audio), 200


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
