"""Real-time agent nudge engine with cooldown, deduplication, and suppression policies."""

from q4_realtime.nudges.engine import NudgeEngine, get_nudge_engine

__all__ = ["NudgeEngine", "get_nudge_engine"]
