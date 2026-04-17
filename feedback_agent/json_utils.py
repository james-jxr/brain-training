"""Robust JSON extraction from Claude responses.

Claude occasionally wraps its output in markdown fences or adds preamble
text even when instructed not to. This module provides a single helper
that strips all of that before parsing.
"""
import json


def extract_json(raw: str, expected_start: str = "{") -> object:
    """
    Parse JSON from a Claude response that may contain preamble or markdown.

    Strategy (in order):
      1. Strip whitespace and try raw_decode (handles trailing prose after valid JSON).
      2. Look for a ```json ... ``` or ``` ... ``` code block.
      3. Find the first occurrence of expected_start and raw_decode from there.

    Uses raw_decode throughout so trailing text after the JSON never causes
    "Extra data" errors.

    Raises json.JSONDecodeError if no valid JSON is found.
    """
    decoder = json.JSONDecoder()
    raw = raw.strip()

    def _raw_decode(s: str):
        """Return parsed object, ignoring anything after the first valid JSON value."""
        obj, _ = decoder.raw_decode(s)
        return obj

    # 1. Direct parse (may have trailing prose — raw_decode handles it)
    if raw.startswith(expected_start):
        return _raw_decode(raw)

    # 2. Markdown code block
    if "```" in raw:
        parts = raw.split("```")
        for block in parts[1::2]:  # every odd element is inside fences
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            if block.startswith(expected_start):
                return _raw_decode(block)

    # 3. Find first expected_start character and raw_decode from there
    idx = raw.find(expected_start)
    if idx != -1:
        return _raw_decode(raw[idx:])

    raise json.JSONDecodeError(
        f"No JSON starting with '{expected_start}' found in response",
        raw, 0
    )
