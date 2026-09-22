# AI and Economics Lab

Source for [ai-econ-lab.org](https://ai-econ-lab.org), the AI and Economics Lab at ETH Zurich.
`ai-econ-lab.com` and both `www` aliases redirect to the canonical `.org` address.

- `src/pages/` — homepage, people, research, and grants
- `src/data/` — lab description, team, and research YAML
- `public/assets/` — public images
- `scripts/` and `tests/` — content audit, sitemap, and validation

The 2026 summer school is maintained separately at [zrh-ai-econ.com](https://zrh-ai-econ.com),
in [elliottash/zrh_ai_econ](https://github.com/elliottash/zrh_ai_econ).
This repository preserves the original course repository's Git ancestry, but its current tree contains only the lab site.

## Development

Use Node.js compatible with the pinned Astro version, Python 3, and PyYAML:

```sh
npm ci
python3 -m pip install -r requirements.txt
npm run dev
```

Validate with `npm test`, `npm run build`, and `python3 scripts/check_site.py`.
The content audit currently reports one existing missing-abstract warning.

## Deployment

`./deploy.sh` tests and builds, checks local links, dry-runs the upload, then deploys
to `deploy@138.201.189.28:/opt/ai-econ-lab/site/dist/` and verifies public routes.
Nginx configuration is in `ops/ai-econ-lab.nginx.conf`; TLS and DNS use Cloudflare.

Private knowledge-base sources in `src/pages/kb/` are deliberately git-ignored.
They are available in the maintainer's local checkout and restricted admin backups.
They compile into `/kb/`, which nginx protects with HTTP basic authentication.
Deploy refuses to run without those local sources. Never publish them or `dist/`
to GitHub, and never serve the production KB without the nginx authentication rules.
Lab chat is at [chat.ai-econ-lab.org](https://chat.ai-econ-lab.org). The old
`chat.zrh-ai-econ.com` hostname redirects there. The website’s Chat link opens it.
