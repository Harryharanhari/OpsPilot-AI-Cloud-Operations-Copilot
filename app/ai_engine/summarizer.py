import logging
from ..config import settings

logger = logging.getLogger(__name__)

# Safe top-level import
try:
    from transformers import pipeline as hf_pipeline
    _TRANSFORMERS_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"transformers unavailable: {e}. Using truncation-based summarization.")
    _TRANSFORMERS_AVAILABLE = False


def _truncate_summarize(text: str, max_chars: int = 200) -> str:
    """Simple fallback: return first N chars with ellipsis."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    # Try to cut at a sentence boundary
    cut = text[:max_chars]
    last_dot = cut.rfind(". ")
    return (cut[:last_dot + 1] if last_dot > 50 else cut) + "..."


class LogSummarizer:
    def __init__(self):
        self.summarizer = None
        self.enabled = False

        if _TRANSFORMERS_AVAILABLE:
            try:
                self.summarizer = hf_pipeline("summarization", model=settings.SUMMARIZER_MODEL)
                self.enabled = True
                logger.info("✅ LogSummarizer (BART) loaded.")
            except Exception as e:
                logger.warning(f"Could not load summarizer model: {e}. Using truncation fallback.")

    def summarize(self, text: str) -> str:
        if not self.enabled or not self.summarizer or not text:
            return _truncate_summarize(text)

        try:
            result = self.summarizer(text[:1024], max_length=130, min_length=30, do_sample=False)
            return result[0]["summary_text"]
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return _truncate_summarize(text)


summarizer = LogSummarizer()
