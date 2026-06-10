---
name: test-driven-development
description: Drives development with tests. Red-Green-Refactor, test pyramid (80/15/5), DAMP over DRY, Beyonce Rule.
---

# Test-Driven Development

## The TDD Cycle
```
RED (write failing test) → GREEN (minimal code to pass) → REFACTOR (clean up)
```

## The Prove-It Pattern (Bug Fixes)
Write a reproduction test BEFORE fixing the bug. Test FAILS → fix → test PASSES.

## The Test Pyramid
- **80% Unit** — Pure logic, milliseconds each
- **15% Integration** — Component interactions, API boundaries
- **5% E2E** — Critical user flows only

### Beyonce Rule
If you liked it, you should have put a test on it.

## Writing Good Tests
- Test state, not interactions (assert on outcome, not method calls)
- DAMP over DRY (Descriptive And Meaningful Phrases)
- Prefer real implementations over mocks (real > fake > stub > mock)
- Arrange-Act-Assert pattern
- One assertion per concept

## Verification
- [ ] Every new behavior has a corresponding test
- [ ] All tests pass
- [ ] Bug fixes include a reproduction test that failed before the fix
- [ ] Test names describe the behavior being verified
- [ ] No tests were skipped or disabled
