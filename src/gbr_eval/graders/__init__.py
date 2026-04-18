"""Grader registry and base interface."""

from gbr_eval.graders.base import GraderResult, grade, register_grader, get_grader

__all__ = ["GraderResult", "grade", "register_grader", "get_grader"]
