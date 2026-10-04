"""Opt-in generative-motion track. Fail closed to Showcase; never writes CompositionSpec."""

from .pipeline import MotionPipeline
from .scene import LayerKind, MotionLayer, MotionSpec

__all__ = ["LayerKind", "MotionLayer", "MotionPipeline", "MotionSpec"]
