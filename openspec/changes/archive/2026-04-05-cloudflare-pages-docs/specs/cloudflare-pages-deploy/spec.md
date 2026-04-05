## ADDED Requirements

### Requirement: Docs deploy to Cloudflare Pages
The GitHub Actions workflow SHALL build mkdocs and deploy the `site/` directory to Cloudflare Pages.

#### Scenario: Successful deployment on push to master
- **WHEN** code is pushed to the `master` branch
- **THEN** the workflow SHALL run `mkdocs build` and deploy `site/` to Cloudflare Pages

#### Scenario: Secrets required
- **WHEN** the workflow runs
- **THEN** it SHALL use `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` from GitHub secrets

## REMOVED Requirements

### Requirement: GitHub Pages deployment
**Reason**: Replaced by Cloudflare Pages (free tier, no GitHub plan needed)
**Migration**: Set up Cloudflare Pages project + add GitHub secrets
