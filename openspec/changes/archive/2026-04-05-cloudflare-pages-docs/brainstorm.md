# Deploy Docs to Cloudflare Pages

**Goal**: Replace GitHub Pages deployment with Cloudflare Pages (free tier, no GitHub plan needed).
**Architecture**: Update `.github/workflows/docs.yml` to build mkdocs and deploy via Cloudflare Pages action.
**Tech Stack**: GitHub Actions, Cloudflare Pages, mkdocs
**Spec**: N/A — simple CI config swap

## File Map:

1. Modify : `.github/workflows/docs.yml` - Replace `mkdocs gh-deploy` with Cloudflare Pages deploy

## Chunks

### Chunk 1: Replace deployment target
Replace the `mkdocs gh-deploy --force` step with: `mkdocs build` → `cloudflare/wrangler-action` or `cloudflare/pages-action` to deploy the `site/` directory.

Cloudflare Pages requires:
- `CLOUDFLARE_API_TOKEN` secret in GitHub repo settings
- `CLOUDFLARE_ACCOUNT_ID` secret in GitHub repo settings
- A Cloudflare Pages project (created manually or via wrangler)
