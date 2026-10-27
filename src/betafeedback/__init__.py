"""beta-feedback-collector-cli: normalize, cluster, and report on beta-reader feedback.

Copyright (c) 2026 Asdale Dynamics, LLC. MIT licensed.
"""

from .models import FeedbackItem
from .normalize import collect_items, load_sheet
from .classify import classify
from .cluster import cluster_items
from .contradictions import find_contradictions
from .report import chapter_report
from .readers import readers_summary
from .backlog import build_backlog, write_backlog_csv, write_backlog_md

__version__ = "0.1.0"

__all__ = [
    "FeedbackItem",
    "collect_items",
    "load_sheet",
    "classify",
    "cluster_items",
    "find_contradictions",
    "chapter_report",
    "readers_summary",
    "build_backlog",
    "write_backlog_csv",
    "write_backlog_md",
    "__version__",
]
