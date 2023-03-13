#! /bin/bash

detect_count=0
ok_count=0

check_output() {
  echo "$1"|grep -v '//:'|xargs dirname|uniq|grep "src/ai/backend/$2\$" && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
}

manager_deps=$(./pants dependencies src/ai/backend/manager:: 2>/dev/null)
echo -n "manager -> agent: ";   check_output "$manager_deps" "agent"
echo -n "manager -> client: ";  check_output "$manager_deps" "client"
echo -n "manager -> storage: "; check_output "$manager_deps" "storage"
echo -n "manager -> web: ";     check_output "$manager_deps" "web"
agent_deps=$(./pants dependencies src/ai/backend/agent:: 2>/dev/null)
echo -n "agent -> manager: "; check_output "$agent_deps" "manager"
echo -n "agent -> client: ";  check_output "$agent_deps" "client"
echo -n "agent -> storage: "; check_output "$agent_deps" "storage"
echo -n "agent -> web: ";     check_output "$agent_deps" "web"
client_deps=$(./pants dependencies src/ai/backend/client:: 2>/dev/null)
echo -n "client -> manager: "; check_output "$client_deps" "manager"
echo -n "client -> agent: ";   check_output "$client_deps" "agent"
echo -n "client -> storage: "; check_output "$client_deps" "storage"
echo -n "client -> web: ";     check_output "$client_deps" "web"
storage_deps=$(./pants dependencies src/ai/backend/storage:: 2>/dev/null)
echo -n "storage -> manager: "; check_output "$storage_deps" "manager"
echo -n "storage -> agent: ";   check_output "$storage_deps" "agent"
echo -n "storage -> client: ";  check_output "$storage_deps" "client"
echo -n "storage -> web: ";     check_output "$storage_deps" "web"
web_deps=$(./pants dependencies src/ai/backend/web:: 2>/dev/null)
echo -n "web -> manager: "; check_output "$web_deps" "manager"
echo -n "web -> agent: ";   check_output "$web_deps" "agent"
echo -n "web -> storage: "; check_output "$web_deps" "storage"
common_deps=$(./pants dependencies src/ai/backend/common:: 2>/dev/null)
echo -n "common -> manager: "; check_output "$common_deps" "manager"
echo -n "common -> agent: ";   check_output "$common_deps" "agent"
echo -n "common -> storage: "; check_output "$common_deps" "storage"
echo -n "common -> web: ";     check_output "$common_deps" "web"
echo -n "common -> client: ";  check_output "$common_deps" "client"

if [ "$detect_count" -gt 0 ]; then
  echo "Detected invalid cross imports!"
  exit 1
fi
