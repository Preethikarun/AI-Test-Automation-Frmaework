"""
Base agent — auto-selects Anthropic or Gemini
based on which API key is available in .env
"""
import os
from urllib import response
from dotenv import load_dotenv

load_dotenv()


class BaseAgent:

    MAX_TOKENS = 2048

    def __init__(self):
        self.provider = self._detect_provider()
        self._init_client()
        print(f"{self.__class__.__name__} initialised "
              f"[provider: {self.provider}]")

    def _detect_provider(self) -> str:
        if os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        elif os.getenv("GEMINI_API_KEY"):
            return "gemini"
        else:
            raise ValueError(
                "No API key found. Add ANTHROPIC_API_KEY or "
                "GEMINI_API_KEY to your .env file."
            )

    def _init_client(self):
        if self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            self.model = "claude-sonnet-4-6"

        elif self.provider == "gemini":
            from google import genai
            self.client = genai.Client(
                api_key=os.getenv("GEMINI_API_KEY")
            )
            self.model = "gemini-2.0-flash"

    def call_claude(self, prompt: str, system: str = None) -> str:
        if self.provider == "anthropic":
            return self._call_anthropic(prompt, system)
        else:
            return self._call_gemini(prompt, system)

    def _call_anthropic(self, prompt: str, system: str) -> str:
        kwargs = {
            "model":      self.model,
            "max_tokens": self.MAX_TOKENS,
            "messages":   [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def _call_gemini(self, prompt: str, system: str) -> str:
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt
        )
        return response.text

    def save_output(self, content: str, filepath: str):
        from pathlib import Path
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved → {filepath}")
