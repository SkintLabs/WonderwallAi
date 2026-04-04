"""
MeatHead — AI Content Generation Engine
Generates humanized marketing content using Groq/Llama 3.3.
Includes a "First-Time-Right" validation pipeline that rejects AI fingerprints
and forces self-correction before the output ever reaches the dashboard.
"""

import re
import logging
from typing import Optional

from groq import AsyncGroq

from server.utils.humanizer import apply_human_entropy

logger = logging.getLogger("meathead.ai")

# Terms that scream "AI wrote this"
BANNED_TERMS = [
    "delve", "seamless", "robust", "game-changer", "pain point",
    "edge case", "empower", "leverage", "moreover", "furthermore",
    "revolutionize", "cutting-edge", "paradigm", "synergy", "holistic",
    "streamline", "innovative", "next-generation", "best-in-class",
]

# Structural patterns that AIs love but humans don't use
BANNED_PATTERNS = [
    r"\u2014",             # Em-dash
    r"--",                 # Double hyphen (em-dash substitute)
    r"^\d+\.\s+",         # Numbered lists (e.g., "1. ")
    r"In conclusion",
    r"Hope this helps",
    r"Here's why",
    r"Let me explain",
    r"Great question",
]


class MeatHeadEngine:
    """
    Content generation engine with strict anti-AI validation.
    Generates → validates → retries if needed → humanizes.
    """

    def __init__(self):
        from server.config import get_settings
        settings = get_settings()
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.configured = bool(self.api_key)

        if self.configured:
            self.client = AsyncGroq(api_key=self.api_key)
            logger.info("MeatHeadEngine initialized (Groq connected)")
        else:
            self.client = None
            logger.warning("MeatHeadEngine: GROQ_API_KEY not set")

    def _build_system_prompt(self, platform: str, mention_count: int = 0) -> str:
        """Build platform-specific system prompt with anti-AI constraints."""
        base = (
            "You are a pragmatic, technical developer from Australia/UK. You speak in clean, natural English. "
            "You have zero tolerance for corporate jargon, fluff, or standard AI formatting.\n\n"
            "CORE OBJECTIVE: Help the user solve their problem. Mention WonderwallAi (for LLM security, <2ms latency) "
            "or Jerry (Shopify customer service bot) ONLY if it naturally solves their specific issue.\n\n"
            "STRICT CONSTRAINTS:\n"
            "- Use ONLY standard keyboard characters. Do not use em-dashes. Use commas or full stops instead.\n"
            "- Do not use bullet points or numbered lists. Write in natural paragraphs.\n"
            "- Do not summarise your own points at the end.\n"
            "- Never sound confident. Use phrases like 'I'm pretty sure', 'from memory', or 'correct me if I'm wrong'.\n"
            "- Keep responses concise, under 200 words unless the topic genuinely demands more.\n"
            "- Do not start with 'I' as the first word.\n"
        )

        if platform == "reddit":
            base += (
                "\nREDDIT RULES:\n"
                "- Write like a real Redditor. No marketing speak.\n"
                "- Match the subreddit's culture and technical level.\n"
                "- If recommending a tool, frame it as personal experience, not a pitch.\n"
                "- Use casual language. Contractions are good.\n"
            )
        elif platform == "facebook":
            base += (
                "\nFACEBOOK RULES:\n"
                "- Write an engaging, shareable post.\n"
                "- Can be slightly more polished than Reddit but still authentic.\n"
                "- Include a soft call-to-action if relevant.\n"
                "- Keep it under 300 words.\n"
            )
        elif platform == "email":
            base += (
                "\nEMAIL RULES:\n"
                "- Write a professional but personal cold email.\n"
                "- Clear value proposition in the first sentence.\n"
                "- Keep it short, 3-4 sentences max for the body.\n"
                "- End with a specific, low-commitment ask.\n"
            )

        if mention_count > 2:
            base += (
                "\nCRITICAL: You have mentioned Skint Labs products recently. "
                "Acknowledge this naturally. Example: 'I know I keep banging on about this, "
                "but WonderwallAi genuinely stopped the breaches we were seeing...'\n"
            )

        return base

    def _validate_output(self, text: str) -> tuple[bool, str]:
        """Check text for AI fingerprints. Returns (is_valid, reason_if_invalid)."""
        for term in BANNED_TERMS:
            if term.lower() in text.lower():
                return False, f"Used banned corporate term: '{term}'"

        for pattern in BANNED_PATTERNS:
            if re.search(pattern, text, re.MULTILINE):
                return False, f"Used banned structural pattern: {pattern}"

        return True, ""

    async def generate_reply(
        self,
        platform: str,
        context: str,
        mention_count: int = 0,
        max_retries: int = 2,
    ) -> str:
        """
        Generate a humanized reply for a specific platform.
        Validates output, retries with feedback if AI fingerprints detected.
        """
        if not self.configured or not self.client:
            raise RuntimeError("MeatHeadEngine not configured (missing GROQ_API_KEY)")

        messages = [
            {"role": "system", "content": self._build_system_prompt(platform, mention_count)},
            {"role": "user", "content": f"Context/Original Post:\n{context}\n\nDraft a reply."},
        ]

        draft = ""
        for attempt in range(max_retries + 1):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=400,
            )

            draft = response.choices[0].message.content.strip()

            is_valid, reason = self._validate_output(draft)
            if is_valid:
                return apply_human_entropy(draft)

            logger.warning(f"MeatHead validation failed (attempt {attempt + 1}): {reason}")
            # Feed the failure back so Groq corrects itself
            messages.append({"role": "assistant", "content": draft})
            messages.append({
                "role": "user",
                "content": (
                    f"Validation failed: {reason}. "
                    "Rewrite the response, explicitly avoiding that error. "
                    "Do not apologize, just provide the fixed text."
                ),
            })

        # Last resort: strip obvious markers manually
        logger.error("MeatHead failed all validation retries. Applying forced manual override.")
        draft = draft.replace("\u2014", ",").replace("--", ",")
        return apply_human_entropy(draft)

    async def generate_content(
        self,
        platform: str,
        product: str,
        topic: str,
        tone: str = "casual",
    ) -> dict:
        """
        Generate platform-specific marketing content.
        Returns {title, body, raw_body} where body has humanizer applied.
        """
        context = f"Product: {product}\nTopic: {topic}\nTone: {tone}"

        if platform == "email":
            context += "\n\nGenerate a subject line on the first line, then the email body."

        raw_body = await self.generate_reply(platform, context)
        # raw_body already has humanizer applied from generate_reply

        title = None
        body = raw_body
        if platform == "email" and "\n" in raw_body:
            lines = raw_body.split("\n", 1)
            title = lines[0].strip().lstrip("Subject:").strip()
            body = lines[1].strip() if len(lines) > 1 else raw_body

        return {"title": title, "body": body, "raw_body": raw_body}

    async def improve_draft(self, text: str, instruction: str) -> str:
        """Apply a specific editing instruction to existing text."""
        if not self.configured or not self.client:
            raise RuntimeError("MeatHeadEngine not configured")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a pragmatic editor. Apply the user's instruction to the text exactly. "
                    "Do not use em-dashes. Do not add bullet points or numbered lists. "
                    "Return only the improved text, nothing else."
                ),
            },
            {"role": "user", "content": f"Text:\n{text}\n\nInstruction: {instruction}"},
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.5,
            max_tokens=400,
        )

        improved = response.choices[0].message.content.strip()
        improved = improved.replace("\u2014", ",").replace("--", ",")
        return apply_human_entropy(improved)

    # --- Legacy method for GiLLBoT email sequences (backward compat) ---

    async def personalize_message(
        self,
        template: str,
        lead_context: dict,
        campaign_context: str,
        subject_template: Optional[str] = None,
    ) -> dict[str, str]:
        """Personalize a message template for a specific lead."""
        if not self.configured:
            return {"subject": subject_template or "", "body": template}

        context = (
            f"Campaign context: {campaign_context}\n"
            f"Lead info: {lead_context}\n"
            f"Template to personalize:\n{template}"
        )
        result = await self.generate_reply("email", context)
        return {"subject": subject_template or "", "body": result}
