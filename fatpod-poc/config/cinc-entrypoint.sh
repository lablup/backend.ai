#!/bin/sh
set -e
mkdir -p /usr/local/bin /run/containerd /var/lib/nested-cd /run/nested-cd /var/lib/backend.ai/containerd-logs
# runc MUST be a normal file: a bind-mount over an empty inode breaks runc's overlayfs self-seal (CVE-2019-5736 path)
cp -f /hostbin/runc /usr/local/bin/runc && chmod +x /usr/local/bin/runc
# nested containerd at the agent's DEFAULT socket path -> agent talks to NESTED containerd (CinC), not the host
/hostbin/containerd --root /var/lib/nested-cd --state /run/nested-cd --address /run/containerd/containerd.sock > /var/lib/backend.ai/nested-cd.log 2>&1 &
for i in $(seq 1 60); do [ -S /run/containerd/containerd.sock ] && break; sleep 1; done
[ -S /run/containerd/containerd.sock ] || { echo "FATAL: nested containerd did not start"; tail -20 /var/lib/backend.ai/nested-cd.log; exit 1; }
echo "[cinc] nested containerd up (runc=$(/usr/local/bin/runc --version | head -1))"
# import the session image into the nested containerd if absent (backend-ai namespace)
if ! /hostbin/ctr -a /run/containerd/containerd.sock -n backend-ai images ls -q 2>/dev/null | grep -q python; then
  echo "[cinc] importing session image into nested containerd..."
  /hostbin/ctr -a /run/containerd/containerd.sock -n backend-ai images import /share/nested-img.tar >/dev/null 2>&1 && echo "[cinc] image imported"
fi
echo "[cinc] starting agent (containerd target = nested /run/containerd/containerd.sock)"
exec /home/charsyam/develop/lablup/backend.ai/dist/export/python/virtualenvs/python-default/3.13.7/bin/python -c "from ai.backend.agent.cli.start_server import main; main()" --config /etc/backend.ai/agent.toml
