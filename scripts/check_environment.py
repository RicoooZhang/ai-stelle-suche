#!/usr/bin/env python3
"""Check local tools without installing or modifying them."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = {
    "git": (["git", "--version"], True), "python": ([sys.executable, "--version"], True),
    "pip": (["pip", "--version"], False), "node": (["node", "--version"], False),
    "npm": (["npm.cmd" if sys.platform == "win32" else "npm", "--version"], False),
    "bun": (["bun", "--version"], False), "pdflatex": (["pdflatex", "--version"], False),
    "lualatex": (["lualatex", "--version"], False), "xelatex": (["xelatex", "--version"], False),
    "powershell": (["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"], True),
    "pwsh": (["pwsh", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"], False),
}


def check() -> list[dict]:
    results = []
    for name, (command, required) in TOOLS.items():
        executable = shutil.which(command[0])
        record = {"tool": name, "found": bool(executable), "path": executable or "", "required": required, "version": ""}
        if executable:
            try:
                proc = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
                record["version"] = ((proc.stdout or proc.stderr).splitlines() or [""])[0].strip()
                if proc.returncode != 0:
                    record["error"] = f"exit {proc.returncode}"
            except (OSError, subprocess.TimeoutExpired) as exc:
                record["error"] = str(exc)
        results.append(record)
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="检查 Git/Python/Node/Bun/LaTeX/PowerShell，不安装软件")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args(argv)
    results = check()
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"{item['tool']:<12} {'FOUND' if item['found'] else 'MISSING':<8} required={item['required']!s:<5} {item['version']} {item['path']}")
    return 0 if all(x["found"] for x in results if x["required"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
