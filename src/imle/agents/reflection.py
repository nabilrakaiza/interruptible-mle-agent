"""A4: reflection agent.

At phase boundaries, compresses completed nodes into findings. Every finding
carries its evidence (node IDs and scores) so it can be checked or corrected.

This module also holds `ask_json`, the structured-output loop shared with A1's
optional LLM leakage review.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from imle.agents.coding import LLM

M = TypeVar("M", bound=BaseModel)

MAX_RETRIES = 2

_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class StructuredOutputError(Exception):
    """The model did not return valid JSON for the schema within the allowed attempts."""


def parse_json(text: str) -> object:
    """The JSON value in a reply, allowing a ```json fence or text around one object."""
    text = text.strip()
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def ask_json(llm: LLM, *, agent: str, system: str, user: str, schema: type[M], max_retries: int = MAX_RETRIES,
             check=None) -> M:
    """Ask for JSON matching `schema`, retrying up to `max_retries` times with the error shown.

    `check(model)` may raise ValueError for problems the schema cannot express, such
    as unknown node IDs; that counts as an invalid reply too. LLMUnavailable from the
    client is not caught. Raises StructuredOutputError after the last attempt.
    """
    prompt, errors = user, []
    for _ in range(max_retries + 1):
        reply = llm(agent=agent, system=system, user=prompt)
        try:
            model = schema.model_validate(parse_json(reply))
            if check is not None:
                check(model)
            return model
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            error = str(e).splitlines()[0] if isinstance(e, json.JSONDecodeError) else str(e)
            errors.append(error[:300])
            prompt = (f"{user}\n\nYour previous reply was not valid: {error[:300]}\n"
                      "Reply again with only the JSON object, in the format given above.")
    raise StructuredOutputError(f"{agent}: no valid JSON after {max_retries + 1} attempts: {errors[-1]}")
