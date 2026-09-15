"""Pluggable AI backend.

Callers never talk to a specific provider directly — they call
`generate_text(system_prompt, user_prompt, fallback_text)` and get back
either a real LLM completion (when AI_PROVIDER=anthropic and an API key is
configured) or the deterministic `fallback_text` built by the rule-based
recommendation logic. This keeps the whole recommendation flow runnable
with zero external dependencies, while making it a one-env-var swap to
plug in a real model later.
"""

from flask import current_app


def generate_text(system_prompt, user_prompt, fallback_text):
    provider = current_app.config.get("AI_PROVIDER", "rule_based")
    api_key = current_app.config.get("ANTHROPIC_API_KEY")

    if provider != "anthropic" or not api_key:
        return fallback_text

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=current_app.config.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ) or fallback_text
    except Exception:
        # Never let an AI provider outage break the recommendation flow —
        # the rule-based draft is always a valid answer on its own.
        return fallback_text
