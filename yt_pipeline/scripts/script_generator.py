import json
import os
import random
import time
from typing import Any

from google import genai
from google.genai import types

from scripts.env_loader import load_local_env


NICHE_PRESETS: dict[str, dict[str, Any]] = {
    "betrayal_revenge": {
        "short": {
            "duration_target": "35 to 55 seconds",
            "style": "fast, emotional, first-person storytime with a hard reversal",
            "structure": [
                "Open with a betrayal in the first sentence and make viewers wonder what happened next.",
                "Add one concrete object, receipt, message, or timestamp that proves the lie.",
                "Escalate through one personal consequence and one public consequence.",
                "Reveal the legal, ethical revenge as a twist the betrayer caused themselves.",
                "End with a punchy comment-bait question or final line.",
            ],
            "body_words": "95 to 135 words",
        },
        "long": {
            "duration_target": "6 to 9 minutes",
            "style": "cinematic narrated confession with escalating tension and clean payoff",
            "structure": [
                "Open with a high-stakes hook that creates an unanswered question.",
                "Introduce the relationship, money, and hidden betrayal.",
                "Escalate through three specific discoveries, each worse than the last.",
                "Resolve with legal, ethical revenge and a reflective ending.",
                "Close with a discussion-provoking final question viewers will argue about.",
            ],
            "body_words": "850 to 1250 words",
        },
    }
}


REQUIRED_KEYS = ("title", "hook", "body", "description", "tags")

STORY_FLAVORS = [
    {
        "name": "cold open receipt reveal",
        "pattern": "Start at the exact moment a receipt, alert, or file appears, then rewind briefly.",
        "payoff": "The betrayer is exposed by a record they personally created.",
    },
    {
        "name": "public event reversal",
        "pattern": "Build toward a wedding, dinner, board meeting, reunion, launch, or court date.",
        "payoff": "The public moment flips because the narrator prepared quietly.",
    },
    {
        "name": "fake ally betrayal",
        "pattern": "Make the betrayer look helpful at first, then reveal they engineered the problem.",
        "payoff": "Their helpful mask collapses when the narrator asks one calm question.",
    },
    {
        "name": "money trail mystery",
        "pattern": "Follow one suspicious charge, payment, loan, invoice, or missing deposit.",
        "payoff": "The financial trail leads to a social betrayal nobody expected.",
    },
    {
        "name": "wrong target setup",
        "pattern": "Everyone blames the narrator early, but each clue quietly points elsewhere.",
        "payoff": "The final proof makes the accusers realize they defended the wrong person.",
    },
    {
        "name": "silent exit",
        "pattern": "The narrator does not confront anyone; they remove access, money, venue, or leverage.",
        "payoff": "The betrayer discovers the consequence only after it is irreversible.",
    },
]


def _fallback_script(topic: str, video_type: str, niche: str, reason: Exception | None) -> dict[str, Any]:
    print(
        "Gemini generation unavailable after retries; using local fallback script. "
        f"Reason: {reason}",
        flush=True,
    )
    fallback_angles = [
        (
            "The Receipt That Ended Everything",
            "The part he forgot to delete was the part that destroyed his whole story.",
            "receipt",
            "I started with one charge that made no sense",
        ),
        (
            "He Lied Until The Timestamp Exposed Him",
            "I almost believed him, until one timestamp made the entire lie fall apart.",
            "timestamp",
            "The timestamp was small, but it changed the entire order of events",
        ),
        (
            "She Thought The Group Chat Was Gone",
            "She deleted the messages, but she forgot screenshots do not ask for permission.",
            "screenshots",
            "The group chat was supposed to make me look dramatic",
        ),
        (
            "He Tried To Steal From Me In Writing",
            "He would have gotten away with it if he had not put the plan in an email.",
            "email",
            "The email was forwarded to me by mistake",
        ),
        (
            "They Picked The Wrong Person To Blame",
            "Everyone believed their version until I showed them the one thing they could not explain.",
            "proof",
            "The worst part was how confident they sounded",
        ),
        (
            "I Let Them Celebrate First",
            "I waited until they thought they had won, because that was when they got careless.",
            "timeline",
            "They were already celebrating before they noticed my name was still on the paperwork",
        ),
        (
            "The Apology Came Too Late",
            "The apology only arrived after the evidence reached the person they were trying to impress.",
            "message",
            "I knew it was fake because it started with an excuse",
        ),
    ]
    title, hook, proof_object, first_turn = random.choice(fallback_angles)
    second_turns = [
        "Then I found a second detail that proved it was planned.",
        "Then one tiny mismatch told me this had been going on for weeks.",
        "Then the person defending them accidentally confirmed my timeline.",
        "Then I realized the lie only worked if I stayed quiet.",
    ]
    consequences = [
        "The meeting got very quiet.",
        "The group chat stopped moving.",
        "The person they were trying to impress asked for the full folder.",
        "The money trail became impossible to explain.",
    ]

    short_body = (
        f"{hook} {topic} {first_turn}, so I did not confront anyone. I built a clean folder "
        f"around the {proof_object}. {random.choice(second_turns)} By the time I sent the timeline, "
        f"there was nothing emotional in it, just names, dates, and proof. {random.choice(consequences)} "
        "The apology came after the consequence, which told me everything. When they asked why I made "
        "it public, I said I did not. I only stopped protecting a private lie."
    )
    long_body = (
        f"{hook}\n\n{topic}\n\n"
        f"For weeks, the details felt small enough to ignore. One changed story. One missing payment. "
        f"One message that arrived too late. Then I found the {proof_object}, and suddenly every excuse "
        "lined up like it had been rehearsed. That was when I stopped asking questions out loud and started "
        "writing everything down.\n\n"
        "The first discovery hurt. The second one made me angry. The third one made me careful, because it "
        "proved the betrayal was not a misunderstanding. It was a plan with dates, names, and a paper trail. "
        "So I made my own timeline. No insults, no threats, no dramatic confrontation. Just the facts, the "
        "attachments, and the one person who had the authority to do something about it.\n\n"
        "When the truth landed, it did not explode. It got very quiet. People stopped defending him. The "
        "private calls started, but I refused every conversation that was not in writing. By the end of the "
        "week, he had to explain the missing money, the changed story, and the evidence he created himself. "
        "He said I ruined his reputation. I told him reputation is what remains after the receipts are read."
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

    load_local_env()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        if os.getenv("YT_PIPELINE_STRICT_GEMINI", "0") == "1":
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Export it or add it to yt_pipeline/.env so "
                "google-genai can authenticate the Gemini request."
            )
        return _fallback_script(
            topic,
            video_type,
            niche,
            RuntimeError("GEMINI_API_KEY is not set; using local script fallback."),
        )

    preset = NICHE_PRESETS[niche][video_type]
    story_flavor = random.choice(STORY_FLAVORS)
    os.environ["GEMINI_API_KEY"] = api_key
    client = genai.Client()

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
- Every 2 to 3 sentences should create a new open loop, reveal, or reversal.
- Use specific receipts: dates, screenshots, bank alerts, doorbell footage, invoices, contracts, emails, or location pings.
- Keep the narrator emotionally controlled; the satisfaction should come from evidence and consequences.
- Avoid generic phrasing like "little did he know" unless it is followed by a specific reveal.
- Use this story flavor for this run: {story_flavor['name']}.
- Flavor pattern: {story_flavor['pattern']}
- Flavor payoff: {story_flavor['payoff']}
- Do not reuse common betrayal-story beats unless they are made specific to the topic.
- Avoid repeating the same sentence openings. Vary sentence length aggressively.
- Give the narrator one distinctive personal motive, weakness, or boundary.
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
