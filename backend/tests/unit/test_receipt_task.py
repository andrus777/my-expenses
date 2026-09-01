from app.receipts.tasks import process_receipt_job, retry_countdown


def test_receipt_task_has_bounded_exponential_backoff():
    assert process_receipt_job.max_retries == 3
    assert [retry_countdown(attempt) for attempt in range(3)] == [2, 4, 8]
