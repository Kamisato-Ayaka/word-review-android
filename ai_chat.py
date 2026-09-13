# -*- coding: utf-8 -*-
"""AI聊天模块 - 支持豆包和DeepSeek"""
import os
import base64
import traceback


class AIChat:
    """AI聊天管理器"""

    def __init__(self, config_file):
        self.config_file = config_file
        # 默认配置（豆包 - 火山引擎）
        self.doubao_api_key = "8c870ba3-617c-49f5-96ce-10281efde366"
        self.doubao_endpoint = "https://ark.cn-beijing.volces.com/api/v1/"
        self.doubao_model = "ep-20260305155939-p2bwt"
        # DeepSeek配置
        self.deepseek_api_key = ""
        self.deepseek_endpoint = "https://api.deepseek.com"
        self.deepseek_model = "deepseek-chat"
        # 当前提供商
        self.current_provider = "豆包"
        self.load_config()

    def load_config(self):
        """加载AI配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip()
                        if key == "doubao_api_key":
                            self.doubao_api_key = val
                        elif key == "doubao_endpoint":
                            self.doubao_endpoint = val
                        elif key == "doubao_model":
                            self.doubao_model = val
                        elif key == "deepseek_api_key":
                            self.deepseek_api_key = val
                        elif key == "deepseek_endpoint":
                            self.deepseek_endpoint = val
                        elif key == "deepseek_model":
                            self.deepseek_model = val
                        elif key == "current_provider":
                            self.current_provider = val
            except Exception:
                pass

    def save_config(self):
        """保存AI配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(f"doubao_api_key={self.doubao_api_key}\n")
                f.write(f"doubao_endpoint={self.doubao_endpoint}\n")
                f.write(f"doubao_model={self.doubao_model}\n")
                f.write(f"deepseek_api_key={self.deepseek_api_key}\n")
                f.write(f"deepseek_endpoint={self.deepseek_endpoint}\n")
                f.write(f"deepseek_model={self.deepseek_model}\n")
                f.write(f"current_provider={self.current_provider}\n")
        except Exception:
            pass

    def get_current_config(self):
        """获取当前AI配置"""
        if self.current_provider == "DeepSeek":
            return (self.deepseek_api_key, self.deepseek_endpoint,
                    self.deepseek_model, "DeepSeek")
        return (self.doubao_api_key, self.doubao_endpoint,
                self.doubao_model, "豆包")

    def send_message(self, user_message, uploaded_files=None, callback=None):
        """发送消息给AI（在线程中调用）
        callback: 用于更新UI的回调函数 callback(status, message)
        返回: (success, response_text, provider_tag)
        """
        if uploaded_files is None:
            uploaded_files = []

        try:
            from openai import OpenAI
            import httpx

            api_key, endpoint, model, provider_name = self.get_current_config()

            if not api_key:
                return (False, f"{provider_name} API Key未配置，请先在设置中填写", provider_name)

            client = OpenAI(
                api_key=api_key,
                base_url=endpoint,
                http_client=httpx.Client(timeout=300)
            )

            # 构建内容
            content_parts = []
            plain_parts = []

            if user_message:
                content_parts.append({"type": "text", "text": user_message})
                plain_parts.append(user_message)

            img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            for file_info in uploaded_files:
                try:
                    if isinstance(file_info, tuple):
                        file_path, file_type, display_name = file_info
                    else:
                        file_path = file_info
                        file_type = "file"
                        display_name = os.path.basename(file_path)

                    file_ext = os.path.splitext(file_path)[1].lower()
                    is_image = (file_type == "image") or (file_ext in img_exts)

                    if is_image:
                        try:
                            with open(file_path, "rb") as image_file:
                                raw = image_file.read()
                            base64_image = base64.b64encode(raw).decode("utf-8")
                            ext_for_mime = file_ext.lstrip('.').lower() or "png"
                            if ext_for_mime == "jpg":
                                ext_for_mime = "jpeg"
                            if ext_for_mime not in {"jpeg", "png", "gif", "webp", "bmp"}:
                                try:
                                    from PIL import Image
                                    import io
                                    pil_img = Image.open(file_path)
                                    if pil_img.mode not in ("RGB", "RGBA"):
                                        pil_img = pil_img.convert("RGBA")
                                    buf = io.BytesIO()
                                    pil_img.save(buf, format="PNG")
                                    base64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
                                    ext_for_mime = "png"
                                except Exception:
                                    pass
                            data_url = f"data:image/{ext_for_mime};base64,{base64_image}"
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            })
                            plain_parts.append(
                                f"\n[图片附件：{display_name}]\n"
                            )
                        except Exception as ie:
                            plain_parts.append(f"\n[图片附件：{display_name} 读取失败: {ie}]\n")
                            content_parts.append({
                                "type": "text",
                                "text": f"\n[图片附件：{display_name} 读取失败: {ie}]\n"
                            })
                    else:
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                fc = f.read()
                            block = f"\n\n--- 文件: {display_name} ---\n{fc}"
                            content_parts.append({"type": "text", "text": block})
                            plain_parts.append(block)
                        except Exception:
                            block = f"\n\n--- 文件: {display_name}（二进制文件）---\n"
                            content_parts.append({"type": "text", "text": block})
                            plain_parts.append(block)
                except Exception as e:
                    pass

            has_image = any(p.get("type") == "image_url" for p in content_parts)
            plain_content = "\n".join(plain_parts).strip() or "（无文本内容）"

            sys_msg = {"role": "system", "content": "你是一个有用的AI助手。"}

            attempts = []
            if has_image:
                attempts.append(("multimodal", [sys_msg, {"role": "user", "content": content_parts}]))
                attempts.append(("plain", [sys_msg, {"role": "user", "content": plain_content}], True))
            else:
                attempts.append(("plain", [sys_msg, {"role": "user", "content": plain_content}]))
                attempts.append(("multimodal", [sys_msg, {"role": "user", "content": content_parts}]))

            last_error = None
            ai_response = None
            tried_label = []
            for attempt in attempts:
                try:
                    label = attempt[0]
                    messages = attempt[1]
                    is_fallback = len(attempt) >= 3 and attempt[2] is True
                    tried_label.append(label)

                    if is_fallback and callback:
                        callback("系统", "提示：当前模型不支持图片输入，已降级为纯文本。")

                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                    )
                    ai_response = response.choices[0].message.content
                    fmt = "multimodal" if label == "multimodal" else "plain"
                    return (True, ai_response, f"{provider_name}（{fmt}）")
                except Exception as e:
                    last_error = e
                    continue

            return (False, f"AI请求失败: {str(last_error)[:200]}", provider_name)

        except ImportError:
            return (False, "缺少openai或httpx库，请先安装", "")
        except Exception as e:
            return (False, f"发生错误: {str(e)[:200]}", "")

    def check_connection(self):
        """检查AI连接状态"""
        try:
            from openai import OpenAI
            import httpx
            api_key, endpoint, model, provider_name = self.get_current_config()
            if not api_key:
                return (False, f"{provider_name} API Key未配置")
            client = OpenAI(
                api_key=api_key,
                base_url=endpoint,
                http_client=httpx.Client(timeout=10)
            )
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "你好"}],
                max_tokens=5
            )
            return (True, "AI在线")
        except Exception as e:
            return (False, f"离线: {str(e)[:50]}")
