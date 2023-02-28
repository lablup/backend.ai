#! /bin/bash

detect_count=0
ok_count=0

manager_deps=$(./pants dependencies src/ai/backend/manager:: 2>/dev/null)
echo -n "manager -> agent: ";   echo "$manager_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/agent$'   && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "manager -> client: ";  echo "$manager_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/client$'  && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "manager -> storage: "; echo "$manager_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/storage$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "manager -> web: ";     echo "$manager_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/web$'     && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
agent_deps=$(./pants dependencies src/ai/backend/agent:: 2>/dev/null)
echo -n "agent -> manager: "; echo "$agent_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/manager$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "agent -> client: ";  echo "$agent_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/client$'  && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "agent -> storage: "; echo "$agent_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/storage$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "agent -> web: ";     echo "$agent_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/web$'     && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
client_deps=$(./pants dependencies src/ai/backend/client:: 2>/dev/null)
echo -n "client -> manager: "; echo "$client_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/manager$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "client -> agent: ";   echo "$client_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/agent$'   && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "client -> storage: "; echo "$client_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/storage$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "client -> web: ";     echo "$client_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/web$    ' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
storage_deps=$(./pants dependencies src/ai/backend/storage:: 2>/dev/null)
echo -n "storage -> manager: "; echo "$storage_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/manager$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "storage -> agent: ";   echo "$storage_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/agent$'   && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "storage -> client: ";  echo "$storage_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/client$'  && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "storage -> web: ";     echo "$storage_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/web$'     && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
web_deps=$(./pants dependencies src/ai/backend/web:: 2>/dev/null)
echo -n "web -> manager: "; echo "$web_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/manager$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "web -> agent: ";   echo "$web_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/agent$'   && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "web -> storage: "; echo "$web_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/storage$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
common_deps=$(./pants dependencies src/ai/backend/common:: 2>/dev/null)
echo -n "common -> manager: "; echo "$common_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/manager$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "common -> agent: ";   echo "$common_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/agent$'   && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "common -> storage: "; echo "$common_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/storage$' && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "common -> web: ";     echo "$common_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/web$'     && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }
echo -n "common -> client: ";  echo "$common_deps"|grep -v '//:'|xargs dirname|uniq|grep 'src/ai/backend/client$'  && { echo "detected cross imports"; detect_count=$((detect_count + 1)); } || { echo "clean"; ok_count=$((ok_count + 1)); }

if [ "$detect_count" -gt 0 ]; then
  echo "Detected invalid cross imports!"
  exit 1
fi
