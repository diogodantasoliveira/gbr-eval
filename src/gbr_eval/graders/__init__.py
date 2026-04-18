"""Grader registry and base interface."""

from gbr_eval.graders.base import GraderResult, get_grader, grade, register_grader

__all__ = ["GraderResult", "grade", "register_grader", "get_grader"]
