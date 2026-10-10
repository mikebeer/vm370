#!/usr/bin/env bash
# =========================================================================
#  Turbo CREXX CLI
#  A small Turbo-Pascal-style terminal front end for the REAL, open-source
#  CREXX compiler/VM toolchain (https://github.com/adesutherland/CREXX).
#
#  This script does not implement REXX itself -- it edits your .crexx file
#  with a real text editor and shells out to the genuine `crexx` driver
#  (rxc compiler -> rxas assembler -> rxvm/rxvme virtual machine) to
#  compile and run it. Nothing here is a reimplementation of the language.
# =========================================================================
set -u

# ---- Locate the bundled toolchain -------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"
CREXX="$BIN_DIR/crexx"

if [ ! -x "$CREXX" ]; then
  # fall back to a crexx already on PATH (e.g. installed system-wide)
  if command -v crexx >/dev/null 2>&1; then
    CREXX="$(command -v crexx)"
    BIN_DIR="$(dirname "$CREXX")"
  else
    echo "error: could not find the crexx toolchain."
    echo "Expected it bundled at: $BIN_DIR/crexx"
    echo "or available on PATH as 'crexx'."
    echo "See BUILD.md to build it from source for your platform."
    exit 1
  fi
fi

# ---- Colours (classic Turbo Pascal blue screen, degrades gracefully) --
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
  C_RESET="$(tput sgr0)"
  C_BLUEBG="$(tput setab 4)"
  C_WHITE="$(tput setaf 7)"
  C_YELLOW="$(tput bold; tput setaf 3)"
  C_CYAN="$(tput setaf 6)"
  C_RED="$(tput bold; tput setaf 1)"
  C_GREEN="$(tput setaf 2)"
  C_BOLD="$(tput bold)"
else
  C_RESET=""; C_BLUEBG=""; C_WHITE=""; C_YELLOW=""; C_CYAN=""; C_RED=""; C_GREEN=""; C_BOLD=""
fi

CURFILE="${1:-}"

banner() {
  clear 2>/dev/null || printf '\033c'
  printf '%s%s' "$C_BLUEBG" "$C_WHITE"
  echo "==============================================================="
  echo "  T U R B O   C R E X X   ---   powered by the real crexx toolchain"
  echo "==============================================================="
  printf '%s' "$C_RESET"
  echo
  if [ -n "$CURFILE" ]; then
    echo "  Current file: ${C_YELLOW}${CURFILE}${C_RESET}"
  else
    echo "  Current file: ${C_YELLOW}(none -- use N to create or O to open)${C_RESET}"
  fi
  echo
}

pause() {
  echo
  read -r -p "Press Enter to continue..." _
}

pick_editor() {
  if [ -n "${EDITOR:-}" ] && command -v "$EDITOR" >/dev/null 2>&1; then
    echo "$EDITOR"; return
  fi
  for e in nano vi vim; do
    if command -v "$e" >/dev/null 2>&1; then echo "$e"; return; fi
  done
  echo ""
}

new_file() {
  read -r -p "New file name (e.g. myprog.crexx): " name
  [ -z "$name" ] && return
  case "$name" in
    *.crexx|*.crx|*.rexx) : ;;
    *) name="$name.crexx" ;;
  esac
  if [ -e "$name" ]; then
    read -r -p "$name already exists. Overwrite? [y/N] " ok
    [ "$ok" != "y" ] && [ "$ok" != "Y" ] && return
  fi
  cat > "$name" <<'EOF'
options levelb
import rxfnsb

say "Hello, CREXX World!"
EOF
  CURFILE="$name"
  echo "Created $name"
}

open_file() {
  echo "Available .crexx/.crx/.rexx files here:"
  local files=(*.crexx *.crx *.rexx)
  local any=0
  for f in "${files[@]}"; do
    [ -e "$f" ] && { echo "  $f"; any=1; }
  done
  [ "$any" -eq 0 ] && echo "  (none found in $(pwd))"
  echo
  read -r -p "File to open: " name
  [ -z "$name" ] && return
  if [ ! -f "$name" ]; then
    echo "Not found: $name"
    return
  fi
  CURFILE="$name"
}

edit_file() {
  if [ -z "$CURFILE" ]; then
    echo "No file open yet -- use N (new) or O (open) first."
    return
  fi
  local ed
  ed="$(pick_editor)"
  if [ -z "$ed" ]; then
    echo "No terminal editor found (tried \$EDITOR, nano, vi, vim)."
    echo "Edit $CURFILE with any editor, then come back."
    return
  fi
  "$ed" "$CURFILE"
}

compile_only() {
  if [ -z "$CURFILE" ]; then
    echo "No file open yet -- use N (new) or O (open) first."
    return
  fi
  echo "Compiling $CURFILE ..."
  echo "-----------------------------------------------------------------"
  "$CREXX" -noexec "$CURFILE"
  local rc=$?
  echo "-----------------------------------------------------------------"
  if [ $rc -eq 0 ]; then
    echo "${C_GREEN}0 error(s).${C_RESET}"
  else
    echo "${C_RED}Compile failed (exit $rc). See messages above.${C_RESET}"
  fi
}

run_program() {
  if [ -z "$CURFILE" ]; then
    echo "No file open yet -- use N (new) or O (open) first."
    return
  fi
  echo "Compiling and running $CURFILE ..."
  echo "==================== program output ============================"
  "$CREXX" "$CURFILE"
  local rc=$?
  echo "==================================================================="
  echo "(exit code: $rc)"
}

show_help() {
  cat <<EOF

  Turbo CREXX CLI -- commands
  ----------------------------
  N  New file            O  Open file            E  Edit current file
  C  Compile (check only, no run)
  R  Run (compile + execute)
  L  List examples/      D  Show toolchain versions
  Q  Quit

  This wraps the real, open-source crexx toolchain:
    crexx   - driver (compile, assemble, link, run)
    rxc     - compiler (cREXX source -> .rxas)
    rxas    - assembler (.rxas -> .rxbin bytecode)
    rxvm/rxvme - virtual machine (executes .rxbin)

  Programs are written in Level B cREXX. A minimal header looks like:
    options levelb
    import rxfnsb

  See docs/ (bundled) or https://github.com/adesutherland/CREXX for the
  full language reference.
EOF
}

list_examples() {
  echo "Bundled examples:"
  if [ -d "$SCRIPT_DIR/examples" ]; then
    for f in "$SCRIPT_DIR/examples"/*; do
      [ -f "$f" ] && echo "  $f"
    done
    echo
    read -r -p "Copy one into the current directory? (filename or blank to skip): " pick
    if [ -n "$pick" ] && [ -f "$SCRIPT_DIR/examples/$pick" ]; then
      cp "$SCRIPT_DIR/examples/$pick" .
      CURFILE="$pick"
      echo "Copied. Current file is now $pick"
    fi
  else
    echo "  (no examples/ directory found)"
  fi
}

show_versions() {
  echo "crexx  : $("$CREXX" -version 2>&1 | head -1 | sed 's/\x1b\[[0-9;]*m//g')"
  [ -x "$BIN_DIR/rxc" ]  && echo "rxc    : $("$BIN_DIR/rxc" -v 2>&1 | head -1)"
  [ -x "$BIN_DIR/rxas" ] && echo "rxas   : present"
  [ -x "$BIN_DIR/rxvm" ] && echo "rxvm   : present"
}

# ---- Main loop ----------------------------------------------------------
while true; do
  banner
  echo "  [N] New   [O] Open   [E] Edit   [C] Compile   [R] Run"
  echo "  [L] Examples   [D] Versions   [H] Help   [Q] Quit"
  echo
  read -r -p "Command: " cmd || { echo; exit 0; }   # VM/370plus: end of input ends the menu
  case "$cmd" in
    [Nn]) new_file; pause ;;
    [Oo]) open_file; pause ;;
    [Ee]) edit_file ;;
    [Cc]) compile_only; pause ;;
    [Rr]) run_program; pause ;;
    [Ll]) list_examples; pause ;;
    [Dd]) show_versions; pause ;;
    [Hh]) show_help; pause ;;
    [Qq]) echo "Goodbye."; exit 0 ;;
    "") ;;
    *) echo "Unknown command: $cmd"; pause ;;
  esac
done
