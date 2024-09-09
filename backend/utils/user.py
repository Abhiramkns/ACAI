import json
import os
from pathlib import Path


class User:
    def __init__(self, unique_id) -> None:
        self.unique_id = unique_id

        config = {}

        upload_folder = os.path.join(os.getcwd(), "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        self.user_upload_folder = f"{upload_folder}/user/{self.unique_id}"
        self.bot_upload_folder = f"{upload_folder}/bot/{self.unique_id}"
        os.makedirs(self.user_upload_folder, exist_ok=True)
        os.makedirs(self.bot_upload_folder, exist_ok=True)
        config["ALLOWED_EXTENSION"] = {"png", "jpg", "jpeg", "gif"}
        config["USER_UPLOAD_FOLDER"] = self.user_upload_folder
        config["BOT_UPLOAD_FOLDER"] = self.bot_upload_folder

        logs_path = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_path, exist_ok=True)
        config["logs"] = logs_path

        self.config = config

        self.history = []
        if os.path.exists(
            os.path.join(config["logs"], f"llm_conv_{self.unique_id}.json")
        ):
            with open(
                os.path.join(config["logs"], f"llm_conv_{self.unique_id}.json"), "r"
            ) as f:
                self.conv_log = json.load(f)
        else:
            self.conv_log = self.history.copy()

        self.curr_conv = []

        if not os.path.exists(
            os.path.join(config["logs"], f"personal_info_{self.unique_id}")
        ):
            os.makedirs(os.path.join(config["logs"], f"personal_info_{self.unique_id}"))
        self.personal_info_dir = os.path.join(
            config["logs"], f"personal_info_{self.unique_id}"
        )
        files = [
            *Path(os.path.join(config["logs"], f"personal_info_{unique_id}")).glob("*")
        ]
        self.personal_info_files = files

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

    def add_to_conv(self, content, img_url=None, role="user"):
        if role == "user":
            content = '{"message": ' + f'"{content}"' + "}"
        self.history.append({"role": role, "content": content})
        self.conv_log.append({"role": role, "content": content, "img_url": img_url})

        self.curr_conv.append({"role": role, "content": content})
        if os.path.exists(
            os.path.join(self.config["logs"], f"conversation_{self.unique_id}.json")
        ):
            with open(
                os.path.join(
                    self.config["logs"], f"conversation_{self.unique_id}.json"
                ),
                "w",
            ) as f:
                json.dump(self.curr_conv, f)
        return self.history

    def add_personal_info(self, entity, summary, img_url=None, bot_image=None):
        file_path = os.path.join(
            self.config["logs"], f"personal_info_{self.unique_id}", f"{entity}.txt"
        )
        directory_path = os.path.dirname(file_path)
        os.makedirs(directory_path, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(summary)
        self.personal_info_files.append(file_path)

        if img_url is not None:
            file_path = os.path.join(
                self.config["logs"],
                f"personal_info_{self.unique_id}",
                f"{entity}_img_url.txt",
            )
            with open(file_path, "w") as f:
                f.write(img_url)

        if bot_image is not None:
            img_save_path = os.path.join(
                self.config["BOT_UPLOAD_FOLDER"], f"{entity}_bot_img.jpg"
            )
            bot_image.save(img_save_path)

            file_path = os.path.join(
                self.config["logs"], "personal_info", f"{entity}_bot_img_url.txt"
            )
            with open(file_path, "w") as f:
                f.write(img_save_path)
