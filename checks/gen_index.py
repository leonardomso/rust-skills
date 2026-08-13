#!/usr/bin/env python3
"""Generate SKILL.md's priority table + Quick Reference from rules/ and README counts.

Single source of truth: each rule file's `# id` header, its `> summary` line, and
the ordered CATEGORIES config below (prefix -> title + impact). Rule order within a
category is preserved from the current SKILL.md and any new rules are appended.

  python3 checks/gen_index.py            rewrite SKILL.md + README counts
  python3 checks/gen_index.py --check    exit 1 if they are out of date (CI)
"""
import re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
RULES = ROOT / "rules"
SKILL = ROOT / "SKILL.md"
README = ROOT / "README.md"

# (prefix, title, impact) in display order
CATEGORIES = [
    ("own-",    "Ownership & Borrowing",     "CRITICAL"),
    ("err-",    "Error Handling",            "CRITICAL"),
    ("mem-",    "Memory Optimization",       "CRITICAL"),
    ("unsafe-", "Unsafe Code",               "CRITICAL"),
    ("api-",    "API Design",                "HIGH"),
    ("async-",  "Async/Await",               "HIGH"),
    ("conc-",   "Concurrency",               "HIGH"),
    ("opt-",    "Compiler Optimization",     "HIGH"),
    ("num-",    "Numeric & Arithmetic Safety", "HIGH"),
    ("type-",   "Type Safety",               "MEDIUM"),
    ("trait-",  "Trait & Generics Design",   "MEDIUM"),
    ("conv-",   "Conversions",               "MEDIUM"),
    ("const-",  "Const & Compile-Time",      "MEDIUM"),
    ("serde-",  "Serde",                     "MEDIUM"),
    ("pat-",    "Pattern Matching",          "MEDIUM"),
    ("macro-",  "Macros",                    "MEDIUM"),
    ("closure-","Closures",                  "MEDIUM"),
    ("coll-",   "Collections",               "MEDIUM"),
    ("name-",   "Naming Conventions",        "MEDIUM"),
    ("test-",   "Testing",                   "MEDIUM"),
    ("doc-",    "Documentation",             "MEDIUM"),
    ("obs-",    "Observability",             "MEDIUM"),
    ("perf-",   "Performance Patterns",      "MEDIUM"),
    ("proj-",   "Project Structure",         "LOW"),
    ("ffi-",    "FFI & Interop",             "LOW"),
    ("lint-",   "Clippy & Linting",          "LOW"),
    ("anti-",   "Anti-patterns",             "REFERENCE"),
]

def prefix_of(rule_id):
    return rule_id.split("-", 1)[0] + "-"

def summary_of(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("> "):
            return line[2:].strip()
    raise SystemExit(f"{path.name}: no '> summary' line")

def build():
    ids = sorted(p.stem for p in RULES.glob("*.md"))
    by_prefix = {}
    for rid in ids:
        by_prefix.setdefault(prefix_of(rid), []).append(rid)

    known = {p for p, _, _ in CATEGORIES}
    stray = sorted(set(by_prefix) - known)
    if stray:
        raise SystemExit(f"rules with unknown prefix (add to CATEGORIES): {stray}")

    # preserve existing Quick Reference order; append new rules (sorted)
    existing = []
    seen = set()
    for m in re.finditer(r'rules/([a-z0-9-]+)\.md', SKILL.read_text(encoding="utf-8")):
        if m.group(1) not in seen:
            seen.add(m.group(1)); existing.append(m.group(1))

    table_rows, qr_sections = [], []
    total = 0
    for i, (prefix, title, impact) in enumerate(CATEGORIES, 1):
        rules = by_prefix.get(prefix, [])
        ordered = [r for r in existing if r in rules] + sorted(r for r in rules if r not in existing)
        total += len(ordered)
        table_rows.append(f"| {i} | {title} | {impact} | `{prefix}` | {len(ordered)} |")
        lines = [f"### {i}. {title} ({impact})", ""]
        for rid in ordered:
            lines.append(f"- [`{rid}`](rules/{rid}.md) - {summary_of(RULES / f'{rid}.md')}")
        qr_sections.append("\n".join(lines))

    table = ("| Priority | Category | Impact | Prefix | Rules |\n"
             "|----------|----------|--------|--------|-------|\n"
             + "\n".join(table_rows))
    quickref = "\n\n".join(qr_sections)
    return table, quickref, total, len(CATEGORIES)

def render_skill(text, table, quickref, total, ncat):
    text = re.sub(r"(## Rule Categories by Priority\n\n).*?(\n\n---\n\n## Quick Reference)",
                  lambda m: m.group(1) + table + m.group(2), text, flags=re.S)
    text = re.sub(r"(## Quick Reference\n\n).*?(\n\n---\n\n## Recommended Cargo\.toml Settings)",
                  lambda m: m.group(1) + quickref + m.group(2), text, flags=re.S)
    text = re.sub(r"\d+ rules across \d+ categories", f"{total} rules across {ncat} categories", text)
    return text

def render_readme(text, total, ncat):
    text = re.sub(r"rules-\d+", f"rules-{total}", text)
    text = re.sub(r"categories-\d+", f"categories-{ncat}", text)
    text = re.sub(r"\d+ Rust rules", f"{total} Rust rules", text)
    text = re.sub(r"\d+ rules split into \d+ categories", f"{total} rules split into {ncat} categories", text)
    return text

def main():
    table, quickref, total, ncat = build()
    skill_new = render_skill(SKILL.read_text(encoding="utf-8"), table, quickref, total, ncat)
    readme_new = render_readme(README.read_text(encoding="utf-8"), total, ncat)

    if "--check" in sys.argv:
        stale = []
        if skill_new != SKILL.read_text(encoding="utf-8"): stale.append("SKILL.md")
        if readme_new != README.read_text(encoding="utf-8"): stale.append("README.md")
        if stale:
            print(f"OUT OF DATE: {', '.join(stale)} — run `python3 checks/gen_index.py`")
            sys.exit(1)
        print(f"OK: index up to date ({total} rules, {ncat} categories)")
        return

    SKILL.write_text(skill_new, encoding="utf-8")
    README.write_text(readme_new, encoding="utf-8")
    print(f"wrote index: {total} rules across {ncat} categories")

if __name__ == "__main__":
    main()
