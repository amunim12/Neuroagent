<!--
Thanks for contributing to NeuroAgent! Please fill in every section below.
A PR that skips the checklist will likely be asked to update before review.
-->

## Summary

<!-- 1-3 sentences on what this PR does and why. Focus on the *why*. -->

## Related issue

<!-- Use "Closes #N" so the issue auto-closes on merge. -->
Closes #

## Type of change

<!-- Tick whichever apply. -->
- [ ] feat — new user-facing capability
- [ ] fix — bug fix (include reproduction in the description)
- [ ] refactor — no behaviour change
- [ ] perf — measurable performance improvement
- [ ] docs — documentation only
- [ ] test — adds or improves tests only
- [ ] chore / ci — tooling, CI, build, dependencies
- [ ] BREAKING CHANGE — requires user action to upgrade

## What changed

<!-- Bullet list of the concrete changes — files, modules, endpoints, nodes, tools. -->
-
-

## How to test

<!--
Step-by-step reproduction the reviewer can run locally. Include commands,
sample inputs, expected outputs. If you added a test, name it here.
-->

```bash
```

## Screenshots / recordings (UI or agent output changes)

<!-- Drop images or a short clip if the change is user-visible. Delete the section otherwise. -->

## Checklist

- [ ] Code follows the conventions in [CLAUDE.md](../CLAUDE.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] New behaviour has tests; modified behaviour has updated tests.
- [ ] `ruff check .`, `mypy app/`, and `pytest tests/ -v` all pass locally (backend).
- [ ] `npm run lint`, `npm run type-check`, and `npm run build` all pass locally (frontend, if touched).
- [ ] Public functions / classes / endpoints are documented.
- [ ] README / docs updated if behaviour or setup changed.
- [ ] An entry is added under `[Unreleased]` in [CHANGELOG.md](../CHANGELOG.md).
- [ ] No secrets, API keys, or environment-specific values committed.
- [ ] No debug prints, `console.log`, or commented-out code left in the diff.
- [ ] I've self-reviewed the diff before requesting review.

## Notes for reviewers

<!-- Anything non-obvious: trade-offs considered, alternatives rejected, follow-up work intentionally deferred. -->
