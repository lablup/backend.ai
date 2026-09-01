# Shared helpers for the backend acceptance suite. Sourced by run.sh.
#
# Everything here talks to a live deployment: the manager through `./bai`, the node through sudo,
# and the peer node through ssh. Nothing is mocked — the whole point of this suite is the parts a
# unit test cannot reach.

: "${BAI_ROOT:=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
: "${ACC_LOCAL_HOST:=127.0.0.1}"        # this node, as the manager knows it
: "${ACC_PEER_HOST:=}"                  # the second node; empty disables the multi-node cases
: "${ACC_PEER_SSH:=${ACC_PEER_HOST}}"   # ssh target for the peer
: "${ACC_AGENT_SUFFIX_LOCAL:=104}"      # agent ids are i-<backend>-<suffix>
: "${ACC_AGENT_SUFFIX_PEER:=156}"
: "${ACC_IMAGE_ID:=}"                   # required: the image to launch
: "${ACC_PROJECT_ID:=}"                 # required
: "${ACC_RESOURCE_GROUP:=default}"
: "${ACC_CHURN:=5}"                     # B3 repetitions
: "${ACC_CHURN_GAP:=12}"                # seconds between B3 runs
OVERLAY_IF=baimulti0   # the overlay NIC name the vxlan backend gives a container
: "${ACC_WORK:=${TMPDIR:-/tmp}/bai-acceptance}"

mkdir -p "$ACC_WORK"

# --- backend-specific facts -------------------------------------------------
# rpc port, var-base-path and whether the backend needs a privnet. Kept in one place so a new
# backend is one row rather than a grep across the suite.
backend_rpc_port() { case "$1" in cd) echo 6211;; en) echo 6011;; sg) echo 6111;; pm) echo 6311;; esac; }
backend_var_base() { case "$1" in cd) echo /var/lib/bai-containerd;; en) echo /var/lib/bai-enroot;; sg) echo /var/lib/bai-singularity;; pm) echo /var/lib/bai-podman;; esac; }
backend_agent_kind() { case "$1" in cd) echo cd;; en) echo en;; sg) echo sg;; pm) echo pm;; esac; }
backend_is_rootless() { case "$1" in en|sg|pm) return 0;; *) return 1;; esac; }
# podman is rootless but caps the log in conmon, like containerd's log writer does.
backend_hard_log_cap() { case "$1" in cd|pm) return 0;; *) return 1;; esac; }

agent_id() { echo "i-$(backend_agent_kind "$1")-$2"; }
log_root() { echo "$(backend_var_base "$1")/containerd-logs"; }
scratch_root() { echo "$(backend_var_base "$1")/scratches"; }

# --- output and the run record ----------------------------------------------
# testcase.md is the specification and says nothing about outcomes; a run writes its own record
# here so the two never have to be kept in step by hand.
: "${ACC_RESULT_DIR:=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/results}"
mkdir -p "$ACC_RESULT_DIR"
RESULT_FILE=""

result_open() {  # $1 = backend, $2 = selected case ids
  local stamp
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  RESULT_FILE="$ACC_RESULT_DIR/$1-$stamp.tsv"
  {
    printf '# backend\t%s\n' "$1"
    printf '# started_utc\t%s\n' "$stamp"
    printf '# cases\t%s\n' "$2"
    printf '# churn\t%s x %ss\n' "$ACC_CHURN" "$ACC_CHURN_GAP"
    printf '# local_host\t%s\n' "$ACC_LOCAL_HOST"
    printf '# peer_host\t%s\n' "${ACC_PEER_HOST:-none}"
    printf '# image_id\t%s\n' "$ACC_IMAGE_ID"
    printf '# git_commit\t%s\n' "$( cd "$BAI_ROOT" && git rev-parse --short HEAD 2>/dev/null )"
    printf '# host\t%s\n' "$(uname -srm)"
    printf 'case\tstatus\tdetail\n'
  } > "$RESULT_FILE"
}

result_row() { [ -n "$RESULT_FILE" ] && printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$RESULT_FILE"; }

result_close() {
  [ -n "$RESULT_FILE" ] || return 0
  {
    printf '# finished_utc\t%s\n' "$(date -u +%Y%m%dT%H%M%SZ)"
    printf '# pass\t%s\n# fail\t%s\n# skip\t%s\n' "$PASS" "$FAIL" "$SKIP"
  } >> "$RESULT_FILE"
  ln -sf "$(basename "$RESULT_FILE")" "$ACC_RESULT_DIR/latest-$1.tsv"
}

PASS=0; FAIL=0; SKIP=0; FAILED_IDS=""
_c() { case "$1" in ok) printf '\033[32m';; no) printf '\033[31m';; sk) printf '\033[33m';; *) printf '';; esac; }
_r() { printf '\033[0m'; }
pass()  { PASS=$((PASS+1)); _c ok; printf 'PASS'; _r; printf ' %-4s %s\n' "$CASE_ID" "$1"; result_row "$CASE_ID" PASS "$1"; }
fail()  { FAIL=$((FAIL+1)); FAILED_IDS="$FAILED_IDS $CASE_ID"; _c no; printf 'FAIL'; _r; printf ' %-4s %s\n' "$CASE_ID" "$1"; result_row "$CASE_ID" FAIL "$1"; }
skip()  { SKIP=$((SKIP+1)); _c sk; printf 'SKIP'; _r; printf ' %-4s %s\n' "$CASE_ID" "$1"; result_row "$CASE_ID" SKIP "$1"; }
info()  { printf '       %s\n' "$1"; }
check() { if [ "$2" = "$3" ]; then pass "$1 ($2)"; else fail "$1 — 기대 $3, 실제 $2"; fi; }

# --- manager ----------------------------------------------------------------
bai() { ( cd "$BAI_ROOT" && ./bai "$@" ); }

_jq() { python3 -c "import sys,json;d=json.load(sys.stdin);$1" 2>/dev/null; }

session_status() { bai session get "$1" 2>/dev/null | _jq "print(d.get('lifecycle',{}).get('status'))"; }

alive_agents() {
  bai admin agent search --limit 40 --status ALIVE 2>/dev/null \
    | _jq "xs=d.get('agents') or d.get('items') or []; print(' '.join(sorted(x.get('id') or '' for x in xs)))"
}

# $1 = out path, $2 = name, $3 = cpu, $4 = yes|no multinode, $5 = backend
mk_request() {
  python3 - "$1" "$2" "$3" "$4" "$5" "$ACC_IMAGE_ID" "$ACC_PROJECT_ID" "$ACC_RESOURCE_GROUP" \
      "$ACC_AGENT_SUFFIX_LOCAL" "$ACC_AGENT_SUFFIX_PEER" <<'PY'
import json, sys, pathlib
out, name, cpu, multi, bk, image, project, rg, local, peer = sys.argv[1:11]
d = {
    "session_name": name,
    "session_type": "interactive",
    "image_id": image,
    "project_id": project,
    "resource_group": rg,
    "resource_entries": [
        {"resource_type": "cpu", "quantity": cpu},
        {"resource_type": "mem", "quantity": "2g"},
    ],
}
if multi == "yes":
    d["cluster_mode"] = "multi-node"
    d["cluster_size"] = 2
    d["agent_list"] = [f"i-{bk}-{local}", f"i-{bk}-{peer}"]
else:
    d["agent_list"] = [f"i-{bk}-{local}"]
pathlib.Path(out).write_text(json.dumps(d, indent=1))
PY
}

enqueue() { bai session enqueue @"$1" 2>&1 | _jq "print((d.get('session') or {}).get('id',''))"; }

wait_session() {  # $1 = id, $2 = timeout seconds (default 240)
  local deadline=$(( $(date +%s) + ${2:-240} )) s
  while [ "$(date +%s)" -lt "$deadline" ]; do
    s=$(session_status "$1")
    case "$s" in RUNNING|TERMINATED|CANCELLED) echo "$s"; return;; esac
    sleep 5
  done
  echo "${s:-TIMEOUT}"
}

teardown_session() {
  [ -n "$1" ] || return 0
  bai session terminate "$1" >/dev/null 2>&1
  local deadline=$(( $(date +%s) + 180 ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    [ "$(session_status "$1")" = "TERMINATED" ] && return 0
    sleep 5
  done
}

teardown_all() {
  local id
  for id in $(bai admin session search --limit 40 2>/dev/null \
      | _jq "
for x in (d.get('sessions') or d.get('items') or []):
    if (x.get('lifecycle') or {}).get('status') not in ('TERMINATED','CANCELLED'): print(x.get('id'))"); do
    bai session terminate "$id" >/dev/null 2>&1
  done
  sleep 15
}

# hostname<TAB>agent<TAB>container for every kernel of a session
placement() {
  bai admin session kernel search --limit 60 2>&1 | _jq "
sid='$1'
for k in d.get('items',[]):
    if (k.get('session_info') or {}).get('session_id')==sid:
        c=k.get('cluster') or {}; r=k.get('resource') or {}
        print(f\"{c.get('cluster_hostname')}\t{r.get('agent_id')}\t{r.get('container_id')}\")"
}

# --- node access ------------------------------------------------------------
have_peer() { [ -n "$ACC_PEER_SSH" ]; }
on_peer() { ssh -o BatchMode=yes -o ConnectTimeout=8 "$ACC_PEER_SSH" "$@" 2>/dev/null; }

# $1 = node suffix (local|peer), rest = command
on_node() {
  local where="$1"; shift
  if [ "$where" = "local" ]; then bash -c "$*"; else on_peer "$*"; fi
}

agent_up() {  # $1 = backend, $2 = local|peer
  local port host
  port=$(backend_rpc_port "$1")
  if [ "$2" = "local" ]; then host="$ACC_LOCAL_HOST"; else host="$ACC_PEER_HOST"; fi
  on_node "$2" "sudo -n ss -tlnp 2>/dev/null | grep -q ':$port ' && echo up || echo down"
}

# The kernel process of a container: the one inside the container's netns AND running the kernel
# entrypoint. The runtime's own scaffolding (apptainer's starter/appinit, enroot-nsenter) is in the
# netns too, and picking it reads the container as unconfined.
kernel_pid() {  # $1 = backend, $2 = container id, $3 = local|peer
  local script
  script='
CID="'"$2"'"; BK="'"$1"'"
if [ "$BK" = "cd" ]; then
  sudo -n ctr -n backend-ai t ls 2>/dev/null | awk -v c="$CID" "\$1==c {print \$2}" | head -1
  exit 0
fi
HOSTNS=$(sudo -n readlink /proc/1/ns/net 2>/dev/null)
for f in $(sudo -n grep -ls "/backend-ai/$CID\$" /proc/[0-9]*/cgroup 2>/dev/null); do
  p=$(echo "$f" | cut -d/ -f3)
  ns=$(sudo -n readlink /proc/$p/ns/net 2>/dev/null)
  [ -n "$ns" ] && [ "$ns" != "$HOSTNS" ] || continue
  sudo -n grep -qs "init.py" /proc/$p/cmdline 2>/dev/null || continue
  echo "$p"; exit 0
done'
  on_node "$3" "$script"
}

ns_addr() { on_node "$2" "sudo -n nsenter -t $1 -n ip -4 -br addr show 2>/dev/null | awk '\$1!=\"lo\"{print \$3}' | tr '\n' ' '"; }
ns_gw()   { on_node "$2" "sudo -n nsenter -t $1 -n ip -4 route show default 2>/dev/null | awk '{print \$3}' | head -1"; }
ns_dns()  { on_node "$3" "sudo -n nsenter -t $1 -n dig +short +time=2 +tries=1 $2 @$4 2>/dev/null | head -1"; }
ns_ping() { on_node "$3" "sudo -n nsenter -t $1 -n ping -c 3 -W 2 -q $2 2>&1 | grep -oE '[0-9]+% packet loss' | head -1"; }
ns_run()  { on_node "$3" "sudo -n nsenter -t $1 -m -p -u --preserve-credentials -S 0 -G 0 sh -c '$2'"; }

# --- inside the container -----------------------------------------------------
# The cases above enter the netns and use the HOST's tools, which answers "does the fabric carry
# this". These run in the container's own mount and pid namespaces instead, which is the only way
# to ask "can the workload use it": its resolver, its routing view, its addresses. Do not assume a
# tool is there -- the kernel image has no `ping`, and probing with it reported every packet as
# dropped when the truth was that the command did not exist. probe.py is stdlib-only for that
# reason.
push_probe() {  # $1 = kernel pid, $2 = local|peer
  if [ "$2" = "local" ]; then
    sudo -n cp "$(dirname "${BASH_SOURCE[0]}")/probe.py" "/proc/$1/root/tmp/bai-probe.py"
  else
    scp -q -o BatchMode=yes "$(dirname "${BASH_SOURCE[0]}")/probe.py" "$ACC_PEER_SSH:/tmp/bai-probe.py" \
      && on_peer "sudo -n cp /tmp/bai-probe.py /proc/$1/root/tmp/bai-probe.py"
  fi
}

in_container() {  # $1 = kernel pid, $2 = local|peer, rest = probe.py args
  local pid="$1" where="$2"; shift 2
  on_node "$where" "sudo -n nsenter -t $pid -m -p -u -n --preserve-credentials -S 0 -G 0 -- python3 /tmp/bai-probe.py $*"
}

in_container_bg() {  # same, detached (for listeners)
  local pid="$1" where="$2"; shift 2
  on_node "$where" "setsid sudo -n nsenter -t $pid -m -p -u -n --preserve-credentials -S 0 -G 0 -- python3 /tmp/bai-probe.py $* >/dev/null 2>&1 < /dev/null &"
}

cgroup_val() { on_node "$3" "sudo -n head -1 /sys/fs/cgroup/backend-ai/$1/$2 2>/dev/null"; }
repl_sockets() { on_node "$1" "sudo -n ss -tn 2>/dev/null | grep -cE '172\.30\.[0-9]+\.[0-9]+:200[01]'"; }
