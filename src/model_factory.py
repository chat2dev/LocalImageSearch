"""
Model Interface Module
"""
import os
import requests
import json
from pathlib import Path
from typing import List, Optional
from .prompt_manager import PromptManager


class ModelAPIError(Exception):
    """Model interface error, carrying detailed information for database logging"""
    def __init__(self, error_type: str, message: str, raw_response: str = ""):
        self.error_type = error_type
        self.raw_response = raw_response
        super().__init__(message)

    def to_error_message(self) -> str:
        """Format as error message for database storage"""
        msg = f"[{self.error_type}] {str(self)}"
        if self.raw_response:
            msg += f" | raw_response: {self.raw_response[:300]}"
        return msg


class BaseModel:
    """Base model interface"""
    def __init__(self, model_name: str, language: str = "en"):
        self.model_name = model_name
        self.language = language

    def generate_tags(self, image_bytes: bytes, tag_count: int) -> List[str]:
        """Generate image tags"""
        raise NotImplementedError("Subclasses must implement this method")

    def generate_description(self, image_bytes: bytes) -> str:
        """Generate image description"""
        raise NotImplementedError("Subclasses must implement this method")

    def _parse_response(self, response_text: str) -> str:
        """Parse model response (supports multi-language fallback, prioritizes configured language)"""
        if not response_text:
            return ""

        # Remove excess formatting markers
        response_text = response_text.strip()
        if response_text.startswith('"') and response_text.endswith('"'):
            response_text = response_text[1:-1]
        if response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()

        import re

        # Define parsing functions for each language
        def try_parse_zh(text):
            """Try to parse Chinese tags"""
            tag_pattern = r"([\u4e00-\u9fff]+(?:[,，、]\s*[\u4e00-\u9fff]+){2,})"
            matches = re.findall(tag_pattern, text)
            if matches:
                result = matches[-1].strip()
                for sep in [',', '，', '、', ';', '；']:
                    if sep in result:
                        tags = [t.strip() for t in result.split(sep) if t.strip()]
                        return ','.join(list(dict.fromkeys(tags)))
            words = re.findall(r"[\u4e00-\u9fff]{2,}", text)
            if words:
                return ','.join(list(dict.fromkeys(words))[:8])
            return None

        def try_parse_en(text):
            """Try to parse English tags (supports multi-word tags like 'search engine')"""
            # Priority: check if there is a comma-separated list of tags
            if ',' in text:
                tags = [t.strip() for t in text.split(',') if t.strip()]
                # Validate whether primarily composed of letters + spaces (allows multi-word tags)
                valid_tags = []
                for tag in tags:
                    # Strip punctuation and check if mainly composed of letters
                    clean = ''.join(c for c in tag if c.isalpha() or c.isspace()).strip()
                    if clean and len(clean) >= 2:  # At least 2 characters
                        valid_tags.append(tag)
                if len(valid_tags) >= 3:  # At least 3 tags
                    return ', '.join(list(dict.fromkeys(valid_tags)))

            # Fallback: extract individual English words
            words = re.findall(r"[a-zA-Z]{3,}", text)
            if words:
                unique = [w for w in words if w.isalpha()]
                return ', '.join(list(dict.fromkeys(unique))[:8])
            return None

        def try_parse_ja(text):
            """Try to parse Japanese tags"""
            tag_pattern = r"([\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+(?:[,，、]\s*[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+){2,})"
            matches = re.findall(tag_pattern, text)
            if matches:
                result = matches[-1].strip()
                for sep in [',', '，', '、']:
                    if sep in result:
                        tags = [t.strip() for t in result.split(sep) if t.strip()]
                        return ','.join(list(dict.fromkeys(tags)))
            words = re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]{2,}", text)
            if words:
                return ','.join(list(dict.fromkeys(words))[:8])
            return None

        def try_parse_ko(text):
            """Try to parse Korean tags"""
            tag_pattern = r"([\uac00-\ud7af]+(?:[,，、]\s*[\uac00-\ud7af]+){2,})"
            matches = re.findall(tag_pattern, text)
            if matches:
                result = matches[-1].strip()
                for sep in [',', '，', '、']:
                    if sep in result:
                        tags = [t.strip() for t in result.split(sep) if t.strip()]
                        return ','.join(list(dict.fromkeys(tags)))
            words = re.findall(r"[\uac00-\ud7af]{2,}", text)
            if words:
                return ','.join(list(dict.fromkeys(words))[:8])
            return None

        def try_parse_other(text):
            """Try to parse other European language tags (supports multi-word tags)"""
            # Priority: check if there is a comma-separated list of tags
            if ',' in text:
                tags = [t.strip() for t in text.split(',') if t.strip()]
                # Validate whether primarily composed of letters + spaces (allows accented characters and multi-word tags)
                valid_tags = []
                for tag in tags:
                    # Check if mainly composed of letters (including accented characters)
                    clean = ''.join(c for c in tag if c.isalpha() or c.isspace()).strip()
                    if clean and len(clean) >= 2:
                        valid_tags.append(tag)
                if len(valid_tags) >= 3:  # At least 3 tags
                    return ','.join(list(dict.fromkeys(valid_tags)))

            # Fallback: extract individual words
            words = re.findall(r"[a-zA-Zà-žÀ-Ž]{3,}", text)
            if words:
                return ','.join(list(dict.fromkeys(words))[:8])
            return None

        # Build parser priority list (configured language first)
        parsers = []
        if self.language == "zh":
            parsers = [try_parse_zh, try_parse_en, try_parse_ja, try_parse_ko, try_parse_other]
        elif self.language == "en":
            parsers = [try_parse_en, try_parse_zh, try_parse_ja, try_parse_ko, try_parse_other]
        elif self.language == "ja":
            parsers = [try_parse_ja, try_parse_zh, try_parse_en, try_parse_ko, try_parse_other]
        elif self.language == "ko":
            parsers = [try_parse_ko, try_parse_zh, try_parse_en, try_parse_ja, try_parse_other]
        else:
            parsers = [try_parse_other, try_parse_en, try_parse_zh, try_parse_ja, try_parse_ko]

        # Try each language parser in order
        for parser in parsers:
            result = parser(response_text)
            if result:
                return result

        return ""


class OllamaModel(BaseModel):
    """Ollama local model interface"""
    def __init__(self, model_name: str, language: str = "en", prompt_config_path: Optional[str] = None):
        super().__init__(model_name, language)
        # Read OLLAMA_HOST from environment, default to localhost:11434
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        # Ensure http:// prefix
        if not ollama_host.startswith("http"):
            ollama_host = f"http://{ollama_host}"
        self.base_url_generate = f"{ollama_host}/api/generate"
        self.base_url_chat = f"{ollama_host}/api/chat"

        # Initialize PromptManager
        self.prompt_manager = PromptManager(prompt_config_path)

        # Retain language_names for compatibility (PromptManager is now prioritized)
        self.language_names = {
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ru": "Russian"
        }

    def generate_tags(self, image_bytes: bytes, tag_count: int) -> List[str]:
        """Generate image tags (reads prompt from config file)"""
        # Use PromptManager to get the prompt template
        prompt = self.prompt_manager.get_tag_prompt(self.language, tag_count)
        return self._call_ollama_api(image_bytes, prompt)

    def generate_description(self, image_bytes: bytes) -> str:
        """Generate image description (reads prompt from config file)"""
        # Use PromptManager to get the prompt template
        prompt = self.prompt_manager.get_description_prompt(self.language)
        return self._call_ollama_api(image_bytes, prompt)

    def _call_ollama_api(self, image_bytes: bytes, prompt: str) -> str:
        """Call Ollama Chat API (disables thinking mode for speed)"""
        import base64

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Use PromptManager to get the system prompt
        system_prompt = self.prompt_manager.get_system_prompt(self.language)

        # Use chat API + pre-filled empty thinking block to disable thinking mode, greatly speeds up processing (15-300s -> 2-5s)
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt, "images": [image_b64]},
                {"role": "assistant", "content": "<think></think>"}  # Pre-filled empty thinking block
            ],
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.9,
                "num_predict": 300,
                "num_ctx": 4096,
                "repeat_penalty": 1.1
            }
        }

        try:
            response = requests.post(
                self.base_url_chat,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                raise ModelAPIError(
                    "HTTP_ERROR",
                    f"HTTP {response.status_code}",
                    response.text[:500]
                )

            result = response.json()

            # Chat API response is in the message.content field
            response_text = result.get("message", {}).get("content", "")

            if not response_text or response_text.strip() == "":
                raise ModelAPIError(
                    "EMPTY_RESPONSE",
                    "Model returned empty response (message.content is empty)",
                    json.dumps(result, ensure_ascii=False)[:500]
                )

            parsed = self._parse_response(response_text)

            if not parsed:
                raise ModelAPIError(
                    "PARSE_FAILED",
                    f"Failed to parse tags from response (language={self.language})",
                    response_text[:500]
                )

            return parsed

        except ModelAPIError:
            raise
        except requests.exceptions.Timeout:
            raise ModelAPIError(
                "TIMEOUT",
                f"API request timed out (60s), URL={self.base_url_chat}",
                ""
            )
        except requests.exceptions.ConnectionError as e:
            raise ModelAPIError(
                "CONNECTION_ERROR",
                f"Failed to connect to Ollama service: {str(e)[:200]}",
                ""
            )
        except requests.exceptions.RequestException as e:
            raise ModelAPIError(
                "REQUEST_ERROR",
                f"{type(e).__name__}: {str(e)[:200]}",
                ""
            )
        except Exception as e:
            import traceback
            raise ModelAPIError(
                "GENERAL_ERROR",
                f"{type(e).__name__}: {str(e)[:200]}",
                traceback.format_exc()[:500]
            )


class OpenAICompatibleModel(BaseModel):
    """OpenAI-compatible API model interface"""
    def __init__(self, model_name: str, api_base: str, api_key: str = "", language: str = "en",
                 prompt_config_path: Optional[str] = None):
        super().__init__(model_name, language)
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.prompt_manager = PromptManager(prompt_config_path)

    def generate_tags(self, image_bytes: bytes, tag_count: int) -> List[str]:
        """Generate image tags (reads prompt from config file)"""
        prompt = self.prompt_manager.get_tag_prompt(self.language, tag_count)
        return self._call_openai_api(image_bytes, prompt)

    def generate_description(self, image_bytes: bytes) -> str:
        """Generate image description (reads prompt from config file)"""
        prompt = self.prompt_manager.get_description_prompt(self.language)
        return self._call_openai_api(image_bytes, prompt)

    def _call_openai_api(self, image_bytes: bytes, prompt: str) -> str:
        """Call OpenAI-compatible API"""
        import base64

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 512,
            "temperature": 0.1
        }

        try:
            response = requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                raise ModelAPIError(
                    "HTTP_ERROR",
                    f"HTTP {response.status_code}",
                    response.text[:500]
                )

            result = response.json()
            response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not response_text or response_text.strip() == "":
                raise ModelAPIError(
                    "EMPTY_RESPONSE",
                    "OpenAI API returned empty response",
                    json.dumps(result, ensure_ascii=False)[:500]
                )

            parsed = self._parse_response(response_text)

            if not parsed:
                raise ModelAPIError(
                    "PARSE_FAILED",
                    f"Failed to parse tags from response (language={self.language})",
                    response_text[:500]
                )

            return parsed

        except ModelAPIError:
            raise
        except requests.exceptions.Timeout:
            raise ModelAPIError(
                "TIMEOUT",
                f"API request timed out (60s), URL={self.api_base}",
                ""
            )
        except requests.exceptions.ConnectionError as e:
            raise ModelAPIError(
                "CONNECTION_ERROR",
                f"Failed to connect to API service: {str(e)[:200]}",
                ""
            )
        except requests.exceptions.RequestException as e:
            raise ModelAPIError(
                "REQUEST_ERROR",
                f"{type(e).__name__}: {str(e)[:200]}",
                ""
            )
        except Exception as e:
            import traceback
            raise ModelAPIError(
                "GENERAL_ERROR",
                f"{type(e).__name__}: {str(e)[:200]}",
                traceback.format_exc()[:500]
            )



def create_model(model_name: str, language: str = "en", model_type: str = "ollama",
                 api_base: str = "", api_key: str = "",
                 prompt_config_path: Optional[str] = None) -> BaseModel:
    """Create a model instance (only supports ollama and openai)"""
    if model_type == "openai":
        if not api_base:
            raise ValueError("api_base is required for OpenAI-compatible API")
        return OpenAICompatibleModel(model_name, api_base, api_key, language, prompt_config_path)
    else:  # ollama (default)
        return OllamaModel(model_name, language, prompt_config_path)
