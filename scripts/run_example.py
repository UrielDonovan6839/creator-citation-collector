import json
import os

from src.citation_service import CitationCollector, ResearchNote


def main() -> None:
    collector = CitationCollector(collection=os.environ.get("INFRAI_COLLECTION", "creator-research"))
    note = ResearchNote(
        title="Subscriber update cadence",
        text="Creators report that a predictable weekly update improves retention.",
        source_url=os.environ.get("RESEARCH_SOURCE_URL", "https://example.com/research/subscriber-updates"),
    )
    print(json.dumps(collector.collect(note), indent=2))


if __name__ == "__main__":
    main()
