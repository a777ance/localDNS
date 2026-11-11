# nftables volume layer — deploy checklist

Moved here from `CLAUDE.md` section F on 2026-11-11 (DEC-013), unchanged. `CLAUDE.md` § F points here.

Run this once on the t630 to stand up per-category byte accounting. All four
steps can be done in one SSH session.

```bash
# 1. Copy the collect tools to the box (from your machine)
scp -r docs/statements/tools/collect/ user@192.168.1.118:~/a777ance/collect/

# 2. Load the accounting ruleset (idempotent — safe to re-run)
sudo nft -f ~/a777ance/collect/nftables-accounting.nft
sudo nft list table inet a777acct          # sets + counters exist, all zero — expected

# 3. Dry-run the set populator (resolves DNS, touches nothing)
python3 ~/a777ance/collect/populate_sets.py | head

# 4. Apply for real (programs the IP sets; counters start counting)
sudo python3 ~/a777ance/collect/populate_sets.py --apply
sudo nft -j list counters table inet a777acct   # should show non-zero bytes within minutes

# 5. Add to ROOT's cron (sudo crontab -e) — see the note below on why root
sudo install -d -m 755 /var/log/a777ance
# refresh IP sets every 6h (CDN IPs rotate; elements time out in 24h)
3 */6 * * *  /usr/bin/python3 /home/USER/a777ance/collect/populate_sets.py --apply >>/var/log/a777ance/populate-sets.log 2>&1
# collect monthly stats nightly
30 0 * * *   /usr/bin/python3 /home/USER/a777ance/collect/collect_stats.py \
             --out /var/lib/a777ance/$(date +\%Y-\%m).stats.json >>/var/log/a777ance/collect-stats.log 2>&1
```

Replace `USER` with the actual username on the t630. After the cron runs once,
verify with: `sudo nft -j list counters table inet a777acct`

**Both jobs belong in `sudo crontab -e` (root's), not the login user's, and they log
to a file rather than `/dev/null`.** Every source they touch is root-only:
`populate_sets.py --apply` programs the nft sets, and `collect_stats.py` reads
`/etc/pihole/pihole-FTL.db`, runs `nft -j list counters` and `wg show`, and writes
`/var/lib/a777ance`. Installed as the login user, both fail **silently** — the IP sets
stop refreshing, their 24h element timeout ages them out, and the counters decay
toward zero while the statement pipeline keeps reading them as measured fact. That is
the honesty rule failing closed in the wrong direction, so the failure has to be
loud: `tail /var/log/a777ance/*.log` after the first scheduled run.
`tools/deploy-volume-layer.sh` installs it this way for you.

**Uptime Kuma's `/metrics` is authenticated** — `collect_stats.py --kuma-key` defaults
to empty, so an unkeyed run gets `HTTP 401` and `uptime`/`latency_ms` come back `null`
no matter which user runs it. That is two of the four figures a Statement prints. The
key lives in `/etc/a777ance/collect.env` (`chmod 600`, git-ignored by living off-repo,
created empty by the deploy helper); mint one in Kuma under *Settings → API Keys* and
fill it in, or the uptime figure has to be **omitted** from the Statement rather than
guessed.
