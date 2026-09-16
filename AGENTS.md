# AGENTS.md

Instructions for AI coding agents (Claude Code, Copilot, Cursor, etc.) working in this repository.

## What this repo is

A collection of example Jupyter notebooks demonstrating [Haystack](https://github.com/deepset-ai/haystack).
Each notebook is a small, focused demo of a Haystack feature, integration, or best practice —
not a showcase for a third-party product.

## Contribution process — read before writing any new example

New examples require an issue **assigned by a maintainer** before a PR is opened. Do not create a
notebook and open a PR for it speculatively — a CI workflow (`.github/workflows/enforce_issue_link.yml`)
auto-closes PRs that don't reference an issue assigned to the PR author. Full process in
[CONTRIBUTING.md](CONTRIBUTING.md).

If you're an agent acting on behalf of a user who wants to add an example:
1. Check whether an issue for it already exists and is assigned to the user.
2. If not, tell the user to open one via `.github/ISSUE_TEMPLATE/new_example.yml` and wait for assignment.
3. Only write the notebook and PR once the issue is confirmed assigned.

## Adding/editing a notebook

1. Place notebooks in `/notebooks`, named descriptively (model providers, databases, technologies, task).
2. Register every notebook in `index.toml` under `[[cookbook]]` with `title`, `notebook` (filename), and
   `topics`. Experimental features also need `experimental = true` and a discussion link.
3. Validate with `python scripts/verify_index.py` — checks every notebook is indexed, every indexed
   entry's file exists, and each has a title and topics. This runs in CI on PRs touching notebooks or
   `index.toml`.
4. Keep notebook output cells present but minimal — don't leave huge dumps or secrets/API keys in
   committed output.
5. Dependencies used by notebooks go in `requirements.txt` when shared, otherwise `pip install` cells
   inside the notebook itself (repo convention: check a few existing notebooks in `/notebooks` for the
   pattern before adding a new one).

## Don't

- Don't add a notebook that primarily promotes a third-party tool with Haystack as an afterthought.
- Don't open a PR without a linked, assigned issue — it will be auto-closed.
- Don't hardcode API keys or secrets in notebook cells or outputs.
