#!/usr/bin/env python3
"""Generate SKILL.md's rule index (the `## Index` section, which runs to EOF) and README counts.

Single source of truth: each rule file's `# id` header, its `> summary` line, and
the ordered CATEGORIES config below (prefix -> title + impact). Rule order within a
category is preserved from the current SKILL.md and any new rules are appended.

Also kept in sync: the per-category counts in README's "What's in here" table
(rows are matched to CATEGORIES by order), and the "Current for Rust X" version
in SKILL.md/README, which is read from checks/rust-toolchain.toml so the
documented version is always the one CI compile-checks against.

  python3 checks/gen_index.py            rewrite SKILL.md + README counts
  python3 checks/gen_index.py --check    exit 1 if they are out of date (CI)
"""
import re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
RULES = ROOT / "rules"
SKILL = ROOT / "SKILL.md"
README = ROOT / "README.md"
TOOLCHAIN = HERE / "rust-toolchain.toml"

def rust_version():
    m = re.search(r'channel\s*=\s*"(\d+)\.(\d+)(?:\.\d+)?"', TOOLCHAIN.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit("checks/rust-toolchain.toml: no numeric channel")
    return f"{m.group(1)}.{m.group(2)}"

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
    ("lint-",   "Clippy & Linting",          "LOW"),
    ("anti-",   "Anti-patterns",             "REFERENCE"),
]

# Anti-patterns section: common mistakes, each pointing at the rule that fixes it.
# The fixes live in their home categories (one source of truth per meaning);
# this list is the symptom -> rule lookup a reviewer scans. Real `anti-` rule
# files, for mistakes with no other home, are listed above the lookup.
ANTI_LOOKUP = [
    ("`.unwrap()` in production code", ["err-no-unwrap-prod"]),
    ("`expect()` on a recoverable error", ["err-expect-bugs-only"]),
    ("Panicking on expected failures", ["err-result-over-panic"]),
    ("`.clone()` to quiet the borrow checker", ["own-borrow-over-clone"]),
    ("`&String` / `&Vec<T>` parameters", ["own-slice-over-vec"]),
    ("A lock guard held across `.await`", ["async-no-lock-await"]),
    ("Index loops where an iterator fits", ["perf-iter-over-index"]),
    ("Collecting between iterator steps", ["perf-collect-once"]),
    ("`format!` in a hot path", ["mem-write-over-format", "mem-avoid-format"]),
    ("Optimizing without a profile", ["perf-profile-first"]),
    ("Strings where an enum or newtype fits", ["type-no-stringly"]),
    ("`Box<dyn Trait>` where `impl Trait` works", ["trait-dyn-vs-generic"]),
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

    qr_sections = []
    total = 0
    for i, (prefix, title, impact) in enumerate(CATEGORIES, 1):
        rules = by_prefix.get(prefix, [])
        ordered = [r for r in existing if r in rules] + sorted(r for r in rules if r not in existing)
        total += len(ordered)
        lines = [f"### {i}. {title} ({impact})", ""]
        for rid in ordered:
            lines.append(f"- [`{rid}`](rules/{rid}.md) - {summary_of(RULES / f'{rid}.md')}")
        if prefix == "anti-":
            if ordered:
                lines.append("")
            lines += ["Common mistakes and the rule that fixes each:", "",
                      "| Symptom | Fix |", "|---------|-----|"]
            for symptom, fixes in ANTI_LOOKUP:
                for rid in fixes:
                    if not (RULES / f"{rid}.md").exists():
                        raise SystemExit(f"ANTI_LOOKUP: rules/{rid}.md does not exist")
                links = ", ".join(f"[`{rid}`](rules/{rid}.md)" for rid in fixes)
                lines.append(f"| {symptom} | {links} |")
        qr_sections.append("\n".join(lines))

    counts = [len(by_prefix.get(prefix, [])) for prefix, _, _ in CATEGORIES]
    quickref = "\n\n".join(qr_sections)
    return quickref, total, len(CATEGORIES), counts

def render_skill(text, quickref, total, ncat):
    head, sep, _ = text.partition("\n## Index\n")
    if not sep:
        raise SystemExit("SKILL.md: no '## Index' section")
    text = head + sep + "\n" + quickref + "\n"
    text = re.sub(r"\d+ rules across \d+ categories", f"{total} rules across {ncat} categories", text)
    text = re.sub(r"Current for Rust [\d.]+", f"Current for Rust {rust_version()}", text)
    return text

def render_readme(text, total, ncat, counts):
    ver = rust_version()
    text = re.sub(r"Current for Rust [\d.]+", f"Current for Rust {ver}", text)
    text = re.sub(r"badge/Rust-[\d.]+%20", f"badge/Rust-{ver}%20", text)
    # "What's in here" table: | **Category** | N | description |, one row per category in order
    m = re.search(r"(\| Category \| Rules \| What it covers \|\n\|[-|]+\|\n)((?:\|.*\|\n)+)", text)
    if not m:
        raise SystemExit("README.md: category table not found")
    rows = m.group(2).splitlines()
    if len(rows) != len(counts):
        raise SystemExit(f"README.md: category table has {len(rows)} rows, expected {len(counts)}")
    rows = [re.sub(r"^(\| [^|]+ \| )\d+( \|)", lambda r, n=n: f"{r.group(1)}{n}{r.group(2)}", row)
            for row, n in zip(rows, counts)]
    text = text[:m.start(2)] + "\n".join(rows) + "\n" + text[m.end(2):]
    text = re.sub(r"rules-\d+", f"rules-{total}", text)
    text = re.sub(r"categories-\d+", f"categories-{ncat}", text)
    text = re.sub(r"\d+ Rust rules", f"{total} Rust rules", text)
    text = re.sub(r"\d+ rules split into \d+ categories", f"{total} rules split into {ncat} categories", text)
    return text

def main():
    quickref, total, ncat, counts = build()
    skill_new = render_skill(SKILL.read_text(encoding="utf-8"), quickref, total, ncat)
    readme_new = render_readme(README.read_text(encoding="utf-8"), total, ncat, counts)

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
