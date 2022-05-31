#! /bin/sh

USER_ID=${LOCAL_USER_ID:-9001}
GROUP_ID=${LOCAL_GROUP_ID:-9001}

echo "Kernel started at: $(date -Iseconds -u)"

if [ $USER_ID -eq 0 ]; then

  echo "WARNING: Running the user codes as root is not recommended."
  if [ -f /bin/ash ]; then  # for alpine
    export SHELL=/bin/ash
  else
    export SHELL=/bin/bash
    echo "$LD_PRELOAD" | tr ':' '\n' > /etc/ld.so.preload
    unset LD_PRELOAD
  fi
  export LD_LIBRARY_PATH="/opt/backend.ai/lib:$LD_LIBRARY_PATH"
  export HOME="/home/work"

  # Invoke image-specific bootstrap hook.
  if [ -x "/opt/container/bootstrap.sh" ]; then
    echo 'Executing image bootstrap... '
    . /opt/container/bootstrap.sh
    echo 'Image bootstrap executed.'
  fi

  # Extract dotfiles
  /opt/backend.ai/bin/python /opt/kernel/extract_dotfiles.py

  echo "Executing the main program..."
  exec "$@"

else

  echo "Setting up uid and gid: $USER_ID:$GROUP_ID"
  USER_NAME=$(getent group $USER_ID | cut -d: -f1)
  GROUP_NAME=$(getent group $GROUP_ID | cut -d: -f1)
  if [ -f /bin/ash ]; then  # for alpine (busybox)
    if [ -z "$GROUP_NAME" ]; then
      GROUP_NAME=work
      addgroup -g $GROUP_ID $GROUP_NAME
    fi
    if [ -z "$USER_NAME" ]; then
      USER_NAME=work
      adduser -s /bin/ash -h "/home/$USER_NAME" -H -D -u $USER_ID -G $GROUP_NAME -g "User" $USER_NAME
    fi
    export SHELL=/bin/ash
  else
    echo "$LD_PRELOAD" | tr ':' '\n' > /etc/ld.so.preload
    unset LD_PRELOAD
    if [ -z "$GROUP_NAME" ]; then
      GROUP_NAME=work
      groupadd -g $GROUP_ID $GROUP_NAME
    fi
    if [ -z "$USER_NAME" ]; then
      USER_NAME=work
      useradd -s /bin/bash -d "/home/$USER_NAME" -M -r -u $USER_ID -g $GROUP_NAME -o -c "User" $USER_NAME
    else
      cp -R "/home/$USER_NAME/*" /home/work/
      cp -R "/home/$USER_NAME/.*" /home/work/
      usermod -s /bin/bash -d /home/work -l work -g $GROUP_NAME $USER_NAME
      USER_NAME=work
      chown -R $USER_NAME:$GROUP_NAME /home/work
    fi
    export SHELL=/bin/bash
  fi
  export LD_LIBRARY_PATH="/opt/backend.ai/lib:$LD_LIBRARY_PATH"
  export HOME="/home/$USER_NAME"

  # Invoke image-specific bootstrap hook.
  if [ -x "/opt/container/bootstrap.sh" ]; then
    echo 'Executing image bootstrap... '
    export LOCAL_USER_ID=$USER_ID
    export LOCAL_GROUP_ID=$GROUP_ID
    . /opt/container/bootstrap.sh
    echo 'Image bootstrap executed.'
  fi

  # Correct the ownership of agent socket.
  chown $USER_ID:$GROUP_ID /opt/kernel/agent.sock

  # Extract dotfiles
  /opt/kernel/su-exec $USER_ID:$GROUP_ID /opt/backend.ai/bin/python /opt/kernel/extract_dotfiles.py

  echo "Executing the main program..."
  exec /opt/kernel/su-exec $USER_ID:$GROUP_ID "$@"

fi
