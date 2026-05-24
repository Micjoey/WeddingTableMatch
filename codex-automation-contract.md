# Codex Daily Automation Contract: Wedding Planner

## Where to paste this
Use this file in two places:

1. **Automation Instructions field** in your Codex scheduled automation.
   - Copy the contents under **"Codex Automation Prompt (copy/paste)"** into the instruction/prompt box.
2. **Repository root file** (this file) as the source of truth.
   - Keep `codex-automation-contract.md` committed so future runs can read/update against a stable contract.

## Schedule
- **Run time:** 9:00 AM
- **Timezone:** `America/Los_Angeles` (Pacific Time)
- **Frequency:** Daily

## Objective
Continuously evolve Wedding Planner toward a sellable, production-ready seating product by delivering one scoped improvement per run.

## Daily Workflow
1. Read current project state and backlog.
2. Update `automation-goals.json` with:
   - the next feature slice,
   - measurable success criteria,
   - acceptance checks for unit tests, lint, and UI/UX.
3. Create branch: `auto/YYYY-MM-DD-feature-slug`.
4. Implement one scoped feature/fix.
5. Run quality gates:
   - unit tests,
   - lint,
   - UI/UX validation.
6. Append run details to `automation-log.jsonl`.
7. Open a pull request with "done vs pending" summary.
8. Auto-merge to `main` only if all required gates pass.

## Merge Policy
- Base branch: `main`
- Review requirement: none (fully automated)
- Auto-merge condition: all configured quality gates pass

## Required Gate Commands (set once per environment)
Replace placeholders with repo-specific commands:
- Unit tests: `UNIT_TEST_COMMAND`
- Lint: `LINT_COMMAND`
- UI/UX validation: `UI_UX_COMMAND`

## Codex Automation Prompt (copy/paste)
```text
You are the Wedding Planner daily automation agent.

Schedule context:
- This run was triggered at 9:00 AM America/Los_Angeles.

Mission:
- Move Wedding Planner toward a sellable, production-ready app for wedding seating planning.

Do the following every run:
1) Read current project state and backlog.
2) Update automation-goals.json with:
   - next feature slice,
   - measurable success criteria,
   - test/UX acceptance checks.
3) Create a branch named auto/YYYY-MM-DD-feature-slug.
4) Implement exactly one scoped feature or fix.
5) Run these required quality gates:
   - UNIT_TEST_COMMAND
   - LINT_COMMAND
   - UI_UX_COMMAND
6) Append a structured line to automation-log.jsonl with timestamp, branch, feature, gate results, PR URL, and merge status.
7) Open a PR that includes:
   - feature slice attempted,
   - success criteria checklist,
   - quality gate outputs,
   - done vs pending,
   - blockers/risks.
8) If and only if all gates pass, auto-merge the PR into main.

Rules:
- Keep changes scoped to one meaningful increment.
- Do not skip gate execution.
- If any gate fails, do not merge; report failures and next actions in the PR.
- Always leave automation-goals.json and automation-log.jsonl updated.
```
