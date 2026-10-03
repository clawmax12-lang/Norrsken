"""FR-06: deterministic, source-grounded reasons and next-time suggestions."""

from .rule_based import RuleBasedExplainer
from .suggestions import next_time_suggestions
from .wording import format_timestamp

__all__ = ["RuleBasedExplainer", "format_timestamp", "next_time_suggestions"]
