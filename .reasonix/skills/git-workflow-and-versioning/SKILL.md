---
name: git-workflow-and-versioning
description: Trunk-based development, atomic commits, change sizing, descriptive messages.
---

# Git Workflow and Versioning

## Core Principles
### Trunk-Based Development
Keep `main` always deployable. Short-lived branches (1-3 days). Feature flags > long branches.

### Atomic Commits
One logical thing per commit. Each commit is a save point.

### Descriptive Messages
Format: `<type>: <short description>`
Types: feat / fix / refactor / test / docs / chore

### Keep Concerns Separate
Don't mix formatting with behavior changes. Don't mix refactors with features.

### Change Sizing
~100 lines per commit. ~300 lines acceptable. ~1000 lines → split.

## Pre-Commit Hygiene
```bash
git diff --staged  (check what you're committing)
git diff --staged | grep -i "password\|secret\|api_key\|token"
npm test
npm run lint
```

## Verification
- [ ] Commit does one logical thing
- [ ] Message explains the why
- [ ] Tests pass before committing
- [ ] No secrets in the diff
- [ ] No formatting mixed with behavior changes
