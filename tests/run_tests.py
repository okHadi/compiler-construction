#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAMS = ROOT / "tests" / "programs"
EXPECTED = ROOT / "tests" / "expected"


def run_compiler(source: Path, phase: str = "tac"):
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), str(source), "--phase", phase],
        capture_output=True, text=True, cwd=ROOT,
    )
    return result.returncode, result.stdout, result.stderr


def diff(actual: str, expected: str) -> str:
    a_lines = actual.splitlines()
    e_lines = expected.splitlines()
    out = []
    for i in range(max(len(a_lines), len(e_lines))):
        a = a_lines[i] if i < len(a_lines) else "<missing>"
        e = e_lines[i] if i < len(e_lines) else "<missing>"
        if a != e:
            out.append(f"  line {i+1}: expected {e!r} got {a!r}")
    return "\n".join(out)


def main():
    passed = 0
    failed = 0

    for src in sorted(PROGRAMS.glob("*.c")):
        name = src.stem
        if name == "errors_semantic":
            code, _, _ = run_compiler(src, "semantic")
            if code != 0:
                print(f"PASS  {name} (semantic errors detected as expected)")
                passed += 1
            else:
                print(f"FAIL  {name} (expected semantic errors but got none)")
                failed += 1
            continue

        expected_path = EXPECTED / f"{name}.tac"
        if not expected_path.exists():
            print(f"SKIP  {name} (no golden file)")
            continue

        code, stdout, stderr = run_compiler(src, "tac")
        if code != 0:
            print(f"FAIL  {name} (compiler exited {code})")
            print(stderr)
            failed += 1
            continue
        expected = expected_path.read_text()
        if stdout == expected:
            print(f"PASS  {name}")
            passed += 1
        else:
            print(f"FAIL  {name}")
            print(diff(stdout, expected))
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
