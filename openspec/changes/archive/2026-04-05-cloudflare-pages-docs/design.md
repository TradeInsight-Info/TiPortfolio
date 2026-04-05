## Context

The current `.github/workflows/docs.yml` uses `mkdocs gh-deploy --force` which requires GitHub Pages (paid plan). Cloudflare Pages is a free alternative.

## Goals / Non-Goals

**Goals:**
- Deploy docs to Cloudflare Pages on push to master
- Keep the same build process (mkdocs build)

**Non-Goals:**
- Custom domain setup (can be done later in Cloudflare dashboard)
- Preview deployments for PRs (can be added later)

## Decisions

### Decision 1: Use `cloudflare/pages-action@v1`

The official Cloudflare Pages GitHub Action. It uploads the built `site/` directory directly.

```yaml
- name: Deploy to Cloudflare Pages
  uses: cloudflare/pages-action@v1
  with:
    apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
    projectName: tiportfolio-docs
    directory: site
```

### Decision 2: Project name `tiportfolio-docs`

The Cloudflare Pages project needs to be created first (via dashboard or `wrangler pages project create tiportfolio-docs`). The URL will be `tiportfolio-docs.pages.dev`.

## Risks / Trade-offs

- **Requires manual Cloudflare setup**: User must create the project and add secrets. Documented in workflow comments.
