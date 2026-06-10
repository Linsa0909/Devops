---
name: code-review-and-quality
description: Multi-axis code review (5 axes). Use before merging any change.
---

# Code Review and Quality

## The Five-Axis Review
### 1. Correctness
Edge cases handled? Error paths handled? Tests pass?

### 2. Readability & Simplicity
Names clear? Control flow straightforward? Could be fewer lines? Abstractions earning their complexity?

### 3. Architecture
Follows existing patterns? Clean module boundaries? No circular dependencies?

### 4. Security (see security-and-hardening)
Input validated? Secrets in code? SQL parameterized? External data treated as untrusted?

### 5. Performance
N+1 queries? Unbounded loops? Missing pagination? Sync operations that should be async?

## Change Sizing
- ~100 lines → Good
- ~300 lines → Acceptable if single logical change
- ~1000 lines → Too large, split it

## Severity Labels
- **(no prefix)** Required change — must address before merge
- **Critical:** Blocks merge — security vulnerability, data loss
- **Nit:** Minor, optional — author may ignore
- **Optional:** / **Consider:** Suggestion
- **FYI** Informational only

## Verification
- [ ] All Critical issues resolved
- [ ] Tests pass
- [ ] Build succeeds
- [ ] Verify 5 axes: Correctness, Readability, Architecture, Security, Performance
