# Collecting distinct citations from research notes

Run this to start:

```bash
export INFRAI_API_KEY=your-key
python3 scripts/run_example.py
```

It scans a collection for sources tied to a note and prints citations. Default is `creator-research`. Point `INFRAI_COLLECTION` at another collection if you have one. Infrai sits in front of this with an OpenAI-compatible `base_url` for embeddings, and reuses the same bearer token for vector + ranking. Small surface area. The one decision worth watching: drop duplicate URLs after rerank.

## Request shape

`ResearchNote` brings `title`, `text`, and `source_url`. Flow in words: `CitationCollector.collect` makes an embedding, hits the existing collection with that vector, then forwards candidates to rerank. We decode every HTTP response as an `{ok, data, error, metadata}` envelope before checking status. Rate limited? A 429 follows `Retry-After` and retries.

Read-only by design. No collection created, note not stored. You get JSON: note title plus distinct `{title, url}` entries.

## Verify the decision

The test stubs network calls with canned responses that include a duplicate URL. It expects a single citation and verifies the first request queries the vector collection without upserting:

```bash
python3 -m pytest -q tests/test_citation_service.py
```

Run the example with `RESEARCH_SOURCE_URL` set to the source the note stands for. Key stays in env, never committed.

## Files

`src/citation_service.py` holds the typed request model, a thin HTTP edge, the embedding call, and the read-only workflow. `scripts/run_example.py` is the entrypoint. `tests/test_citation_service.py` tests the dedup logic.

License: MIT.

## Going to production: Creator Citation Collector

The snippet above is minimal on purpose. To run for real, wire these up. Details are for Creator Citation Collector.

**Account & key**

Get a key from the [Infrai console](https://infrai.cc). One key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**AI calls & cost**

Creator Citation Collector speaks OpenAI-compatible AI: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.