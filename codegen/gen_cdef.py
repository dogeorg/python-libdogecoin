#!/usr/bin/env python3
"""Generate the cffi cdef from the *fetched* libdogecoin header.

This is what makes "release each version" work: the bound surface is a function
of whichever libdogecoin release fetch.py pulled in, not a hand-maintained list.
v0.1.0 binds its ~18 functions; a newer pin binds whatever it exports. No manual
edits when the pin moves.

Strategy:
  1. Parse include/libdogecoin.h for function prototypes actually present.
  2. For each, lower array/typedef params to concrete C types cffi can parse,
     using idl_tier1.json's annotations where the function is known, and a
     best-effort lowering otherwise.
  3. Emit a cdef block + a JSON manifest of what was bound, so _build.py and the
     wrapper agree on the surface at runtime.

Run:  python -m codegen.gen_cdef --header include/libdogecoin.h \
          --out-cdef python/_cdef.h --out-manifest python/_surface.json
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDL = HERE / "idl_tier1.json"

# typedef'd array / scalar params in the header lowered to what cffi accepts.
# These names appear as parameter types in various libdogecoin releases.
TYPEDEF_LOWERING = {
    "SEED": "uint8_t*",
    "MNEMONIC": "char*",
    "PASS": "char*",
    "HEX_ENTROPY": "char*",
    "ENTROPY_SIZE": "char*",
    "CHANGE_LEVEL": "char*",
    "KEY_PATH": "char*",
    "dogecoin_bool": "int",   # ABI: dogecoin_bool is an int/uint8; cffi-safe as int
    "bool": "int",
}

# size-macro-bearing array params like `char wif[PRIVKEYWIFLEN]` -> `char* wif`.
ARRAY_PARAM = re.compile(r'^\s*(const\s+)?([A-Za-z_]\w*)\s+(\w+)\s*\[[^\]]*\]\s*$')
SIMPLE_PARAM = re.compile(r'^\s*(const\s+)?([A-Za-z_][\w\s\*]*?)\s*(\**)\s*(\w+)\s*$')


def strip_comments(src: str) -> str:
    src = re.sub(r'/\*.*?\*/', ' ', src, flags=re.S)
    src = re.sub(r'//[^\n]*', ' ', src)
    return src


def extract_prototypes(header_src: str):
    """Return list of (ret, name, [raw_param,...]) for top-level func decls."""
    flat = re.sub(r'\s+', ' ', strip_comments(header_src))
    protos = []
    # ret types we treat as function returns in this API
    pat = re.compile(
        r'\b(int|void|uint64_t|dogecoin_bool|char)\s*(\*?)\s*([A-Za-z_]\w*)\s*\(([^;{]*)\)\s*;'
    )
    for m in pat.finditer(flat):
        ret_base, ret_ptr, name, params_raw = m.groups()
        ret = (ret_base + ret_ptr).strip()
        params = [p.strip() for p in split_params(params_raw) if p.strip()]
        if params == ["void"]:
            params = []
        protos.append((ret, name, params))
    return protos


def split_params(s: str):
    out, depth, cur = [], 0, ""
    for c in s:
        if c in "([": depth += 1
        elif c in ")]": depth -= 1
        if c == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += c
    if cur.strip():
        out.append(cur)
    return out


def lower_param(raw: str) -> str:
    """Lower one C parameter declaration to a cffi-parseable concrete type."""
    raw = raw.strip()
    # array param: `char foo[BAR]` or `const char foo[BAR]`
    m = ARRAY_PARAM.match(raw)
    if m:
        const, typ, var = m.groups()
        typ = TYPEDEF_LOWERING.get(typ, typ)
        return f"{typ}* {var}"
    # typedef'd array type used directly: `SEED seed`, `MNEMONIC m`
    parts = raw.split()
    if parts:
        head = parts[0] if parts[0] != "const" else (parts[1] if len(parts) > 1 else "")
        if head in TYPEDEF_LOWERING and "*" not in raw and "[" not in raw:
            var = parts[-1]
            return f"{TYPEDEF_LOWERING[head]} {var}"
    # general: replace any known typedef token, keep the rest
    tokens = raw.split()
    tokens = [TYPEDEF_LOWERING.get(t, t) for t in tokens]
    return " ".join(tokens)


def lower_ret(ret: str) -> str:
    return TYPEDEF_LOWERING.get(ret, ret)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--header", required=True)
    ap.add_argument("--out-cdef", required=True)
    ap.add_argument("--out-manifest", required=True)
    args = ap.parse_args()

    header_src = Path(args.header).read_text()
    protos = extract_prototypes(header_src)

    idl = json.loads(IDL.read_text()) if IDL.exists() else {"functions": []}
    idl_names = {f["name"] for f in idl["functions"]}

    lines = ["/* AUTO-GENERATED from the fetched libdogecoin header. */"]
    bound = []
    for ret, name, params in protos:
        lowered = [lower_param(p) for p in params]
        sig = f"{lower_ret(ret)} {name}({', '.join(lowered) or 'void'});"
        lines.append(sig)
        bound.append({"name": name, "in_idl": name in idl_names})

    Path(args.out_cdef).write_text("\n".join(lines) + "\n")
    Path(args.out_manifest).write_text(
        json.dumps({"functions": bound, "count": len(bound)}, indent=2) + "\n"
    )
    n_idl = sum(1 for b in bound if b["in_idl"])
    print(f"bound {len(bound)} functions ({n_idl} annotated by IDL, "
          f"{len(bound) - n_idl} header-only) -> {args.out_cdef}")


if __name__ == "__main__":
    main()
