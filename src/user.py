import base64
import requests
import json
import uuid


class User:
    def __init__(self) -> None:
        self.unique_id = uuid.uuid4()

    def chat(self, message, audio):
        data = {"id": str(self.unique_id), "message": message}
        url = "http://127.0.0.1:5000/agent"
        audio_data_encoded = None
        if audio is not None:
            sample_rate = audio[0]
            audio_data = audio[1]
            audio_data_encoded = base64.b64encode(audio_data.tobytes()).decode("utf-8")
            data["sample_rate"] = sample_rate
            data["audio"] = audio_data_encoded
        json_data = json.dumps(data)
        response = requests.post(
            url, data=json_data, headers={"Content-Type": "application/json"}
        )
        response_json = response.json()
        bot_message = response_json["bot_msg"]
        bot_img_url = response_json["bot_img_url"]
        user_message = response_json["user_msg"]
        user_img_url = response_json["user_img_url"]

        return bot_message, bot_img_url, user_message, user_img_url
