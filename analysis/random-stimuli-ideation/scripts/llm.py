"""Isolated headless Claude calls with structured JSON output."""

import json
import subprocess
import tempfile
import time

from config import LLM_MAX_ATTEMPTS, SYSTEM_PROMPT

_EMPTY_CWD = tempfile.mkdtemp(prefix="rsi_empty_cwd_")


class ClaudeRefusal(RuntimeError):
    """The model or an API safety classifier declined this exact prompt. Deterministic for a
    given prompt, so it is never retried; callers decide explicitly how to record it."""


def call_claude(prompt: str, model: str, schema: dict) -> dict:
    """Run one fresh-context `claude -p` call; return the full JSON envelope.

    Raises on any non-zero exit, error flag, or missing structured output, so a
    failed call can never be silently recorded as an empty idea list.
    """
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--tools", "",
        "--system-prompt", SYSTEM_PROMPT,
        "--setting-sources", "",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--output-format", "json",
        "--json-schema", json.dumps(schema),
    ]
    # A non-zero exit (e.g. a transient API/rate-limit error) is retried with backoff and logged;
    # the request is identical between attempts, and persistent failure is still fatal.
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        proc = subprocess.run(cmd, cwd=_EMPTY_CWD, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=600)
        if proc.returncode == 0:
            break
        if '"stop_reason":"refusal"' in proc.stdout:
            # A model/API refusal is deterministic for a given prompt; retrying will not help.
            raise ClaudeRefusal("claude refused this prompt (stop_reason=refusal)")
        detail = f"stdout={proc.stdout[:1500]!r} stderr={proc.stderr[:500]!r}"
        print(f"WARNING claude exited {proc.returncode} (attempt {attempt}/{LLM_MAX_ATTEMPTS}): {detail}", flush=True)
        if attempt < LLM_MAX_ATTEMPTS:
            time.sleep(20 * attempt)
    else:
        raise RuntimeError(f"claude exited {proc.returncode} after {LLM_MAX_ATTEMPTS} attempts: {detail}")
    envelope = json.loads(proc.stdout)
    if envelope.get("is_error"):
        raise RuntimeError(f"claude returned error: {envelope.get('result')}")
    if not isinstance(envelope.get("structured_output"), dict) and "safety classifier" in str(envelope.get("result")):
        # The model reports that a safety classifier stopped an earlier turn and declines to resubmit.
        raise ClaudeRefusal(f"safety-classifier stop reported by model: {envelope.get('result')}")
    if not isinstance(envelope.get("structured_output"), dict):
        raise RuntimeError(f"no structured_output in response: {proc.stdout[:2000]}")
    used = list((envelope.get("modelUsage") or {}).keys())
    if model not in used:
        raise RuntimeError(f"requested model {model} but usage shows {used}")
    return envelope
