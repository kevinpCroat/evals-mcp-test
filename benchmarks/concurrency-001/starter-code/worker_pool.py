"""
Thread-safe worker pool using queue.Queue and threading.Lock.

Uses queue.Queue for task queue and Lock for results/state so submit/task handling are thread-safe.
"""

import queue
import threading
from typing import Callable, Any, List
from enum import Enum


class WorkerState(Enum):
    IDLE = "idle"
    BUSY = "busy"
    STOPPED = "stopped"


class WorkerPool:
    """A simple worker pool, thread-safe via Queue and Lock."""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.task_queue = queue.Queue()
        self.results = []
        self._results_lock = threading.Lock()
        self.worker_states = [WorkerState.IDLE] * num_workers
        self._states_lock = threading.Lock()
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.active_workers = 0

    def submit_task(self, task: Callable[[], Any]) -> None:
        """Submit a task to the pool."""
        self.task_queue.put(task)

    def get_next_task(self, worker_id: int) -> Callable[[], Any]:
        """Get next task from queue. Returns None if no task available (non-blocking)."""
        try:
            task = self.task_queue.get_nowait()
        except queue.Empty:
            return None
        with self._states_lock:
            self.worker_states[worker_id] = WorkerState.BUSY
            self.active_workers += 1
        return task

    def execute_task(self, worker_id: int, task: Callable[[], Any]) -> None:
        """Execute a task and store result."""
        try:
            result = task()
            with self._results_lock:
                self.results.append(result)
                self.completed_tasks += 1
        except Exception as e:
            with self._results_lock:
                self.failed_tasks += 1
                self.results.append(f"Error: {e}")
        finally:
            with self._states_lock:
                self.worker_states[worker_id] = WorkerState.IDLE
                self.active_workers -= 1

    def get_pending_count(self) -> int:
        """Get number of pending tasks."""
        return self.task_queue.qsize()

    def get_results(self) -> List[Any]:
        """Get all results (copy of list)."""
        with self._results_lock:
            return list(self.results)

    def get_stats(self) -> dict:
        """Get pool statistics."""
        with self._states_lock:
            with self._results_lock:
                idle = sum(1 for s in self.worker_states if s == WorkerState.IDLE)
                return {
                    'pending_tasks': self.task_queue.qsize(),
                    'completed_tasks': self.completed_tasks,
                    'failed_tasks': self.failed_tasks,
                    'active_workers': self.active_workers,
                    'idle_workers': idle
                }

    def reset(self) -> None:
        """Reset the pool."""
        with self._states_lock:
            with self._results_lock:
                while True:
                    try:
                        self.task_queue.get_nowait()
                    except queue.Empty:
                        break
                self.results = []
                self.worker_states = [WorkerState.IDLE] * self.num_workers
                self.completed_tasks = 0
                self.failed_tasks = 0
                self.active_workers = 0
