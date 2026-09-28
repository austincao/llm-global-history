"""Parse BCE/CE years from Global History Chinese text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ParsedYear:
    year: int
    parse_method: str
    confidence: float


@dataclass(frozen=True)
class ParsedYearRange:
    start_year: int
    end_year: int
    parse_method: str
    confidence: float


_RE_GONGYUANQIAN = re.compile(r"公元前\s*(\d{1,5})")
_RE_QIAN_YEAR = re.compile(r"前\s*(\d{1,5})\s*年")
_RE_GONGYUAN = re.compile(r"公元\s*(\d{1,4})")
_RE_CE_YEAR = re.compile(r"(?<![前约])(\d{3,4})\s*年")
_RE_CENTURY = re.compile(r"(\d{1,2})\s*世纪")
_RE_CIRCA_BCE = re.compile(r"约\s*公元前\s*(\d{1,5})")
_RE_CIRCA_CE = re.compile(r"约\s*(\d{3,4})\s*年")
_RE_BEFORE_YEAR = re.compile(r"(\d{3,4})\s*年\s*以前")
_RE_RANGE_MIXED = re.compile(
    r"公元前\s*(\d{1,5})\s*[—\-–至到]\s*(?:公元\s*)?(\d{1,4})"
)
_RE_RANGE_BCE = re.compile(r"公元前\s*(\d{1,5})\s*[—\-–至到]\s*前\s*(\d{1,5})")
_RE_RANGE_CE = re.compile(r"(\d{3,4})\s*[—\-–至到]\s*(\d{3,4})\s*年?")
_RE_RANGE_CE_SHORT = re.compile(r"(\d{3,4})\s*[—\-–]\s*(\d{3,4})")


def bce(year: int) -> int:
    return -abs(year)


def parse_year_range_from_text(text: str) -> Optional[ParsedYearRange]:
    if not text:
        return None

    match = _RE_RANGE_MIXED.search(text)
    if match:
        return ParsedYearRange(
            start_year=bce(int(match.group(1))),
            end_year=int(match.group(2)),
            parse_method="regex:公元前—公元",
            confidence=0.95,
        )

    match = _RE_RANGE_BCE.search(text)
    if match:
        return ParsedYearRange(
            start_year=bce(int(match.group(1))),
            end_year=bce(int(match.group(2))),
            parse_method="regex:公元前—前",
            confidence=0.95,
        )

    match = _RE_RANGE_CE.search(text) or _RE_RANGE_CE_SHORT.search(text)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        if start <= end:
            return ParsedYearRange(
                start_year=start,
                end_year=end,
                parse_method="regex:ce_range",
                confidence=0.9,
            )

    match = _RE_BEFORE_YEAR.search(text)
    if match:
        end = int(match.group(1))
        return ParsedYearRange(
            start_year=end - 100,
            end_year=end,
            parse_method="regex:before_year",
            confidence=0.6,
        )

    single = parse_year_from_text(text)
    if single:
        return ParsedYearRange(
            start_year=single.year,
            end_year=single.year,
            parse_method=single.parse_method,
            confidence=single.confidence,
        )
    return None


def parse_year_from_text(text: str) -> Optional[ParsedYear]:
    if not text:
        return None

    for pattern, method, confidence, transform in (
        (_RE_CIRCA_BCE, "regex:约公元前", 0.75, bce),
        (_RE_GONGYUANQIAN, "regex:公元前", 1.0, bce),
        (_RE_QIAN_YEAR, "regex:前年", 0.95, bce),
        (_RE_CIRCA_CE, "regex:约年", 0.75, int),
        (_RE_GONGYUAN, "regex:公元", 0.95, int),
        (_RE_CE_YEAR, "regex:年", 0.85, int),
    ):
        match = pattern.search(text)
        if match:
            return ParsedYear(
                year=transform(int(match.group(1))),
                parse_method=method,
                confidence=confidence,
            )

    match = _RE_CENTURY.search(text)
    if match:
        century = int(match.group(1))
        return ParsedYear(
            year=(century - 1) * 100 + 1,
            parse_method="regex:世纪",
            confidence=0.7,
        )

    return None


def parse_chapter_title_years(title: str) -> Optional[ParsedYearRange]:
    """Extract year range from chapter title parentheses, e.g. （1500—1600年）."""
    match = re.search(r"[（(]([^）)]+)[）)]", title)
    if not match:
        return None
    return parse_year_range_from_text(match.group(1))


def parse_part_title_years(title: str) -> Optional[ParsedYearRange]:
    return parse_year_range_from_text(title)
