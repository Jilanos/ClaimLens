# ClaimLens MVP Roadmap

## Product Definition

ClaimLens is a pipeline for turning selected YouTube videos into concise, sourced briefs. The MVP should prove that the workflow can reliably process a small number of high-potential channels and produce useful summaries with evidence checks.

## MVP Success Criteria

- A user can define a small list of YouTube channels to monitor.
- The system can fetch recent videos and store their metadata.
- The user can select a video for processing.
- The system can create or retrieve a transcript.
- The system can produce a structured summary.
- The system can extract checkable claims.
- The system can search reliable sources for each claim.
- The final output is a Markdown brief with citations and confidence labels.

## Phase 0: Repository Foundation

- Create a minimal project structure.
- Add configuration examples.
- Add environment variable documentation.
- Add basic developer commands.
- Add a local SQLite storage plan.

Deliverable: a clean repository ready for implementation.

## Phase 1: YouTube Ingestion

Build the first ingestion module.

Scope:

- Read channel IDs from a config file.
- Fetch recent videos via the YouTube Data API.
- Store channel and video metadata in SQLite.
- Avoid duplicate video records.
- Track processing status per video.

Suggested tables:

- `channels`
- `videos`
- `pipeline_runs`

Deliverable: `claimlens ingest` fetches videos for configured channels.

## Phase 2: Video Selection

Add simple scoring and filtering.

Scope:

- Score videos by age, title keywords, description keywords, duration, and channel priority.
- Allow manual selection by video ID.
- Persist selected videos as processing candidates.

Deliverable: `claimlens candidates` lists videos worth processing.

## Phase 3: Transcript Pipeline

Create the transcript module.

Scope:

- Try to use existing YouTube captions when available.
- Fall back to audio download and OpenAI transcription.
- Store transcript text and metadata.
- Preserve timestamps when available.

Suggested tables:

- `transcripts`
- `transcript_segments`

Deliverable: `claimlens transcribe <video_id>` creates a reusable transcript.

## Phase 4: Summary and Claim Extraction

Use OpenAI to generate structured analysis.

Scope:

- Produce a concise summary.
- Extract key points.
- Extract verifiable claims.
- Classify claims by domain: science, health, finance, history, technology, general.
- Assign an initial verifiability score.

Suggested tables:

- `summaries`
- `claims`

Deliverable: `claimlens analyze <video_id>` stores summary and claims.

## Phase 5: Source Retrieval

Search for evidence.

Scope:

- Use PubMed for biomedical or health claims.
- Use Semantic Scholar for scientific claims.
- Add a generic source adapter for reputable web sources.
- Store source title, URL, publisher, publication date, abstract/snippet, and retrieval date.

Suggested tables:

- `sources`
- `claim_sources`

Deliverable: `claimlens source-check <video_id>` attaches candidate sources to claims.

## Phase 6: Evidence Assessment

Compare each claim against retrieved sources.

Scope:

- Label each claim as `supported`, `contradicted`, `mixed`, `unclear`, or `not_checked`.
- Provide a short rationale.
- Keep direct quotes short.
- Include source links.
- Preserve uncertainty instead of forcing binary verdicts.

Deliverable: each claim has a verdict, rationale, confidence, and sources.

## Phase 7: Markdown Brief Generation

Generate a reviewable output file.

Scope:

- Produce one Markdown file per processed video.
- Include video metadata.
- Include transcript status.
- Include summary.
- Include key claims and evidence checks.
- Include source links.
- Include editorial notes for weak or risky claims.

Deliverable: `outputs/briefs/<video_id>.md`.

## Phase 8: Quality Gates

Add reliability checks before scaling.

Scope:

- Unit tests for scoring, persistence, and source routing.
- Snapshot tests for Markdown generation.
- Manual review checklist for fact-check outputs.
- Cost logging for OpenAI calls.
- Retry and rate-limit handling.

Deliverable: the MVP is predictable enough to run repeatedly.

## Phase 9: First Automation

Schedule the pipeline.

Scope:

- Add a daily run command.
- Ingest new videos.
- Generate candidate list.
- Process only manually approved or top-scored videos.
- Produce local Markdown briefs.

Deliverable: a daily local workflow that creates review-ready briefs.

## Proposed CLI

```bash
claimlens init-db
claimlens ingest
claimlens candidates
claimlens transcribe <video_id>
claimlens analyze <video_id>
claimlens source-check <video_id>
claimlens brief <video_id>
claimlens run-daily
```

## Environment Variables

```bash
YOUTUBE_API_KEY=
OPENAI_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=
NCBI_API_KEY=
```

Only `OPENAI_API_KEY` is expected to be paid for the MVP. The other APIs can start on free quotas, subject to rate limits and terms.

## Initial Milestone Plan

### Milestone 1: Local Skeleton

- Python package skeleton.
- CLI entry point.
- SQLite schema.
- Config loading.

### Milestone 2: Metadata Ingestion

- YouTube channel config.
- Recent video ingestion.
- Candidate list.

### Milestone 3: First End-to-End Video

- Transcript creation.
- Summary generation.
- Claim extraction.
- Markdown export.

### Milestone 4: Evidence Checks

- PubMed adapter.
- Semantic Scholar adapter.
- Evidence labels.
- Source citations in output.

### Milestone 5: Repeatable MVP

- Tests.
- Cost tracking.
- Error handling.
- Daily run command.

## Key Risks

- YouTube transcript availability varies by video.
- Local audio download can be brittle and must respect platform terms.
- Automated fact-checking is probabilistic and requires human review.
- Scientific claims often need nuanced interpretation.
- API rate limits need explicit backoff and caching.
- SQLite schema version 2 must not ship without a tested migration path from schema version 1.

## MVP Principle

Keep the workflow small, auditable, and review-first. The MVP should help decide which videos deserve an article, not automatically publish claims without human validation.
