"""
Configuration management module
"""
import argparse
import yaml
from pathlib import Path
import os
from dotenv import load_dotenv


# Application data directory under user home
APP_DATA_DIR = Path.home() / ".LocalImageSearch" / "data"


def ensure_app_dirs():
    """Ensure application directories exist"""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def str_to_bool(value):
    """Convert string to boolean"""
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', 'yes', '1', 'on'):
        return True
    elif value.lower() in ('false', 'no', '0', 'off', ''):
        return False
    else:
        raise ValueError(f"Cannot convert '{value}' to boolean")


class Config:
    """Configuration class

    Configuration priority (highest to lowest):
    1. CLI arguments
    2. .env file
    3. Default values
    """
    def __init__(self):
        # Ensure application directories exist
        ensure_app_dirs()

        # Load .env file if exists
        load_dotenv()

        # Set defaults, then override with .env values if present
        self.model = os.getenv("MODEL_NAME", "qwen3-vl:4b")
        self.model_type = os.getenv("MODEL_TYPE", "ollama")
        self.api_base = os.getenv("API_BASE", "")
        self.api_key = os.getenv("API_KEY", "")
        self.image_path = ""  # Must be provided via CLI or config file
        self.resize = os.getenv("IMAGE_RESIZE", "512x512")
        self.tag_count = int(os.getenv("TAG_COUNT", "10"))
        self.generate_description = str_to_bool(os.getenv("GENERATE_DESCRIPTION", "false"))
        self.db_path = os.getenv("DB_PATH", str(APP_DATA_DIR / "image_tags.db"))
        self.language = os.getenv("LANGUAGE", "zh")
        self.reprocess = str_to_bool(os.getenv("REPROCESS", "false"))
        self.prompt_config_path = os.getenv("PROMPT_CONFIG", "")

    def parse_args(self):
        """Parse command line arguments

        Priority: CLI arguments > .env file > default values
        Only CLI arguments explicitly provided will override .env values
        """
        parser = argparse.ArgumentParser(
            description="Image auto-tagging system",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Configuration priority:
  1. CLI arguments (highest)
  2. .env file
  3. Default values (lowest)

Example:
  # Use .env file for configuration
  uv run python src/main.py --image-path ~/Pictures

  # Override .env with CLI arguments
  uv run python src/main.py --image-path ~/Pictures --model llava:13b --language en
            """
        )
        parser.add_argument(
            "--model",
            type=str,
            default=None,  # Use None to detect if explicitly set
            help=f"Model name (default from .env: {self.model})"
        )
        parser.add_argument(
            "--model-type",
            type=str,
            default=None,
            choices=["ollama", "openai"],
            help=f"Model type (default from .env: {self.model_type})"
        )
        parser.add_argument(
            "--api-base",
            type=str,
            default=None,
            help="OpenAI-compatible API base URL"
        )
        parser.add_argument(
            "--api-key",
            type=str,
            default=None,
            help="API key for OpenAI-compatible API"
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
            default=None,
            help=f"Image resize dimensions (default from .env: {self.resize})"
        )
        parser.add_argument(
            "--tag-count",
            type=int,
            default=None,
            help=f"Number of tags per image (default from .env: {self.tag_count})"
        )
        parser.add_argument(
            "--description",
            action="store_true",
            default=None,
            help="Generate image description"
        )
        parser.add_argument(
            "--db-path",
            type=str,
            default=None,
            help=f"Database file path (default from .env: {self.db_path})"
        )
        parser.add_argument(
            "--language",
            type=str,
            default=None,
            choices=["en", "zh", "ja", "ko", "es", "fr", "de", "ru"],
            help=f"Language for tags/descriptions (default from .env: {self.language})"
        )
        parser.add_argument(
            "--reprocess",
            action="store_true",
            default=None,
            help="Force reprocess already tagged images"
        )
        parser.add_argument(
            "--prompt-config",
            type=str,
            default=None,
            help="Prompt config file path"
        )

        args = parser.parse_args()

        # Only override with CLI args if explicitly provided
        if args.model is not None:
            self.model = args.model
        if args.model_type is not None:
            self.model_type = args.model_type
        if args.api_base is not None:
            self.api_base = args.api_base
        if args.api_key is not None:
            self.api_key = args.api_key

        self.image_path = args.image_path  # Always required

        if args.resize is not None:
            self.resize = args.resize
        if args.tag_count is not None:
            self.tag_count = args.tag_count
        if args.description is not None:
            self.generate_description = args.description
        if args.db_path is not None:
            self.db_path = args.db_path
        if args.language is not None:
            self.language = args.language
        if args.reprocess is not None:
            self.reprocess = args.reprocess
        if args.prompt_config is not None:
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