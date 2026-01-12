"""Translation module for Japanese to other languages"""

import re
from typing import Optional
import httpx
from rich.console import Console

console = Console()


def contains_japanese(text: str) -> bool:
    """Check if text contains Japanese characters (Hiragana, Katakana, Kanji)"""
    if not text:
        return False
    # Hiragana: \u3040-\u309f
    # Katakana: \u30a0-\u30ff
    # Half-width Katakana: \uff66-\uff9f
    # Kanji: \u4e00-\u9faf
    pattern = r"[\u3040-\u309f\u30a0-\u30ff\uff66-\uff9f\u4e00-\u9faf]"
    return bool(re.search(pattern, text))


class Translator:
    """Translate text using Google Translate or DeepL"""

    def __init__(
        self,
        provider: str = "google",
        target_language: str = "en",
        deepl_api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.provider = provider.lower()
        self.target_language = target_language
        self.deepl_api_key = deepl_api_key
        self.timeout = timeout

    def translate(self, text: str) -> str:
        """
        Translate text to target language.
        Only translates if text contains Japanese characters.
        """
        if not text or not contains_japanese(text):
            return text

        try:
            if self.provider == "deepl":
                return self._translate_deepl(text)
            else:
                return self._translate_google(text)
        except Exception as e:
            console.print(f"[yellow]Translation failed: {e}[/]")
            return text  # Return original on failure

    def _translate_google(self, text: str) -> str:
        """Translate using Google Translate (free, unofficial API)"""
        # Use the free Google Translate API endpoint
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "ja",  # Source: Japanese
            "tl": self.target_language,
            "dt": "t",
            "q": text,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                # Response is nested array: [[["translated text", "original", ...]]]
                data = response.json()
                if data and data[0]:
                    # Join all translated parts
                    translated = "".join(part[0] for part in data[0] if part[0])
                    return translated
                return text
        except Exception as e:
            raise RuntimeError(f"Google Translate error: {e}")

    def _translate_deepl(self, text: str) -> str:
        """Translate using DeepL API"""
        if not self.deepl_api_key:
            raise ValueError("DeepL API key is required")

        # Free API uses different endpoint
        if self.deepl_api_key.endswith(":fx"):
            base_url = "https://api-free.deepl.com/v2/translate"
        else:
            base_url = "https://api.deepl.com/v2/translate"

        # Map language codes (DeepL uses different codes)
        lang_map = {
            "en": "EN",
            "vi": "VI",  # Vietnamese not supported by DeepL free
            "zh": "ZH",
            "ko": "KO",
        }
        target = lang_map.get(self.target_language, self.target_language.upper())

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    base_url,
                    data={
                        "auth_key": self.deepl_api_key,
                        "text": text,
                        "target_lang": target,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["translations"][0]["text"]
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"DeepL API error: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"DeepL error: {e}")


def translate_metadata(
    metadata,
    translator: Translator,
    translate_title: bool = True,
    translate_description: bool = True,
):
    """
    Translate metadata fields in-place.

    Args:
        metadata: MovieMetadata object
        translator: Translator instance
        translate_title: Whether to translate title
        translate_description: Whether to translate description
    """
    if translate_title and metadata.title:
        original = metadata.title
        translated = translator.translate(metadata.title)
        if translated != original:
            # Store original in original_title if not already set
            if not metadata.original_title:
                metadata.original_title = original
            metadata.title = translated
            console.print("[dim]Translated title[/]")

    if translate_description and metadata.description:
        translated = translator.translate(metadata.description)
        if translated != metadata.description:
            metadata.description = translated
            console.print("[dim]Translated description[/]")
