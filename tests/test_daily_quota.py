import unittest

from langchain_core.exceptions import ModelRateLimitError
from model_limits import retryable_model_error


class DailyQuotaTests(unittest.TestCase):
    def test_day_exhaustion_is_not_a_transient_retry(self):
        for detail in ("GenerateRequestsPerDayPerProjectPerModel-FreeTier", "free-models-per-day", "Daily quota exceeded"):
            with self.subTest(detail=detail):
                self.assertFalse(retryable_model_error(ModelRateLimitError(detail)))

    def test_minute_windows_remain_retryable(self):
        self.assertTrue(retryable_model_error(ModelRateLimitError("GenerateContentInputTokensPerMinute")))
