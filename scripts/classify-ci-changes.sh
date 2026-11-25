#!/bin/sh
set -eu

usage() {
  echo 'usage: classify-ci-changes.sh --git <base-sha> <head-sha>' >&2
  echo '       classify-ci-changes.sh --files' >&2
  exit 2
}

classify_files() {
  _files="$1"
  if [ -z "$_files" ]; then
    run_ci=true
    return
  fi
  run_ci=false
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
      # README.md is packaged inside release archives; LICENSE/NOTICE are legal files.
      README.md|LICENSE*|*/LICENSE*|NOTICE*|*/NOTICE*|*THIRD_PARTY*|*LICENSES*)
        run_ci=true
        ;;
      AGENTS.md|RELEASING.md|CHANGELOG.md|docs/*.md|.github/ISSUE_TEMPLATE/*|.github/PULL_REQUEST_TEMPLATE.md)
        ;;
      *)
        run_ci=true
        ;;
    esac
  done <<EOF
$_files
EOF
}

mode="${1:-}"
run_ci=true

case "$mode" in
  --git)
    [ "$#" -eq 3 ] || usage
    merge_base="$(git merge-base "$2" "$3")"
    changed="$(git -c core.quotePath=false diff --no-renames --name-only "$merge_base" "$3")"
    classify_files "$changed"
    ;;
  --files)
    [ "$#" -eq 1 ] || usage
    changed="$(cat)"
    classify_files "$changed"
    ;;
  *)
    usage
    ;;
esac

printf 'run_ci=%s\n' "$run_ci"
