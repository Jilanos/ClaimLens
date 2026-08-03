"""Fixtures shared by more than one test module.

They live here rather than in one of the test modules so that neither module has to
import the other, which only works when the repository root happens to be importable.
"""

from dataclasses import dataclass

from claimlens import db
from claimlens.analysis import TranscriptAnalysis
from claimlens.config import SourceConfig


@dataclass(frozen=True)
class Client:
    model: str = "test-model"

    def analyze(self, transcript_text: str) -> TranscriptAnalysis:
        assert "clean text" in transcript_text
        return TranscriptAnalysis(
            summary="Concise summary.",
            key_points=["Point one", "Point two"],
            notable_claims=["Claim one"],
            caveats=["Caveat one"],
            editorial_notes=["Note one"],
        )


@dataclass(frozen=True)
class Segment:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class Transcript:
    video_id: str
    source: str
    language: str
    text: str
    segments: list[Segment]


def store_cleaned_fixture(database, video_id: str) -> None:
    transcript_id = db.upsert_transcript(
        database,
        Transcript(
            video_id=video_id,
            source="youtube",
            language="en",
            text="clean text",
            segments=[Segment(start_seconds=0.0, end_seconds=1.0, text="clean text")],
        ),
    )
    db.upsert_cleaned_transcript(
        database,
        video_id=video_id,
        transcript_id=transcript_id,
        text="clean text",
    )


def source_config(*, advanced: bool) -> SourceConfig:
    return SourceConfig(
        advanced_source_verification=advanced,
        enable_pubmed=True,
        enable_semantic_scholar=True,
        enable_web_search=False,
    )
