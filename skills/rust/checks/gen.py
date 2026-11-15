#!/usr/bin/env python3
"""Extract ```rust blocks from ../rules/*.md into cargo examples for compile checking.

Each candidate block becomes examples/<name>.rs. Blocks that are intentionally
non-compiling or unresolvable are skipped:
  - under a "## Bad" section (anti-patterns, often deliberately wrong)
  - nightly feature gates (#![feature ...])
  - procedural-macro code (needs a proc-macro crate)
  - placeholder crate names (my_crate, mycrate, mylib, ...)
  - bare pseudocode ellipses (a line that is exactly `...`)

Fragments (snippets that reference undefined domain symbols) are still emitted;
the analyzer separates "only-resolution-errors" (fragments) from real bugs.
"""
import re, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
RULES = (HERE.parent / "rules").resolve()
OUT = HERE / "examples"
OUT.mkdir(exist_ok=True)
for f in OUT.glob("*.rs"):
    f.unlink()

placeholder = re.compile(r'\b(my_crate|mycrate|mylib|my_app|my_project|my_lib|mycrate_derive)\b')
placeholder_use = re.compile(r'\buse\s+(model|transport|service|internal|app|domain)\b')

HEADER = ("#![allow(unused, dead_code, unreachable_code, unused_imports, "
          "unused_variables, unused_mut, unused_assignments, unused_macros, "
          "non_local_definitions)]\n")

def is_candidate(block: str, section: str) -> bool:
    if section.strip().lower() == "bad":
        return False
    if "#![feature" in block:
        return False
    if "proc_macro" in block:
        return False
    if placeholder.search(block) or placeholder_use.search(block):
        return False
    for ln in block.splitlines():
        if ln.strip() == "...":
            return False
    return True

manifest = {}
idx = 0
for md in sorted(RULES.glob("*.md")):
    lines = md.read_text(encoding="utf-8").splitlines()
    section = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^#{2,}\s+(.*)', line)
        if m:
            section = m.group(1).strip()
        if line.strip() == "```rust":
            start = i + 1
            j = start
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            block = "\n".join(lines[start:j])
            if is_candidate(block, section):
                name = f"{md.stem.replace('-', '_')}__{idx}"
                has_main = re.search(r'\bfn\s+main\s*\(', block) is not None
                has_inner_attr = "#![" in block
                # A block that defines a module is item-level: compile it at the
                # crate root so `mod m { use super::* }` resolves correctly.
                has_mod = re.search(r'(?m)^\s*(pub(\([^)]*\))?\s+)?mod\s+\w', block) is not None
                if has_main:
                    content = HEADER + block + "\n"
                elif has_inner_attr or has_mod:
                    content = HEADER + block + "\nfn main() {}\n"
                else:
                    content = (HEADER +
                               "async fn __ex() -> Result<(), Box<dyn std::error::Error>> {\n" +
                               block + "\n;\nOk(())\n}\nfn main() {}\n")
                (OUT / f"{name}.rs").write_text(content, encoding="utf-8")
                manifest[name] = {"file": md.name, "line": start + 1, "section": section}
            idx += 1
            i = j
        i += 1

(HERE / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
print(f"generated {len(manifest)} example files (scanned {idx} rust blocks)")
