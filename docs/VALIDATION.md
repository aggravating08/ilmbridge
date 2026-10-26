# Validation - 26 October 2026

## Automated suite
Command: `python3 -m unittest discover -s tests -v`

Result: **19 tests passed** on Python 3.12. Tests exercise retrieval ranking, multi-passage questions, no-match abstention, source substring identity, Unicode tokens, bounded chunks, quiz reconstruction, empty input, model errors, invalid source IDs, API errors, cross-origin requests, and security headers. Model-boundary unit tests use mocks; they do not prove model quality.

## Actual local inference
Runtime: Ollama 0.40.11 on macOS arm64. Model: `qwen2.5:0.5b`, Q4_K_M, 494.03M parameters. Model digest: `a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67`.

A real HTTP call through `/api/ask` used the built-in notes and the question "How do light-dependent reactions support the Calvin cycle?" The final response was:

> The light-dependent reactions support the Calvin cycle by splitting water, releasing oxygen as a by-product, and producing ATP and NADPH, which carry energy to the Calvin cycle.

Measured application round trip: **0.65 seconds** after model warm-up. Ollama reported 210 input tokens and 36 output tokens. This is one observed example, not a benchmark or an accuracy estimate. The answer omitted inline citations; the app explicitly warns and separately displays the two retrieved passages. See `live-inference.json` for the actual response and source text.

### Failure found and improvement
The original longer prompt and three-passage context yielded an incorrect sentence claiming that light-dependent reactions do not directly use light. We shortened the prompt, limited retrieval to two passages and asked for a concise process-specific explanation. The rerun corrected that sentence. This is a targeted improvement on a demo case; it does not establish general correctness. Missing citations remain a known small-model limitation.

## Browser verification
- Built-in sample loads, notes count updates, and local-model status is detected.
- Source search for the two-stage question displays the Calvin-cycle and light-dependent-reaction passages.
- A revision card flips to the exact supporting sentence.
- The first sample quiz gap accepts `Photosynthesis`; five blanks score incorrect, giving 1/6, with source feedback.
- Desktop (1280 px) and narrow default browser layouts were visually reviewed.
- Local AI explanation was generated through the interface; the missing-citation warning appeared.
- Export downloaded a Markdown file containing notes, revision cards, the AI answer and original passages.
- A full-page interface capture is included as `desktop.jpg`.

## Privacy and limits
No cloud API is called for inference. The app binds to loopback and does not persist notes or log request URLs. The local Ollama process is separate. Export deliberately creates a local file. The project makes no measured claims about learning gains, translation quality or resistance to all prompt injection attempts.
