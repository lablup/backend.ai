#!/usr/bin/env bash
set -euo pipefail

PKI_DIR="${PKI_DIR:-/var/lib/backendai-pki}"
TRUST_DOMAIN="${TRUST_DOMAIN:-coco.lablup.internal}"
ROOT_DAYS="${ROOT_DAYS:-3650}"
INTERMEDIATE_DAYS="${INTERMEDIATE_DAYS:-1825}"
LISTENER_DAYS="${LISTENER_DAYS:-90}"
CURVE=prime256v1

die() { printf 'pki: %s\n' "$*" >&2; exit 1; }
note() { printf 'pki: %s\n' "$*" >&2; }

genkey() {
    local out=$1
    [[ -e $out ]] && die "$out already exists; key material is never regenerated in place"
    (umask 077; openssl genpkey -algorithm EC -pkeyopt "ec_paramgen_curve:$CURVE" -out "$out" >/dev/null 2>&1)
}

extfile() {
    local path=$1 kind=$2 name=${3:-}
    case $kind in
        ca)
            cat >"$path" <<'EOF'
basicConstraints = critical, CA:TRUE, pathlen:0
keyUsage = critical, keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
EOF
            ;;
        listener)
            cat >"$path" <<EOF
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = serverAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
subjectAltName = DNS:$name, URI:spiffe://$TRUST_DOMAIN/key-broker/$name
EOF
            ;;
    esac
}

fingerprint() { openssl x509 -in "$1" -noout -sha256 -fingerprint | cut -d= -f2; }

cmd_root() {
    mkdir -p "$PKI_DIR/root"
    if [[ -e $PKI_DIR/root/ca.crt ]]; then
        note "root already present, fingerprint $(fingerprint "$PKI_DIR/root/ca.crt")"
        return 0
    fi
    genkey "$PKI_DIR/root/ca.key"
    openssl req -x509 -new -key "$PKI_DIR/root/ca.key" -sha256 -days "$ROOT_DAYS" \
        -subj "/O=Backend.AI/CN=Backend.AI confidential root ($TRUST_DOMAIN)" \
        -addext "basicConstraints=critical,CA:TRUE" \
        -addext "keyUsage=critical,keyCertSign,cRLSign" \
        -addext "subjectKeyIdentifier=hash" \
        -out "$PKI_DIR/root/ca.crt"
    note "root created, fingerprint $(fingerprint "$PKI_DIR/root/ca.crt")"
}

cmd_intermediate() {
    local role=$1 dir="$PKI_DIR/$1"
    case $role in services|standby) ;; *) die "intermediate role must be services or standby" ;; esac
    [[ -e $PKI_DIR/root/ca.key ]] || die "root key absent; run this on the host holding the root"
    mkdir -p "$dir"
    if [[ -e $dir/intermediate.crt ]]; then
        note "$role intermediate already present, fingerprint $(fingerprint "$dir/intermediate.crt")"
        return 0
    fi
    genkey "$dir/intermediate.key"
    openssl req -new -key "$dir/intermediate.key" -sha256 \
        -subj "/O=Backend.AI/CN=Backend.AI $role intermediate ($TRUST_DOMAIN)" \
        -out "$dir/intermediate.csr"
    extfile "$dir/ext.cnf" ca
    openssl x509 -req -in "$dir/intermediate.csr" -CA "$PKI_DIR/root/ca.crt" -CAkey "$PKI_DIR/root/ca.key" \
        -CAcreateserial -sha256 -days "$INTERMEDIATE_DAYS" -extfile "$dir/ext.cnf" -out "$dir/intermediate.crt"
    rm -f "$dir/intermediate.csr" "$dir/ext.cnf"
    cat "$dir/intermediate.crt" "$PKI_DIR/root/ca.crt" >"$dir/chain.crt"
    note "$role intermediate created, fingerprint $(fingerprint "$dir/intermediate.crt")"
}

cmd_listener() {
    local name=${1:?listener needs a DNS name} dir="$PKI_DIR/listener"
    [[ -e $PKI_DIR/services/intermediate.key ]] || die "services intermediate absent"
    mkdir -p "$dir"
    if [[ -e $dir/$name.crt ]]; then
        note "listener $name already present, fingerprint $(fingerprint "$dir/$name.crt")"
        return 0
    fi
    genkey "$dir/$name.key"
    openssl req -new -key "$dir/$name.key" -sha256 -subj "/O=Backend.AI/CN=$name" -out "$dir/$name.csr"
    extfile "$dir/$name.ext" listener "$name"
    openssl x509 -req -in "$dir/$name.csr" -CA "$PKI_DIR/services/intermediate.crt" \
        -CAkey "$PKI_DIR/services/intermediate.key" -CAcreateserial -sha256 -days "$LISTENER_DAYS" \
        -extfile "$dir/$name.ext" -out "$dir/$name.crt"
    rm -f "$dir/$name.csr" "$dir/$name.ext"
    cat "$dir/$name.crt" "$PKI_DIR/services/chain.crt" >"$dir/$name.chain.crt"
    note "listener $name created, expires in $LISTENER_DAYS days"
}

cmd_export() {
    local out=${1:-$PKI_DIR/export}
    mkdir -p "$out"
    [[ -e $PKI_DIR/root/ca.crt ]] || die "no root to export"
    cp "$PKI_DIR/root/ca.crt" "$out/root.crt"
    [[ -e $PKI_DIR/services/intermediate.crt ]] && cp "$PKI_DIR/services/intermediate.crt" "$out/services-intermediate.crt"
    [[ -e $PKI_DIR/standby/intermediate.crt ]] && cp "$PKI_DIR/standby/intermediate.crt" "$out/standby-intermediate.crt"
    note "public material exported to $out; no private key is ever exported"
}

cmd_fingerprints() {
    local path
    for path in "$PKI_DIR"/*/*.crt; do
        [[ -e $path ]] || continue
        printf '%s\t%s\t%s\n' "$(fingerprint "$path")" "$(openssl x509 -in "$path" -noout -enddate | cut -d= -f2)" "$path"
    done
}

case "${1:-}" in
    root) cmd_root ;;
    intermediate) shift; cmd_intermediate "$@" ;;
    listener) shift; cmd_listener "$@" ;;
    export) shift; cmd_export "$@" ;;
    fingerprints) cmd_fingerprints ;;
    *) die "usage: $0 {root|intermediate services|intermediate standby|listener <dns-name>|export [dir]|fingerprints}" ;;
esac
