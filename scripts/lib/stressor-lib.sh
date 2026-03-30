#!/bin/bash
# stressor-lib.sh — Shared helpers for stressor harvesting
set -euo pipefail

# PyYAML dependency guard (for callers that source this lib and use python3+yaml)
_check_pyyaml() {
  if ! python3 -c "import yaml" 2>/dev/null; then
    echo "ERROR: PyYAML not installed. Run: pip3 install pyyaml" >&2
    return 1
  fi
}

# compute_sampling_seed <task_id>
# Returns a float in [0, 1) derived deterministically from sha256(task_id).
# Uses the first 8 hex digits of the hash to ensure reproducibility.
compute_sampling_seed() {
  local task_id="$1"
  local hex
  hex=$(echo -n "$task_id" | shasum -a 256 | cut -c1-8)
  python3 -c "print(int('$hex', 16) / 0xFFFFFFFF)"
}

# evaluate_fft15 <budget_state> <clean_streak> <has_complex_security> <profile> <seed> <rules_file>
#
# Arguments:
#   budget_state          — "ok" | "warning" | "depleted"
#   clean_streak          — integer: consecutive tasks with zero escapes
#   has_complex_security  — "true" | "false": bead is complex + security-sensitive
#   profile               — bead type string (e.g. INVESTIGATE, EVOLVE, BUILD, ...)
#   seed                  — float [0,1) from compute_sampling_seed
#   rules_file            — path to stressor-rules.yaml (sampling rates)
#
# Returns one of: FULL | TARGETED | SAMPLED | ANTI_TURKEY | HORMETIC | SKIP
evaluate_fft15() {
  local budget_state="$1" clean_streak="$2" has_complex_security="$3" profile="$4" seed="$5" rules_file="${6:-}"

  # Read sampling rates from rules file (no hardcoded values)
  local sampled_rate anti_turkey_rate hormetic_rate clean_streak_threshold
  if [ -n "$rules_file" ] && [ -f "$rules_file" ]; then
    sampled_rate=$(python3 -c "import yaml; r=yaml.safe_load(open('$rules_file')); print(r.get('fft15_sampling',{}).get('sampled_rate', 0.50))" 2>/dev/null || echo "0.50")
    anti_turkey_rate=$(python3 -c "import yaml; r=yaml.safe_load(open('$rules_file')); print(r.get('fft15_sampling',{}).get('anti_turkey_rate', 0.30))" 2>/dev/null || echo "0.30")
    hormetic_rate=$(python3 -c "import yaml; r=yaml.safe_load(open('$rules_file')); print(r.get('fft15_sampling',{}).get('hormetic_rate', 0.10))" 2>/dev/null || echo "0.10")
    clean_streak_threshold=$(python3 -c "import yaml; r=yaml.safe_load(open('$rules_file')); print(r.get('fft15_sampling',{}).get('clean_streak_threshold', 5))" 2>/dev/null || echo "5")
  else
    # Fallback defaults (same as spec) — but callers should always pass rules_file
    sampled_rate="0.50"
    anti_turkey_rate="0.30"
    hormetic_rate="0.10"
    clean_streak_threshold="5"
  fi

  # Cue 1: INVESTIGATE or EVOLVE profile → SKIP (no stress on exploratory beads)
  if [[ "$profile" == "INVESTIGATE" || "$profile" == "EVOLVE" ]]; then
    echo "SKIP"
    return
  fi

  # Cue 2: budget DEPLETED → FULL stress (system is already failing; stress everything)
  if [[ "$budget_state" == "depleted" ]]; then
    echo "FULL"
    return
  fi

  # Cue 3: complex + security-sensitive bead → TARGETED stress
  if [[ "$has_complex_security" == "true" ]]; then
    echo "TARGETED"
    return
  fi

  # Cue 4: budget WARNING → SAMPLED at sampled_rate probability
  if [[ "$budget_state" == "warning" ]]; then
    if [ "$(echo "$seed < $sampled_rate" | bc -l)" -eq 1 ]; then
      echo "SAMPLED"
    else
      echo "SKIP"
    fi
    return
  fi

  # Cue 5: clean streak >= threshold → ANTI_TURKEY at anti_turkey_rate probability
  if [ "$clean_streak" -ge "$clean_streak_threshold" ]; then
    if [ "$(echo "$seed < $anti_turkey_rate" | bc -l)" -eq 1 ]; then
      echo "ANTI_TURKEY"
    else
      echo "SKIP"
    fi
    return
  fi

  # Cue 6: baseline HORMETIC sampling at hormetic_rate probability
  if [ "$(echo "$seed < $hormetic_rate" | bc -l)" -eq 1 ]; then
    echo "HORMETIC"
  else
    echo "SKIP"
  fi
}

# select_applicable_stressors <library_path> <cynefin_domain> <tags_csv>
#
# Matches stressor library entries against the bead's cynefin domain and tags.
# Prefers established stressors over provisional ones.
# Outputs YAML list of matching stressor ids to stdout.
select_applicable_stressors() {
  local library_path="$1" cynefin_domain="$2" tags_csv="$3"
  _check_pyyaml || return 1
  python3 - "$library_path" "$cynefin_domain" "$tags_csv" <<'PYEOF'
import sys, yaml

library_path, cynefin_domain, tags_csv = sys.argv[1], sys.argv[2], sys.argv[3]
bead_tags = set(t.strip() for t in tags_csv.split(',') if t.strip())

with open(library_path) as f:
    lib = yaml.safe_load(f)

stressors = lib.get('stressors') or []
matched = []
for s in stressors:
    if s.get('lindy_status') == 'retired':
        continue
    aw = s.get('applicable_when', {})
    cynefin_match = not aw.get('cynefin') or cynefin_domain in aw['cynefin']
    tag_match = not aw.get('tags') or bool(bead_tags & set(aw['tags']))
    if cynefin_match and tag_match:
        matched.append(s)

# Prefer established over provisional
matched.sort(key=lambda s: (0 if s.get('lindy_status') == 'established' else 1))

print(yaml.dump([{'id': s['id'], 'name': s['name'], 'lindy_status': s.get('lindy_status')} for s in matched]))
PYEOF
}

# compute_stress_yield <applied> <caught>
# Returns catch rate as a decimal (e.g. 0.75), or 0.0 if nothing was applied.
compute_stress_yield() {
  local applied="$1" caught="$2"
  if [ "$applied" -eq 0 ]; then
    echo "0.0"
    return
  fi
  echo "scale=2; $caught / $applied" | bc
}

# compute_lindy_transition <lindy_status> <times_applied> <catch_rate> <last5_misses>
#
# Arguments:
#   lindy_status   — "provisional" | "established" | "retired"
#   times_applied  — integer
#   catch_rate     — float (0.0–1.0) or "null"
#   last5_misses   — integer: number of misses in last 5 applications (0–5)
#
# Outputs one of: promote | retire | unchanged
compute_lindy_transition() {
  local lindy_status="$1" times_applied="$2" catch_rate="$3" last5_misses="$4"

  case "$lindy_status" in
    provisional)
      if [ "$times_applied" -ge 3 ] && [ "$catch_rate" != "null" ] && \
         [ "$(echo "$catch_rate > 0" | bc -l)" -eq 1 ]; then
        echo "promote"
        return
      fi
      if [ "$times_applied" -ge 5 ] && ( [ "$catch_rate" = "null" ] || \
         [ "$(echo "$catch_rate == 0" | bc -l)" -eq 1 ] ); then
        echo "retire"
        return
      fi
      ;;
    established)
      if [ "$times_applied" -ge 10 ] && [ "$last5_misses" -eq 5 ]; then
        echo "retire"
        return
      fi
      ;;
  esac

  echo "unchanged"
}

# now_utc
# Outputs current UTC time in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
