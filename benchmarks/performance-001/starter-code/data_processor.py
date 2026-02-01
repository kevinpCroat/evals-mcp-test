"""
Data Processor - Finds duplicate entries and generates statistics

This module processes log data to find duplicate user sessions and
compute session statistics. It's used for analyzing user behavior patterns.
Optimized: parse each log line once, use dict for grouping, sorted() for top users.
"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple

# Precompile regexes for reuse
_USER_RE = re.compile(r'user_id=(\w+)')
_DURATION_RE = re.compile(r'duration=(\d+)')


class LogProcessor:
    """Processes log entries to find duplicates and compute statistics."""

    def __init__(self):
        self.logs = []
        # Parsed once: list of (user_id, duration, line_idx) for lines with user_id
        self._parsed: List[Tuple[str, int, int]] = []

    def load_logs(self, log_entries: List[str]) -> None:
        """Load log entries for processing. Parses each line once and caches."""
        self.logs = log_entries
        self._parsed = []
        for line_idx, log in enumerate(self.logs):
            user_match = _USER_RE.search(log)
            duration_match = _DURATION_RE.search(log)
            user_id = user_match.group(1) if user_match else None
            duration = int(duration_match.group(1)) if duration_match else 0
            if user_id is not None:
                self._parsed.append((user_id, duration, line_idx))

    def find_duplicate_sessions(self) -> List[Tuple[str, List[int]]]:
        """
        Find all duplicate user sessions in the logs.

        Returns:
            List of tuples (user_id, [line_numbers]) for users with duplicate sessions
        """
        # Group original line indices by user_id (one pass over parsed data)
        user_to_lines: Dict[str, List[int]] = defaultdict(list)
        for user_id, _, line_idx in self._parsed:
            user_to_lines[user_id].append(line_idx)

        duplicates = [(uid, line_nums) for uid, line_nums in user_to_lines.items() if len(line_nums) > 1]
        return duplicates

    def compute_session_stats(self) -> Dict[str, int]:
        """
        Compute session duration statistics for each user.

        Returns:
            Dictionary mapping user_id to total session time in seconds
        """
        stats: Dict[str, int] = defaultdict(int)
        for user_id, duration, _ in self._parsed:
            stats[user_id] += duration
        return dict(stats)

    def get_top_users(self, stats: Dict[str, int], n: int = 10) -> List[Tuple[str, int]]:
        """
        Get top N users by session time.

        Args:
            stats: Dictionary of user_id -> total_time
            n: Number of top users to return

        Returns:
            List of (user_id, total_time) tuples, sorted by time descending
        """
        items = list(stats.items())
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:n]

    def process_all(self) -> Dict:
        """
        Run full analysis pipeline.

        Returns:
            Dictionary with duplicates and top users
        """
        duplicates = self.find_duplicate_sessions()
        stats = self.compute_session_stats()
        top_users = self.get_top_users(stats)

        return {
            'duplicates': duplicates,
            'stats': stats,
            'top_users': top_users
        }


def generate_test_logs(num_users: int = 1000, entries_per_user: int = 5) -> List[str]:
    """Generate test log data."""
    logs = []
    for user_num in range(num_users):
        user_id = f"user{user_num:04d}"
        for entry_num in range(entries_per_user):
            duration = (user_num + entry_num) % 100 + 10
            logs.append(
                f"[2024-01-{(entry_num % 28) + 1:02d}] session_start user_id={user_id} duration={duration}s status=active"
            )
    return logs


if __name__ == "__main__":
    # Demo usage
    processor = LogProcessor()
    logs = generate_test_logs(num_users=500, entries_per_user=3)
    processor.load_logs(logs)

    print("Processing logs...")
    import time
    start = time.time()
    result = processor.process_all()
    elapsed = time.time() - start

    print(f"\nProcessed {len(logs)} log entries in {elapsed:.2f} seconds")
    print(f"Found {len(result['duplicates'])} users with duplicate sessions")
    print(f"\nTop 5 users by session time:")
    for user_id, total_time in result['top_users'][:5]:
        print(f"  {user_id}: {total_time}s")
