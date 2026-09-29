#!/usr/bin/env bash
# Run the pending Jev jobs in priority order until the free route's daily cap stops them.
#
# OpenCode Zen's free jev-1.13-free allows roughly 250 requests per IP per day, resetting at
# 00:00 UTC. Every answer is cached as it arrives, so running this again the next day
# resumes exactly where it stopped, and jobs already finished cost nothing.
#
# Usage (from the project root, once a day):  scripts/run_jev_daily.sh
# Afterwards, commit the new answers so they are never lost:
#   git add .cache/jev_decisions.jsonl results && git commit -m "chore: add daily Jev answers"
#
# The first run replays 6 published reference answers (6 calls) to check that the route
# really serves TypeSafe's Jev; later runs replay 1 as a drift canary.
set -uo pipefail
cd "$(dirname "$0")/.."

readonly PYTHON=".venv/bin/python"

# Highest showcase value first; the full 1,001-message sample last.
readonly JOBS=(
  "--probe tricky.v1"
  "--probe hinglish.v1"
  "--probe tanglish.v1"
  "--limit 249 --examples-per-label 5"
  ""
)

# 1. Check the route still serves TypeSafe's Jev before spending the day's quota.
#    First run: all 6 published reference cases. Later runs: 1-call drift canary.
if compgen -G "results/route_verification/*.json" > /dev/null; then
  verify_cases=1
else
  verify_cases=6
fi
echo "== verify-route --max-cases ${verify_cases}"
if ! "$PYTHON" -m app.main verify-route --max-cases "$verify_cases"; then
  echo "Stopped: the route did not match TypeSafe's published answers (or hit the cap)."
  echo "Inspect results/route_verification/ before running any Jev jobs."
  exit 1
fi

# 2. The Jev jobs.
for job in "${JOBS[@]}"; do
  echo "== run-jev ${job:-(full sample)}"
  # shellcheck disable=SC2086  # the job string is a list of CLI flags, split on purpose
  if ! "$PYTHON" -m app.main run-jev $job; then
    echo "Stopped: daily cap or an error (see above). Run this again after 00:00 UTC."
    exit 1
  fi
  report_flags="${job/--examples-per-label 5/}"
  # shellcheck disable=SC2086
  "$PYTHON" -m app.main report $report_flags
done
echo "All Jev jobs are complete."
