---
name: api-and-interface-design
description: Contract-first API design with Hyrum's Law, consistent error semantics, boundary validation, and backward-compatible interfaces.
---

# API and Interface Design

## Core Principles
### Contract First
Define the interface before implementing it. Types ARE the documentation.

### Consistent Error Semantics
- 400 → Invalid input | 401 → Not authenticated | 403 → Not authorized
- 404 → Not found | 409 → Conflict | 422 → Validation failed | 500 → Server error
- Every error follows: `{"code": "ERROR_CODE", "message": "...", "details": ...}`

### Validate at Boundaries
Trust internal code. Validate only where external input enters. Third-party API responses are untrusted data.

### Prefer Addition Over Modification
Extend interfaces without breaking consumers. New fields are optional.

### Hyrum's Law
Every observable behavior becomes a de facto contract. Be intentional about what you expose.

## Verification
- [ ] Every endpoint has typed input/output schemas
- [ ] Error responses follow a single consistent format
- [ ] Validation happens at system boundaries only
- [ ] List endpoints support pagination
- [ ] New fields are additive and optional
