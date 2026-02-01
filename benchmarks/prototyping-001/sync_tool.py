#!/usr/bin/env python3
"""Proof-of-concept CLI: watch a directory and sync changes to a simulated cloud (local backup dir)."""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Install watchdog: pip install watchdog", file=sys.stderr)
    sys.exit(1)


class CloudSyncHandler(FileSystemEventHandler):
    """Handle file events and 'sync' to cloud (local backup directory)."""

    def __init__(self, watch_dir: str, cloud_dir: str):
        self.watch_dir = Path(watch_dir)
        self.cloud_dir = Path(cloud_dir)
        self.cloud_dir.mkdir(parents=True, exist_ok=True)

    def _rel_path(self, src: Path) -> Path:
        return src.relative_to(self.watch_dir)

    def _cloud_path(self, rel: Path) -> Path:
        return self.cloud_dir / rel

    def on_created(self, event):
        if event.is_directory:
            return
        src = Path(event.src_path)
        rel = self._rel_path(src)
        dst = self._cloud_path(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
            print(f"[created] {rel} -> synced to cloud")
        except Exception as e:
            print(f"[created] {rel} -> sync failed: {e}")

    def on_modified(self, event):
        if event.is_directory:
            return
        src = Path(event.src_path)
        rel = self._rel_path(src)
        dst = self._cloud_path(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
            print(f"[modified] {rel} -> synced to cloud")
        except Exception as e:
            print(f"[modified] {rel} -> sync failed: {e}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        src = Path(event.src_path)
        rel = self._rel_path(src)
        dst = self._cloud_path(rel)
        try:
            if dst.exists():
                dst.unlink()
                print(f"[deleted] {rel} -> removed from cloud")
        except Exception as e:
            print(f"[deleted] {rel} -> cloud remove failed: {e}")


def cmd_watch(watch_path: str, cloud_path: str) -> None:
    """Start watching directory and syncing to cloud."""
    watch_dir = Path(watch_path).resolve()
    if not watch_dir.is_dir():
        print(f"Error: not a directory: {watch_path}", file=sys.stderr)
        sys.exit(1)
    cloud_dir = Path(cloud_path or str(watch_dir) + "_cloud").resolve()
    print(f"Watching: {watch_dir}")
    print(f"Cloud (backup): {cloud_dir}")
    print("Press Ctrl+C to stop.")
    handler = CloudSyncHandler(str(watch_dir), str(cloud_dir))
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Stopped.")


def cmd_status(cloud_path: str) -> None:
    """Show current cloud backup status."""
    cloud_dir = Path(cloud_path or ".").resolve()
    if not cloud_dir.is_dir():
        print("No cloud backup directory found.", file=sys.stderr)
        sys.exit(1)
    count = sum(1 for _ in cloud_dir.rglob("*") if _.is_file())
    print(f"Cloud backup: {cloud_dir}")
    print(f"Files synced: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch directory and sync to cloud (POC)")
    sub = parser.add_subparsers(dest="command", help="command")
    watch_p = sub.add_parser("watch", help="Watch a directory and sync to cloud")
    watch_p.add_argument("directory", help="Directory to watch")
    watch_p.add_argument("--cloud", default="", help="Cloud backup directory (default: <dir>_cloud)")
    status_p = sub.add_parser("status", help="Show sync status")
    status_p.add_argument("--cloud", default="", help="Cloud backup directory")
    args = parser.parse_args()
    if args.command == "watch":
        cmd_watch(args.directory, getattr(args, "cloud", ""))
    elif args.command == "status":
        cmd_status(getattr(args, "cloud", ""))
    else:
        parser.print_help()
        sys.exit(0 if not sys.argv[1:] else 1)


if __name__ == "__main__":
    main()
