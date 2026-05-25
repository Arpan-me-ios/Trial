import json
import os
import time
from typing import Any

from google import genai
from google.genai import types


NICHE_PRESETS: dict[str, dict[str, Any]] = {
    "betrayal_revenge": {
        "short": {
            "duration_target": "35 to 55 seconds",
            "style": "fast, emotional, first-person storytime with a hard reversal",
            "structure": [
                "Open with the betrayal in the first sentence.",
                "Add one concrete financial or social consequence.",
                "Reveal the revenge without promoting violence, harassment, or illegal behavior.",
                "End with a satisfying final line that invites comments.",
            ],
            "body_words": "95 to 135 words",
        },
        "long": {
            "duration_target": "6 to 9 minutes",
            "style": "cinematic narrated confession with escalating tension and clean payoff",
            "structure": [
                "Open with a high-stakes hook.",
                "Introduce the relationship, money, and hidden betrayal.",
                "Escalate through three specific discoveries.",
                "Resolve with legal, ethical revenge and a reflective ending.",
                "Close with a discussion-provoking final question.",
            ],
            "body_words": "850 to 1250 words",
        },
    }
}


REQUIRED_KEYS = ("title", "hook", "body", "description", "tags")


def _fallback_script(topic: str, video_type: str, niche: str, reason: Exception | None) -> dict[str, Any]:
    print(
        "Gemini generation unavailable after retries; using local fallback script. "
        f"Reason: {reason}",
        flush=True,
    )
    title = "He Thought I Would Never Check The Receipts"
    hook = "He betrayed me in the one place he thought I would never look."

    short_body = (
        f"{hook} {topic} At first, I wanted to confront him immediately, but I stayed quiet "
        "and opened every statement, message, invoice, and timestamp I could find. The pattern "
        "was worse than I expected. He had been moving money, changing names, and telling everyone "
        "I was the problem. So I did not yell. I built one clean folder with every receipt, sent it "
        "to the people who actually had power, and waited. By morning, his story collapsed. He lost "
        "the deal, had to repay what he took, and asked me why I ruined him. I told him the truth: "
        "I only organized what he left behind."
    )
    long_body = (
        f"{hook}\n\n{topic}\n\n"
        "For weeks, the small details did not add up. The missing money was always explained away, "
        "the strange messages were always called misunderstandings, and every question somehow became "
        "my fault. I stopped arguing and started documenting. I saved bank records, screenshots, edit "
        "history, calendar invites, and the one invoice he forgot to delete. Once I saw the whole picture, "
        "I realized the betrayal was not emotional only. It was planned.\n\n"
        "The revenge was simple because it was legal. I sent the evidence to the right people, asked for "
        "everything in writing, and refused every private phone call. By the end of the week, the lies had "
        "nowhere left to hide. He had to return the money, explain the paper trail, and watch the reputation "
        "he borrowed from me disappear. The best part was that I never had to raise my voice. I just let the "
        "receipts speak in the order he created them."
    )

    body = short_body if video_type == "short" else long_body
    return {
        "title": title,
        "hook": hook,
        "body": body,
        "description": (
            "A dramatic betrayal and ethical revenge story about receipts, timing, and the moment "
            "a lie finally collapses."
        ),
        "tags": [
            "betrayal story",
            "revenge story",
            "storytime",
            "receipts",
            "karma",
            "dramatic story",
            "youtube shorts",
            niche,
        ],
    }


def _extract_response_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) if content is not None else None
        if not parts:
            continue
        joined = "".join(getattr(part, "text", "") for part in parts)
        if joined.strip():
            return joined.strip()

    raise ValueError("Gemini returned an empty response; no JSON text was available to parse.")


def _validate_script_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"Expected Gemini JSON object, received {type(payload).__name__}.")

    missing = [key for key in REQUIRED_KEYS if key not in payload]
    extra = [key for key in payload.keys() if key not in REQUIRED_KEYS]
    if missing or extra:
        raise ValueError(
            "Gemini JSON schema mismatch. "
            f"Missing keys: {missing or 'none'}. Extra keys: {extra or 'none'}."
        )

    cleaned = {
        "title": str(payload["title"]).strip(),
        "hook": str(payload["hook"]).strip(),
        "body": str(payload["body"]).strip(),
        "description": str(payload["description"]).strip(),
        "tags": payload["tags"],
    }

    if isinstance(cleaned["tags"], str):
        cleaned["tags"] = [
            tag.strip().lstrip("#") for tag in cleaned["tags"].split(",") if tag.strip()
        ]
    elif isinstance(cleaned["tags"], list):
        cleaned["tags"] = [
            str(tag).strip().lstrip("#") for tag in cleaned["tags"] if str(tag).strip()
        ]
    else:
        raise ValueError("Gemini JSON field 'tags' must be a list of strings or a comma string.")

    empty_fields = [key for key in ("title", "hook", "body", "description") if not cleaned[key]]
    if empty_fields:
        raise ValueError(f"Gemini JSON contained empty required fields: {empty_fields}.")
    if not cleaned["tags"]:
        raise ValueError("Gemini JSON contained no usable tags.")

    return cleaned


def generate_script(topic: str, video_type: str, niche: str = "betrayal_revenge") -> dict[str, Any]:
    if video_type not in {"short", "long"}:
        raise ValueError("video_type must be either 'short' or 'long'.")
    if niche not in NICHE_PRESETS:
        raise ValueError(f"Unsupported niche '{niche}'. Available niches: {sorted(NICHE_PRESETS)}.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Export it before running the generator so google-genai "
            "can authenticate the Gemini request."
        )

    preset = NICHE_PRESETS[niche][video_type]
    client = genai.Client(api_key=api_key)

    prompt = f"""
Create a YouTube {'Shorts' if video_type == 'short' else 'long-form'} script package.

Topic:
{topic}

Niche:
{niche}

Rules:
- Theme: dramatic betrayal and ethical revenge.
- Target duration: {preset['duration_target']}.
- Writing style: {preset['style']}.
- Voiceover body length: {preset['body_words']}.
- Avoid hate, explicit sexual content, instructions for crimes, doxxing, threats, or real-person defamation.
- Revenge must be legal, nonviolent, and platform-safe.
- Return exactly these JSON keys and no others: title, hook, body, description, tags.
- tags must be a JSON array of 6 to 12 concise YouTube tags without hash symbols.

Story structure:
{json.dumps(preset['structure'], indent=2)}
""".strip()

    response = None
    last_error: Exception | None = None
    for attempt in range(1, 6):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                    top_p=0.95,
                ),
            )
            break
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            retryable = any(
                marker in message
                for marker in (
                    "unavailable",
                    "high demand",
                    "resource exhausted",
                    "rate limit",
                    "timeout",
                    "temporarily",
                    "503",
                    "429",
                )
            )
            if not retryable:
                raise
            if attempt == 5:
                return _fallback_script(topic, video_type, niche, exc)
            sleep_seconds = min(90, 8 * attempt * attempt)
            print(
                f"Gemini request failed on attempt {attempt}/5; retrying in "
                f"{sleep_seconds}s. Error: {exc}",
                flush=True,
            )
            time.sleep(sleep_seconds)

    if response is None:
        raise RuntimeError(f"Gemini did not return a response. Last error: {last_error}")

    raw_text = _extract_response_text(response)
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        preview = raw_text[:600].replace("\n", " ")
        raise ValueError(
            f"Gemini response was not valid JSON: {exc.msg} at line {exc.lineno}, "
            f"column {exc.colno}. Response preview: {preview}"
        ) from exc

    return _validate_script_payload(parsed)
