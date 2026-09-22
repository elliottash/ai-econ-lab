#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# These private, ignored sources must be present to preserve the production KB.
test -f src/pages/kb/index.astro || { echo 'Private KB source missing; restore it from the admin backup before deploying.'; exit 1; }
npm test --silent
npm run build
python3 scripts/check_site.py
rsync -rltzn --checksum --delete --itemize-changes --chmod=D755,F644 -e ssh dist/ deploy@138.201.189.28:/opt/ai-econ-lab/site/dist/
rsync -rltz --checksum --delete --chmod=D755,F644 -e ssh dist/ deploy@138.201.189.28:/opt/ai-econ-lab/site/dist/
python3 scripts/check_site.py --live
