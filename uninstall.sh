#!/usr/bin/env bash
set -euo pipefail

TARGETS=(
  "/opt/homebrew/bin/legends"
  "/usr/local/bin/legends"
)

removed=0
for t in "${TARGETS[@]}"; do
  if [[ -x "$t" || -f "$t" ]]; then
    echo "Removing $t"
    if [[ -w "$(dirname "$t")" ]]; then
      rm -f "$t"
    else
      sudo rm -f "$t"
    fi
    removed=1
  fi
done

if [[ $removed -eq 0 ]]; then
  echo "No legends binary found in common locations."
else
  echo "Done."
fi
