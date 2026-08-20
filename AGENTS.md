# Rebar.Shop Agent Pointer

This repo uses the canonical Rebar.Shop agent operating stack from:

- `REBAR-SHOP-OS/rebar-os-core`
- Canonical rules: Core `main` under `docs/team`

Agents must load the Core repo's `docs/team` policy files before changing this
repo:

1. `docs/team/STARTUP-PROTOCOL.md`
2. `docs/team/AGENT-OPERATING-STANDARD.md`
3. `docs/team/AGENT-ROLLOUT-AUDIT-COMMANDS.md`
4. `docs/team/AGENT-DEPLOYMENT-HANDOFF.md`
5. `docs/team/CLAUDE-DELEGATION.md`
6. `docs/team/CLAUDE-COMMAND-TEMPLATE.md`
7. the active persona file: `START-SATTAR`, `START-ZAHRA`, or `START-RADIN`

Do not treat this pointer as standalone authority. If the Core docs cannot be
loaded, keep this repo's work draft-only and stop for Sattar.

## Final Button Rule

Only Sattar personally marks ready, approves, merges, enables auto-merge,
publishes/deploys, changes WordPress/Odoo production, changes settings or branch
protection, and touches secrets. An approval phrase is a decision record, not
delegation of those actions to an agent.

## Required Identity Check

Before any repo write, branch operation, push, PR update, or GitHub API
mutation, verify the active GitHub login:

```powershell
gh api user --jq .login
```

Expected logins:

| Persona | Expected GitHub login |
|---|---|
| Sattar | `rebarshop-24` |
| Radin | `radin-ux` |

If identity is wrong, unknown, or unavailable, stop before writing.

Zahra does not work in this repository and is not expected to have GitHub
access. If the active persona is Zahra, stop before any branch, commit, push,
or PR action and route the repository work to Sattar or Radin. Zahra may
provide Odoo/shop operations context and acceptance evidence only.

## Repo-Specific Scope

This repository contains rebar.shop/Odoo integration code and related modules.
It is not permission to edit the live WordPress/SiteGround site. See
`README-DEPLOYMENT.md` for the credential-free deploy/smoke/rollback runbook and
the Odoo (this repo → Odoo.sh) vs WordPress (separate system) surface boundary.

High-risk areas in this repo:

- QuickBooks/accounting modules
- Odoo production modules
- WooCommerce/payment/checkout/RFQ/customer-facing behavior
- email sending and customer messages
- audit logging
- GitHub workflows, branch protection, repo settings, secrets, deploy scripts

Any change in those areas requires explicit Sattar approval and must remain a
draft PR until reviewed.

## Required Local Checks

Run the closest available checks before pushing:

```powershell
py -3 .github/scripts/validate_manifests.py
```

If Python dependencies are available, mirror the GitHub workflow:

```powershell
pip install flake8 pylint-odoo
flake8 --select=E9,F63,F7,F82 <addon-directories>
```

If a local check cannot run, say why in the PR proof strip and rely on GitHub
Actions for the missing evidence.

## Local Safety Rules

- Keep repair work on a scoped branch, never `main`.
- Open or update draft PRs only.
- Do not mark ready, merge, approve, enable auto-merge, deploy, publish, change
  settings, alter branch protection, change secrets, or edit live WordPress.
  Prepare the exact handoff; Sattar performs the final action personally.
- Report proof strip: requester, repo, branch, PR, draft/ready state, changed
  files, local checks, GitHub checks, risk, rollback, and approval still needed.
- If ready/merge/deploy/publish is requested, use the Core
  `AGENT-DEPLOYMENT-HANDOFF.md` packet and stop at Sattar's gate.

---

## RECURRING-DEFECT GUARDRAILS (from 2-year PR-history audit)

These rules exist because the patterns below actually shipped and had to be
reverted or re-fixed across the REBAR repos. They apply to every change here.
The **Coder** subsection is how you avoid producing them; the **Reviewer**
subsection is the hard checklist a review must clear before a PR is handed to
Sattar.

### Coder — prevent (mandatory)

1. **Domain values are load-bearing.** Never emit, convert, or store a quantity
   without an explicit unit/type, and never convert without a written check of
   the factor — physical units (inches↔mm, kg/m), money, tax, credits, and IDs.
   State the unit at the call site and show any conversion.
2. **Root-cause, not band-aid.** Before touching a subsystem, check whether it
   already has prior fixes (`git log --oneline -- <path>`, recent PRs). If this
   is the Nth patch to the same area (QuickBooks/accounting and WooCommerce sync
   have been repeat offenders), fix the underlying cause and say so in the PR
   body — do not stack another surface patch.
3. **Green-before-PR is absolute.** Pass the repo's required local checks above
   (manifest validation / flake8 where applicable). Never open or update a red
   PR; never mark a `[WIP]` change as done.
4. **No silent failures; status must be truthful.** Surface errors to logs and
   UI. Never show "Connected"/success on a failed path, never swallow an
   exception, never return empty-as-if-ok.
5. **Security self-check before every PR.** No hardcoded secrets, keys, or IVs;
   generate IVs/nonces randomly per use. Request the minimum OAuth scopes.
   Sanitize/encode untrusted strings reaching the DOM or a query. Least-privilege
   workflow permissions. Clear CodeQL-class issues yourself.
6. **Scope and idempotency.** Scope every query by company/user/tenant. Make
   writes idempotent and dedupe events, webhooks, and cron so a retry cannot
   double-count or double-schedule.
7. **Runtime-order safety.** Declare before use (no TDZ) and defensively parse
   anything from an upstream API (never assume JSON/shape) so a bad response
   degrades instead of crashing.

### Reviewer — catch (block the PR if any fails)

- **Domain values:** units/types labelled; conversions show their factor.
- **WIP/red:** reject any `[WIP]` marker or non-green CI; require the proof strip.
- **Repeat offender:** another fix to a frequently-patched area → require a
  root-cause statement, not a surface patch.
- **Regression risk:** touches a high-risk area (accounting, payment/checkout,
  Odoo production) → require evidence it does not reintroduce a past failure.
- **Security:** no new CodeQL alerts, no hardcoded secrets/keys/IVs, no
  over-broad scopes, least-privilege workflow perms.
- **Observability:** failures surfaced, status strings truthful, no swallowed
  errors.
- **Data integrity:** tenant/user scoping present; writes/events/cron idempotent.
- The Reviewer inspects, runs checks, and reports. It does **not** author code,
  approve, or merge — those remain Sattar-only.

## Fleet PR Lessons (Mandatory, 2026-08-12)

- Treat the current PR head SHA as the unit of truth; every push invalidates older reviews and checks.
- Verify agent classification, exact-head OpenClaw review, exact-head GitHub bot review, required checks, auto-merge state, merge SHA, and Lovable staging as separate stages.
- Fix code, infrastructure, and policy failures differently on the existing PR; never create a duplicate to escape a failed gate.
- Follow `/home/openclaw/.openclaw/workspace/memory/pr-lessons-2026-08-12.md` for the complete mandatory procedure and today???s verified incidents.
