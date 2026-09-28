from pathlib import Path

from gh_pipeline.rag_hybrid import HybridParagraphIndex


def test_get_chapter_context_highlights_neighbors():
    index = HybridParagraphIndex.load(Path("tests/fixtures/mini_rag_index.json"))
    items = index.get_chapter_context(22, 1, before=1, after=1)
    assert len(items) == 2
    assert items[0].paragraph_index == 1
    assert items[1].paragraph_index == 2


def test_hybrid_load_without_embeddings_falls_back_to_bm25():
    index = HybridParagraphIndex.load(Path("tests/fixtures/mini_rag_index.json"))
    assert not index.has_embeddings
    hits = index.search("美洲", chapter_start=22, chapter_end=22, top_k=1)
    assert hits
    assert hits[0].paragraph.chapter_index == 22
