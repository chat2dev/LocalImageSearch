"""
Prompt template management module
"""
import yaml
from pathlib import Path
from typing import Dict, Optional


class PromptManager:
    """Prompt template manager"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Prompt manager

        Args:
            config_path: Path to prompt config file, defaults to prompts.yaml in the project root
        """
        if not config_path:  # Both None and empty string use the default path
            # Default to prompts.yaml in the project root
            config_path = Path(__file__).parent.parent / "prompts.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Prompt config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.system_prompts = self.config.get("system_prompts", {})
        self.tag_prompts = self.config.get("tag_prompts", {})
        self.description_prompts = self.config.get("description_prompts", {})
        self.language_names = self.config.get("language_names", {})

    def get_system_prompt(self, language: str) -> str:
        """
        Get system prompt

        Args:
            language: Language code (e.g. "zh", "en")

        Returns:
            System prompt string
        """
        return self.system_prompts.get(language, self.system_prompts.get("default", ""))

    def get_tag_prompt(self, language: str, tag_count: int) -> str:
        """
        Get tag generation prompt

        Args:
            language: Language code (e.g. "zh", "en")
            tag_count: Tag count

        Returns:
            Formatted prompt string
        """
        template = self.tag_prompts.get(language, self.tag_prompts.get("default", ""))
        language_name = self.language_names.get(language, "English")

        return template.format(
            language=language,
            language_name=language_name,
            tag_count=tag_count
        )

    def get_description_prompt(self, language: str) -> str:
        """
        Get description generation prompt

        Args:
            language: Language code (e.g. "zh", "en")

        Returns:
            Formatted prompt string
        """
        template = self.description_prompts.get(language, self.description_prompts.get("default", ""))
        language_name = self.language_names.get(language, "English")

        return template.format(
            language=language,
            language_name=language_name
        )

    def get_language_name(self, language: str) -> str:
        """
        Get the natural language name for a language code

        Args:
            language: Language code (e.g. "zh", "en")

        Returns:
            Natural language name (e.g. "Chinese", "English")
        """
        return self.language_names.get(language, "English")
