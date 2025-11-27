#!/bin/bash

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

# For Kubernetes deployments: Create symlinks to files/dirs in scratch volume
# This must be done in the main container (not init container) since symlinks don't persist across containers
if [ -d "/mnt/scratch" ]; then
  # Find the krunner directory (matches backendai-krunner.v*.*.static-gnu pattern)
  KRUNNER_DIR=$(find /mnt/scratch -maxdepth 1 -type d -name "backendai-krunner.v*.*.static-gnu" 2>/dev/null | head -1)
  if [ -n "$KRUNNER_DIR" ]; then
    echo "Creating /opt/backend.ai symlink to $KRUNNER_DIR"
    echo "Verifying krunner directory contents:"
    ls -la "$KRUNNER_DIR" | head -10
    mkdir -p /opt
    rm -rf /opt/backend.ai
    ln -sf "$KRUNNER_DIR" /opt/backend.ai
    echo "Symlink created, verifying:"
    ls -la /opt/backend.ai | head -10
  else
    echo "ERROR: Could not find krunner directory in /mnt/scratch"
    echo "Contents of /mnt/scratch:"
    ls -la /mnt/scratch
  fi

  # Find the kernel-specific scratch directory (UUID pattern)
  KERNEL_SCRATCH=$(find /mnt/scratch -maxdepth 1 -type d -regextype posix-extended -regex '.*/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' 2>/dev/null | head -1)
  if [ -n "$KERNEL_SCRATCH" ]; then
    echo "Found kernel scratch directory: $KERNEL_SCRATCH"

    # Create symlinks for /home/work and /home/config
    if [ -d "$KERNEL_SCRATCH/work" ]; then
      echo "Creating /home/work symlink"
      mkdir -p /home
      rm -rf /home/work
      ln -sf "$KERNEL_SCRATCH/work" /home/work
    fi

    if [ -d "$KERNEL_SCRATCH/config" ]; then
      echo "Creating /home/config symlink"
      mkdir -p /home
      rm -rf /home/config
      ln -sf "$KERNEL_SCRATCH/config" /home/config
    fi

    # Create symlink for agent.sock
    if [ -f "$KERNEL_SCRATCH/agent.sock" ]; then
      echo "Creating /opt/kernel/agent.sock symlink"
      mkdir -p /opt/kernel
      rm -rf /opt/kernel/agent.sock
      ln -sf "$KERNEL_SCRATCH/agent.sock" /opt/kernel/agent.sock
    fi
  fi
fi

# For Kubernetes deployments: Create symlinks from /opt/kernel-runner/* to /opt/kernel/*
# This allows us to mount the entire runner/ directory once instead of 20+ individual files
# Only needed if /opt/kernel-runner exists (K8s deployment)
if [ -d "/opt/kernel-runner" ]; then
  echo "Setting up runner file symlinks from /opt/kernel-runner to /opt/kernel..."
  mkdir -p /opt/kernel /usr/local/bin /usr/local/share/man/man1

  # Create symlinks for all runner files
  for file in /opt/kernel-runner/*; do
    if [ -f "$file" ]; then
      filename=$(basename "$file")

      # Determine target location based on file purpose
      case "$filename" in
        all-smi.*.bin)
          # all-smi goes to /usr/local/bin
          ln -sf "$file" /usr/local/bin/all-smi
          ;;
        all-smi.1)
          # Man page for all-smi
          ln -sf "$file" /usr/local/share/man/man1/all-smi.1
          ;;
        *)
          # Everything else goes to /opt/kernel
          # Remove architecture suffixes for cleaner names (e.g., su-exec.aarch64.bin -> su-exec)
          target_name=$(echo "$filename" | sed -E 's/\.(aarch64|x86_64)\.(bin|so)$//; s/\.(ubuntu[0-9.]+|alpine[0-9.]+)\.//; s/\.bin$//')
          ln -sf "$file" "/opt/kernel/$target_name"
          ;;
      esac
    fi
  done
  echo "Runner file symlinks created successfully"
fi

# Symlink the scp binary
if [ ! -f "/usr/bin/scp" ]; then
  ln -s /opt/kernel/dropbearmulti /usr/bin/scp
fi

if [ $USER_ID -eq 0 ]; then

  echo "WARNING: Running the user codes as root is not recommended."
  if [ -f /bin/ash ]; then  # for alpine
    export SHELL=/bin/ash
    addgroup -g 1002 grpread
    usermod -aG grpread $USER_NAME
  else  # for other distros (ubuntu, centos, etc.)
    export SHELL=/bin/bash
    addgroup -g 1002 grpread
    usermod -aG grpread $USER_NAME
    echo "$LD_PRELOAD" | tr ':' '\n' > /etc/ld.so.preload
    unset LD_PRELOAD
  fi
  export LD_LIBRARY_PATH="/opt/backend.ai/lib:$LD_LIBRARY_PATH"
  export HOME="/home/work"

  # Invoke image-specific bootstrap hook.
  if [ -f "/opt/container/bootstrap.sh" ]; then
    if [ -x "/opt/container/bootstrap.sh" ]; then
      echo 'Executing image bootstrap…'
      . /opt/container/bootstrap.sh
      echo 'Image bootstrap executed.'
    else
      echo 'WARNING: /opt/container/bootstrap.sh exists but is not executable; bootstrap.sh execution was skipped.'
    fi
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
    echo "work:$ALPHA_NUMERIC_VAL" | chpasswd -c SHA512
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
      addgroup --gid 1002 grpread
      usermod -aG grpread $USER_NAME
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
      addgroup --gid 1002 grpread
      usermod -aG 1002 $USER_NAME
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
  if [ -f "/opt/container/bootstrap.sh" ]; then
    if [ -x "/opt/container/bootstrap.sh" ]; then
      echo 'Executing image bootstrap... '
      export LOCAL_USER_ID=$USER_ID
      export LOCAL_GROUP_ID=$GROUP_ID
      . /opt/container/bootstrap.sh
      echo 'Image bootstrap executed.'
    else
      echo 'WARNING: /opt/container/bootstrap.sh exists but is not executable; bootstrap.sh execution was skipped.'
    fi
  fi

  # Correct the ownership of agent socket (if it exists).
  if [ -e /opt/kernel/agent.sock ]; then
    chown $USER_ID:$GROUP_ID /opt/kernel/agent.sock
  fi

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
    echo "$USER_NAME:$ALPHA_NUMERIC_VAL" | chpasswd -c SHA512
  fi

  # Create groups for ADDITIONAL_GIDS if they don't exist
  if [ ! -z "${ADDITIONAL_GIDS}" ]; then
    echo "Processing additional GIDs: ${ADDITIONAL_GIDS}"

    # Convert comma-separated list to individual lines and process
    echo "${ADDITIONAL_GIDS}" | tr ',' '\n' | while read -r gid; do
      if [ ! -z "$gid" ]; then
        # Clean whitespace
        gid=$(echo "$gid" | tr -d ' \t')

        # Check if group exists, create if not
        if ! getent group "$gid" > /dev/null 2>&1; then
          echo "Creating group with GID $gid"
          addgroup --gid "$gid" "group$gid"
          if usermod -aG "$gid" $USER_NAME 2>/dev/null; then
            echo "Added $USER_NAME to group$gid"
          else
            echo "Failed to add $USER_NAME to group$gid"
          fi
        else
          echo "Group with GID $gid already exists"
        fi
      fi
    done
  fi

  # The gid 42 is a reserved gid for "shadow" to allow passwrd-based SSH login. (lablup/backend.ai#751)
  # Note that we also need to use our own patched version of su-exec to support multiple gids.

  # Change to /home/work to ensure the working directory is accessible to the non-root user
  # This prevents "pwd: couldn't find directory entry in '..'" errors when Python's getpath
  # tries to resolve paths during initialization
  cd /home/work

  echo "Executing the main program: /opt/kernel/su-exec \"$USER_ID:$GROUP_ID${ADDITIONAL_GIDS:+,$ADDITIONAL_GIDS},42\" \"$@\"..."
  exec /opt/kernel/su-exec "$USER_ID:$GROUP_ID${ADDITIONAL_GIDS:+,$ADDITIONAL_GIDS},42" "$@"

fi
