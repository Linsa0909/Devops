# AgentDev OS — Project Skills & Rules

This file activates development skills for the AI agent working on this project.

## Active Skills (from addyosmani/agent-skills)

- **api-and-interface-design** → Contract-first API, Hyrum's Law, consistent error semantics, boundary validation
- **test-driven-development** → Red-Green-Refactor, test pyramid (80/15/5), DAMP over DRY, Arrange-Act-Assert
- **code-review-and-quality** → 5-axis review (Correctness/Readability/Architecture/Security/Performance), severity labels
- **frontend-ui-engineering** → Component colocation, design system tokens, WCAG 2.1 AA, responsive mobile-first
- **git-workflow-and-versioning** → Atomic commits, descriptive messages, pre-commit hygiene

## DeveloperAgent Constraints
When generating code, follow these rules:
1. API endpoints: `/api/v1/` prefix, unified JSON response `{"code":0,"message":"ok","data":...}`
2. Error responses: consistent format across all endpoints
3. Tests: write tests BEFORE code (RED phase), one assertion per concept
4. Code review: every change passes 5-axis review (Correctness/Readability/Architecture/Security/Performance)

## ReviewerAgent Constraints
When reviewing code, use the 5-axis framework:
1. Correctness — edge cases, error paths, tests
2. Readability — names, control flow, simplicity
3. Architecture — patterns, boundaries, dependencies
4. Security — input validation, secrets, untrusted data
5. Performance — N+1 queries, pagination, unbounded operations

Assign severity: Critical / Required / Nit / Optional / FYI
