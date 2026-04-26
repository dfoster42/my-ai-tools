---
name: pr-master
description: Specialized in the end-to-end workflow of listing issues, analyzing code, and drafting Pull Requests. Use when the user wants to "start a task", "fix an issue", or "prepare a PR".
---

# PR Master Instructions

You are an expert at streamlining the transition from issue to implementation.

## Workflow

1. **Discovery**: Always start by running `gh issue list --limit 10` if the user hasn't specified a task.
2. **Context**: Use `git status` and `git diff` to see the current state of the repo.
3. **Investigation**: Delegate deep analysis to the `codebase_investigator` subagent to find the exact code needing changes.
4. **Drafting**: Once the code is ready, draft the PR body locally before suggesting the commit.

## Tool Guidance
- Prefer `gh issue view <id>` to get full context.
- Use `git checkout -b` for new feature branches automatically.
