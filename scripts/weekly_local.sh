#!/bin/zsh
# Weekly rich harvest from this Mac (launchd: Monday 06:30 Beijing).
# The GitHub Actions run (Sun 21:00 UTC = Mon 05:00 Beijing) is the fallback when this Mac is asleep;
# this job replaces its thin pull with the full local harvest and redeploys.
set -e
cd /Users/bu-fan.chen/socialscan
exec >> /Users/bu-fan.chen/socialscan/scripts/weekly_local.log 2>&1
echo "=== $(date) weekly local scan ==="
/usr/bin/git pull --no-rebase origin main
.venv/bin/python -m scan.run --no-x --no-llm
/usr/bin/git add -A
/usr/bin/git commit -m "weekly scan $(date +%F) (local)" || { echo "nothing to commit"; exit 0; }
/usr/bin/git push origin main
TOKEN=$(printf "protocol=https\nhost=github.com\n" | /usr/bin/git credential-osxkeychain get | /usr/bin/sed -n 's/^password=//p')
/usr/bin/curl -s -o /dev/null -w "deploy dispatch: %{http_code}\n" -X POST \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/bu-fanchen-maker/socialscan/actions/workflows/daily.yml/dispatches \
  -d '{"ref":"main","inputs":{"harvest":"false"}}'
echo "=== done ==="
