import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, StringVar, BooleanVar, Toplevel
from pydantic import BaseModel
import requests
import threading
import re

# 定义配置模型
class Config(BaseModel):
    api_url: str = "https://api.example.com/v1/chat/completions"
    api_key: str = "your_api_key_here"
    model: str = "default_model"
    user_name: str = "用户"
    robot_name: str = "AI"
    analysis_prompt_file: str = "无"  # 分析机器人的提示词文件
    reply_prompt_file: str = "无"     # 回复机器人的提示词文件
    context_enabled: bool = False

    def save_to_file(self, file_path="config.json"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.dict(), f, indent=4)

    @classmethod
    def load_from_file(cls, file_path="config.json"):
        if not os.path.exists(file_path):
            return cls()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except json.JSONDecodeError:
            return cls()

# 定义聊天工具类
class RobotChatTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Chat Tool")
        self.config = Config.load_from_file()
        self.emotion_window = None  # 分析机器人的分析窗口
        self.expected_window = None  # 回复机器人的回复窗口
        self.last_robot_reply = None  # 存储机器人的回复内容
        self.prompt_files = self.get_prompt_files()  # 获取当前目录下的所有 .txt 文件
        self.create_widgets()

    def get_prompt_files(self):
        """获取当前目录下所有 .txt 后缀的文件"""
        prompt_files = [f for f in os.listdir() if f.endswith('.txt')]
        prompt_files.insert(0, "无")  # 添加“无”选项
        return prompt_files

    def create_widgets(self):
        # 配置框
        config_frame = ttk.LabelFrame(self.root, text="配置", padding=5)
        config_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(config_frame, text="API URL:").grid(row=0, column=0, sticky="w")
        self.api_url_entry = ttk.Entry(config_frame, width=50)
        self.api_url_entry.grid(row=0, column=1, padx=5, pady=2)
        self.api_url_entry.insert(0, self.config.api_url)

        ttk.Label(config_frame, text="API Key:").grid(row=1, column=0, sticky="w")
        self.api_key_entry = ttk.Entry(config_frame, width=50)
        self.api_key_entry.grid(row=1, column=1, padx=5, pady=2)
        self.api_key_entry.insert(0, self.config.api_key)

        ttk.Label(config_frame, text="模型:").grid(row=2, column=0, sticky="w")
        self.model_entry = ttk.Entry(config_frame, width=50)
        self.model_entry.grid(row=2, column=1, padx=5, pady=2)
        self.model_entry.insert(0, self.config.model)

        ttk.Label(config_frame, text="用户名:").grid(row=3, column=0, sticky="w")
        self.user_name_entry = ttk.Entry(config_frame, width=50)
        self.user_name_entry.grid(row=3, column=1, padx=5, pady=2)
        self.user_name_entry.insert(0, self.config.user_name)

        ttk.Label(config_frame, text="机器人名字:").grid(row=4, column=0, sticky="w")
        self.robot_name_entry = ttk.Entry(config_frame, width=50)
        self.robot_name_entry.grid(row=4, column=1, padx=5, pady=2)
        self.robot_name_entry.insert(0, self.config.robot_name)

        # 分析机器人的提示词文件选择框
        ttk.Label(config_frame, text="【分析】提示词文件:").grid(row=5, column=0, sticky="w")
        self.analysis_prompt_file_var = StringVar()
        self.analysis_prompt_file_combobox = ttk.Combobox(
            config_frame,
            textvariable=self.analysis_prompt_file_var,
            values=self.prompt_files,
            state='readonly'
        )
        self.analysis_prompt_file_combobox.grid(row=5, column=1, padx=5, pady=2, sticky="w")
        self.analysis_prompt_file_combobox.set(self.config.analysis_prompt_file)

        # 回复机器人的提示词文件选择框
        ttk.Label(config_frame, text="【回复】提示词文件:").grid(row=6, column=0, sticky="w")
        self.reply_prompt_file_var = StringVar()
        self.reply_prompt_file_combobox = ttk.Combobox(
            config_frame,
            textvariable=self.reply_prompt_file_var,
            values=self.prompt_files,
            state='readonly'
        )
        self.reply_prompt_file_combobox.grid(row=6, column=1, padx=5, pady=2, sticky="w")
        self.reply_prompt_file_combobox.set(self.config.reply_prompt_file)

        # 上下文复选框
        self.context_enabled_var = BooleanVar(value=self.config.context_enabled)
        ttk.Checkbutton(config_frame, text="开启上下文", variable=self.context_enabled_var).grid(row=7, column=0, sticky="w")

        save_config_button = ttk.Button(config_frame, text="保存配置", command=self.save_config)
        save_config_button.grid(row=8, column=1, pady=5, sticky="e")

        # 聊天框
        chat_frame = ttk.LabelFrame(self.root, text="聊天", padding=5)
        chat_frame.pack(padx=10, pady=5, fill="both", expand=True)
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, width=60, height=20)
        self.chat_display.pack(padx=5, pady=5, fill="both", expand=True)

        # 输入框
        input_frame = ttk.Frame(self.root)
        input_frame.pack(padx=10, pady=5, fill="x")
        self.user_input = ttk.Entry(input_frame)
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 5))
        send_button = ttk.Button(input_frame, text="发送", command=self.send_message)
        send_button.pack(side="right")

    def save_config(self):
        self.config.api_url = self.api_url_entry.get()
        self.config.api_key = self.api_key_entry.get()
        self.config.model = self.model_entry.get()
        self.config.user_name = self.user_name_entry.get()
        self.config.robot_name = self.robot_name_entry.get()
        self.config.analysis_prompt_file = self.analysis_prompt_file_var.get()
        self.config.reply_prompt_file = self.reply_prompt_file_var.get()
        self.config.context_enabled = self.context_enabled_var.get()
        self.config.save_to_file()
        messagebox.showinfo("提示", "配置已保存！")

    def send_message(self):
        user_message = self.user_input.get()
        if not user_message:
            return
        self.chat_display.insert(tk.END, f"{self.config.user_name}: {user_message}\n")
        self.user_input.delete(0, tk.END)

        # 读取【分析】机器人的提示词文件内容
        analysis_prompt_file = self.analysis_prompt_file_var.get()
        if analysis_prompt_file != "无":
            try:
                with open(analysis_prompt_file, "r", encoding="utf-8") as f:
                    analysis_prompt_content = f.read().strip()
            except FileNotFoundError:
                analysis_prompt_content = f"{self.config.robot_name}，你是一个情绪分析机器人，请分析用户的情绪。"
                messagebox.showwarning("警告", f"提示词文件 {analysis_prompt_file} 未找到，使用默认提示词。")
        else:
            analysis_prompt_content = f"{self.config.robot_name}，你是一个情绪分析机器人，请分析用户的情绪。"

        # 读取【回复】机器人的提示词文件内容
        reply_prompt_file = self.reply_prompt_file_var.get()
        if reply_prompt_file != "无":
            try:
                with open(reply_prompt_file, "r", encoding="utf-8") as f:
                    reply_prompt_content = f.read().strip()
            except FileNotFoundError:
                reply_prompt_content = f"{self.config.robot_name}，你是一个回复机器人，请友好地回复用户。"
                messagebox.showwarning("警告", f"提示词文件 {reply_prompt_file} 未找到，使用默认提示词。")
        else:
            reply_prompt_content = f"{self.config.robot_name}，你是一个回复机器人，请友好地回复用户。"

        # 构建 Robot1（分析机器人）的系统提示词
        robot1_system_prompt = (
            f"你是一个名为{self.config.robot_name}的情绪分析机器人，你的任务是根据用户消息，决定机器人应该表现出的情绪，并生成提示词来控制机器人的行为。\n"
            "你需要返回模型参数（temperature 和 topp）、机器人应该表现的情绪权重，以及提示词。\n"
            "temperature 的范围是 0.0 到 2.0，topp 的范围是 0.0 到 1.0。\n"
            "请严格按照以下格式返回内容，否则你的输出将被忽略，不会显示在界面或发送给机器人：\n"
            "~!modelparam:{temperature:[<value>],topp:[<value>]}!~\n"
            "~!emoweight:{happiness:[<value>];anger:[<value>];fear:[<value>];sadness:[<value>];disgust:[<value>];surprise:[<value>]}!~\n"
            "~!prompt:[<提示词内容>]!~\n"
            "例如：\n"
            "~!modelparam:{temperature:[0.7],topp:[0.9]}!~\n"
            "~!emoweight:{happiness:[0.5];anger:[0.1];fear:[0.2];sadness:[0.1];disgust:[0.0];surprise:[0.1]}!~\n"
            f"~!prompt:[{analysis_prompt_content}]!~\n"
            "请严格遵循上述格式返回内容，不要返回其他任何多余的内容！\n"
        )

        # 如果有上次机器人的回复，一起发送给 Robot1
        if self.last_robot_reply:
            user_message_with_reply = f"用户消息: {user_message}\n上次机器人回复: {self.last_robot_reply}\n用户名: {self.config.user_name}"
        else:
            user_message_with_reply = f"用户消息: {user_message}\n用户名: {self.config.user_name}"

        threading.Thread(
            target=self.call_robot1,
            args=(robot1_system_prompt, user_message_with_reply, reply_prompt_content),
            daemon=True
        ).start()

    def call_robot1(self, system_prompt, user_message, reply_prompt_content):
        """调用 Robot1（情绪分析机器人）"""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            response = requests.post(
                self.config.api_url,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={"model": self.config.model, "messages": messages}
            )
            if response.status_code == 200:
                robot1_response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                model_params, emotion_weight, prompt = self.parse_robot1_response(robot1_response)
                if model_params is None or emotion_weight is None or prompt is None:
                    messagebox.showerror("错误", "Robot1 返回的内容格式不正确，请检查 Robot1 的输出是否符合指定格式！")
                    return
                self.show_emotion_window(emotion_weight, model_params, prompt)
                # 调用回复机器人
                self.call_robot(user_message, model_params, emotion_weight, reply_prompt_content)
            else:
                messagebox.showerror("错误", f"Robot1 请求失败: {response.text}")
        except Exception as e:
            messagebox.showerror("错误", f"Robot1 请求失败: {str(e)}")

    def call_robot(self, user_message, robot1_model_params, robot1_emotion_weight, reply_prompt_content):
        """调用回复机器人"""
        try:
            # 解析 Robot1 的模型参数
            temperature = 0.7
            topp = 0.9
            if "temperature:" in robot1_model_params:
                temp_start = robot1_model_params.find("temperature:[") + 13
                temp_end = robot1_model_params.find("]", temp_start)
                temperature = float(robot1_model_params[temp_start:temp_end])
            if "topp:" in robot1_model_params:
                topp_start = robot1_model_params.find("topp:[") + 6
                topp_end = robot1_model_params.find("]", topp_start)
                topp = float(robot1_model_params[topp_start:topp_end])

            # 构建回复机器人的系统提示词
            emotions = self.parse_emotion_weight(robot1_emotion_weight)
            emotion_prompt = "\n".join([f"- {k}: {v}" for k, v in emotions.items()])
            robot_system_prompt = (
                f"你是一个名为{self.config.robot_name}的机器人，用户名是 {self.config.user_name}，根据以下情绪权重和提示词调整语气：\n"
                f"情绪权重：\n{emotion_prompt}\n"
                f"提示词：\n{reply_prompt_content}\n"
                "请根据这些信息调整回复语气。\n"
            )

            # 如果开启上下文，将聊天记录作为上下文发送给回复机器人
            if self.config.context_enabled:
                context = self.chat_display.get("1.0", tk.END).strip()
                robot_system_prompt += f"上下文：\n{context}\n"

            messages = [
                {"role": "system", "content": robot_system_prompt},
                {"role": "user", "content": user_message}
            ]
            response = requests.post(
                self.config.api_url,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": temperature,
                    "top_p": topp
                }
            )
            if response.status_code == 200:
                robot_response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                robot_reply = self.extract_robot_reply(robot_response)
                # 修复重复名称问题
                if robot_reply.startswith(f"{self.config.robot_name}:"):
                    self.chat_display.insert(tk.END, f"{robot_reply}\n")
                else:
                    self.chat_display.insert(tk.END, f"{self.config.robot_name}: {robot_reply}\n")
                self.last_robot_reply = robot_reply
                self.show_expected_window(robot1_model_params, robot1_emotion_weight)
            else:
                self.chat_display.insert(tk.END, f"{self.config.robot_name}: 错误: {response.text}\n")
        except Exception as e:
            self.chat_display.insert(tk.END, f"{self.config.robot_name}: 请求失败: {str(e)}\n")

    def parse_robot1_response(self, response):
        """解析 Robot1 的返回，提取模型参数、情绪权重和提示词"""
        model_params = "~!modelparam:{temperature:[0.7],topp:[0.9]}!~"
        emotion_weight = "~!emoweight:{happiness:[0.0];anger:[0.0];fear:[0.0];sadness:[0.0];disgust:[0.0];surprise:[0.0]}!~"
        prompt = ""
        if "~!modelparam:" not in response or "~!emoweight:" not in response or "~!prompt:[" not in response:
            return None, None, None
        if "~!modelparam:" in response:
            start = response.find("~!modelparam:")
            end = response.find("!~", start)
            model_params = response[start:end + 2]
        if "~!emoweight:" in response:
            start = response.find("~!emoweight:")
            end = response.find("!~", start)
            emotion_weight = response[start:end + 2]
        if "~!prompt:[" in response:
            start = response.find("~!prompt:[") + 9
            end = response.find("]!~", start)
            prompt = response[start:end]
            prompt = prompt.replace("[", "").replace("]", "")
        return model_params, emotion_weight, prompt

    def extract_robot_reply(self, response):
        """提取机器人的回复内容"""
        return response.strip()

    def parse_emotion_weight(self, emotion_weight):
        """解析情绪权重，返回字典"""
        emotions = {}
        pattern = r'(\w+):\[([\d.]+)\]'
        matches = re.findall(pattern, emotion_weight)
        for key, value in matches:
            emotions[key] = float(value)
        return emotions

    def show_emotion_window(self, emotion_weight, model_params, prompt):
        """展示 Robot1 的情绪权重、模型参数和提示词的窗口"""
        if self.emotion_window is None or not self.emotion_window.winfo_exists():
            self.emotion_window = Toplevel(self.root)
            self.emotion_window.title(f"【分析】{self.config.robot_name}")
            self.emotion_window.geometry("400x400")
            # 模型参数文本框
            ttk.Label(self.emotion_window, text="模型参数:").pack(pady=5)
            self.emotion_param_text = scrolledtext.ScrolledText(self.emotion_window, wrap=tk.WORD, width=40, height=3)
            self.emotion_param_text.pack(padx=5, pady=5)
            # 情绪权重文本框
            ttk.Label(self.emotion_window, text="情绪权重:").pack(pady=5)
            self.emotion_text = scrolledtext.ScrolledText(self.emotion_window, wrap=tk.WORD, width=40, height=8)
            self.emotion_text.pack(padx=5, pady=5)
            # 提示词文本框
            ttk.Label(self.emotion_window, text="提示词:").pack(pady=5)
            self.prompt_text = scrolledtext.ScrolledText(self.emotion_window, wrap=tk.WORD, width=40, height=8)
            self.prompt_text.pack(padx=5, pady=5)

        # 解析模型参数
        temperature = 0.7
        topp = 0.9
        if "temperature:" in model_params:
            temp_start = model_params.find("temperature:[") + 13
            temp_end = model_params.find("]", temp_start)
            temperature = model_params[temp_start:temp_end]
        if "topp:" in model_params:
            topp_start = model_params.find("topp:[") + 6
            topp_end = model_params.find("]", topp_start)
            topp = model_params[topp_start:topp_end]

        # 解析情绪权重
        emotions = self.parse_emotion_weight(emotion_weight)

        # 去掉提示词中的中括号
        prompt = prompt.replace("[", "").replace("]", "")

        # 更新模型参数文本框
        self.emotion_param_text.config(state=tk.NORMAL)
        self.emotion_param_text.delete(1.0, tk.END)
        self.emotion_param_text.insert(tk.END, f"Temperature: {temperature}\nTop P: {topp}")
        self.emotion_param_text.config(state=tk.DISABLED)

        # 更新情绪权重文本框
        self.emotion_text.config(state=tk.NORMAL)
        self.emotion_text.delete(1.0, tk.END)
        self.emotion_text.insert(tk.END, "\n".join([f"{k}: {v}" for k, v in emotions.items()]))
        self.emotion_text.config(state=tk.DISABLED)

        # 更新提示词文本框
        self.prompt_text.config(state=tk.NORMAL)
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(tk.END, prompt)
        self.prompt_text.config(state=tk.DISABLED)

        self.emotion_window.lift()

    def show_expected_window(self, expected_model_params, expected_emotion_weight):
        """展示回复机器人的预期模型参数和预期情绪权重的窗口"""
        if self.expected_window is None or not self.expected_window.winfo_exists():
            self.expected_window = Toplevel(self.root)
            self.expected_window.title(f"【回复】{self.config.robot_name}")
            self.expected_window.geometry("400x300")
            # 预期模型参数文本框
            ttk.Label(self.expected_window, text="预期模型参数:").pack(pady=5)
            self.expected_param_text = scrolledtext.ScrolledText(self.expected_window, wrap=tk.WORD, width=40, height=3)
            self.expected_param_text.pack(padx=5, pady=5)
            # 预期情绪权重文本框
            ttk.Label(self.expected_window, text="预期情绪权重:").pack(pady=5)
            self.expected_emotion_text = scrolledtext.ScrolledText(self.expected_window, wrap=tk.WORD, width=40, height=10)
            self.expected_emotion_text.pack(padx=5, pady=5)

        # 解析预期模型参数
        expected_temperature = 0.7
        expected_topp = 0.9
        if "temperature:" in expected_model_params:
            temp_start = expected_model_params.find("temperature:[") + 13
            temp_end = expected_model_params.find("]", temp_start)
            expected_temperature = expected_model_params[temp_start:temp_end]
        if "topp:" in expected_model_params:
            topp_start = expected_model_params.find("topp:[") + 6
            topp_end = expected_model_params.find("]", topp_start)
            expected_topp = expected_model_params[topp_start:topp_end]

        # 解析预期情绪权重
        expected_emotions = self.parse_emotion_weight(expected_emotion_weight)

        # 更新预期模型参数文本框
        self.expected_param_text.config(state=tk.NORMAL)
        self.expected_param_text.delete(1.0, tk.END)
        self.expected_param_text.insert(tk.END, f"Temperature: {expected_temperature}\nTop P: {expected_topp}")
        self.expected_param_text.config(state=tk.DISABLED)

        # 更新预期情绪权重文本框
        self.expected_emotion_text.config(state=tk.NORMAL)
        self.expected_emotion_text.delete(1.0, tk.END)
        self.expected_emotion_text.insert(tk.END, "\n".join([f"{k}: {v}" for k, v in expected_emotions.items()]))
        self.expected_emotion_text.config(state=tk.DISABLED)

        self.expected_window.lift()

# 运行程序
if __name__ == "__main__":
    root = tk.Tk()
    app = RobotChatTool(root)
    root.mainloop()
