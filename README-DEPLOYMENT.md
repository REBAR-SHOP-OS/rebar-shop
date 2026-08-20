# Rebar.Shop — Deployment Runbook

Credential-free. No hostnames, keys, users, ports, or instance URLs are stored
here — use the machine's existing SSH aliases and the Odoo.sh dashboard. This is
documentation only: no automation and no executable deploy script live in this
repo.

There are **two independent production surfaces**. This GitHub repository
(`rebarshop-24/rebar.shop`) controls **only Surface A (Odoo)**. Surface B
(WordPress) is a separate system and is **not** deployed from this repository.

| Surface | What it is | Source of truth | Deploy channel |
|---|---|---|---|
| **A — Odoo** | The Odoo 17/18 addon modules in this repo (`*/__manifest__.py`, `requirements.txt`) | **This repo** | **Odoo.sh**, driven by a GitHub branch push/merge (no SSH) |
| **B — WordPress** | The public `rebar.shop` storefront on SiteGround (PHP) | **NOT this repo** — the Core repo's `wordpress/mu-plugins/*` (WORDPRESS lane) | SSH to the SiteGround host via the existing SSH alias |

## Final-action authority (both surfaces)

Only **Sattar** personally merges, deploys, publishes, restarts/rebuilds an
instance, runs an Odoo module upgrade against production, touches the live
WordPress files, or changes settings/secrets. Agents prepare and verify the
handoff and **STOP** at Sattar's gate. An approval phrase records Sattar's
decision; it does not delegate a final button. **Zahra does not work in this
repository** — route rebar.shop repo work to Sattar or Radin (Zahra may supply
Odoo/shop operations context and acceptance evidence only).

---

## Surface A — Odoo (this repository → Odoo.sh)

Odoo.sh watches this repo's branches and builds/deploys the tracked branches
(e.g. `production`, `Staging`). Deployment happens by **merging to the Odoo.sh
production branch**, which Sattar does; there is no SSH deploy step and no local
deploy script.

### A1. Preflight (agent may run; all non-mutating)
- `py -3 .github/scripts/validate_manifests.py` — every `__manifest__.py` valid, series `17.0`/`18.0`.
- Confirm the changed module's `version` in `__manifest__.py` is bumped (Odoo only upgrades a module when its version increases).
- CI (`.github/workflows/lint-odoo.yml`) is green: blocking `flake8 --select=E9,F63,F7,F82` (fatal syntax/undefined-name), manifest validation, and the "no committed build artifacts" gate. Full flake8 + pylint-odoo run non-blocking.
- If flake8 is unavailable locally, say so in the PR proof strip and rely on GitHub Actions (per `AGENTS.md`).

### A2. Safe handoff (agent → Sattar)
- Work on a scoped branch; open/update a **DRAFT PR** into `main` with the proof strip (changed modules, version bumps, CI result, risk, rollback, high-risk areas touched).
- Do **not** push to `production`/`Staging`, do **not** merge, do **not** trigger an Odoo.sh build.
- Hand to Sattar the exact action requested (e.g. "merge PR #NNN, then promote to the Odoo.sh production branch").

### A3. Sattar-only deploy
- Sattar merges the reviewed PR and promotes it to the Odoo.sh production branch (or rebuilds from the Odoo.sh dashboard). Odoo.sh builds, installs/upgrades the changed modules, and deploys.

### A4. Post-deploy smoke (evidence to record)
- Odoo.sh build status is **green / no failed build stage**.
- The changed module's upgrade completed (Apps shows the new version; no "to upgrade" left pending).
- Functional check of the changed behavior in the Odoo instance (e.g. the affected view opens, the affected action runs, no server error in the Odoo.sh log for that request).

### A5. Rollback decision points
- **Build failed / module upgrade errored:** Odoo.sh keeps the previous build. Sattar reverts the merge commit on the production branch (Odoo.sh redeploys the prior commit) or restores the prior build/backup from the Odoo.sh dashboard.
- **Deployed but behavior is wrong:** revert the PR merge commit → Sattar re-promotes → Odoo.sh redeploys the reverted state. If data was changed by a broken upgrade, restore from the Odoo.sh backup (Sattar only).

### A6. STOP conditions (do not proceed; escalate to Sattar)
- Any change under a high-risk area (`AGENTS.md`): QuickBooks/accounting, WooCommerce/payment/checkout/RFQ, email/customer messages, audit logging, workflows/secrets/deploy config.
- A migration/data-affecting module upgrade, or anything that alters the Odoo database schema.
- Manifest validation or the blocking flake8 gate is red.
- Unclear which Odoo.sh branch/instance is the target.

---

## Surface B — WordPress storefront (NOT this repository)

The public `rebar.shop` site is **WordPress on SiteGround** and is **not**
deployed from this repo. Its source of truth is the Core repo's
`wordpress/mu-plugins/*` (the WORDPRESS lane), and its deploy gate is documented
in the Core repo `CLAUDE.md` ("WORDPRESS / REBAR.SHOP"). It is listed here only
to make the boundary explicit and to keep operators from cross-wiring the two
surfaces.

- **Do not** deploy WordPress changes from this repo; there are no WordPress files here.
- The WordPress deploy channel is SSH via the machine's existing SSH alias (see the operator's `~/.ssh/config`; no host/user/key is recorded in this repo). Connection health can be checked non-mutatingly (authenticate + `id -un`/`pwd`/`php -v`) without changing anything.
- Sattar-only deploy gate (from Core `CLAUDE.md`, summarized): `php -l` locally → snapshot to the audit-graveyard dir → copy to remote → `php -l` remotely → cache purge → `curl -s` GET probe (never HEAD).
- **Smoke:** the `curl -s` GET probe returns the expected page; no PHP fatal in the site error log.
- **Rollback:** restore the pre-deploy snapshot from the audit-graveyard dir (Sattar only).
- **STOP:** any request to edit the live WordPress/SiteGround site from this Odoo repo — route it to the Core repo's WORDPRESS lane and Sattar.

---

## Measured vs estimated handoff

- **Measured this session (read-only):** manifest validation passes (12 manifests, 0 errors); GitHub repo reachable with push rights (Odoo.sh channel); WordPress SSH alias authenticates read-only (SiteGround `/home/customer`, PHP CLI present).
- **Estimated:** scoped fix + draft PR ≈ agent time varies; Sattar merge + Odoo.sh build/deploy ≈ minutes (Odoo.sh build time); smoke + rollback are Sattar-gated. These are estimates, not measured deploys — no deployment was performed.
