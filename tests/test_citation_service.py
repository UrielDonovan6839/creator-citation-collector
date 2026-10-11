import json

from src.citation_service import CitationCollector, ResearchNote


def test_collect_dedupes_urls(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    collector = CitationCollector()
    collector.embedding_client = type("Emb", (), {"embeddings": type("E", (), {"create": lambda *a, **k: type("R", (), {"data": [type("D", (), {"embedding": [0.1, 0.2]})()]})()})()})()
    calls = []
    def fake_post(path, payload):
        calls.append((path, payload))
        if path.endswith("query"):
            return {"matches": [{"metadata": {"title": "A", "url": "https://a"}}, {"metadata": {"title": "A copy", "url": "https://a"}}]}
        if path.endswith("rerank"):
            return {"results": [{"metadata": {"title": "A", "url": "https://a"}}, {"metadata": {"title": "A copy", "url": "https://a"}}]}
        return {}
    collector._post = fake_post
    result = collector.collect(ResearchNote("n", "text", "https://source"))
    assert result["citations"] == [{"title": "A", "url": "https://a"}]
    assert calls[0][0] == "/v1/vector/query"
    assert all(path != "/v1/vector/upsert" for path, _ in calls)
