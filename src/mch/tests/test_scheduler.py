import pytest
from mch.utils.scheduler import determine_bucket, make_task_key

class TestSchedulerLogic:
    
    # --- Happy Path ---
    def test_bucket_classification_standard(self):
        assert determine_bucket(50) == "small"
        assert determine_bucket(200) == "mid"
        assert determine_bucket(1000) == "large"

    def test_task_key_generation(self):
        assert make_task_key("S", 1) == "S_001"
        assert make_task_key("M", 99) == "M_099"

    # --- Edge Cases ---
    def test_bucket_boundaries(self):
        assert determine_bucket(79) == "small"
        assert determine_bucket(80) == "mid"
        assert determine_bucket(499) == "mid"
        assert determine_bucket(500) == "large"

    # --- Robustness / Sad Cases ---
    def test_bucket_robustness(self):
        assert determine_bucket(None) == "small"
        assert determine_bucket(0) == "small"
        assert determine_bucket(-100) == "small"
        assert determine_bucket("invalid_string") == "small"