import logging
from ..config import settings

logger = logging.getLogger(__name__)

# Safe top-level import — transformers may not be installed or compatible
try:
    from transformers import pipeline as hf_pipeline
    _TRANSFORMERS_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"transformers unavailable: {e}. Using rule-based classifier.")
    _TRANSFORMERS_AVAILABLE = False

# Keyword-based fallback rules
_ERROR_KEYWORDS = {"error", "exception", "fail", "fatal", "critical", "crash", "panic"}
_WARN_KEYWORDS  = {"warn", "timeout", "retry", "slow", "deprecated", "unavailable"}

def _rule_based_classify(message: str) -> dict:
    lower = message.lower()
    if any(k in lower for k in _ERROR_KEYWORDS):
        return {"label": "ERROR", "score": 0.9}
    if any(k in lower for k in _WARN_KEYWORDS):
        return {"label": "WARNING", "score": 0.8}
    return {"label": "INFO", "score": 0.7}


class LogClassifier:
    def __init__(self):
        self.classifier = None
        self.enabled = False

        if _TRANSFORMERS_AVAILABLE:
            try:
                self.classifier = hf_pipeline("text-classification", model=settings.CLASSIFIER_MODEL)
                self.enabled = True
                logger.info("✅ LogClassifier (transformer) loaded.")
            except Exception as e:
                logger.warning(f"Could not load classifier model: {e}. Using rule-based fallback.")

    def classify(self, message: str) -> dict:
        if not self.enabled or not self.classifier:
            return _rule_based_classify(message)

        try:
            result = self.classifier(message[:512])[0]
            label, score = result["label"], result["score"]
            if label in ("negative", "LABEL_0"):
                return {"label": "ERROR", "score": score}
            elif label in ("neutral", "LABEL_1"):
                return {"label": "WARNING", "score": score}
            else:
                return {"label": "INFO", "score": score}
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return _rule_based_classify(message)


classifier = LogClassifier()
