#!/usr/bin/env bash
# laptop-sync.sh — keep a checkout of the leader branch current without opening a terminal.
#
#   bash tools/laptop-sync.sh run        one fast-forward-only pull, if it is safe
#   bash tools/laptop-sync.sh install    systemd user timer: 2 minutes after login, then every 15 minutes
#   bash tools/laptop-sync.sh status     the timer and the last ten log lines
#   bash tools/laptop-sync.sh uninstall  remove the timer
#
# Safe by construction: it only ever fast-forwards. It skips, and says why in the log,
# when the checkout is not on the leader branch, has uncommitted changes, or has commits of its own.
# It never stashes, resets, merges, or pushes.
set -eu

TRUNK="${LOCALDNS_BRANCH:-leader}"  # where work lands; main is intent cold storage (DEC-015)
REPO="${LOCALDNS_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG="${LOCALDNS_SYNC_LOG:-$HOME/.local/state/localdns-sync.log}"
UNITS="$HOME/.config/systemd/user"

say() {
  mkdir -p "$(dirname "$LOG")"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"
}

run() {
  cd "$REPO"
  branch="$(git branch --show-current)"
  if [ "$branch" != "$TRUNK" ]; then say "skip: on branch '$branch', not $TRUNK"; return 0; fi
  if [ -n "$(git status --porcelain)" ]; then say "skip: uncommitted changes"; return 0; fi
  if ! git fetch -q origin "$TRUNK"; then say "skip: fetch failed (offline?)"; return 0; fi
  ahead="$(git rev-list --count "origin/$TRUNK"..HEAD)"
  behind="$(git rev-list --count HEAD.."origin/$TRUNK")"
  if [ "$ahead" != "0" ]; then say "skip: $ahead local commit(s) not on origin/$TRUNK; push or sort them out by hand"; return 0; fi
  if [ "$behind" = "0" ]; then say "current at $(git rev-parse --short HEAD)"; return 0; fi
  old="$(git rev-parse --short HEAD)"
  git merge -q --ff-only "origin/$TRUNK"
  say "updated $old -> $(git rev-parse --short HEAD) ($behind commit(s))"
}

install() {
  mkdir -p "$UNITS"
  cat > "$UNITS/localdns-sync.service" <<UNIT
[Unit]
Description=Fast-forward the localDNS checkout to origin/$TRUNK

[Service]
Type=oneshot
ExecStart=/usr/bin/env bash $REPO/tools/laptop-sync.sh run
UNIT
  cat > "$UNITS/localdns-sync.timer" <<UNIT
[Unit]
Description=Keep the localDNS checkout current

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
UNIT
  systemctl --user daemon-reload
  systemctl --user enable --now localdns-sync.timer
  say "installed: timer every 15 minutes for $REPO"
}

case "${1:-}" in
  run) run ;;
  install) install ;;
  status) systemctl --user list-timers localdns-sync.timer --no-pager 2>/dev/null || true; tail -n 10 "$LOG" 2>/dev/null || echo "no log yet" ;;
  uninstall) systemctl --user disable --now localdns-sync.timer 2>/dev/null || true; rm -f "$UNITS"/localdns-sync.{service,timer}; say "uninstalled" ;;
  *) sed -n '2,12p' "$0"; exit 2 ;;
esac
