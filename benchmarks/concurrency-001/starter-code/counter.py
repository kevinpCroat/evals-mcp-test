"""
Thread-safe counter using threading.Lock.

Uses a lock so increment and read operations are atomic.
"""

import threading
import time


class MetricsCounter:
    """A metrics counter, thread-safe via Lock."""

    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_processing_time = 0.0
        self.request_count = 0
        self._lock = threading.Lock()

    def record_request(self, success: bool, processing_time: float) -> None:
        """Record a request with its outcome and processing time."""
        with self._lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            self.total_processing_time += processing_time
            self.request_count += 1

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        with self._lock:
            if self.total_requests == 0:
                return 0.0
            return self.successful_requests / self.total_requests

    def get_average_processing_time(self) -> float:
        """Calculate average processing time."""
        with self._lock:
            if self.request_count == 0:
                return 0.0
            return self.total_processing_time / self.request_count

    def get_stats(self) -> dict:
        """Get all statistics."""
        with self._lock:
            sr = self.successful_requests / self.total_requests if self.total_requests else 0.0
            avg = self.total_processing_time / self.request_count if self.request_count else 0.0
            return {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': sr,
                'avg_processing_time': avg
            }

    def increment_simple(self) -> None:
        """Simple increment operation, atomic under lock."""
        with self._lock:
            current = self.total_requests
            time.sleep(0.0001)
            self.total_requests = current + 1

    def reset(self) -> None:
        """Reset all counters."""
        with self._lock:
            self.total_requests = 0
            self.successful_requests = 0
            self.failed_requests = 0
            self.total_processing_time = 0.0
            self.request_count = 0
