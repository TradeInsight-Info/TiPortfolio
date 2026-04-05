## Why

GitHub Pages requires a paid GitHub plan. Cloudflare Pages offers free static site hosting with generous limits (500 builds/month, unlimited bandwidth), making it a cost-effective alternative for deploying mkdocs documentation.

## What Changes

- Replace `mkdocs gh-deploy --force` with `mkdocs build` + Cloudflare Pages deploy in `.github/workflows/docs.yml`
- Requires `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` GitHub secrets

## Capabilities

### New Capabilities
- `cloudflare-pages-deploy`: Deploy docs to Cloudflare Pages via GitHub Actions

### Modified Capabilities
- `ghpages-deployment`: **Replaced** — GitHub Pages deployment removed in favor of Cloudflare Pages

## Impact

- **CI**: `.github/workflows/docs.yml` updated
- **Infra**: Requires Cloudflare account + Pages project setup
- **Code**: No source code changes
