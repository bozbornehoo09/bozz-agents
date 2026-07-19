# Sunday 2026-07-19 — v0.4.0 install refresh; cross-review dogfood note

## Decisions
- Kept the `version` field in the plugin manifests (deliberate release gating)
  rather than dropping it for commit-SHA tracking. No ADR — operational choice.

## Implemented
- Refreshed the installed plugin to **v0.4.0** on both hosts after the release
  (PR #9). Codex: re-added from its local in-place marketplace, now 0.4.0.
  Claude: version-gated GitHub marketplace — updated via
  `/plugin marketplace update` → `/plugin update` → `/reload-plugins`.

## Notes
- **ADR-0003 validated in practice.** During the self-review of the cross-review
  skills (bridge `rvw-20260718T201151Z-40c0aebf`), the independent fold
  *rejected a confidently-wrong reviewer finding* — F1.2, a false
  `__pycache__`-in-pinned-identity claim — with equal-quality counter-evidence.
  The adjudication layer earned its keep on first live use.
- End-of-session `/update-context` found the repo already reconciled by Codex's
  post-v0.4.0 sweep (PR #10, `1d0b684`); this entry captures only the
  reviewer-side install/dogfood details that sweep did not.

## Up next
- No active milestone — select the next scope in `work_tracker/work_plan.md`.
