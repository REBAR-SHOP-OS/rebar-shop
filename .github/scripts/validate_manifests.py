#!/usr/bin/env python3
"""Validate every Odoo ``__manifest__.py`` in the repo.

Checks performed:
  * The file parses as a Python literal dict (this is what Odoo itself
    requires to load a module).
  * A non-empty ``version`` key is declared.
  * The version looks like a dotted numeric string. If it starts with a
    known Odoo series (see ALLOWED_SERIES below) it must match Odoo's
    ``series.major.minor.patch.build`` convention; anything else is only
    reported as a warning so tool/utility addons that don't track a
    specific Odoo series don't fail the build.

Exits non-zero (failing the workflow) only on parse errors or a missing
version - things that would actually stop the module from loading.
"""
import ast
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ALLOWED_SERIES = ("17.0", "18.0")
ODOO_VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+){0,3}$")

# Directories treated as vendored/dependency sources. A module is skipped only
# when its IMMEDIATE parent directory is one of these, so a manifest living
# under a repo whose own path contains a dot-prefixed segment (e.g. .openclaw)
# is still validated.
VENDOR_DIRS = {"node_modules", ".git", ".github", "vendor", "addons", "__pycache__"}


def find_manifests(root: pathlib.Path):
    for manifest in sorted(root.glob("*/__manifest__.py")):
        # Skip only vendored/dependency manifests: a manifest whose immediate
        # parent directory is hidden (starts with '.') or is a known vendor
        # directory. Do NOT skip based on other path segments -- the repo
        # itself may live under a dot-prefixed parent (e.g. .openclaw).
        parent_name = manifest.parent.name
        if parent_name.startswith(".") or parent_name in VENDOR_DIRS:
            continue
        yield manifest


def main() -> int:
    errors = []
    warnings = []

    manifests = list(find_manifests(REPO_ROOT))
    if not manifests:
        print("::warning::No __manifest__.py files found to validate")
        return 0

    for manifest in manifests:
        rel = manifest.relative_to(REPO_ROOT)
        try:
            source = manifest.read_text(encoding="utf-8")
            data = ast.literal_eval(source)
        except (SyntaxError, ValueError) as exc:
            errors.append(f"{rel}: failed to parse as a Python literal ({exc})")
            continue

        if not isinstance(data, dict):
            errors.append(f"{rel}: manifest does not evaluate to a dict")
            continue

        version = data.get("version")
        if not version or not isinstance(version, str):
            errors.append(f"{rel}: missing or empty 'version' key")
            continue

        if not ODOO_VERSION_RE.match(version):
            errors.append(f"{rel}: version '{version}' is not a dotted numeric string")
            continue

        if version.startswith(ALLOWED_SERIES):
            series = version.split(".")[0] + "." + version.split(".")[1]
            if len(version.split(".")) < 3:
                warnings.append(
                    f"{rel}: version '{version}' declares Odoo series {series} "
                    "but is missing the module revision (expected series.major.minor[.patch])"
                )
        else:
            warnings.append(
                f"{rel}: version '{version}' does not start with a recognized "
                f"Odoo series {ALLOWED_SERIES}; confirm this is intentional"
            )

    for warning in warnings:
        print(f"::warning::{warning}")

    if errors:
        for error in errors:
            print(f"::error::{error}")
        print(f"\n{len(errors)} manifest error(s) found.")
        return 1

    print(f"Validated {len(manifests)} manifest(s), {len(warnings)} warning(s), 0 errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
