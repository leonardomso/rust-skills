#!/usr/bin/env python3
"""Classify `cargo check --examples --message-format=json` output.

Buckets per example:
  FRAGMENT  - every error is name resolution (undefined symbol/crate/import).
              Expected for illustrative snippets; ignored.
  ARTIFACT  - errors from extracting a fragment (a `&self` method body wrapped
              as a free fn, pseudocode `...`/`???` tokens, dangling doc comments).
  LOW       - only "type annotations needed" (E0282/E0283).
  SUSPECT   - anything else (type mismatch, no-method, bad syntax, wrong arity,
              missing trait impl, ...). These are real or likely-real bugs.

Modes:
  analyze.py check.json                      print summary + suspect details
  analyze.py check.json --emit-baseline      print one signature per suspect
  analyze.py check.json --check-baseline F   exit 1 if any suspect is not in F
A signature is `file :: section :: sorted(error-tokens)` so it is stable across
line-number edits. CI gates on signatures absent from the committed baseline.
"""
import json, sys, pathlib, collections

HERE = pathlib.Path(__file__).resolve().parent
manifest = json.loads((HERE / "manifest.json").read_text())

RES_CODES = {"E0432","E0433","E0412","E0425","E0405","E0531","E0422",
             "E0423","E0573","E0463","E0583","E0561","E0658"}
RES_PREFIXES = ("cannot find","unresolved import","failed to resolve",
                "use of undeclared","cannot determine","can't find crate",
                "maybe a missing crate","unresolved module")
LOW_CODES = {"E0282","E0283"}

def code_of(d):
    return (d.get("code") or {}).get("code")

def is_resolution(d):
    if code_of(d) in RES_CODES:
        return True
    m = d.get("message","")
    return any(m.startswith(p) for p in RES_PREFIXES)

def is_artifact(d):
    m = d.get("message","")
    if "parameter is only allowed in associated functions" in m:
        return True
    if code_of(d) in {"E0586","E0585"}:
        return True
    if "`...`" in m or "missing documentation" in m:
        return True
    if "await is only allowed inside" in m:
        return True
    return False

def token(d):
    c = code_of(d)
    if c:
        return c
    # parse errors have no code: use a short normalized message stem
    words = d.get("message","").lower().split()
    return "P:" + " ".join(words[:5])

def parse(path):
    errors = collections.defaultdict(list)
    with open(path) as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw.startswith("{"):
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if rec.get("reason") != "compiler-message":
                continue
            msg = rec.get("message", {})
            if msg.get("level") != "error":
                continue
            tgt = (rec.get("target") or {}).get("name")
            if tgt:
                errors[tgt].append(msg)
    return errors

def classify(errors):
    frag = artifact = low = 0
    suspects = {}
    for ex, diags in errors.items():
        nonres = [d for d in diags if not is_resolution(d)]
        if not nonres:
            frag += 1; continue
        if all(is_artifact(d) for d in nonres):
            artifact += 1; continue
        real = [d for d in nonres if not is_artifact(d)]
        if all(code_of(d) in LOW_CODES for d in real):
            low += 1; continue
        suspects[ex] = [d for d in real if code_of(d) not in LOW_CODES]
    return frag, artifact, low, suspects

def signature(ex, diags):
    info = manifest.get(ex, {})
    toks = ",".join(sorted({token(d) for d in diags}))
    return f"{info.get('file','?')} :: {info.get('section','?')} :: {toks}"

def main():
    args = sys.argv[1:]
    path = next((a for a in args if not a.startswith("--")), "check.json")
    errors = parse(path)
    frag, artifact, low, suspects = classify(errors)
    sigs = sorted({signature(ex, d) for ex, d in suspects.items()})

    if "--emit-baseline" in args:
        print("\n".join(sigs))
        return
    if "--check-baseline" in args:
        bpath = args[args.index("--check-baseline") + 1]
        base = set(l.strip() for l in open(bpath) if l.strip() and not l.startswith("#"))
        new = [s for s in sigs if s not in base]
        if new:
            print(f"FAIL: {len(new)} new compile-suspect(s) not in baseline:\n")
            print("\n".join(f"  + {s}" for s in new))
            print("\nIf these are real bugs, fix the example. If they are new "
                  "intentional fragments, regenerate the baseline:\n"
                  "  python3 analyze.py check.json --emit-baseline > baseline.txt")
            sys.exit(1)
        print(f"OK: no new compile suspects ({len(sigs)} known, all in baseline)")
        return

    checked = len(manifest); failed = len(errors)
    print("== compile-check summary ==")
    print(f"examples checked          : {checked}")
    print(f"compiled clean            : {checked - failed}")
    print(f"fragments (undefined syms): {frag}")
    print(f"wrapper/pseudocode artifacts: {artifact}")
    print(f"low-signal (needs type ann): {low}")
    print(f"SUSPECT (review these)    : {len(suspects)}")
    print()
    rows = []
    for ex, diags in suspects.items():
        info = manifest.get(ex, {})
        rows.append((info.get("file","?"), info.get("line",0), info.get("section","?"), diags))
    for file, line, section, diags in sorted(rows):
        print(f"\n--- {file}:{line}  [{section}]")
        seen = set()
        for d in diags:
            c = code_of(d) or "----"
            m = d.get("message","").splitlines()[0]
            if (c, m) in seen:
                continue
            seen.add((c, m))
            print(f"    {c}: {m}")

if __name__ == "__main__":
    main()
