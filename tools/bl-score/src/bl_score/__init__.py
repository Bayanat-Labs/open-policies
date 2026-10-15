"""bl-score: Bayanat Labs open-programme scoring CLI.

Scores a stage-0 scoping memo (YAML) against the selection rubric in
policy/rubric.yaml of Bayanat-Labs/open-policies: weighted score, legal gate
verdict, release-tier cap and suggested priority.
"""
from .scoring import (CRITERIA, EFFORTS, MemoError, Rubric, RubricError, check_weights, load_rubric,
                      memo_schema, output_schema, rank, score_memo, suggest_priority, validate_memo,
                      weighted_score)

__version__ = "0.1.0"
__all__ = ["CRITERIA", "EFFORTS", "MemoError", "Rubric", "RubricError", "check_weights", "load_rubric",
           "memo_schema", "output_schema", "rank", "score_memo", "suggest_priority", "validate_memo",
           "weighted_score", "__version__"]
