#!/bin/bash
# Retire every stale claude/* branch across the A777ance portfolio.
#
# SAFE BY CONSTRUCTION: every commit that existed only on one of these branches is
# already reachable from doom-drawer/2026-08-08 in the same repo, pushed 2026-08-08.
# Deleting them loses no history.
#
# THE DOOM DRAWER — "Didn't Organize, Only Moved". The ADHD filing trick applied to git
# refs: one drawer you can stuff things into without sorting them, exactly so nothing has
# to be thrown out to get the desk clear. The drawer is KEPT. This script empties the
# desk around it.
#
#   inspect : git log --oneline doom-drawer/2026-08-08 --not origin/Yggdrasil
#   restore : git branch <name> <sha>
#
# Generated because branch deletion is blocked (HTTP 403) from the agent environment.
set -u
FAIL=0

echo '=== Azure-lab (9 branches) ==='
cd "$(dirname "$0")/../Azure-lab" 2>/dev/null || cd ~/Azure-lab || { echo 'skip Azure-lab'; FAIL=1; }
git push origin --delete 'claude/ai-cto-architecture-MZ2NF' || FAIL=1
git push origin --delete 'claude/code-review-distillation-ti8h8a' || FAIL=1
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/eager-ptolemy-sk6d50' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/exciting-mccarthy-bq9R0' || FAIL=1
git push origin --delete 'claude/jolly-tesla-PQDGb' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1
git push origin --delete 'claude/stoic-ride-bcm0ln' || FAIL=1

echo '=== Chronikomicon (7 branches) ==='
cd "$(dirname "$0")/../Chronikomicon" 2>/dev/null || cd ~/Chronikomicon || { echo 'skip Chronikomicon'; FAIL=1; }
git push origin --delete 'claude/admiring-hopper-iiOIu' || FAIL=1
git push origin --delete 'claude/affectionate-knuth-bcm0ln' || FAIL=1
git push origin --delete 'claude/bifrost-notation-qa-78yp9b' || FAIL=1
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/exciting-mccarthy-bq9R0' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1

echo '=== DESIGN-Full-Workflow-Integration-end-to-end- (229 branches) ==='
cd "$(dirname "$0")/../DESIGN-Full-Workflow-Integration-end-to-end-" 2>/dev/null || cd ~/DESIGN-Full-Workflow-Integration-end-to-end- || { echo 'skip DESIGN-Full-Workflow-Integration-end-to-end-'; FAIL=1; }
git push origin --delete 'claude/ai-cto-architecture-MZ2NF' || FAIL=1
git push origin --delete 'claude/beautiful-mccarthy-RrX8A' || FAIL=1
git push origin --delete 'claude/busy-johnson-098d2q' || FAIL=1
git push origin --delete 'claude/busy-johnson-09us0s' || FAIL=1
git push origin --delete 'claude/busy-johnson-0eineo' || FAIL=1
git push origin --delete 'claude/busy-johnson-0f1nsb' || FAIL=1
git push origin --delete 'claude/busy-johnson-0ny3la' || FAIL=1
git push origin --delete 'claude/busy-johnson-0um0rn' || FAIL=1
git push origin --delete 'claude/busy-johnson-0uq6zd' || FAIL=1
git push origin --delete 'claude/busy-johnson-14t8u5' || FAIL=1
git push origin --delete 'claude/busy-johnson-166hth' || FAIL=1
git push origin --delete 'claude/busy-johnson-17j0v7' || FAIL=1
git push origin --delete 'claude/busy-johnson-1a02ay' || FAIL=1
git push origin --delete 'claude/busy-johnson-1f60nd' || FAIL=1
git push origin --delete 'claude/busy-johnson-1h7kak' || FAIL=1
git push origin --delete 'claude/busy-johnson-2332rs' || FAIL=1
git push origin --delete 'claude/busy-johnson-23jrno' || FAIL=1
git push origin --delete 'claude/busy-johnson-28cgkz' || FAIL=1
git push origin --delete 'claude/busy-johnson-2b31ug' || FAIL=1
git push origin --delete 'claude/busy-johnson-2ei76d' || FAIL=1
git push origin --delete 'claude/busy-johnson-2t2jpt' || FAIL=1
git push origin --delete 'claude/busy-johnson-33ae6j' || FAIL=1
git push origin --delete 'claude/busy-johnson-33nrew' || FAIL=1
git push origin --delete 'claude/busy-johnson-35jyp0' || FAIL=1
git push origin --delete 'claude/busy-johnson-35mlvt' || FAIL=1
git push origin --delete 'claude/busy-johnson-3cb0co' || FAIL=1
git push origin --delete 'claude/busy-johnson-3ehmdd' || FAIL=1
git push origin --delete 'claude/busy-johnson-3nnol1' || FAIL=1
git push origin --delete 'claude/busy-johnson-3ocb6f' || FAIL=1
git push origin --delete 'claude/busy-johnson-3q6ilk' || FAIL=1
git push origin --delete 'claude/busy-johnson-3v0zpa' || FAIL=1
git push origin --delete 'claude/busy-johnson-49v0bb' || FAIL=1
git push origin --delete 'claude/busy-johnson-4ejcqr' || FAIL=1
git push origin --delete 'claude/busy-johnson-53g69v' || FAIL=1
git push origin --delete 'claude/busy-johnson-5w5b6n' || FAIL=1
git push origin --delete 'claude/busy-johnson-60ms2f' || FAIL=1
git push origin --delete 'claude/busy-johnson-63dwrs' || FAIL=1
git push origin --delete 'claude/busy-johnson-6ai2v5' || FAIL=1
git push origin --delete 'claude/busy-johnson-6eqamc' || FAIL=1
git push origin --delete 'claude/busy-johnson-6i8rt0' || FAIL=1
git push origin --delete 'claude/busy-johnson-6j5p20' || FAIL=1
git push origin --delete 'claude/busy-johnson-6kg7yl' || FAIL=1
git push origin --delete 'claude/busy-johnson-6wdjkd' || FAIL=1
git push origin --delete 'claude/busy-johnson-715wa4' || FAIL=1
git push origin --delete 'claude/busy-johnson-7ezyzb' || FAIL=1
git push origin --delete 'claude/busy-johnson-7qfpyp' || FAIL=1
git push origin --delete 'claude/busy-johnson-7qptw8' || FAIL=1
git push origin --delete 'claude/busy-johnson-7s3tni' || FAIL=1
git push origin --delete 'claude/busy-johnson-7we5vh' || FAIL=1
git push origin --delete 'claude/busy-johnson-83gswq' || FAIL=1
git push origin --delete 'claude/busy-johnson-8e1hpl' || FAIL=1
git push origin --delete 'claude/busy-johnson-8f2okn' || FAIL=1
git push origin --delete 'claude/busy-johnson-8lp3kd' || FAIL=1
git push origin --delete 'claude/busy-johnson-8oxmfh' || FAIL=1
git push origin --delete 'claude/busy-johnson-8rj624' || FAIL=1
git push origin --delete 'claude/busy-johnson-8vx7z0' || FAIL=1
git push origin --delete 'claude/busy-johnson-8xgqb6' || FAIL=1
git push origin --delete 'claude/busy-johnson-90oe2a' || FAIL=1
git push origin --delete 'claude/busy-johnson-91oh4e' || FAIL=1
git push origin --delete 'claude/busy-johnson-92z349' || FAIL=1
git push origin --delete 'claude/busy-johnson-93vynn' || FAIL=1
git push origin --delete 'claude/busy-johnson-96h8pa' || FAIL=1
git push origin --delete 'claude/busy-johnson-9sfsv0' || FAIL=1
git push origin --delete 'claude/busy-johnson-9vlbcs' || FAIL=1
git push origin --delete 'claude/busy-johnson-9ylrmk' || FAIL=1
git push origin --delete 'claude/busy-johnson-a0r50k' || FAIL=1
git push origin --delete 'claude/busy-johnson-a6lfmg' || FAIL=1
git push origin --delete 'claude/busy-johnson-alv5v0' || FAIL=1
git push origin --delete 'claude/busy-johnson-aw8puk' || FAIL=1
git push origin --delete 'claude/busy-johnson-b6g46u' || FAIL=1
git push origin --delete 'claude/busy-johnson-b7ec0l' || FAIL=1
git push origin --delete 'claude/busy-johnson-b7xho8' || FAIL=1
git push origin --delete 'claude/busy-johnson-bn2hpe' || FAIL=1
git push origin --delete 'claude/busy-johnson-c0jpbb' || FAIL=1
git push origin --delete 'claude/busy-johnson-c9drqr' || FAIL=1
git push origin --delete 'claude/busy-johnson-c9z4ag' || FAIL=1
git push origin --delete 'claude/busy-johnson-co4cf8' || FAIL=1
git push origin --delete 'claude/busy-johnson-cz6ku8' || FAIL=1
git push origin --delete 'claude/busy-johnson-d0hmz7' || FAIL=1
git push origin --delete 'claude/busy-johnson-d7msc0' || FAIL=1
git push origin --delete 'claude/busy-johnson-dfqni7' || FAIL=1
git push origin --delete 'claude/busy-johnson-dlf2wz' || FAIL=1
git push origin --delete 'claude/busy-johnson-dmhcoc' || FAIL=1
git push origin --delete 'claude/busy-johnson-dnjlau' || FAIL=1
git push origin --delete 'claude/busy-johnson-dwp32m' || FAIL=1
git push origin --delete 'claude/busy-johnson-e1fwfm' || FAIL=1
git push origin --delete 'claude/busy-johnson-e1wpb5' || FAIL=1
git push origin --delete 'claude/busy-johnson-e3jxvm' || FAIL=1
git push origin --delete 'claude/busy-johnson-ebtle0' || FAIL=1
git push origin --delete 'claude/busy-johnson-ecy40q' || FAIL=1
git push origin --delete 'claude/busy-johnson-edyiw4' || FAIL=1
git push origin --delete 'claude/busy-johnson-eeiw8s' || FAIL=1
git push origin --delete 'claude/busy-johnson-eqd9gq' || FAIL=1
git push origin --delete 'claude/busy-johnson-et3vws' || FAIL=1
git push origin --delete 'claude/busy-johnson-eut0er' || FAIL=1
git push origin --delete 'claude/busy-johnson-euu92t' || FAIL=1
git push origin --delete 'claude/busy-johnson-f26o9c' || FAIL=1
git push origin --delete 'claude/busy-johnson-f36gep' || FAIL=1
git push origin --delete 'claude/busy-johnson-f3fsb3' || FAIL=1
git push origin --delete 'claude/busy-johnson-fkyxtr' || FAIL=1
git push origin --delete 'claude/busy-johnson-fnbwpp' || FAIL=1
git push origin --delete 'claude/busy-johnson-fxw144' || FAIL=1
git push origin --delete 'claude/busy-johnson-g11ez1' || FAIL=1
git push origin --delete 'claude/busy-johnson-gas70f' || FAIL=1
git push origin --delete 'claude/busy-johnson-gd0cy0' || FAIL=1
git push origin --delete 'claude/busy-johnson-gncw9y' || FAIL=1
git push origin --delete 'claude/busy-johnson-gqu7rl' || FAIL=1
git push origin --delete 'claude/busy-johnson-gsea9h' || FAIL=1
git push origin --delete 'claude/busy-johnson-gvdhk5' || FAIL=1
git push origin --delete 'claude/busy-johnson-gx4wi5' || FAIL=1
git push origin --delete 'claude/busy-johnson-h14xln' || FAIL=1
git push origin --delete 'claude/busy-johnson-h3hhg2' || FAIL=1
git push origin --delete 'claude/busy-johnson-h59nz0' || FAIL=1
git push origin --delete 'claude/busy-johnson-hco4o2' || FAIL=1
git push origin --delete 'claude/busy-johnson-hjxog2' || FAIL=1
git push origin --delete 'claude/busy-johnson-i5iogn' || FAIL=1
git push origin --delete 'claude/busy-johnson-iill68' || FAIL=1
git push origin --delete 'claude/busy-johnson-irzbz8' || FAIL=1
git push origin --delete 'claude/busy-johnson-itpb6t' || FAIL=1
git push origin --delete 'claude/busy-johnson-jgxzvk' || FAIL=1
git push origin --delete 'claude/busy-johnson-jh48ej' || FAIL=1
git push origin --delete 'claude/busy-johnson-jhdu1g' || FAIL=1
git push origin --delete 'claude/busy-johnson-jlwk4t' || FAIL=1
git push origin --delete 'claude/busy-johnson-jmvtgr' || FAIL=1
git push origin --delete 'claude/busy-johnson-jwzcbd' || FAIL=1
git push origin --delete 'claude/busy-johnson-jx7wl7' || FAIL=1
git push origin --delete 'claude/busy-johnson-k425b4' || FAIL=1
git push origin --delete 'claude/busy-johnson-kazouo' || FAIL=1
git push origin --delete 'claude/busy-johnson-kqemh1' || FAIL=1
git push origin --delete 'claude/busy-johnson-kvw72r' || FAIL=1
git push origin --delete 'claude/busy-johnson-ky4d9i' || FAIL=1
git push origin --delete 'claude/busy-johnson-l4relp' || FAIL=1
git push origin --delete 'claude/busy-johnson-lakpgi' || FAIL=1
git push origin --delete 'claude/busy-johnson-lboyf9' || FAIL=1
git push origin --delete 'claude/busy-johnson-m15vjx' || FAIL=1
git push origin --delete 'claude/busy-johnson-muz02a' || FAIL=1
git push origin --delete 'claude/busy-johnson-mzb4eh' || FAIL=1
git push origin --delete 'claude/busy-johnson-nlrvzd' || FAIL=1
git push origin --delete 'claude/busy-johnson-nn2ieq' || FAIL=1
git push origin --delete 'claude/busy-johnson-ntbxco' || FAIL=1
git push origin --delete 'claude/busy-johnson-ntv9q8' || FAIL=1
git push origin --delete 'claude/busy-johnson-o3mju5' || FAIL=1
git push origin --delete 'claude/busy-johnson-o5gqpj' || FAIL=1
git push origin --delete 'claude/busy-johnson-ohcze6' || FAIL=1
git push origin --delete 'claude/busy-johnson-okhyy2' || FAIL=1
git push origin --delete 'claude/busy-johnson-oncm08' || FAIL=1
git push origin --delete 'claude/busy-johnson-oruosz' || FAIL=1
git push origin --delete 'claude/busy-johnson-oye00d' || FAIL=1
git push origin --delete 'claude/busy-johnson-oz98im' || FAIL=1
git push origin --delete 'claude/busy-johnson-p0h3px' || FAIL=1
git push origin --delete 'claude/busy-johnson-p0qwg5' || FAIL=1
git push origin --delete 'claude/busy-johnson-p2db0d' || FAIL=1
git push origin --delete 'claude/busy-johnson-phlphv' || FAIL=1
git push origin --delete 'claude/busy-johnson-pjms5u' || FAIL=1
git push origin --delete 'claude/busy-johnson-pnvle2' || FAIL=1
git push origin --delete 'claude/busy-johnson-poz5xr' || FAIL=1
git push origin --delete 'claude/busy-johnson-psxffw' || FAIL=1
git push origin --delete 'claude/busy-johnson-q0qprp' || FAIL=1
git push origin --delete 'claude/busy-johnson-q5tl6d' || FAIL=1
git push origin --delete 'claude/busy-johnson-qbge01' || FAIL=1
git push origin --delete 'claude/busy-johnson-qg0sjg' || FAIL=1
git push origin --delete 'claude/busy-johnson-qgcqhi' || FAIL=1
git push origin --delete 'claude/busy-johnson-qivpi6' || FAIL=1
git push origin --delete 'claude/busy-johnson-qkb7gq' || FAIL=1
git push origin --delete 'claude/busy-johnson-r1b4p7' || FAIL=1
git push origin --delete 'claude/busy-johnson-rkvi8t' || FAIL=1
git push origin --delete 'claude/busy-johnson-rww4cu' || FAIL=1
git push origin --delete 'claude/busy-johnson-rxns5d' || FAIL=1
git push origin --delete 'claude/busy-johnson-s6foi6' || FAIL=1
git push origin --delete 'claude/busy-johnson-silmj3' || FAIL=1
git push origin --delete 'claude/busy-johnson-sk6d50' || FAIL=1
git push origin --delete 'claude/busy-johnson-sldgiw' || FAIL=1
git push origin --delete 'claude/busy-johnson-spj70m' || FAIL=1
git push origin --delete 'claude/busy-johnson-sruhtj' || FAIL=1
git push origin --delete 'claude/busy-johnson-sxpzom' || FAIL=1
git push origin --delete 'claude/busy-johnson-t08se1' || FAIL=1
git push origin --delete 'claude/busy-johnson-t5s7qi' || FAIL=1
git push origin --delete 'claude/busy-johnson-tb99jj' || FAIL=1
git push origin --delete 'claude/busy-johnson-tpxpsw' || FAIL=1
git push origin --delete 'claude/busy-johnson-tt20jr' || FAIL=1
git push origin --delete 'claude/busy-johnson-tx5zwx' || FAIL=1
git push origin --delete 'claude/busy-johnson-u6n1vt' || FAIL=1
git push origin --delete 'claude/busy-johnson-uj9bd6' || FAIL=1
git push origin --delete 'claude/busy-johnson-uu721r' || FAIL=1
git push origin --delete 'claude/busy-johnson-v3ubcf' || FAIL=1
git push origin --delete 'claude/busy-johnson-vj7iqw' || FAIL=1
git push origin --delete 'claude/busy-johnson-vrsww6' || FAIL=1
git push origin --delete 'claude/busy-johnson-vxb82u' || FAIL=1
git push origin --delete 'claude/busy-johnson-w17wcw' || FAIL=1
git push origin --delete 'claude/busy-johnson-wia1b2' || FAIL=1
git push origin --delete 'claude/busy-johnson-wt5zqv' || FAIL=1
git push origin --delete 'claude/busy-johnson-x6bma1' || FAIL=1
git push origin --delete 'claude/busy-johnson-x8yzx9' || FAIL=1
git push origin --delete 'claude/busy-johnson-xii62w' || FAIL=1
git push origin --delete 'claude/busy-johnson-xn9nhk' || FAIL=1
git push origin --delete 'claude/busy-johnson-xr66lq' || FAIL=1
git push origin --delete 'claude/busy-johnson-y1hede' || FAIL=1
git push origin --delete 'claude/busy-johnson-y6ygb8' || FAIL=1
git push origin --delete 'claude/busy-johnson-y8xo97' || FAIL=1
git push origin --delete 'claude/busy-johnson-yb40pl' || FAIL=1
git push origin --delete 'claude/busy-johnson-yui5m4' || FAIL=1
git push origin --delete 'claude/busy-johnson-zaqieh' || FAIL=1
git push origin --delete 'claude/code-review-distillation-ti8h8a' || FAIL=1
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/elegant-sagan-plx5ms' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-06lewn' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-3cmlhl' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-4uagvy' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-5vvg7n' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-77jcvz' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-7e8sas' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-83q97r' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-892iji' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-8lewt4' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-bcm0ln' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-du7qvj' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-i4wuqk' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-mj319b' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-nvnxnt' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-qw4hbo' || FAIL=1
git push origin --delete 'claude/eloquent-bardeen-wzcmfb' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/exciting-mccarthy-bq9R0' || FAIL=1
git push origin --delete 'claude/funny-bohr-xv1ir' || FAIL=1
git push origin --delete 'claude/llm-self-hosting-factcheck-vdzVH' || FAIL=1
git push origin --delete 'claude/nifty-carson-Je7aG' || FAIL=1
git push origin --delete 'claude/os-choice-project-setup-AntEJ' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1
git push origin --delete 'claude/vigilant-curie-McPcX' || FAIL=1

echo '=== Home-Sovereign-Full-Field-Guide (4 branches) ==='
cd "$(dirname "$0")/../Home-Sovereign-Full-Field-Guide" 2>/dev/null || cd ~/Home-Sovereign-Full-Field-Guide || { echo 'skip Home-Sovereign-Full-Field-Guide'; FAIL=1; }
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/pihole-unbound-dns-config-2h5j5f' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1

echo '=== MARKETING (13 branches) ==='
cd "$(dirname "$0")/../MARKETING" 2>/dev/null || cd ~/MARKETING || { echo 'skip MARKETING'; FAIL=1; }
git push origin --delete 'claude/ai-cto-architecture-MZ2NF' || FAIL=1
git push origin --delete 'claude/code-review-distillation-ti8h8a' || FAIL=1
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/eager-brown-MebMh' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/exciting-mccarthy-bq9R0' || FAIL=1
git push origin --delete 'claude/funny-bohr-xv1ir' || FAIL=1
git push origin --delete 'claude/keen-hamilton-sk6d50' || FAIL=1
git push origin --delete 'claude/master-amounts-calculator-okqphz' || FAIL=1
git push origin --delete 'claude/modest-newton-bcm0ln' || FAIL=1
git push origin --delete 'claude/nifty-carson-Je7aG' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1
git push origin --delete 'claude/vigilant-curie-McPcX' || FAIL=1

echo '=== Marketing-Strategy-1 (3 branches) ==='
cd "$(dirname "$0")/../Marketing-Strategy-1" 2>/dev/null || cd ~/Marketing-Strategy-1 || { echo 'skip Marketing-Strategy-1'; FAIL=1; }
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1

echo '=== PRICING-MODELS---ALL-THREE (3 branches) ==='
cd "$(dirname "$0")/../PRICING-MODELS---ALL-THREE" 2>/dev/null || cd ~/PRICING-MODELS---ALL-THREE || { echo 'skip PRICING-MODELS---ALL-THREE'; FAIL=1; }
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1

echo '=== claude-code-homelab (13 branches) ==='
cd "$(dirname "$0")/../claude-code-homelab" 2>/dev/null || cd ~/claude-code-homelab || { echo 'skip claude-code-homelab'; FAIL=1; }
git push origin --delete 'claude/admiring-hopper-iiOIu' || FAIL=1
git push origin --delete 'claude/adoring-lamport-q2zjae' || FAIL=1
git push origin --delete 'claude/adoring-lamport-sk6d50' || FAIL=1
git push origin --delete 'claude/adoring-lamport-t5qquv' || FAIL=1
git push origin --delete 'claude/ai-cto-architecture-MZ2NF' || FAIL=1
git push origin --delete 'claude/cleanup-consolidation-7SEt4' || FAIL=1
git push origin --delete 'claude/code-review-distillation-ti8h8a' || FAIL=1
git push origin --delete 'claude/cool-ritchie-bcm0ln' || FAIL=1
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/exciting-mccarthy-bq9R0' || FAIL=1
git push origin --delete 'claude/jolly-tesla-PQDGb' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1

echo '=== customers (8 branches) ==='
cd "$(dirname "$0")/../customers" 2>/dev/null || cd ~/customers || { echo 'skip customers'; FAIL=1; }
git push origin --delete 'claude/amazing-johnson-ARAwI' || FAIL=1
git push origin --delete 'claude/blissful-galileo-sk6d50' || FAIL=1
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/determined-planck-z1jipm' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/exciting-mccarthy-bq9R0' || FAIL=1
git push origin --delete 'claude/optimistic-keller-bcm0ln' || FAIL=1
git push origin --delete 'claude/repos-harness-policies-sync-k0vxl3' || FAIL=1

echo '=== localDNS (49 branches) ==='
cd "$(dirname "$0")/../localDNS" 2>/dev/null || cd ~/localDNS || { echo 'skip localDNS'; FAIL=1; }
git push origin --delete 'claude/ai-cto-architecture-MZ2NF' || FAIL=1
git push origin --delete 'claude/amwins-ai-governance-vu5tk4' || FAIL=1
git push origin --delete 'claude/awesome-archimedes-8lp3kd' || FAIL=1
git push origin --delete 'claude/awesome-archimedes-sk6d50' || FAIL=1
git push origin --delete 'claude/azure-ai-engineer-handoff-bxa6e0' || FAIL=1
git push origin --delete 'claude/bifrost-notation-qa-78yp9b' || FAIL=1
git push origin --delete 'claude/bootstrap-paradox-tr3hbk' || FAIL=1
git push origin --delete 'claude/chronikon-architecture-j9etjz' || FAIL=1
git push origin --delete 'claude/code-cheatsheet-mp9eyb' || FAIL=1
git push origin --delete 'claude/confident-lovelace-onCcf' || FAIL=1
git push origin --delete 'claude/custom-superhuman-docs-8sqk6o' || FAIL=1
git push origin --delete 'claude/deepseek-compute-heat-Fx2Xs' || FAIL=1
git push origin --delete 'claude/default-next-actions-f52saf' || FAIL=1
git push origin --delete 'claude/design-workflow-integration-y8yxx7' || FAIL=1
git push origin --delete 'claude/doctor-command-wac24w' || FAIL=1
git push origin --delete 'claude/eager-maxwell-p5c3jk' || FAIL=1
git push origin --delete 'claude/egress-overview-hslrn1' || FAIL=1
git push origin --delete 'claude/empty-session-7zo8ht' || FAIL=1
git push origin --delete 'claude/exciting-euler-bukqdd' || FAIL=1
git push origin --delete 'claude/exciting-mccarthy-bq9R0' || FAIL=1
git push origin --delete 'claude/festive-maxwell-ab0dmq' || FAIL=1
git push origin --delete 'claude/festive-maxwell-bcm0ln' || FAIL=1
git push origin --delete 'claude/firewalla-network-reachability-526v8h' || FAIL=1
git push origin --delete 'claude/firewalla-purple-se-d7r9hd' || FAIL=1
git push origin --delete 'claude/gallant-brown-CVXM7' || FAIL=1
git push origin --delete 'claude/github-pages-gemini-access-ahu8fw' || FAIL=1
git push origin --delete 'claude/homelab-microbiology-metaphors-18cl3d' || FAIL=1
git push origin --delete 'claude/ingress-egress-hyperspace-e4e9zq' || FAIL=1
git push origin --delete 'claude/inspiring-fermi-FIdYr' || FAIL=1
git push origin --delete 'claude/langgraph-multi-agent-router-SzI4t' || FAIL=1
git push origin --delete 'claude/lazy-anchor-init-luqliv' || FAIL=1
git push origin --delete 'claude/linkedin-connected-apps-eval-sjsnns' || FAIL=1
git push origin --delete 'claude/localdns-home-network-s50zlk' || FAIL=1
git push origin --delete 'claude/lossless-clear-refeed-protocol-7ox7he' || FAIL=1
git push origin --delete 'claude/magical-cray-Vutb7' || FAIL=1
git push origin --delete 'claude/meta-audit-priorities-MzByf' || FAIL=1
git push origin --delete 'claude/mobile-apostrophe-bifrost-bug-8z598j' || FAIL=1
git push origin --delete 'claude/new-session-2eaco5' || FAIL=1
git push origin --delete 'claude/new-session-7vz2t7' || FAIL=1
git push origin --delete 'claude/new-session-nb82mn' || FAIL=1
git push origin --delete 'claude/new-session-yd2q4p' || FAIL=1
git push origin --delete 'claude/nifty-carson-Je7aG' || FAIL=1
git push origin --delete 'claude/pihole-unbound-dns-config-2h5j5f' || FAIL=1
git push origin --delete 'claude/project-structure-order-qnj1gp' || FAIL=1
git push origin --delete 'claude/relaxed-hamilton-Ic16v' || FAIL=1
git push origin --delete 'claude/session-5r2xlc' || FAIL=1
git push origin --delete 'claude/settings-alignment-dh8eua' || FAIL=1
git push origin --delete 'claude/vigilant-curie-McPcX' || FAIL=1
git push origin --delete 'claude/zip-handoff-mechanism-rnl3mo' || FAIL=1

# The drawer's old name. Same commit as doom-drawer/2026-08-08, so removing this
# label loses nothing — the drawer itself stays.
echo '=== retiring the superseded archive/ label ==='
for r in Azure-lab Chronikomicon DESIGN-Full-Workflow-Integration-end-to-end- \
         Home-Sovereign-Full-Field-Guide MARKETING Marketing-Strategy-1 \
         PRICING-MODELS---ALL-THREE claude-code-homelab customers localDNS; do
  ( cd ~/"$r" 2>/dev/null || exit 0
    git push origin --delete archive/claude-sessions-2026-08-08 2>/dev/null \
      && echo "  $r: old label removed" \
      || echo "  $r: no old label (fine)" )
done

exit $FAIL
