"""LLM abstraction clients using direct HTTP requests via httpx (Phase 5)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Base exception for LLM client operations."""
    pass


class BaseLlmClient:
    """Unified interface for LLM operations."""

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        response_format_json: bool = False,
    ) -> str:
        """Send chat messages and return the assistant response string."""
        raise NotImplementedError


class OpenAiLlmClient(BaseLlmClient):
    """Client for OpenAI completion API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.url = "https://api.openai.com/v1/chat/completions"

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        response_format_json: bool = False,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.2,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.error("OpenAI API error: %s", exc)
            raise LLMClientError(f"OpenAI error: {exc}") from exc


class ClaudeLlmClient(BaseLlmClient):
    """Client for Anthropic Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20240620", timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.url = "https://api.anthropic.com/v1/messages"

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        response_format_json: bool = False,
    ) -> str:
        # Note: Anthropic system prompt is a top-level parameter, not inside messages.
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # Claude only permits alternating user/assistant messages.
        # Filter messages and map system roles if any.
        clean_messages = []
        for m in messages:
            role = m["role"]
            if role == "system":
                # If there are system messages in the log, we prepend them to system_prompt
                system_prompt = f"{system_prompt}\n{m['content']}".strip() if system_prompt else m["content"]
            else:
                clean_messages.append({"role": role, "content": m["content"]})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": clean_messages,
            "max_tokens": 4096,
            "temperature": 0.2,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["content"][0]["text"]
                return content
        except Exception as exc:
            logger.error("Claude API error: %s", exc)
            raise LLMClientError(f"Claude error: {exc}") from exc


class AzureOpenAiLlmClient(BaseLlmClient):
    """Client for Azure OpenAI completions."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        deployment_id: str,
        api_version: str = "2024-02-15-preview",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.deployment_id = deployment_id
        self.api_version = api_version
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        response_format_json: bool = False,
    ) -> str:
        # Azure URL format: {base_url}/openai/deployments/{deployment_id}/chat/completions?api-version={api_version}
        url = f"{self.base_url}/openai/deployments/{self.deployment_id}/chat/completions?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload: dict[str, Any] = {
            "messages": formatted_messages,
            "temperature": 0.2,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.error("Azure OpenAI API error: %s", exc)
            raise LLMClientError(f"Azure OpenAI error: {exc}") from exc


class OllamaLlmClient(BaseLlmClient):
    """Client for local Ollama instances."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3", timeout: float = 45.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.url = f"{self.base_url}/api/chat"

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        response_format_json: bool = False,
    ) -> str:
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        if response_format_json:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
        except Exception as exc:
            logger.error("Ollama API error: %s", exc)
            raise LLMClientError(f"Ollama error: {exc}") from exc


class StubLlmClient(BaseLlmClient):
    """Offline stub/mock client for fallback and tests."""

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        response_format_json: bool = False,
    ) -> str:
        logger.warning("Using StubLlmClient - no remote LLM configured.")
        user_msg = messages[-1]["content"] if messages else ""
        
        response_dict = {
            "answer": f"This is a stub LLM response for: '{user_msg}'. Configure your LLM environment variables to enable full AI insights.",
            "summary": "Stub response summary.",
            "sources": [{"type": "system_stub", "detail": "Mock response without active LLM provider."}]
        }
        
        if response_format_json:
            return json.dumps(response_dict)
        return response_dict["answer"]


def get_llm_client(settings: Any) -> BaseLlmClient:
    """Factory to retrieve client based on settings config."""
    # Read environment variables directly or from settings object.
    # Allow settings to hold these, or fall back to system env.
    import os
    
    provider = os.getenv("LLM_PROVIDER", getattr(settings, "llm_provider", "stub")).lower()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found, falling back to stub.")
            return StubLlmClient()
        return OpenAiLlmClient(api_key=api_key, model=model)
        
    elif provider == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20240620")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found, falling back to stub.")
            return StubLlmClient()
        return ClaudeLlmClient(api_key=api_key, model=model)
        
    elif provider == "azure":
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        base_url = os.getenv("AZURE_OPENAI_BASE_URL", "")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "")
        version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        if not api_key or not base_url or not deployment:
            logger.warning("Azure OpenAI configuration incomplete, falling back to stub.")
            return StubLlmClient()
        return AzureOpenAiLlmClient(
            api_key=api_key,
            base_url=base_url,
            deployment_id=deployment,
            api_version=version,
        )
        
    elif provider == "ollama":
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
        model = os.getenv("LLM_MODEL", "llama3")
        return OllamaLlmClient(base_url=base_url, model=model)
        
    else:
        return StubLlmClient()
