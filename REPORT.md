# Online Bookstore – Final Assessment Report

**Author:** _Your Name_  
**Date:** _YYYY-MM-DD_  
**Repository:** _link to your fork_  
**CI Runs:** _link(s) to GitHub Actions runs_

---
## 1. Executive Summary
- All core flows (auth, cart, discount, checkout) covered with automated tests.
- CI/CD pipeline on GitHub Actions runs on every push & PR across Python 3.10–3.12, enforces >= **80%** coverage, uploads artifacts.
- Performance baselines captured with `timeit` and `cProfile`; identified bottlenecks and implemented improvements.

## 2. Test Strategy & Design (Technical Implementation, 50%)
### Scope
- Unit tests for models (`Book`, `Cart`) and helpers.
- Integration tests for Flask routes: `/`, `/login`, `/register`, cart endpoints, discounts, `/checkout`.
- Negative tests: invalid payment (card ends 1111), quantity edge cases (0/negative if supported), duplicate discounts, auth failures.

### Techniques & Oracles
- Black-box assertions based on README-specified behaviors (demo login, `SAVE10`/`WELCOME20`, card ending 1111 fails).
- Property-based checks where applicable (idempotent discount application).

### Coverage
- Overall line coverage must be **>= 80%** (gated in CI).  
- Include coverage XML + term report artifacts.

## 3. Performance Evaluation & Optimizations
### Baselines
- `Cart.total()` time-per-200/250 calls with large cart.
- Discount application per 200/250 runs.
- cProfile of `/` and `/checkout` (top 30 cumulative functions in artifacts).

### Findings (replace with your numbers)
| Scenario | Metric | Before | After | Delta |
|---|---|---:|---:|---:|
| `Cart.total()` (2.5k items) | time/250 calls | 2.10s | 0.38s | **-82%** |
| Checkout POST | cumulative in `Cart.total` | 1.2s | 0.2s | **-83%** |

### Implemented Improvements
- **Memoized cart total** with invalidation on add/update/remove.
- **O(1) discount lookup** via dict mapping; normalize codes to uppercase; prevent double-applying same code.
- **Quantity validation**: clamp to 1..MAX; block zero/negative updates.
- **Template precomputation** of expensive values; minimize loop work.

## 4. CI/CD & Version Control (Critical Evaluation, 30%)
- Matrix on Python 3.10–3.12 ensures cross-version reliability.
- Cached pip improves CI speed.
- Coverage gate enforces quality; artifacts (JUnit, coverage.xml, profiles) enable auditing.
- Git branching model (feature branches + PRs) with automated checks prevents regressions.
- Ethical & operational considerations: no real payments; test data only; secure secrets (none required).

## 5. Evidence
- **Screenshots** of passing Actions, coverage summary, and app flows.
- Attach perf artifacts: `perf_artifacts/*` (catalog & checkout), and reference lines showing improved hotspots.

## 6. References
- Project README (feature oracles)
- Pytest, Coverage.py, cProfile docs

## Appendix A – How to Run Locally
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-test.txt
pytest
python perf/profile_catalog.py
python perf/profile_checkout.py
```
