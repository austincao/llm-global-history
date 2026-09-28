from pathlib import Path

from gh_pipeline.rag_index import ParagraphIndex


def test_bm25_search_ranks_relevant_paragraph():
    index = ParagraphIndex.load(Path("tests/fixtures/mini_rag_index.json"))
    hits = index.search("美洲的发现", top_k=2, chapter_start=22, chapter_end=22)
    assert hits
    assert hits[0].paragraph.chapter_index == 22
    assert "美洲" in hits[0].paragraph.text


def test_chapter_filter_excludes_other_chapters():
    index = ParagraphIndex.load(Path("tests/fixtures/mini_rag_index.json"))
    hits = index.search("文明", top_k=5, chapter_start=22, chapter_end=22)
    assert all(h.paragraph.chapter_index == 22 for h in hits)


def test_chapter_filter_includes_chapter_seven():
    index = ParagraphIndex.load(Path("tests/fixtures/mini_rag_index.json"))
    hits = index.search("黄河流域", top_k=3, chapter_start=7, chapter_end=7)
    assert hits
    assert hits[0].paragraph.chapter_index == 7
