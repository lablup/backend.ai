#! /bin/sh

USER_ID=${LOCAL_USER_ID:-9001}
GROUP_ID=${LOCAL_GROUP_ID:-9001}

echo "Kernel started at: $(date -Iseconds -u)"
echo "LOCAL_USER_ID=$LOCAL_USER_ID"
echo "LOCAL_GROUP_ID=$LOCAL_GROUP_ID"
echo "USER_ID=$USER_ID"
echo "GROUP_ID=$GROUP_ID"
if [ -z "$LOCAL_USER_ID" ]; then
  echo "WARNING: \$LOCAL_USER_ID is an empty value. This may be a misbehavior of plugins manipulating the evironment variables of new containers and cause unexpected errors."
fi

# NOTE: /home/work may have vfolder bind-mounts containing a LOT of files (e.g., more than 10K!).
#       Therefore, we must AVOID any filesystem operation applied RECURSIVELY to /home/work,
#       to prevent indefinite "hangs" during a container startup.

if [ $USER_ID -eq 0 ]; then

  echo "WARNING: Running the user codes as root is not recommended."
  if [ -f /bin/ash ]; then  # for alpine
    export SHELL=/bin/ash
  else  # for other distros (ubuntu, centos, etc.)
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
  /opt/backend.ai/bin/python -s /opt/kernel/extract_dotfiles.py

  # Start ssh-agent if it is available
  if command -v ssh-agent > /dev/null; then
    eval "$(ssh-agent -s)"
    setsid ssh-add /home/work/.ssh/id_rsa < /dev/null
  fi

  echo "Generate random alpha-numeric password"
  if [ ! -f "$HOME/.password" ]; then
    /opt/backend.ai/bin/python -s /opt/kernel/fantompass.py > "$HOME/.password"
    export ALPHA_NUMERIC_VAL=$(cat $HOME/.password)
    chmod 0644 "$HOME/.password"
    echo "work:$ALPHA_NUMERIC_VAL" | chpasswd
  fi

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
      usermod -aG shadow $USER_NAME
    fi
    export SHELL=/bin/ash
  else  # for other distros (ubuntu, centos, etc.)
    echo "$LD_PRELOAD" | tr ':' '\n' > /etc/ld.so.preload
    unset LD_PRELOAD
    if [ -z "$GROUP_NAME" ]; then
      GROUP_NAME=work
      groupadd -g $GROUP_ID $GROUP_NAME
    fi
    if [ -z "$USER_NAME" ]; then
      USER_NAME=work
      useradd -s /bin/bash -d "/home/$USER_NAME" -M -r -u $USER_ID -g $GROUP_NAME -o -c "User" $USER_NAME
      usermod -aG shadow $USER_NAME
    else
      # The image has an existing user name for the given uid.
      # Merge the image's existing home directory into the bind-mounted "/home/work" from the scratch space.
      # NOTE: Since the image layer and the scratch directory may reside in different filesystems,
      #       we cannot use hard-links to reduce the copy overhead.
      #       It assumes that the number/size of files in the image's home directory is not very large.
      cp -Rp "/home/$USER_NAME/*" /home/work/
      cp -Rp "/home/$USER_NAME/.*" /home/work/
      # Rename the user to "work" and let it use "/home/work" as the new home directory.
      usermod -s /bin/bash -d /home/work -l work -g $GROUP_NAME $USER_NAME
      USER_NAME=work
      usermod -aG shadow $USER_NAME
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
  /opt/kernel/su-exec $USER_ID:$GROUP_ID /opt/backend.ai/bin/python -s /opt/kernel/extract_dotfiles.py

  # Start ssh-agent if it is available
  if command -v ssh-agent > /dev/null; then
    eval "$(/opt/kernel/su-exec $USER_ID:$GROUP_ID ssh-agent)"
    setsid ssh-add /home/work/.ssh/id_rsa < /dev/null
  fi

  echo "Generate random alpha-numeric password"
  if [ ! -f "$HOME/.password" ]; then
    /opt/kernel/su-exec $USER_ID:$GROUP_ID /opt/backend.ai/bin/python -s /opt/kernel/fantompass.py > "$HOME/.password"
    export ALPHA_NUMERIC_VAL=$(cat $HOME/.password)
    chmod 0644 "$HOME/.password"
    echo "$USER_NAME:$ALPHA_NUMERIC_VAL" | chpasswd
  fi

  # The gid 42 is a reserved gid for "shadow" to allow passwrd-based SSH login. (lablup/backend.ai#751)
  # Note that we also need to use our own patched version of su-exec to support multiple gids.
  echo "Executing the main program: /opt/kernel/su-exec \"$USER_ID:$GROUP_ID,42\" \"$@\"..."
  exec /opt/kernel/su-exec "$USER_ID:$GROUP_ID,42" "$@"

fi
