# Project Audit Log

> Append-only lifecycle audit trail for SDD decisions, authorizations, state changes, and evidence references. Do not store secrets, tokens, personal data, or full verbose command output here; keep detailed command evidence in the phase `validation.md`.

## Event types

`init` · `refactor` · `log-init` · `stack-approved` · `manifest-authorized` · `manifest-created` · `dependency-authorized` · `phase-created` · `phase-approved` · `branch-created` · `living-spec-change` · `validation-recorded` · `phase-complete` · `commit-requested` · `committed` · `merge-requested` · `merged` · `push-requested` · `pushed` · `emergency-exception`

## Maintenance

- Append entries; never rewrite history to hide an event.
- If this file becomes large, create `LOGGING-YYYY.md`, move only closed historical entries with a link from this file, and preserve the original file in Git history.
- A log row records authorization or lifecycle evidence; it does not replace review, tests, or `validation.md`.

## Entries

| Timestamp (UTC) | Event | Phase / scope | Action / evidence | Authorization | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-09-27T07:51:04Z | refactor | project | audit log initialized | user request | Brownfield discovery scaffold created |
| 2026-09-27T07:51:04Z | phase-created | 2026-09-27-preserve-coursera-behavior | phase packet scaffold created | user request | requirements, plan, validation created |
| 2026-09-27T07:51:04Z | phase-created | 2026-09-27-edx-download-mvp | phase packet scaffold created | user request | requirements, plan, validation created |
| 2026-09-27T08:07:31Z | validation-recorded | project-specs | Brownfield inventory, runtime baseline, external edX evidence, and two complete phase validation contracts recorded | user requested SDD specification rewrite; no code or external account access authorized | scaffold check passed; no placeholders; git diff check passed |
| 2026-09-27T08:13:58Z | phase-approved | 2026-09-27-preserve-coursera-behavior | Approved Phase 01 packet: characterization safety net, neutral model and legacy adapter, shared planning/workflow seam, and regression closeout | Explicit user approval on 2026-09-27 | Approval excludes Task Group execution, dependency installation, commit, merge, push, and live Coursera access |
| 2026-09-27T08:13:58Z | branch-created | 2026-09-27-preserve-coursera-behavior | git checkout -b feature/2026-09-27-preserve-coursera-behavior | phase approval policy | local-only branch; no commit or remote action |
| 2026-09-27T08:23:05Z | validation-recorded | 2026-09-27-preserve-coursera-behavior | Group 1 Characterization safety net complete: 65 tests in tests/ covering pure helpers, CLI contract, workflow traversal, resource policy, downloaders, and network guard; all passing exit 0 | authorized by user for Group 1 | ran 65 tests in 0.054s; AST parse 25 files exit 0; git diff --check clean |
| 2026-09-27T08:25:49Z | validation-recorded | 2026-09-27-preserve-coursera-behavior | Group 2 Neutral model and legacy adapter complete: models.py defines CourseManifest, Module, Section, Lecture, Resource with 100% roundtrip fidelity and traversal equivalence; 77 tests passing exit 0 | authorized by user for Group 2 | ran 77 tests in 0.033s; AST parse 27 files exit 0; git diff --check clean |
| 2026-09-27T08:29:50Z | validation-recorded | 2026-09-27-preserve-coursera-behavior | Group 3 Shared planning and workflow seam complete: plan_downloads extracts pure planning from execution; CourseraDownloader.download_manifest provides shared download entrypoint; 83 tests passing exit 0 | authorized by user for Group 3 | ran 83 tests in 0.047s; AST parse 28 files exit 0; git diff --check clean |
| 2026-09-27T08:40:35Z | validation-recorded | 2026-09-27-preserve-coursera-behavior | Group 4 Regression and Living Spec sync complete: 83 tests passing exit 0, AST parse 26 files exit 0, git diff check clean, Living Spec updated, merge-ready evaluated | authorized by user for Group 4 | Ran full test ladder in 0.04s; 0 regressions; ready for user commit and merge review |
| 2026-09-27T09:30:29Z | commit-requested | 2026-09-27-preserve-coursera-behavior | User requested commit of Phase 01 changes | user request | Commit on feature/2026-09-27-preserve-coursera-behavior |
