#!/usr/bin/env python3
"""Run every Light skill script self-test.

This is the execution gate paired with check_skill_assets.py:
- check_skill_assets.py verifies the manifest / __main__ / explicit --selftest marker;
- this runner actually executes ``python <script> --selftest`` for every script.

The runner is intentionally pure stdlib. Third-party dependencies belong in the
CI workflow, because the scripts under test span scientific plotting, documents,
PDF/XLSX/DOCX handling, and text utilities.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import time
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"

DOCUMENT_IMPORTS = {
    "docx",
    "fitz",
    "openpyxl",
    "pdfplumber",
    "PIL",
    "pptx",
    "pypdf",
    "PyPDF2",
    "reportlab",
}
SCIENCE_IMPORTS = {
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "sklearn",
    "statsmodels",
}


@dataclass(frozen=True)
class ScriptCase:
    path: pathlib.Path
    group: str

    @property
    def rel(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def classify(path: pathlib.Path) -> str:
    """Assign a coarse dependency layer for targeted local runs.

    Priority is documents > science > stdlib because document scripts often also
    import pandas/numpy for profiling; grouping should tell the operator which
    dependency bundle is needed.
    """
    text = read_text(path)
    if any(f"import {name}" in text or f"from {name}" in text for name in DOCUMENT_IMPORTS):
        return "documents"
    if any(f"import {name}" in text or f"from {name}" in text for name in SCIENCE_IMPORTS):
        return "science"
    return "stdlib"


def discover(group: str) -> list[ScriptCase]:
    cases = [ScriptCase(path=p, group=classify(p)) for p in sorted(SKILLS_DIR.glob("light-*/scripts/*.py"))]
    if group != "all":
        cases = [case for case in cases if case.group == group]
    return cases


def tail(text: str, max_lines: int = 20, max_chars: int = 4000) -> str:
    lines = text.splitlines()[-max_lines:]
    out = "\n".join(lines)
    if len(out) > max_chars:
        out = out[-max_chars:]
    return out


def run_case(case: ScriptCase, timeout: int, verbose: bool) -> tuple[bool, float, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("MPLBACKEND", "Agg")
    env.setdefault("LIGHT_SELFTEST_CI", "1")

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(case.path), "--selftest"],
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - start
        captured = (exc.stdout or "") + "\n" + (exc.stderr or "")
        detail = f"TIMEOUT after {timeout}s\n{tail(captured)}"
        return False, elapsed, detail

    elapsed = time.perf_counter() - start
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0:
        if verbose:
            return True, elapsed, tail(output, max_lines=8, max_chars=1200)
        last = ""
        for line in reversed(output.splitlines()):
            if line.strip():
                last = line.strip()
                break
        return True, elapsed, last
    return False, elapsed, f"exit={proc.returncode}\n{tail(output, max_lines=80, max_chars=12000)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Light skill script --selftest commands")
    parser.add_argument("--group", choices=["all", "stdlib", "science", "documents"], default="all")
    parser.add_argument("--timeout", type=int, default=120, help="seconds per script")
    parser.add_argument("--verbose", action="store_true", help="print short output tails for passing tests")
    parser.add_argument("--list", action="store_true", help="list selected scripts without running them")
    parser.add_argument("--fail-fast", action="store_true", help="stop after the first failure")
    args = parser.parse_args(argv)

    cases = discover(args.group)
    if not cases:
        print(f"no scripts selected for group={args.group}")
        return 1

    counts: dict[str, int] = {"stdlib": 0, "science": 0, "documents": 0}
    for case in cases:
        counts[case.group] += 1

    print(
        "skill selftest selection: "
        f"group={args.group}, total={len(cases)}, "
        f"stdlib={counts['stdlib']}, science={counts['science']}, documents={counts['documents']}"
    )

    if args.list:
        for case in cases:
            print(f"[{case.group}] {case.rel}")
        return 0

    failures: list[tuple[ScriptCase, str, float]] = []
    timings: list[tuple[float, ScriptCase]] = []

    for idx, case in enumerate(cases, 1):
        print(f"[{idx:02d}/{len(cases):02d}] {case.group:<9} {case.rel} ... ", end="", flush=True)
        ok, elapsed, detail = run_case(case, timeout=args.timeout, verbose=args.verbose)
        timings.append((elapsed, case))
        if ok:
            print(f"OK {elapsed:.2f}s" + (f" :: {detail}" if detail else ""))
            continue
        print(f"FAIL {elapsed:.2f}s")
        failures.append((case, detail, elapsed))
        print(f"--- failure detail: {case.rel} ---")
        print(detail)
        print("--- end failure detail ---")
        if args.fail_fast:
            break

    total_time = sum(sec for sec, _ in timings)
    print("\nslowest selftests:")
    for sec, case in sorted(timings, key=lambda item: item[0], reverse=True)[:8]:
        print(f"  {sec:6.2f}s  [{case.group}] {case.rel}")
    print(f"\nsummary: passed={len(timings) - len(failures)} failed={len(failures)} total={len(cases)} time={total_time:.2f}s")

    if failures:
        print("\nfailed scripts:")
        for case, _, elapsed in failures:
            print(f"  ✗ {case.rel} ({elapsed:.2f}s)")
        return 1
    print("✓ all selected skill script selftests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
