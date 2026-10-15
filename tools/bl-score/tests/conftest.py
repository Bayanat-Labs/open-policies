import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXAMPLES = os.path.join(ROOT, "examples")


@pytest.fixture
def base_memo():
    return {
        "candidate_id": "T-001",
        "title": "Bayanat Labs test candidate",
        "scores": {"impact": 3, "claim_strength": 3, "ease": 3, "legal_cleanliness": 3, "commercial_pull": 3},
        "legal_tier": "green",
        "effort": "M",
    }
