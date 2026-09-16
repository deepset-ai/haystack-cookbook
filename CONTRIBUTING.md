# Contributing to the Haystack Cookbook

This repository showcases how to use [Haystack](https://github.com/deepset-ai/haystack) well — new
model providers, vector databases, retrieval techniques, experimental features, and best practices.
It is not a place to advertise a third-party product; any tool or service shown here must be used
*with* Haystack to demonstrate a Haystack capability, not the other way around.

## The process

1. **Open an issue first.** Use the [new example issue template](.github/ISSUE_TEMPLATE/new_example.yml)
   to propose your notebook. Describe the Haystack feature or integration it demonstrates and why it's
   a useful addition.
2. **Wait for a maintainer to review and assign it to you.** We check that the proposal fits the
   cookbook's goal before any code is written. Issues that read as promotion for a specific product
   rather than a Haystack use case will not be assigned.
3. **Open your PR only once the issue is assigned to you**, and reference it with `Closes #<issue>`
   in the PR description. PRs that don't reference an issue assigned to their author will be closed
   automatically by CI.

## Writing the notebook

1. Add your notebook to `/notebooks`.
2. Give it a descriptive name that includes the model providers, databases, and/or technologies used,
   and/or the task it completes.
3. Register it in `index.toml`, including its title and topics. If it uses an experimental feature,
   also set `experimental = true` and add the discussion link.

> You can also create a PR directly from Colab: fork this repository, add your example, then use
> "Save a Copy to GitHub" on Colab to push to your fork before opening the PR.
