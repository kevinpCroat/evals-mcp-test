# Plan: Completing the Remaining Benchmarks

**Last updated:** 2026-01-31

## Status Overview

| Status | Count | Benchmarks |
|--------|-------|------------|
| **Done** | 9 | bug-fixing-001, documentation-001, prototyping-001, debugging-001, maintenance-001, code-migration-001, refactoring-001, porting-001, rewriting-001 |
| **Remaining** | 11 | api-design-001, architecture-001, code-review-001, concurrency-001, data-modelling-001, greenfield-001, infrastructure-001, legacy-comprehension-001, performance-001, security-001, testing-001 |

---

## Recommended Order (by effort and type)

### Phase 1: Code-in-starter-code (fastest wins)

These have starter code; you implement or fix code and run verification.

| # | Benchmark | Task | Est. time | Key files |
|---|-----------|------|------------|-----------|
| 1 | **greenfield-001** | Build URL shortener REST API from scratch (Flask/FastAPI, in-memory). | 30–45 min | New: `app.py` (or similar), tests in verification. |
| 2 | **concurrency-001** | Fix race conditions in cache, counter, worker_pool (threading.Lock, Queue). | 25–35 min | `starter-code/cache.py`, `counter.py`, `worker_pool.py`. |
| 3 | **performance-001** | Optimize data_processor (use profiler_output.txt; target 10x speedup). | 25–35 min | `starter-code/data_processor.py`. |
| 4 | **security-001** | Fix OWASP vulns in Flask app; add SECURITY_AUDIT.md. | 40–50 min | `starter-code/app.py`, new SECURITY_AUDIT.md. |
| 5 | **testing-001** | Write tests for shopping_cart.py; aim for coverage + mutation score. | 30–40 min | New: `test_shopping_cart.py` (in repo root or per spec). |
| 6 | **rewriting-001** | (Already passing) Recursive → iterative tree traversal. | 0 | Verify only if needed. |

### Phase 2: Review / Q&A (read code, produce one deliverable)

Single main deliverable per benchmark; verification is scripted.

| # | Benchmark | Task | Est. time | Deliverable |
|---|-----------|------|------------|-------------|
| 7 | **code-review-001** | Review PR; find all planted bugs; classify severity. | 25–35 min | Markdown report (format in spec). |
| 8 | **legacy-comprehension-001** | Answer questions about legacy invoice codebase. | 30–45 min | `answers.json` (format in spec). |

### Phase 3: Design / specs (no app code, produce YAML/JSON/docs)

Outputs are specs or docs; verification checks structure and content.

| # | Benchmark | Task | Est. time | Deliverable |
|---|-----------|------|------------|-------------|
| 9 | **api-design-001** | OpenAPI 3.0 spec for e-commerce (products, orders, payments, etc.). | 40–50 min | `openapi.yaml` or `openapi.json` in expected path. |
| 10 | **data-modelling-001** | DB schema + migrations for blog (e.g. SQLAlchemy/Alembic or SQL). | 35–45 min | Schema + migration files per verification. |
| 11 | **architecture-001** | Real-time collaborative doc editing: ADRs, diagrams, trade-offs. | 45–60 min | `architecture.md`, `trade-offs.md`, `adrs/`, `diagrams/`. |
| 12 | **infrastructure-001** | Terraform for AWS (VPC, ECS, RDS, ALB, S3, etc.). | 40–50 min | `.tf` files in path verification expects. |

---

## Per-benchmark checklist

### greenfield-001
- [ ] Read `spec.md` and `verification/tests/test_api.py` (or equivalent).
- [ ] Implement REST API: POST create short URL, GET redirect, GET stats, list, delete.
- [ ] Short code 6–8 chars; in-memory store; port 8080; validate URLs.
- [ ] Run `./verification/verify.sh`.

### concurrency-001
- [ ] Read `starter-code/cache.py`, `counter.py`, `worker_pool.py`, `test_concurrency.py`.
- [ ] Add locks/Queue so tests pass 100/100 runs; no test changes.
- [ ] Run verification (100 consecutive test runs).

### performance-001
- [ ] Read `starter-code/data_processor.py` and `profiler_output.txt`.
- [ ] Replace O(n²) or other hot spots; keep API and behavior identical.
- [ ] Run tests + benchmark; confirm ≥10x speedup and tests pass.

### security-001
- [ ] Read `starter-code/app.py` and `verification/VULNERABILITIES.md` (if present).
- [ ] Fix all listed vulns (SQLi, XSS, etc.); add SECURITY_AUDIT.md.
- [ ] Run verification (Bandit + tests).

### testing-001
- [ ] Read `shopping_cart.py` and verification (mutation/coverage rules).
- [ ] Add `test_shopping_cart.py` with full coverage and strong assertions.
- [ ] Run verification (mutation score + coverage).

### code-review-001
- [ ] Read `starter-code/PR_DIFF.md` and `user_manager.py`; use `PLANTED_BUGS.md` only to validate after.
- [ ] Produce review report with issues, line numbers, severity.
- [ ] Run verification (script checks for planted bugs found).

### legacy-comprehension-001
- [ ] Read all files in `starter-code/`; read `questions.json`.
- [ ] Write `answers.json` with id + answer per question.
- [ ] Run verification (fuzzy match on answers).

### api-design-001
- [ ] Read spec for resources (products, orders, payments, etc.).
- [ ] Create `openapi.yaml` or `openapi.json` (OpenAPI 3.0) in the path verification expects.
- [ ] Run verification (schema + endpoint checks).

### data-modelling-001
- [ ] Read spec; check verification for expected schema/migration layout.
- [ ] Add schema definitions and migration(s).
- [ ] Run verification.

### architecture-001
- [ ] Read spec and verification (e.g. `evaluate_architecture.py`).
- [ ] Add `architecture.md`, `trade-offs.md`, `adrs/`, `diagrams/` as required.
- [ ] Run verification.

### infrastructure-001
- [ ] Read spec and app requirements; check verification for paths.
- [ ] Write Terraform (VPC, ECS, RDS, ALB, S3, IAM, etc.).
- [ ] Run verification (e.g. `terraform validate` / plan).

---

## Verification commands (quick reference)

```bash
# From repo root
cd benchmarks/<benchmark-name>
./verification/verify.sh
```

Or run one benchmark via the framework:

```bash
python evaluation-framework/run_benchmark.py <benchmark-name>
```

---

## Suggested session order

1. **Session A (code):** greenfield-001 → concurrency-001 → performance-001  
2. **Session B (code):** security-001 → testing-001  
3. **Session C (review/QA):** code-review-001 → legacy-comprehension-001  
4. **Session D (design):** api-design-001 → data-modelling-001  
5. **Session E (design):** architecture-001 → infrastructure-001  

Total rough estimate: **6–9 hours** for all 11 remaining (excluding rewriting-001).

---

## Notes

- **rewriting-001** was already passing; only re-run verify if something changed.
- Where verification expects a specific path (e.g. `submission/`, or a certain filename), check the benchmark’s `verify.sh` and `spec.md`.
- For design benchmarks, look at `verification/example-submission/` or similar if present; it defines expected structure.
