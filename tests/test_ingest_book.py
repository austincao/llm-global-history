"""Tests for ingest_book helpers."""

from scripts.ingest_book import cn_numeral_to_int, parse_chapter_heading


def test_cn_numeral_to_int():
    assert cn_numeral_to_int("7") == 7
    assert cn_numeral_to_int("第七章") is None
    assert cn_numeral_to_int("七") == 7
    assert cn_numeral_to_int("十一") == 11
    assert cn_numeral_to_int("二十二") == 22
    assert cn_numeral_to_int("四十四") == 44


def test_parse_chapter_heading():
    assert parse_chapter_heading("第七章\u3000中国文明") == (7, "中国文明")
    assert parse_chapter_heading("第22章 西欧的扩张") == (22, "西欧的扩张")
    # Inline footnote refs are ignored because only the first line of each document counts.
    assert parse_chapter_heading("第二章引语引自某人") == (2, "引语引自某人")
