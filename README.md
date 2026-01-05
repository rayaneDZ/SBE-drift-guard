# SBE-like Schema Drift Guard

## Problem hypothesis

In market-data systems, exchanges publish binary messages whose **schema changes frequently** (fields added/removed/reordered/type changes). Low-latency feed handlers—often in **C++**—must be updated quickly and safely. Manual updates create downtime risk.

**SBE-like Schema Drift Guard** is a tiny automation of the generation of C++ feed handler code that simulates this reality:

* You keep schemas in a simple JSON format (a stand-in for “real” SBE).
* When a schema changes, the tool:

  1. **diffs** old vs new
  2. **generates** an updated C++ parser
  3. **validates** the parser via automated Python tests
  4. runs in **CI** to keep the pipeline green

This focuses on the core automation idea: **schema drift → code generation → reproducible tests**.

---

## What this MVP includes (tight scope)

### Supported schema format

A minimal JSON schema describing a single message type:

```json
{
  "message": "TradeUpdate",
  "fields": [
    {"name": "ts", "type": "u64"},
    {"name": "price", "type": "i64", "scale": 10000},
    {"name": "qty", "type": "u32"},
    {"name": "symbol", "type": "char[8]"}
  ]
}
```

Supported field types (MVP):

* `u32`, `u64`, `i64`
* fixed strings: `char[N]`

### Supported schema changes

The diff reports:

* Field added / removed
* Field reordered
* Field type changed
* Fixed string length changed (`char[8] -> char[12]`)

### Code generation output

From a schema, the tool generates:

* `generated/trade_parser.h`
* `generated/trade_parser.cpp`

These implement:

* a C++ struct for the message
* a safe parser function that reads from a byte buffer (little-endian)

Example signature:

```cpp
bool parse_trade_update(const uint8_t* buf, size_t len, TradeUpdate& out);
```

### Tests

The MVP prioritizes testability:

* **Unit tests** for schema parsing and diff correctness
* **Codegen tests** to ensure generated C++ contains expected fields and order
* **End-to-end roundtrip test**:

  * Python generates a binary fixture according to the schema
  * Generated C++ parses it
  * Output is compared to expected values

> Note: `test_roundtrip.py` compiles and runs the generated C++ parser using `g++`/`clang++`. If no compiler is available, it is skipped.


### Minimal CI/CD

GitHub Actions runs:

* `pytest -q`
* compile + run the tiny C++ parser test (or compile-only if needed)

No Docker/Kubernetes for now.

---

## Project layout

```
sbe-drift-guard/
  schemas/
    trade_v1.json
    trade_v2.json
  generated/
    trade_parser.h
    trade_parser.cpp
  sbedg/
    schema.py        # dataclasses + validation
    diff.py          # schema diff (adds/removes/changes)
    codegen_cpp.py   # C++ parser generation
    fixtures.py      # binary fixture generation
    cli.py           # CLI entrypoint
  cpp/
    main.cpp         # small runner: parse fixture -> JSON
  tests/
    test_diff.py
    test_codegen.py
    test_roundtrip.py
  .github/workflows/ci.yml
  pyproject.toml
  README.md
```

---

## CLI

The tool exposes 2 core commands:

### 1) Diff schemas

```bash
python -m sbedg diff schemas/trade_v1.json schemas/trade_v2.json
```

Outputs something like:

```
Message: TradeUpdate
+ added field: venue (char[4])
~ changed field: qty u32 -> u64
↔ reordered fields: symbol moved from 4 -> 2
```

### 2) Generate parser

```bash
python -m sbedg generate schemas/trade_v2.json --out generated/
```

Generates:

* `generated/trade_parser.h`
* `generated/trade_parser.cpp`

---

## Demo scripts

1. Show `trade_v1.json` and `trade_v2.json` (simulate “exchange changed schema”)
2. Run:

   ```bash
   python -m sbedg diff schemas/trade_v1.json schemas/trade_v2.json
   ```

   Explain how the diff is the trigger for regeneration.
3. Run:

   ```bash
   python -m sbedg generate schemas/trade_v2.json --out generated/
   ```

   Open the generated C++ and point out:

   * struct definition matches schema
   * parser reads fields in correct order with bounds checks
4. Run tests:

   ```bash
   pytest -q
   ```

   Highlight the roundtrip test: Python writes fixture → C++ parses → output matches expected.
5. Mention CI: every PR regenerates and validates parsers automatically.

> Note: VS Code IntelliSense uses c_cpp_properties.json to locate generated headers.
