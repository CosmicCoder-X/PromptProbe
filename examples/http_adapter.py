from __future__ import annotations

import json
import os
from urllib import request


def http_json_target(prompt: str, metadata: dict | None = None, case=None) -> str:
    metadata = metadata or {}
    endpoint = metadata["endpoint"]
    prompt_field = metadata.get("prompt_field", "prompt")
    response_field = metadata.get("response_field", "response")
    method = metadata.get("method", "POST").upper()

    payload = dict(metadata.get("static_payload", {}))
    payload[prompt_field] = prompt
    if case is not None:
        payload["case_id"] = case.case_id
        payload["category"] = case.category

    headers = {"Content-Type": "application/json"}
    headers.update(metadata.get("headers", {}))
    auth_env = metadata.get("auth_token_env")
    if auth_env and os.environ.get(auth_env):
        headers["Authorization"] = f"Bearer {os.environ[auth_env]}"

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(endpoint, data=body, headers=headers, method=method)
    timeout = float(metadata.get("timeout_seconds", 30))
    with request.urlopen(req, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
    parsed = json.loads(response_body)
    return str(parsed.get(response_field, response_body))
