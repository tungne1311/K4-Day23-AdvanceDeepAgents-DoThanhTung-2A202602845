"""Shared input-token pacing and transient model-error classification."""
import asyncio
import json
import math
import threading
import time
from collections import deque

import httpx
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.exceptions import ModelConnectionError, ModelRateLimitError, ModelTimeoutError
from langchain_core.utils.function_calling import convert_to_openai_tool


def retryable_model_error(exc):
    """Retry quota windows, timeouts and service failures, not auth/billing errors."""
    detail = str(exc).lower()
    if any(marker in detail for marker in ("generaterequestsperday", "requests_per_day",
                                            "free-models-per-day", "daily quota", "daily limit")):
        return False
    if isinstance(exc, (ModelRateLimitError, ModelConnectionError, ModelTimeoutError, httpx.TransportError)):
        return True
    return getattr(exc, "status_code", None) in {429, 500, 502, 503, 504} or getattr(exc, "retryable", None) is True


def estimate_input_tokens(request):
    """Conservative local estimate including system prompt, history and tool schemas.

    This is a pacing heuristic, not a provider tokenizer or billing measurement.
    No prompts, messages, or credentials are printed or sent to a counting API.
    """
    characters = 0
    for message in [getattr(request, "system_message", None), *request.messages]:
        if message is not None:
            characters += len(message.model_dump_json() if hasattr(message, "model_dump_json") else str(message))
    for tool in request.tools or []:
        characters += len(json.dumps(convert_to_openai_tool(tool), ensure_ascii=False))
    return math.ceil(characters / 3) + 4096


class TokenWindow:
    """Reserve estimated input tokens atomically across all parallel agents."""

    def __init__(self, budget=180000, period=60.0, *, clock=time.monotonic, sleep=time.sleep):
        if budget < 1 or period <= 0:
            raise ValueError("budget and period must be positive")
        self.budget, self.period = budget, period
        self._clock, self._sleep = clock, sleep
        self._events = deque()
        self._used = 0
        self._lock = threading.Lock()

    def reserve(self, tokens):
        tokens = max(1, int(tokens))
        if tokens > self.budget:
            raise RuntimeError("one request exceeds LAB_INPUT_TPM; reduce context or configure a suitable input budget")
        announced = False
        while True:
            with self._lock:
                now = self._clock()
                while self._events and self._events[0][0] <= now - self.period:
                    self._used -= self._events.popleft()[1]
                if self._used + tokens <= self.budget:
                    self._events.append((now, tokens))
                    self._used += tokens
                    return
                delay = max(0.01, self._events[0][0] + self.period - now)
            if not announced:
                print(f"[model pacing] Waiting {delay:.1f}s for shared input budget", flush=True)
                announced = True
            # Release the lock while waiting so other agents can finish.
            self._sleep(min(delay, 60.0))


class ModelTokenPacer(AgentMiddleware):
    """One shared window for lead, researchers, checker, and model retries."""

    def __init__(self, window):
        self.window = window

    def wrap_model_call(self, request, handler):
        self.window.reserve(estimate_input_tokens(request))
        return handler(request)

    async def awrap_model_call(self, request, handler):
        await asyncio.to_thread(self.window.reserve, estimate_input_tokens(request))
        return await handler(request)
