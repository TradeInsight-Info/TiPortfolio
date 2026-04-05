> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [x]) syntax for tracking.

## 1. Update Workflow

- [x] 1.1 Update `.github/workflows/docs.yml`: replace `mkdocs gh-deploy --force` with `mkdocs build` + `cloudflare/pages-action@v1`, remove `permissions: contents: write` (not needed for Cloudflare), add secrets for `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`
