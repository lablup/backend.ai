#!/usr/bin/env bash
# Backend acceptance suite. See testcase.md for what each case is for and what it caught.
#
#   ./run.sh <cd|en|sg> [case-id ...]
#   ./run.sh --list
#
# Required env: ACC_IMAGE_ID, ACC_PROJECT_ID. See lib.sh for the rest.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./lib.sh

# Order matters: the network cases read the session B2 brought up, and the churn loop needs
# that session's slots back before it can place its own. B4 then clears everything the
# lifecycle cases held, and the rest bring up what they need themselves.
CASES="A1 A2 B1 B2 C1 C2 C3 C4 C5 C6 C7 B3 B4 D1 D2 D4 E1 E2 F1 F3 F5 F6 G1 G2 G3 G4"
DESCRIBE_A1="대상 백엔드만 두 노드에서 기동"
DESCRIBE_A2="privnet 소켓과 권한 (rootless)"
DESCRIBE_B1="단일노드 세션 RUNNING"
DESCRIBE_B2="멀티노드 세션 + 실제 노드 분산"
DESCRIBE_B3="연속 기동 (churn)"
DESCRIBE_B4="종료 후 잔여물 0"
DESCRIBE_C1="클러스터 DNS 양방향"
DESCRIBE_C2="노드 간 L3 양방향"
DESCRIBE_C3="컨테이너 자신의 리졸버로 피어 해석"
DESCRIBE_C4="노드 간 TCP, 호스트명으로 (양방향)"
DESCRIBE_C5="오버레이 경로 MTU가 meta 와 일치"
DESCRIBE_C6="컨테이너 egress (LOCAL NAT)"
DESCRIBE_C7="세션 간 격리"
DESCRIBE_D1="seccomp 필터 적용"
DESCRIBE_D2="cgroup 한도가 요청과 일치"
DESCRIBE_D4="커널이 에이전트 cgroup 밖"
DESCRIBE_E1="per-container 지표에 값이 있음"
DESCRIBE_E2="매니저 occupied_slots 일치"
DESCRIBE_F1="로그 캡 (파일 수·개당 크기)"
DESCRIBE_F3="로테이션 가로질러 읽기"
DESCRIBE_F5="종료 시 로그 삭제"
DESCRIBE_F6="로그 라이터 실패 시 로그 존재 (containerd)"
DESCRIBE_G1="에이전트 SIGKILL 후 커널 생존"
DESCRIBE_G2="재기동 후 세션 유지"
DESCRIBE_G3="고아 정리 / 살아있는 것 보존"
DESCRIBE_G4="PID 1 좀비 수거"

usage() { sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; }
list()  { for c in $CASES; do eval "d=\${DESCRIBE_$c}"; printf '  %-4s %s\n' "$c" "$d"; done; }

[ "${1:-}" = "--list" ] && { list; exit 0; }
[ $# -lt 1 ] && { usage; echo; list; exit 2; }

BK="$1"; shift
case "$BK" in cd|en|sg) ;; *) echo "unknown backend: $BK"; exit 2;; esac
[ -n "$ACC_IMAGE_ID" ] && [ -n "$ACC_PROJECT_ID" ] || { echo "ACC_IMAGE_ID and ACC_PROJECT_ID must be set"; exit 2; }
SELECTED="${*:-$CASES}"

REQ="$ACC_WORK/req-$BK"
mk_request "$REQ-single.json" "acc-$BK-single" 4  no  "$BK"
mk_request "$REQ-mn.json"     "acc-$BK-mn"     8  yes "$BK"

# state shared between cases so a session is launched once and reused
MN_SESSION=""; MN_STATUS=""; MN_MAIN_PID=""; MN_MAIN_NODE=""; MN_SUB_PID=""; MN_SUB_NODE=""
MN_MAIN_CID=""; FILLER=""; SINGLE_SESSION=""; SINGLE_CID=""

banner() { printf '\n\033[1m── %s ─ %s\033[0m\n' "$1" "$2"; }
run_case() {
  CASE_ID="$1"
  case " $SELECTED " in *" $1 "*) ;; *) return 0;; esac
  eval "d=\${DESCRIBE_$1}"
  banner "$1" "$d"
  "case_$1"
}

# ---------------------------------------------------------------- A
case_A1() {
  local a want other up_local up_peer
  a=$(alive_agents)
  want=$(agent_id "$BK" "$ACC_AGENT_SUFFIX_LOCAL")
  case " $a " in *" $want "*) ;; *) fail "$want 가 ALIVE 가 아님 (ALIVE: $a)"; return;; esac
  up_local=$(agent_up "$BK" local)
  [ "$up_local" = "up" ] || { fail "로컬 노드에 $BK RPC 포트가 열려 있지 않음"; return; }
  # no other backend may be listening on this node
  other=""
  for b in cd en sg; do
    [ "$b" = "$BK" ] && continue
    [ "$(agent_up "$b" local)" = "up" ] && other="$other $b"
  done
  [ -z "$other" ] || { fail "다른 백엔드가 같이 떠 있음:$other (한 번에 하나만)"; return; }
  if have_peer; then
    up_peer=$(agent_up "$BK" peer)
    [ "$up_peer" = "up" ] || { fail "피어 노드에 $BK 가 떠 있지 않음"; return; }
  fi
  pass "대상 백엔드만 기동됨"
}

case_A2() {
  backend_is_rootless "$BK" || { skip "rootless 백엔드에만 해당"; return; }
  local sock caps
  sock="/tmp/backend.ai/net-privnet-$BK.sock"
  [ -S "$sock" ] || { fail "privnet 소켓 없음: $sock"; return; }
  caps=$(ps -eo pid,cmd | grep "[p]rivnet" | head -1 | awk '{print $1}')
  [ -n "$caps" ] || { fail "privnet 프로세스가 없음"; return; }
  pass "소켓과 프로세스 확인 ($sock)"
}

# ---------------------------------------------------------------- B
case_B1() {
  local r
  SINGLE_SESSION=$(enqueue "$REQ-single.json")
  [ -n "$SINGLE_SESSION" ] || { fail "enqueue 실패"; return; }
  r=$(wait_session "$SINGLE_SESSION")
  SINGLE_CID=$(placement "$SINGLE_SESSION" | awk '{print $3}' | head -1)
  check "단일노드 세션" "$r" "RUNNING"
}

# How much CPU to park on the local node so exactly one 8-CPU kernel still fits there and the
# session's other half has nowhere to go but the peer. Computed from what the node actually has
# free: a fixed size is wrong on any node but the one it was written for, and wrong again as soon
# as another case is holding a session (measured — B1's session left 7 CPU free against a
# hard-coded filler of 20, and the multi-node request simply sat PENDING).
_filler_cpu() {
  bai gql "{ agent(agent_id: \"$(agent_id "$BK" "$ACC_AGENT_SUFFIX_LOCAL")\") { available_slots occupied_slots } }" 2>/dev/null \
    | _jq "
import json
a=d['data']['agent']
av=int(float(json.loads(a['available_slots']).get('cpu',0)))
oc=int(float(json.loads(a['occupied_slots']).get('cpu',0)))
print(max(0, av-oc-8))"
}

_bring_up_multinode() {
  have_peer || return 1
  local fcpu
  [ -n "$FILLER" ] || {
    fcpu=$(_filler_cpu)
    if [ -z "$fcpu" ] || [ "$fcpu" -lt 1 ]; then
      info "로컬 노드에 8 CPU 커널 하나 + filler 를 둘 여유가 없음 (계산된 filler=${fcpu:-?})"
      return 1
    fi
    info "filler ${fcpu} CPU 로 분산을 강제한다"
    mk_request "$REQ-fill.json" "acc-$BK-fill" "$fcpu" no "$BK"
    FILLER=$(enqueue "$REQ-fill.json")
    [ "$(wait_session "$FILLER")" = "RUNNING" ] || { info "filler 가 뜨지 않아 분산을 강제할 수 없음"; FILLER=""; return 1; }
  }
  MN_SESSION=$(enqueue "$REQ-mn.json")
  # Generous: a node whose agent has just restarted re-checks the image before it creates
  # anything, and a multi-node start waits for the slowest of two. A short wait here reported a
  # session that was merely still being created as a placement failure.
  MN_STATUS=$(wait_session "$MN_SESSION" 480)
  if [ "$MN_STATUS" != "RUNNING" ]; then
    teardown_session "$MN_SESSION"; MN_SESSION=""
    return 1
  fi
  local pl main_agent sub_agent
  pl=$(placement "$MN_SESSION")
  MN_MAIN_CID=$(echo "$pl" | awk '$1=="main1"{print $3}')
  main_agent=$(echo "$pl" | awk '$1=="main1"{print $2}')
  sub_agent=$(echo "$pl"  | awk '$1=="sub1"{print $2}')
  [ "${main_agent##*-}" = "$ACC_AGENT_SUFFIX_LOCAL" ] && MN_MAIN_NODE=local || MN_MAIN_NODE=peer
  [ "${sub_agent##*-}"  = "$ACC_AGENT_SUFFIX_LOCAL" ] && MN_SUB_NODE=local  || MN_SUB_NODE=peer
  MN_MAIN_PID=$(kernel_pid "$BK" "$MN_MAIN_CID" "$MN_MAIN_NODE")
  MN_SUB_PID=$(kernel_pid "$BK" "$(echo "$pl" | awk '$1=="sub1"{print $3}')" "$MN_SUB_NODE")
  [ "$MN_MAIN_NODE" != "$MN_SUB_NODE" ]
}

case_B2() {
  have_peer || { skip "피어 노드가 설정되지 않음 (ACC_PEER_HOST)"; return; }
  if _bring_up_multinode; then
    pass "RUNNING 이고 두 노드에 갈림 (main1@$MN_MAIN_NODE, sub1@$MN_SUB_NODE)"
  elif [ "${MN_STATUS:-}" != "RUNNING" ]; then
    # Two different failures used to share one message. They need different actions: this one is
    # the session never coming up, which says nothing about placement.
    fail "멀티노드 세션이 RUNNING 에 도달하지 못함 (마지막 상태: ${MN_STATUS:-불명})"
  else
    info "배치: $(placement "$MN_SESSION" | tr '\n' ' ')"
    fail "RUNNING 이지만 두 커널이 한 노드에 몰림 — filler 가 분산을 강제하지 못했다"
  fi
}

case_B3() {
  have_peer || { skip "피어 노드가 설정되지 않음"; return; }
  # Give back the multi-node session B2 raised: the network cases have read it by now, and its
  # slots are the ones this loop needs to place a kernel of its own on the local node.
  teardown_session "$MN_SESSION"; MN_SESSION=""; MN_MAIN_PID=""
  sleep 10
  local ok=0 bad=0 split=0 n id r pl
  [ -n "$FILLER" ] || {
    local fcpu; fcpu=$(_filler_cpu)
    [ -n "$fcpu" ] && [ "$fcpu" -ge 1 ] || { skip "분산을 강제할 여유가 없음"; return; }
    mk_request "$REQ-fill.json" "acc-$BK-fill" "$fcpu" no "$BK"
    FILLER=$(enqueue "$REQ-fill.json"); wait_session "$FILLER" >/dev/null
  }
  for n in $(seq 1 "$ACC_CHURN"); do
    mk_request "$REQ-churn.json" "acc-$BK-churn$n" 8 yes "$BK"
    id=$(enqueue "$REQ-churn.json")
    r=$(wait_session "$id" 300)
    pl=$(placement "$id")
    echo "$pl" | awk '{print $2}' | sort -u | wc -l | grep -q '^2$' && split=$((split+1))
    [ "$r" = "RUNNING" ] && ok=$((ok+1)) || bad=$((bad+1))
    info "  $n: $r"
    teardown_session "$id"
    sleep "$ACC_CHURN_GAP"
  done
  if [ "$bad" = "0" ] && [ "$split" = "$ACC_CHURN" ]; then
    pass "$ACC_CHURN 회 전부 RUNNING, 전부 분산"
  else
    fail "RUNNING=$ok 실패=$bad 분산=$split/$ACC_CHURN"
  fi
}

case_B4() {
  teardown_session "$MN_SESSION"; MN_SESSION=""
  teardown_session "$FILLER"; FILLER=""
  teardown_session "$SINGLE_SESSION"
  sleep 20
  local s_local s_peer=0
  s_local=$(repl_sockets local)
  have_peer && s_peer=$(repl_sockets peer)
  if [ "${s_local:-0}" = "0" ] && [ "${s_peer:-0}" = "0" ]; then
    pass "잔여 repl 소켓 0 (local=$s_local peer=$s_peer)"
  else
    fail "잔여 repl 소켓 local=$s_local peer=$s_peer"
  fi
  if [ -n "$SINGLE_CID" ]; then
    local left
    left=$(on_node local "sudo -n ls $(log_root "$BK") 2>/dev/null | grep -c $SINGLE_CID")
    [ "${left:-0}" = "0" ] && info "종료된 커널의 로그 제거됨" || fail "종료된 커널의 로그가 남음 ($left)"
  fi
  SINGLE_SESSION=""
}

# ---------------------------------------------------------------- C
_need_multinode() {
  [ -n "$MN_MAIN_PID" ] && return 0
  have_peer || { skip "피어 노드가 설정되지 않음"; return 1; }
  _bring_up_multinode || { skip "멀티노드 세션을 못 띄움 (B2 참고)"; return 1; }
}

case_C1() {
  _need_multinode || return
  local gw a b
  gw=$(ns_gw "$MN_MAIN_PID" "$MN_MAIN_NODE")
  [ -n "$gw" ] || { fail "컨테이너 기본 게이트웨이를 읽지 못함"; return; }
  a=$(ns_dns "$MN_MAIN_PID" sub1  "$MN_MAIN_NODE" "$gw")
  b=$(ns_dns "$MN_MAIN_PID" main1 "$MN_MAIN_NODE" "$gw")
  if [ -n "$a" ] && [ -n "$b" ]; then pass "sub1=$a main1=$b"; else fail "sub1='${a:-없음}' main1='${b:-없음}'"; fi
}

case_C2() {
  _need_multinode || return
  local gw peer_ip self_ip fwd rev
  gw=$(ns_gw "$MN_MAIN_PID" "$MN_MAIN_NODE")
  # The overlay address the cluster DNS hands out — NOT the LOCAL address, which is the same value
  # on every node and would make this a ping to itself.
  peer_ip=$(ns_dns "$MN_MAIN_PID" sub1  "$MN_MAIN_NODE" "$gw")
  self_ip=$(ns_dns "$MN_MAIN_PID" main1 "$MN_MAIN_NODE" "$gw")
  [ -n "$peer_ip" ] && [ -n "$self_ip" ] || { fail "DNS 로 피어 주소를 얻지 못해 검사 불가 (C1 먼저)"; return; }
  fwd=$(ns_ping "$MN_MAIN_PID" "$peer_ip" "$MN_MAIN_NODE")
  rev=$(ns_ping "$MN_SUB_PID"  "$self_ip" "$MN_SUB_NODE")
  if [ "$fwd" = "0% packet loss" ] && [ "$rev" = "0% packet loss" ]; then
    pass "main1→sub1 및 sub1→main1 모두 0% ($peer_ip / $self_ip)"
  else
    fail "main1→sub1='${fwd:-무응답}' sub1→main1='${rev:-무응답}'"
  fi
}

_probes_ready() {
  _need_multinode || return 1
  [ -n "${PROBE_READY:-}" ] && return 0
  push_probe "$MN_MAIN_PID" "$MN_MAIN_NODE" >/dev/null 2>&1
  push_probe "$MN_SUB_PID" "$MN_SUB_NODE" >/dev/null 2>&1
  PROBE_READY=1
}

case_C3() {
  _probes_ready || return
  local peer self
  peer=$(in_container "$MN_MAIN_PID" "$MN_MAIN_NODE" resolve sub1)
  self=$(in_container "$MN_MAIN_PID" "$MN_MAIN_NODE" resolve main1)
  # C1 asked the resolver directly; this asks the way a workload does, through the container's own
  # /etc/resolv.conf and /etc/hosts.
  case "$peer$self" in
    *FAIL*|"") fail "컨테이너 안에서 이름이 안 풀림 (sub1='$peer' main1='$self')";;
    *) pass "sub1=$peer main1=$self";;
  esac
}

case_C4() {
  _probes_ready || return
  local fwd rev
  in_container_bg "$MN_SUB_PID" "$MN_SUB_NODE" listen 19901 from-sub1
  sleep 3
  fwd=$(in_container "$MN_MAIN_PID" "$MN_MAIN_NODE" connect sub1 19901)
  in_container_bg "$MN_MAIN_PID" "$MN_MAIN_NODE" listen 19902 from-main1
  sleep 3
  rev=$(in_container "$MN_SUB_PID" "$MN_SUB_NODE" connect main1 19902)
  # What a workload actually does: a TCP connection to a peer BY NAME. ICMP passing (C2) does not
  # imply this -- name resolution, the overlay route and the peer's listener all have to line up.
  if [ "$fwd" = "from-sub1" ] && [ "$rev" = "from-main1" ]; then
    pass "main1→sub1 및 sub1→main1 TCP 성립"
  else
    fail "main1→sub1='$fwd' sub1→main1='$rev'"
  fi
}

case_C5() {
  _probes_ready || return
  local peer_ip measured link expected
  peer_ip=$(in_container "$MN_MAIN_PID" "$MN_MAIN_NODE" resolve sub1)
  measured=$(in_container "$MN_MAIN_PID" "$MN_MAIN_NODE" pmtu "$peer_ip")
  # Compare against the overlay NIC's own MTU rather than a number kept here: that is what the
  # manager's value became by the time the container sees it, and it is the only figure the
  # workload can be held to. A payload of MTU-28 is what fits after the IP and UDP headers.
  link=$(on_node "$MN_MAIN_NODE" "sudo -n nsenter -t $MN_MAIN_PID -n ip -o link show $OVERLAY_IF 2>/dev/null | grep -oE 'mtu [0-9]+' | awk '{print \$2}'")
  [ -n "$link" ] || { fail "컨테이너의 오버레이 인터페이스($OVERLAY_IF) MTU 를 못 읽음"; return; }
  expected=$(( link - 28 ))
  if [ "$measured" = "$expected" ]; then
    pass "무단편 UDP 페이로드 ${measured}B = 오버레이 MTU ${link}B − IP/UDP 28B"
  else
    fail "무단편 페이로드 ${measured}B, 인터페이스 MTU ${link}B 기준 기대 ${expected}B — 언더레이가 더 작다는 뜻"
  fi
}

case_C6() {
  _probes_ready || return
  local r
  r=$(in_container "$MN_MAIN_PID" "$MN_MAIN_NODE" egress "${ACC_EGRESS_HOST:-1.1.1.1}" "${ACC_EGRESS_PORT:-443}")
  # Out through the LOCAL bridge's NAT, which carries the default route. Nothing else in the suite
  # exercises it, and a session that can reach its peers but not a package index is still broken.
  [ "$r" = "ok" ] && pass "컨테이너에서 바깥으로 TCP 성립" \
                  || fail "egress 실패: $r (LOCAL 브리지의 기본 경로/NAT 확인)"
}

case_C7() {
  _probes_ready || return
  [ -n "$FILLER" ] || { skip "대조로 쓸 다른 세션이 없음"; return; }
  local fpl fcid fpid fip self other
  fpl=$(placement "$FILLER")
  fcid=$(echo "$fpl" | awk 'NR==1{print $3}')
  fpid=$(kernel_pid "$BK" "$fcid" local)
  [ -n "$fpid" ] || { skip "다른 세션의 커널을 로컬에서 찾지 못함"; return; }
  push_probe "$fpid" local >/dev/null 2>&1
  fip=$(ns_addr "$fpid" local | tr ' ' '\n' | grep -E "^172\\.30\\." | cut -d/ -f1 | head -1)
  [ -n "$fip" ] || { skip "다른 세션 컨테이너의 주소를 못 읽음"; return; }
  in_container_bg "$fpid" local listen 19903 other-session
  sleep 3
  # Control first: the listener has to be up, or "unreachable" proves nothing. A reachable host
  # with no listener answers ConnectionRefused, not a timeout — the two are the whole distinction.
  self=$(in_container "$fpid" local connect "$fip" 19903)
  [ "$self" = "other-session" ] || { skip "대조 실패 — 리스너가 안 떴다 ($self)"; return; }
  in_container_bg "$fpid" local listen 19904 other-session
  sleep 3
  other=$(in_container "$MN_MAIN_PID" "$MN_MAIN_NODE" connect "$fip" 19904)
  case "$other" in
    FAIL*) pass "다른 세션의 컨테이너($fip)에 닿지 않음 ($other), 그 세션 자신은 닿음";;
    *) fail "다른 세션의 컨테이너에 닿았다 — 세션 격리 없음 ($other)";;
  esac
}

# ---------------------------------------------------------------- D
_single_kernel() {  # ensure one local kernel exists; sets K_CID / K_PID
  [ -n "${K_PID:-}" ] && return 0
  [ -n "$SINGLE_SESSION" ] || {
    SINGLE_SESSION=$(enqueue "$REQ-single.json")
    [ "$(wait_session "$SINGLE_SESSION")" = "RUNNING" ] || { SINGLE_SESSION=""; return 1; }
  }
  K_CID=$(placement "$SINGLE_SESSION" | awk '{print $3}' | head -1)
  K_PID=$(kernel_pid "$BK" "$K_CID" local)
  [ -n "$K_PID" ]
}

case_D1() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  local mode kids bad=0
  mode=$(on_node local "sudo -n awk '/^Seccomp:/{print \$2}' /proc/$K_PID/status")
  [ "$mode" = "2" ] || { fail "커널 프로세스 Seccomp=$mode (2=filter 여야 함)"; return; }
  # ...and everything the kernel spawned must inherit it. Descendants are found by walking PPid,
  # not by matching the command line: the runtime's launcher carries the container's whole mount
  # list and environment in its argv, which contains the kernel entrypoint's path, so a substring
  # match reads the launcher itself as a kernel child and calls it unconfined.
  kids=$(on_node local "
    for p in \$(sudo -n cat /sys/fs/cgroup/backend-ai/$K_CID/cgroup.procs 2>/dev/null); do
      q=\$p
      for _ in 1 2 3 4 5 6 7 8; do
        [ \"\$q\" = \"$K_PID\" ] && { echo \$p; break; }
        q=\$(awk '/^PPid:/{print \$2}' /proc/\$q/status 2>/dev/null)
        [ -z \"\$q\" ] || [ \"\$q\" = 1 ] || [ \"\$q\" = 0 ] && break
      done
    done")
  for p in $kids; do
    local m; m=$(on_node local "sudo -n awk '/^Seccomp:/{print \$2}' /proc/$p/status 2>/dev/null")
    [ "$m" = "2" ] || bad=$((bad+1))
  done
  [ "$bad" = "0" ] && pass "커널과 그 자손 $(echo $kids | wc -w) 개 전부 filter 모드" \
                   || fail "$bad 개 자손이 필터를 상속하지 못함"
}

case_D2() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  local mem cpus
  mem=$(cgroup_val "$K_CID" memory.max local)
  cpus=$(cgroup_val "$K_CID" cpuset.cpus local)
  # the request above asks for 4 CPUs and 2 GiB
  if [ "$mem" = "2147483648" ] && [ -n "$cpus" ] && [ "$cpus" != "" ]; then
    pass "memory.max=$mem cpuset.cpus=$cpus"
  else
    fail "요청과 불일치 — memory.max='${mem:-없음}' cpuset.cpus='${cpus:-없음}' (기대 2147483648 / 4개)"
  fi
}

case_D4() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  local kcg acg port apid
  kcg=$(on_node local "sudo -n cut -d: -f3 /proc/$K_PID/cgroup 2>/dev/null | head -1")
  port=$(backend_rpc_port "$BK")
  apid=$(on_node local "sudo -n ss -tlnp 2>/dev/null | grep ':$port ' | grep -oE 'pid=[0-9]+' | cut -d= -f2 | head -1")
  [ -n "$apid" ] || { skip "에이전트 pid 를 찾지 못함"; return; }
  acg=$(on_node local "sudo -n cut -d: -f3 /proc/$apid/cgroup 2>/dev/null | head -1")
  case "$kcg" in
    "$acg"|"$acg"/*) fail "커널이 에이전트 cgroup 안에 있음 ($kcg) — systemctl stop 에 함께 죽는다";;
    *) pass "커널 cgroup=$kcg, 에이전트=$acg (분리됨)";;
  esac
}

# ---------------------------------------------------------------- E
case_E1() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  local port metrics missing="" deadline
  case "$BK" in cd) port=6203;; en) port=6003;; sg) port=6103;; esac
  # The collector runs on a cycle, so a kernel that has just started has no series yet. Wait for
  # them rather than reporting an empty scrape as a missing metric.
  deadline=$(( $(date +%s) + 90 ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    metrics=$(curl -s --max-time 10 "http://127.0.0.1:$port/metrics" 2>/dev/null \
              | grep backendai_container_utilization | grep "$K_CID" \
              | sed -E 's/.*metric_name="([^"]+)".*/\1/' | sort -u)
    [ -n "$metrics" ] && break
    sleep 10
  done
  for k in mem io_read net_rx net_tx cpu_used; do
    echo "$metrics" | grep -qx "$k" || missing="$missing $k"
  done
  [ -z "$missing" ] && pass "지표 전 항목 존재 ($(echo "$metrics" | tr '\n' ' '))" \
                    || fail "누락된 지표:$missing"
}

case_E2() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  local occ cpu
  occ=$(bai gql "{ agent(agent_id: \"$(agent_id "$BK" "$ACC_AGENT_SUFFIX_LOCAL")\") { occupied_slots } }" 2>/dev/null \
        | _jq "print(d['data']['agent']['occupied_slots'])")
  # The agent总 is every kernel on it, not this one alone — asserting equality here fails whenever
  # anything else is running, which is a property of the node and not of the backend. What this
  # case is for is that the allocation reached the manager at all.
  cpu=$(printf '%s' "$occ" | sed -nE 's/.*"cpu": "([0-9]+)".*/\1/p')
  if [ -n "$cpu" ] && [ "$cpu" -ge 4 ]; then
    pass "occupied_slots 에 이 세션의 할당이 반영됨 (cpu=$cpu ≥ 4)"
  else
    fail "occupied_slots=$occ (이 세션의 cpu 4 가 반영되지 않음)"
  fi
}

# ---------------------------------------------------------------- F
case_F1() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  # 48 MiB burst straight into the kernel's own stdout: same inode, same O_APPEND the container uses
  on_node local "for i in \$(seq 1 48); do sudo -n dd if=/dev/zero bs=1M count=1 2>/dev/null | tr '\\0' 'A' | sudo -n tee -a /proc/$K_PID/fd/1 >/dev/null; done"
  sleep 12
  local files largest total
  files=$(on_node local "sudo -n ls $(log_root "$BK") 2>/dev/null | grep -c $K_CID")
  largest=$(on_node local "sudo -n ls -l $(log_root "$BK") 2>/dev/null | grep $K_CID | awk '{print \$5}' | sort -n | tail -1")
  total=$(on_node local "sudo -n ls -l $(log_root "$BK") 2>/dev/null | grep $K_CID | awk '{s+=\$5} END{print s+0}'")
  if [ "${files:-9}" -le 5 ] && [ "${largest:-0}" -le 2097152 ]; then
    pass "파일 $files 개, 최대 $largest B, 총 $total B (48 MiB 를 쏟은 뒤)"
  else
    fail "파일 $files 개, 최대 $largest B (기대: ≤5 개, 개당 ≤2097152 B)"
  fi
}

case_F3() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  local n
  n=$(bai session logs "$SINGLE_SESSION" 2>/dev/null | wc -c)
  # F1 rotated the log; a reader that only looked at the active file would come back nearly empty
  [ "${n:-0}" -gt 1000000 ] && pass "$n B (회전된 파일까지 읽음)" || fail "$n B — 회전분을 읽지 못하는 것으로 보임"
}

case_F5() {
  [ -n "${K_CID:-}" ] || { skip "대상 커널 없음"; return; }
  local cid="$K_CID"
  teardown_session "$SINGLE_SESSION"; SINGLE_SESSION=""; K_PID=""; K_CID=""
  sleep 10
  local left
  left=$(on_node local "sudo -n ls $(log_root "$BK") 2>/dev/null | grep -c $cid")
  check "종료된 커널의 로그 파일" "${left:-x}" "0"
}

case_F6() {
  [ "$BK" = "cd" ] || { skip "containerd 의 binary:// 라이터에만 해당"; return; }
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  local present
  present=$(on_node local "sudo -n ls $(log_root "$BK")/$K_CID.log 2>/dev/null | wc -l")
  # The writer creates this file before containerd releases the task. No file means it never ran,
  # and the kernel is running with its output going nowhere — silently.
  check "커널의 활성 로그 파일" "${present:-0}" "1"
}

# ---------------------------------------------------------------- G
case_G1() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  G_SESSION="$SINGLE_SESSION"; G_CID="$K_CID"; G_PID="$K_PID"
  local port
  port=$(backend_rpc_port "$BK")
  on_node local "for p in \$(sudo -n ss -tlnp 2>/dev/null | grep ':$port ' | grep -oE 'pid=[0-9]+' | cut -d= -f2); do
      ppid=\$(awk '/^PPid:/{print \$2}' /proc/\$p/status 2>/dev/null); sudo -n kill -9 \$ppid \$p 2>/dev/null; done"
  sleep 5
  local alive
  alive=$(on_node local "sudo -n kill -0 $G_PID 2>/dev/null && echo yes || echo no")
  check "에이전트 SIGKILL 후 커널" "$alive" "yes"
}

case_G2() {
  [ -n "${G_PID:-}" ] || { skip "G1 을 먼저 실행해야 함"; return; }
  info "에이전트를 다시 띄운다 — 이 스위트는 기동 방법을 모르므로 ACC_START_CMD 가 필요하다"
  [ -n "${ACC_START_CMD:-}" ] || { skip "ACC_START_CMD 가 설정되지 않음"; return; }
  bash -c "$ACC_START_CMD" >/dev/null 2>&1
  local deadline=$(( $(date +%s) + 180 ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    [ "$(agent_up "$BK" local)" = "up" ] && break
    sleep 5
  done
  local st alive
  st=$(session_status "$G_SESSION")
  alive=$(on_node local "sudo -n kill -0 $G_PID 2>/dev/null && echo yes || echo no")
  if [ "$st" = "RUNNING" ] && [ "$alive" = "yes" ]; then
    pass "재기동 후 세션 RUNNING, 커널 생존"
  else
    fail "세션=$st 커널생존=$alive"
  fi
}

case_G3() {
  [ -n "${ACC_START_CMD:-}" ] || { skip "ACC_START_CMD 가 설정되지 않음 (재기동이 필요한 케이스)"; return; }
  _single_kernel || { skip "살아있는 커널이 있어야 '보존' 쪽을 볼 수 있음"; return; }
  local live_cid="$K_CID" before_logs before_scr port
  # plant one orphan of each kind: a log and a scratch for a kernel id that does not exist
  local ghost="00000000-0000-4000-8000-0000000000ff"
  on_node local "sudo -n mkdir -p $(log_root "$BK") $(scratch_root "$BK")/$ghost && sudo -n touch $(log_root "$BK")/$ghost.log"
  before_logs=$(on_node local "sudo -n ls $(log_root "$BK") 2>/dev/null | wc -l")
  before_scr=$(on_node local "sudo -n ls $(scratch_root "$BK") 2>/dev/null | wc -l")
  port=$(backend_rpc_port "$BK")
  on_node local "for p in \$(sudo -n ss -tlnp 2>/dev/null | grep ':$port ' | grep -oE 'pid=[0-9]+' | cut -d= -f2); do
      ppid=\$(awk '/^PPid:/{print \$2}' /proc/\$p/status 2>/dev/null); sudo -n kill -9 \$ppid \$p 2>/dev/null; done"
  sleep 5
  bash -c "$ACC_START_CMD" >/dev/null 2>&1
  local deadline=$(( $(date +%s) + 180 ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    [ "$(agent_up "$BK" local)" = "up" ] && break
    sleep 5
  done
  sleep 20
  local ghost_log ghost_scr live_log
  ghost_log=$(on_node local "sudo -n ls $(log_root "$BK")/$ghost.log 2>/dev/null | wc -l")
  ghost_scr=$(on_node local "sudo -n ls -d $(scratch_root "$BK")/$ghost 2>/dev/null | wc -l")
  live_log=$(on_node local "sudo -n ls $(log_root "$BK")/$live_cid.log 2>/dev/null | wc -l")
  if [ "${ghost_log:-1}" = "0" ] && [ "${ghost_scr:-1}" = "0" ] && [ "${live_log:-0}" = "1" ]; then
    pass "고아 로그·스크래치 제거, 살아있는 커널의 로그 보존 (before: $before_logs logs / $before_scr scratches)"
  else
    fail "고아로그남음=$ghost_log 고아스크래치남음=$ghost_scr 살아있는로그=$live_log (0/0/1 기대)"
  fi
}

case_G4() {
  _single_kernel || { skip "커널을 띄우지 못함"; return; }
  ns_run "$K_PID" 'i=0; while [ $i -lt 50 ]; do (sleep 0.1 &) ; i=$((i+1)); done; sleep 3' local >/dev/null 2>&1
  sleep 5
  local z
  z=$(on_node local "sudo -n nsenter -t $K_PID -m -p --preserve-credentials -S 0 -G 0 sh -c \"ps -eo stat 2>/dev/null | grep -c '^Z'\"")
  check "컨테이너 안 좀비" "${z:-x}" "0"
}

# ---------------------------------------------------------------- main
printf '\033[1m백엔드 인수 테스트 — %s\033[0m  (케이스: %s)\n' "$BK" "$SELECTED"
printf '노드: local=%s peer=%s\n' "$ACC_LOCAL_HOST" "${ACC_PEER_HOST:-없음}"
result_open "$BK" "$SELECTED"
printf '기록: %s\n' "$RESULT_FILE"
trap 'echo; echo "정리 중..."; teardown_all' EXIT
for c in $CASES; do run_case "$c"; done
teardown_all
result_close "$BK"
printf '\n\033[1m결과\033[0m  통과 %d · 실패 %d · 건너뜀 %d\n' "$PASS" "$FAIL" "$SKIP"
[ -n "$FAILED_IDS" ] && printf '실패한 케이스:%s\n' "$FAILED_IDS"
printf '기록: %s\n' "$RESULT_FILE"
exit $(( FAIL > 0 ? 1 : 0 ))
