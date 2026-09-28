"""Tests for global history time parsing."""

from gh_pipeline.time_parsing import (
    parse_chapter_title_years,
    parse_year_from_text,
    parse_year_range_from_text,
)


def test_bce_year():
    assert parse_year_from_text("公元前3500年只是个大概的日期").year == -3500


def test_qian_year():
    assert parse_year_from_text("1445年，葡萄牙的早期探险").year == 1445


def test_ce_range_in_title():
    r = parse_chapter_title_years("西欧的扩张：伊比利亚阶段（1500—1600年）")
    assert r is not None
    assert r.start_year == 1500
    assert r.end_year == 1600


def test_mixed_bce_ce_range():
    r = parse_year_range_from_text("公元前1000—公元500年")
    assert r is not None
    assert r.start_year == -1000
    assert r.end_year == 500


def test_bce_range():
    r = parse_year_range_from_text("公元前3500—前1000年")
    assert r is not None
    assert r.start_year == -3500
    assert r.end_year == -1000


def test_century():
    assert parse_year_from_text("16世纪的欧洲扩张").year == 1501
