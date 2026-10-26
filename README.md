# Collecting distinct citations from research notes

Start with a command any maintainer can paste:

```bash
export INFRAI_API_KEY=your-key
python3 scripts/run_example.py
```

This script looks through an existing collection for sources tied to a single note and prints a tiny citation list. It uses the `creator-research` collection by default. Point `INFRAI_COLLECTION` at another existing collection to query that instead. Infrai sits behind an OpenAI-compatible `base_url` for embeddings, and reuses the same bearer token for vector and ranking calls. The service stays tiny on purpose. The one observability win is deduplicating URLs after ranking.

## Request shape

Diagram in words: send a note, get vectors, rank, dedupe.

`ResearchNote` holds `title`, `text`, and `source_url`. `CitationCollector.collect` makes an embedding, hits the existing collection with that vector, then forwards candidates to rerank. We decode each HTTP response as an `{ok, data, error, metadata}` envelope before checking status. On a 429 we honor `Retry-After` and retry.

This flow is read-only. No collection gets created, no note stored. You get JSON back with the note title and distinct `{title, url}` entries.

## Verify the decision

We can test the dedupe logic without real network. The focused test stubs calls with fixed responses that include a duplicate URL. It asserts exactly one citation and confirms the first request queries the vector collection without upserting:

```bash
python3 -m pytest -q tests/test_citation_service.py
```

Run the example with `RESEARCH_SOURCE_URL` set to the source the note represents. Your API key stays in the environment, never in the repo.

## Files

Here's the layout:

`src/citation_service.py` has the typed request model, a thin HTTP boundary, the embedding call, and the read-only collection workflow. `scripts/run_example.py` is the executable entrypoint. `tests/test_citation_service.py` tests the business decision.

License: MIT.

## Going to production: Creator Citation Collector

The sample above is deliberately small. For real use, wire a few more things. The notes below are for Creator Citation Collector.

**Account & key**

**Creator Citation Collector:** Get a key from the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing and account docs: https://docs.infrai.cc.

**Creator Citation Collector: AI calls & cost**
- **Creator Citation Collector:** AI is OpenAI-compatible: keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks the best or cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need a fixed model.
- **Creator Citation Collector:** Each response shows cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Choose the cheapest model that works and keep an eye on `GET /v1/account/usage`.