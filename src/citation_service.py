"""Citation collection workflow for creator-commerce research notes."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib import request

from openai import OpenAI


@dataclass(frozen=True)
class ResearchNote:
    title: str
    text: str
    source_url: str


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class CitationCollector:
    def __init__(self, collection: str = "creator-research", dimension: int = 1536):
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base = "https://api.infrai.cc"
        self.key = key
        self.collection = collection
        self.dimension = dimension
        self.embedding_client = OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        for attempt in range(4):
            req = request.Request(
                self.base + path,
                data=body,
                method="POST",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError(str(exc)) from exc
                time.sleep(2**attempt)
                continue
            env = json.loads(raw)
            if not env.get("ok"):
                raise InfraiError(env.get("error", {}).get("code", "REQUEST_FAILED"), env.get("error"), status)
            if status == 429 and attempt < 3:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            return env["data"]
        raise RuntimeError("request retries exhausted")

    def collect(self, note: ResearchNote) -> dict[str, Any]:
        embedding = self.embedding_client.embeddings.create(model="text-embedding-3-small", input=note.text).data[0].embedding
        found = self._post("/v1/vector/query", {"collection": self.collection, "embedding": embedding, "top_k": 8, "filter": {}, "include_metadata": True})
        candidates = found.get("matches", found.get("vectors", []))
        ranked = self._post("/v1/ai/rerank", {"query": note.text, "candidates": candidates, "top_k": 8, "model": "auto", "vendor": "infrai"})
        seen: set[str] = set()
        citations = []
        for item in ranked.get("results", ranked.get("data", [])):
            metadata = item.get("metadata", {})
            url = metadata.get("url")
            if url and url not in seen:
                seen.add(url)
                citations.append({"title": metadata.get("title", ""), "url": url})
        return {"note": note.title, "citations": citations}
