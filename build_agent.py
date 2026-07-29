from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class ActionResult:
    name: str
    success: bool
    output: str


class BuildAgent:
    def __init__(self, workspace: str = ".", max_steps: int = 10) -> None:
        self.workspace = Path(workspace).resolve()
        self.max_steps = max_steps
        self._tools: Dict[str, Callable[..., ActionResult]] = {
            "scan_directory": self.scan_directory,
            "read_file": self.read_file,
            "overwrite_file": self.overwrite_file,
            "run_python_file": self.run_python_file,
        }

    def scan_directory(self, path: Optional[str] = None) -> ActionResult:
        target = Path(path).resolve() if path else self.workspace
        if not target.exists() or not target.is_dir():
            return ActionResult("scan_directory", False, f"Directory not found: {target}")

        files = sorted(str(p.relative_to(target)) for p in target.rglob("*") if p.is_file())
        return ActionResult("scan_directory", True, "\n".join(files) if files else "<empty>")

    def read_file(self, path: str) -> ActionResult:
        target = Path(path).resolve()
        if not target.exists() or not target.is_file():
            return ActionResult("read_file", False, f"File not found: {target}")

        return ActionResult("read_file", True, target.read_text(encoding="utf-8"))

    def overwrite_file(self, path: str, content: str) -> ActionResult:
        target = Path(path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ActionResult("overwrite_file", True, f"Wrote {len(content)} bytes to {target}")

    def run_python_file(self, path: str) -> ActionResult:
        target = Path(path).resolve()
        if not target.exists() or not target.is_file():
            return ActionResult("run_python_file", False, f"File not found: {target}")

        proc = subprocess.run(
            [sys.executable, str(target)],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
            check=False,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            return ActionResult("run_python_file", False, output.strip() or f"Exit code {proc.returncode}")

        return ActionResult("run_python_file", True, output.strip() or "<no output>")

    def run_task(self, task: str) -> List[ActionResult]:
        actions = self._plan_actions(task)
        if not actions:
            return [
                ActionResult(
                    name="planner",
                    success=False,
                    output="No matching predefined action found in task.",
                )
            ]

        results: List[ActionResult] = []
        for step, action in enumerate(actions, start=1):
            if step > self.max_steps:
                results.append(ActionResult("planner", False, "Max steps reached before completion."))
                break

            tool = self._tools[action["name"]]
            result = tool(*action["args"])
            results.append(result)
            if not result.success:
                break

        return results

    def _plan_actions(self, task: str) -> List[dict]:
        lowered = task.lower()
        paths = self._extract_paths(task)
        actions: List[dict] = []

        if any(token in lowered for token in ("scan", "list files", "directory", "files in")):
            actions.append({"name": "scan_directory", "args": (str(self.workspace),)})

        if any(token in lowered for token in ("read", "contents", "show file")):
            if paths:
                actions.append({"name": "read_file", "args": (paths[0],)})

        if any(token in lowered for token in ("overwrite", "write", "replace")):
            if paths:
                content = self._extract_content(task)
                actions.append({"name": "overwrite_file", "args": (paths[0], content)})

        if any(token in lowered for token in ("run", "execute", "python")):
            run_path = self._pick_python_path(paths)
            if run_path:
                actions.append({"name": "run_python_file", "args": (run_path,)})

        return actions

    @staticmethod
    def _extract_paths(task: str) -> List[str]:
        quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', task)
        extracted = [a or b for a, b in quoted if (a or b)]
        for token in task.split():
            cleaned = token.strip(",.;()")
            if os.path.sep in cleaned or cleaned.endswith((".py", ".txt", ".md", ".json", ".yaml", ".yml")):
                extracted.append(cleaned)
        deduped = []
        for item in extracted:
            if item not in deduped:
                deduped.append(item)
        return deduped

    @staticmethod
    def _extract_content(task: str) -> str:
        match = re.search(r"(?:with|content:)(.+)$", task, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _pick_python_path(paths: List[str]) -> Optional[str]:
        for path in paths:
            if path.endswith(".py"):
                return path
        return paths[0] if paths else None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a coding task with predefined CLI agent tools.")
    parser.add_argument("task", help="Task description for the agent")
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument("--max-steps", type=int, default=10, help="Maximum actions to execute")
    args = parser.parse_args(argv)

    agent = BuildAgent(workspace=args.workspace, max_steps=args.max_steps)
    results = agent.run_task(args.task)

    for idx, result in enumerate(results, start=1):
        status = "OK" if result.success else "FAIL"
        print(f"[{idx}] {result.name}: {status}")
        if result.output:
            print(result.output)

    return 0 if results and all(result.success for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
