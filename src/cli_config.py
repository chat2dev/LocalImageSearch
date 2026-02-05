"""
Configuration management module
"""
import argparse
import yaml
from pathlib import Path
import os


# Application data directory under user home
APP_DATA_DIR = Path.home() / ".LocalImageSearch" / "data"


def ensure_app_dirs():
    """Ensure application directories exist"""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    """Configuration class"""
    def __init__(self):
        # Ensure application directories exist
        ensure_app_dirs()

        self.model = "qwen-vl:4b"
        self.model_type = "ollama"  # ollama, openai
        self.api_base = ""  # OpenAI-compatible API base URL
        self.api_key = ""  # API key
        self.image_path = ""
        self.resize = "512x512"
        self.tag_count = 10
        self.generate_description = False
        self.db_path = str(APP_DATA_DIR / "image_tags.db")  # Defaults to user home directory
        self.language = "en"
        self.reprocess = False
        self.prompt_config_path = ""  # Prompt config file path, defaults to prompts.yaml in project root

    def parse_args(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Image auto-tagging system"
        )
        parser.add_argument(
            "--model",
            type=str,
            default=self.model,
            help=f"Model name (default: {self.model})"
        )
        parser.add_argument(
            "--model-type",
            type=str,
            default=self.model_type,
            choices=["ollama", "openai"],
            help=f"Model type: ollama (Ollama service), openai (OpenAI-compatible API) (default: {self.model_type})"
        )
        parser.add_argument(
            "--api-base",
            type=str,
            default=self.api_base,
            help="OpenAI-compatible API base URL (used when model-type=openai)"
        )
        parser.add_argument(
            "--api-key",
            type=str,
            default=self.api_key,
            help="API key (used when model-type=openai)"
        )
        parser.add_argument(
            "--image-path",
            type=str,
            required=True,
            help="Image path (file or directory)"
        )
        parser.add_argument(
            "--resize",
            type=str,
            default=self.resize,
            help=f"Image resize dimensions (default: {self.resize})"
        )
        parser.add_argument(
            "--tag-count",
            type=int,
            default=self.tag_count,
            help=f"Number of annotation tags (default: {self.tag_count})"
        )
        parser.add_argument(
            "--description",
            action="store_true",
            help="Generate image description (default: False)"
        )
        parser.add_argument(
            "--db-path",
            type=str,
            default=self.db_path,
            help=f"Database file path (default: {self.db_path})"
        )
        parser.add_argument(
            "--language",
            type=str,
            default=self.language,
            choices=["en", "zh", "ja", "ko", "es", "fr", "de", "ru"],
            help=f"Language for tags and descriptions (default: {self.language})"
        )
        parser.add_argument(
            "--reprocess",
            action="store_true",
            help="Force reprocess already processed images (default: False)"
        )
        parser.add_argument(
            "--prompt-config",
            type=str,
            default=self.prompt_config_path,
            help="Prompt config file path (default: prompts.yaml in project root)"
        )

        args = parser.parse_args()
        self.model = args.model
        self.model_type = args.model_type
        self.api_base = args.api_base
        self.api_key = args.api_key
        self.image_path = args.image_path
        self.resize = args.resize
        self.tag_count = args.tag_count
        self.generate_description = args.description
        self.db_path = args.db_path
        self.language = args.language
        self.reprocess = args.reprocess
        self.prompt_config_path = args.prompt_config

    def load_config(self, config_path):
        """Load configuration file"""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config:
                self.model = config.get("model", self.model)
                self.model_type = config.get("model_type", self.model_type)
                self.api_base = config.get("api_base", self.api_base)
                self.api_key = config.get("api_key", self.api_key)
                self.image_path = config.get("image_path", self.image_path)
                self.resize = config.get("resize", self.resize)
                self.tag_count = config.get("tag_count", self.tag_count)
                self.generate_description = config.get(
                    "generate_description", self.generate_description
                )
                self.db_path = config.get("db_path", self.db_path)
                self.language = config.get("language", self.language)
                self.prompt_config_path = config.get("prompt_config_path", self.prompt_config_path)

    def get_resize_dimensions(self):
        """Get resize dimensions"""
        try:
            width, height = map(int, self.resize.split("x"))
            return width, height
        except (ValueError, AttributeError):
            return 512, 512

    def __str__(self):
        config_str = (
            f"Config:\n"
            f"  Model: {self.model}\n"
            f"  Model Type: {self.model_type}\n"
        )
        if self.model_type == "openai":
            config_str += f"  API Base: {self.api_base}\n"
            config_str += f"  API Key: {'***' if self.api_key else 'Not set'}\n"
        config_str += (
            f"  Image Path: {self.image_path}\n"
            f"  Resize: {self.resize}\n"
            f"  Tag Count: {self.tag_count}\n"
            f"  Generate Description: {self.generate_description}\n"
            f"  DB Path: {self.db_path}\n"
            f"  Language: {self.language}"
        )
        return config_str