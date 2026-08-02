import json

import pytest

from claimlens.evidence import (
    EvidenceGrade,
    EvidenceGradingError,
    GradableCandidate,
    build_grading_prompt,
    parse_grading_json,
)


def candidate(title="A trial", text="Findings show X.", source="abstract"):
    return GradableCandidate(
        title=title,
        evidence_text=text,
        publisher="Journal",
        published_at="2021",
        adapter="pubmed",
        evidence_text_source=source,
    )


def test_prompt_numbers_candidates_and_flags_missing_abstracts():
    prompt = build_grading_prompt(
        "Isometrics build tendon strength.",
        [candidate(), candidate(title="Title only", text="Title only", source="title_fallback")],
    )

    assert "Claim: Isometrics build tendon strength." in prompt
    assert "[1] A trial (Journal · 2021 · pubmed)" in prompt
    assert "[2] Title only" in prompt
    assert "No abstract available; only the title is shown." in prompt
    assert "Grade all 2 candidates." in prompt


def test_prompt_trims_long_abstracts():
    prompt = build_grading_prompt("Claim", [candidate(text="word " * 2000)])

    assert len(prompt) < 3000
    assert prompt.rstrip().endswith("Grade all 1 candidates.")


def test_parse_returns_one_grade_per_candidate_in_order():
    content = json.dumps(
        {
            "gradings": [
                {"index": 2, "polarity": "contradicts", "rationale": "Opposes.", "confidence": 0.9},
                {"index": 1, "polarity": "supports", "rationale": "Affirms.", "confidence": 0.7},
            ]
        }
    )

    grades = parse_grading_json(content, expected=2)

    assert [g.polarity for g in grades] == ["supports", "contradicts"]
    assert [g.rationale for g in grades] == ["Affirms.", "Opposes."]
    assert [g.confidence for g in grades] == [0.7, 0.9]


def test_missing_grades_fall_back_to_context_rather_than_evidence():
    content = json.dumps(
        {"gradings": [{"index": 1, "polarity": "supports", "rationale": "Yes", "confidence": 1}]}
    )

    grades = parse_grading_json(content, expected=3)

    assert [g.polarity for g in grades] == ["supports", "context", "context"]
    assert grades[1].confidence is None


@pytest.mark.parametrize(
    "polarity",
    ["", None, "SUPPORTIVE", "maybe", "refutes", 42],
)
def test_unknown_polarity_degrades_to_context(polarity):
    content = json.dumps(
        {"gradings": [{"index": 1, "polarity": polarity, "rationale": "r", "confidence": 0.5}]}
    )

    assert parse_grading_json(content, expected=1)[0].polarity == "context"


def test_polarity_is_case_insensitive():
    content = json.dumps({"gradings": [{"index": 1, "polarity": " Supports ", "rationale": "r"}]})

    assert parse_grading_json(content, expected=1)[0].polarity == "supports"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(1.4, 1.0), (-0.2, 0.0), ("0.5", 0.5), ("high", None), (None, None), (float("nan"), None)],
)
def test_confidence_is_clamped_or_dropped(raw, expected):
    # json.dumps emits a bare NaN token, which json.loads accepts back as float("nan").
    content = json.dumps(
        {"gradings": [{"index": 1, "polarity": "supports", "rationale": "r", "confidence": raw}]}
    )

    grade = parse_grading_json(content, expected=1)[0]

    assert grade.confidence == expected


def test_out_of_range_and_duplicate_indices_are_ignored():
    content = json.dumps(
        {
            "gradings": [
                {"index": 0, "polarity": "supports", "rationale": "out of range"},
                {"index": 9, "polarity": "supports", "rationale": "out of range"},
                {"index": 1, "polarity": "supports", "rationale": "first wins"},
                {"index": 1, "polarity": "contradicts", "rationale": "duplicate ignored"},
            ]
        }
    )

    grades = parse_grading_json(content, expected=1)

    assert len(grades) == 1
    assert grades[0].rationale == "first wins"


def test_empty_rationale_is_replaced_rather_than_left_blank():
    content = json.dumps({"gradings": [{"index": 1, "polarity": "supports", "rationale": "  "}]})

    assert parse_grading_json(content, expected=1)[0].rationale


@pytest.mark.parametrize(
    "content",
    ["not json", "[]", json.dumps({"results": []}), json.dumps({"gradings": "nope"})],
)
def test_malformed_responses_raise(content):
    with pytest.raises(EvidenceGradingError):
        parse_grading_json(content, expected=1)


def test_non_dict_entries_are_skipped():
    content = json.dumps(
        {"gradings": ["junk", 5, {"index": 1, "polarity": "contradicts", "rationale": "ok"}]}
    )

    assert parse_grading_json(content, expected=1)[0].polarity == "contradicts"


def test_grade_dataclass_is_hashable_and_frozen():
    grade = EvidenceGrade(polarity="supports", rationale="r", confidence=0.5)

    with pytest.raises(AttributeError):
        grade.polarity = "context"  # type: ignore[misc]
