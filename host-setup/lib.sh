STATE_DIR="${STATE_DIR:-/var/lib/backendai-coco}"
LEDGER="${LEDGER:-$STATE_DIR/change-ledger}"

_c() { [[ -t 2 ]] && printf '\033[%sm' "$1" >&2 || true; }
info() { _c 0; printf 'coco: %s\n' "$*" >&2; }
ok() { _c 32; printf 'coco: [ok]   %s\n' "$*" >&2; _c 0; }
warn() { _c 33; printf 'coco: [warn] %s\n' "$*" >&2; _c 0; }
bad() { _c 31; printf 'coco: [fail] %s\n' "$*" >&2; _c 0; }
die() { bad "$*"; exit 1; }

as_root() {
    [[ $(id -u) -eq 0 ]] && return 0
    die "must run as root"
}

ledger() {
    mkdir -p "$(dirname "$LEDGER")"
    printf '%s\t%s\t%s\n' "$(date +%FT%T%z)" "${SUDO_USER:-$(id -un)}" "$*" >>"$LEDGER"
}

done_marker() { printf '%s/steps/%s' "$STATE_DIR" "$1"; }

step_done() { [[ -e $(done_marker "$1") ]]; }

mark_done() {
    mkdir -p "$STATE_DIR/steps"
    date +%FT%T%z >"$(done_marker "$1")"
}

step() {
    local name=$1
    if "check_$name"; then
        ok "$name (satisfied)"
        step_done "$name" || mark_done "$name"
        return 0
    fi
    if step_done "$name"; then
        warn "$name was applied on $(cat "$(done_marker "$name")") but its check no longer passes"
    fi
    if [[ ${DRY_RUN:-0} == 1 ]]; then
        warn "$name would run"
        return 0
    fi
    info "$name running"
    "apply_$name"
    "check_$name" || die "$name applied but its check still fails"
    ledger "step $name applied"
    mark_done "$name"
    ok "$name applied"
}

confirm_exact() {
    local phrase=$1 typed
    [[ -t 0 && -t 1 ]] || die "refusing: this action needs an interactive terminal"
    printf 'Type exactly the following phrase to proceed, or anything else to abort:\n  %s\n> ' "$phrase"
    IFS= read -r typed || die "no answer given; nothing was done"
    [[ $typed == "$phrase" ]] || die "phrase did not match; nothing was done"
}
