---
name: terminal-output-hygiene-expertise
description: Principle of zero tolerance for terminal warnings, deprecation notices, and proactive tool maintenance
triggers:
  - "warning:"
  - "new version available"
  - "DeprecationWarning"
  - "terminal output hygiene"
---

# Terminal Output Hygiene & Zero Warning Policy

## The Insight
An `exit code 0` does not mean an execution is clean. Compilers, linters, test runners, and package managers often emit warnings, deprecation notices, or update recommendations alongside a successful exit code.
Treating warnings as noise leads to creeping technical debt, stale dependencies, and unnoticed regressions.

## Why This Matters
- Deprecation warnings often turn into breaking errors in subsequent minor releases.
- Outdated tools (like `pyright`, `eslint`, `vitest`) may produce false positives or miss newly supported language features.
- Cluttered terminal output hides real, critical warnings.

## Recognition Pattern
- Console output contains strings like `WARNING: there is a new version available`
- Pytest output shows unhandled `DeprecationWarning` or `StarletteDeprecationWarning`
- Jest/Vitest output shows module resolution warnings (e.g. Haste duplicate package names)

## The Approach
1. **Active Log Inspection**: Always read the complete `stdout` and `stderr` of every executed command, not just the exit status.
2. **Immediate Remediation**:
   - For outdated tooling warnings (e.g., `pyright`): Run `uv pip install -U <package>` or `npm update <package>` immediately.
   - For deprecation warnings: Add appropriate pytest filters (`filterwarnings`) or update the calling code to modern APIs (e.g. FastAPI `lifespan`).
   - For Jest Haste collisions: Add `modulePathIgnorePatterns: ['<rootDir>/.next/', '<rootDir>/.agent/']` in `jest.config.ts`.
3. **Clean Baseline**: Maintain a clean terminal baseline where routine check commands run with 0 errors and 0 warnings.
