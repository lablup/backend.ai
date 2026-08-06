#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f $HERE/.env ]]; then set -a; . "$HERE/.env"; set +a; fi
OVERLAY="${OVERLAY:-dev}"
INCUMBENT="${INCUMBENT:-trustee-kbs-1}"
RESERVED_PORTS="8080 8081 5000 18080 50000"

die() { printf 'broker: %s\n' "$*" >&2; exit 1; }
note() { printf 'broker: %s\n' "$*" >&2; }

compose() { docker compose -f "$HERE/compose.yaml" -f "$HERE/compose.$OVERLAY.yaml" "$@"; }

scheme() { [[ $OVERLAY == prod ]] && printf https || printf http; }
url() { printf '%s://127.0.0.1:%s' "$(scheme)" "${KBS_PORT:?set KBS_PORT}"; }

admin_curl() {
    local args=(-sS --fail-with-body)
    [[ $(scheme) == https ]] && args+=(--cacert "${PKI_DIR:?}/root/ca.crt")
    [[ -r $HERE/.local/admin-token ]] && args+=(-H "Authorization: Bearer $(<"$HERE/.local/admin-token")")
    curl "${args[@]}" "$@"
}

render_config() {
    local template="$HERE/config/kbs-config.$OVERLAY.toml" out="${BROKER_STATE:?}/kbs-config.toml"
    sed "s|KBS_LISTEN_PORT|${KBS_PORT:?}|" "$template" >"$out.new"
    grep -qF "0.0.0.0:${KBS_PORT}" "$out.new" || die "port substitution produced no listener line; refusing"
    if [[ $OVERLAY == prod ]] && grep -q InsecureAllowAll "$out.new"; then
        die "the production config admits unauthenticated administration; refusing"
    fi
    if cmp -s "$out.new" "$out" 2>/dev/null; then rm -f "$out.new"; else mv "$out.new" "$out"; note "config rendered"; fi
}

guard_port() {
    local port=${KBS_PORT:?} reserved
    for reserved in $RESERVED_PORTS; do
        [[ $port == "$reserved" ]] && die "port $port is spoken for on the rig; pick another"
    done
    ss -Hltn "sport = :$port" | grep -q . || return 0
    compose ps -q 2>/dev/null | grep -q . \
        || die "port $port is already bound by something outside this compose project"
}

cmd_up() {
    guard_port
    mkdir -p "${BROKER_STATE:?}"/{storage,token,admin,backup}
    render_config
    compose up -d
    note "broker up on $(url) under project ${BROKER_PROJECT}"
}

cmd_down() { compose down; }

cmd_reload() { render_config; compose restart kbs; }

cmd_status() {
    compose ps
    note "incumbent: $(docker ps --filter "name=^${INCUMBENT}$" --format '{{.Names}} {{.Status}}' || true)"
    local live
    live=$(live_policy_path) && note "live policy $(sha256sum "$live" | cut -c1-16) at $live" || note "no live policy readable"
    ls -1t "${BROKER_STATE}/backup" 2>/dev/null | head -3 | sed 's/^/broker: backup /' >&2 || true
}

live_policy_path() {
    local ours="${BROKER_STATE:?}/storage/kbs/resource-policy.rego"
    [[ -r $ours ]] && { printf '%s' "$ours"; return 0; }
    return 1
}

backup_live_policy() {
    local dest="${BROKER_STATE:?}/backup/policy-$(date +%Y%m%dT%H%M%S).rego" live
    mkdir -p "${BROKER_STATE}/backup"
    if live=$(live_policy_path); then
        cp "$live" "$dest"
    elif [[ -n ${FROM_CONTAINER:-} ]]; then
        docker cp "$FROM_CONTAINER:/opt/confidential-containers/storage/kbs/resource-policy.rego" "$dest" \
            || die "could not read the live policy out of $FROM_CONTAINER"
    elif [[ -d ${BROKER_STATE}/storage/kbs ]]; then
        printf '(none)'
        return 0
    else
        die "no live policy readable; there is no read-back endpoint, so refusing to upload blind (set FROM_CONTAINER=$INCUMBENT to reach the incumbent)"
    fi
    [[ -s $dest ]] || die "the backup came out empty; refusing to upload"
    printf '%s' "$dest"
}

lint_policy() {
    local f=$1
    grep -q '^package policy' "$f" || die "$f has no 'package policy'; KBS evaluates data.policy.allow and a missing rule denies everything"
    grep -q '^import rego.v1' "$f" || die "$f has no 'import rego.v1'; regorus rejects the old dialect and a policy that fails to load denies everything"
    grep -qE '^[[:space:]]*allow' "$f" || die "$f defines no allow rule"
    grep -qE 'default[[:space:]]+allow[[:space:]]*:?=[[:space:]]*true' "$f" && die "$f defaults to allow; that releases every secret to every presenter"
    grep -q 'input\.tee' "$f" && die "$f uses the input.tee shape, which does not exist in an EAR token and denies everything including real trust domains"
    grep -q 'sample' "$f" && note "WARNING: $f mentions the sample attester, which proves plumbing and never confidentiality"
    return 0
}

cmd_set_policy() {
    local new=${1:?usage: set-policy <file.rego>} backup typed encoded
    [[ -s $new ]] || die "$new is empty or missing"
    lint_policy "$new"
    backup=$(backup_live_policy)
    note "live policy backed up to $backup"
    [[ $backup == "(none)" ]] || diff -u "$backup" "$new" >&2 || true
    printf 'This broker holds exactly ONE release policy, it is replaced wholesale, and it cannot be read back.\n'
    printf 'Every confidential session gated by %s is affected the moment this lands.\n' "$(url)"
    printf 'Type exactly:  replace the release policy on %s\n> ' "$(url)"
    [[ -t 0 ]] || die "refusing: replacing the release policy needs an interactive terminal"
    IFS= read -r typed || die "no answer given; nothing was uploaded"
    [[ $typed == "replace the release policy on $(url)" ]] || die "phrase did not match; nothing was uploaded"
    encoded=$(base64 -w0 "$new" | tr '+/' '-_' | tr -d '=')
    printf '{"policy":"%s"}' "$encoded" \
        | admin_curl -X POST --data-binary @- -H 'Content-Type: application/json' "$(url)/kbs/v0/resource-policy" >/dev/null
    printf '%s\t%s\t%s\t%s\n' "$(date +%FT%T%z)" "$(sha256sum "$new" | cut -d' ' -f1)" "$new" "$backup" \
        >>"${BROKER_STATE}/backup/policy-journal"
    note "uploaded; the document it replaced is at $backup"
}

cmd_set_resource() {
    local path=${1:?usage: set-resource <repo/type/tag> <file>} file=${2:?}
    [[ $(tr -dc / <<<"$path" | wc -c) -eq 2 ]] || die "resource path must be exactly repo/type/tag"
    [[ -s $file ]] || die "$file is empty; an empty resource is served as an empty secret and fails open in the consumer"
    admin_curl -X POST --data-binary "@$file" -H 'Content-Type: application/octet-stream' \
        "$(url)/kbs/v0/resource/$path" >/dev/null
    note "wrote $path"
}

case "${1:-}" in
    up) cmd_up ;;
    down) cmd_down ;;
    reload) cmd_reload ;;
    status) cmd_status ;;
    backup-policy) note "backed up to $(backup_live_policy)" ;;
    lint) shift; lint_policy "${1:?usage: $0 lint <file.rego>}"; note "lint passed: $1" ;;
    set-policy) shift; cmd_set_policy "$@" ;;
    set-resource) shift; cmd_set_resource "$@" ;;
    *) die "usage: $0 {up|down|reload|status|backup-policy|lint <file>|set-policy <file>|set-resource <repo/type/tag> <file>}" ;;
esac
