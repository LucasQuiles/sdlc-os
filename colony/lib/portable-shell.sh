#!/bin/bash

path_size_bytes() {
  local target="${1:?path_size_bytes: path required}"
  local kibibytes
  kibibytes="$(du -sk "$target" | awk 'NR == 1 { print $1 }')"
  [[ "$kibibytes" =~ ^[0-9]+$ ]] || return 1
  printf '%s\n' "$((kibibytes * 1024))"
}

make_temp_file() {
  local prefix="${1:?make_temp_file: prefix required}"
  mktemp "${TMPDIR:-/tmp}/${prefix}.XXXXXX"
}
