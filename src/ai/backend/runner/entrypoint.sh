#! /bin/sh

USER_ID=${LOCAL_USER_ID:-9001}
GROUP_ID=${LOCAL_GROUP_ID:-9001}

# NOTE: /home/work may have vfolder bind-mounts containing a LOT of files (e.g., more than 10K!).
#       Therefore, we must AVOID any filesystem operation applied RECURSIVELY to /home/work,
#       to prevent indefinite "hangs" during a container startup.

# ---------------------------------------------------------------------------------------------
# Account database helpers
#
# The image is not required to ship shadow-utils (getent/groupadd/useradd/usermod/chpasswd),
# sed/awk/cut, or even coreutils: distroless-style images may only have a shell. Each helper
# prefers the native command when the image has it and otherwise edits /etc/passwd, /etc/group
# and /etc/shadow directly using shell builtins only; the few remaining file operations fall
# back to the kernel runner's own Python interpreter under /opt/backend.ai.
#
# NOTE: usermod -u/-g recursively chowns the home directory, so ids are always renumbered by
#       editing the files directly, even when usermod exists.
# ---------------------------------------------------------------------------------------------

PASSWD_FILE=/etc/passwd
GROUP_FILE=/etc/group
SHADOW_FILE=/etc/shadow

has_cmd() {
  command -v "$1" > /dev/null 2>&1
}

KRUNNER_PYTHON=/opt/backend.ai/bin/python

# chown OWNER:GROUP PATH (numeric ids)
do_chown() {
  if has_cmd chown; then
    chown "$1" "$2"
  else
    "$KRUNNER_PYTHON" -s -c 'import os, sys; o, g = sys.argv[1].split(":"); os.chown(sys.argv[2], int(o), int(g))' "$1" "$2"
  fi
}

# chmod OCTAL-MODE PATH
do_chmod() {
  if has_cmd chmod; then
    chmod "$1" "$2"
  else
    "$KRUNNER_PYTHON" -s -c 'import os, sys; os.chmod(sys.argv[2], int(sys.argv[1], 8))' "$1" "$2"
  fi
}

# ln -s TARGET LINK
do_symlink() {
  if has_cmd ln; then
    ln -s "$1" "$2"
  else
    "$KRUNNER_PYTHON" -s -c 'import os, sys; os.symlink(sys.argv[1], sys.argv[2])' "$1" "$2"
  fi
}

# Print the current time as ISO-8601 UTC (for the startup log).
now_iso() {
  if has_cmd date; then
    date -Iseconds -u
  else
    "$KRUNNER_PYTHON" -s -c 'import time; print(time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()))'
  fi
}

# Print the current UNIX timestamp, or nothing when unavailable.
now_epoch() {
  if has_cmd date; then
    date +%s 2> /dev/null
  else
    "$KRUNNER_PYTHON" -s -c 'import time; print(int(time.time()))' 2> /dev/null
  fi
}

# Merge the contents of directory $1 into directory $2 (cp -Rp equivalent, dotfiles included).
merge_dir() {
  if has_cmd cp; then
    (set +f; cp -Rp "$1"/* "$1"/.[!.]* "$1"/..?* "$2"/ 2> /dev/null)
    return 0
  fi
  "$KRUNNER_PYTHON" -s - "$1" "$2" << 'PYEOF'
import os
import shutil
import sys

src, dst = sys.argv[1], sys.argv[2]


def merge(s, d):
    for name in os.listdir(s):
        sp, dp = os.path.join(s, name), os.path.join(d, name)
        try:
            if os.path.islink(sp):
                if os.path.lexists(dp):
                    os.remove(dp)
                os.symlink(os.readlink(sp), dp)
            elif os.path.isdir(sp):
                if not os.path.isdir(dp):
                    os.mkdir(dp)
                shutil.copystat(sp, dp)
                merge(sp, dp)
            else:
                shutil.copy2(sp, dp)
        except OSError as e:
            print("WARNING: failed to copy %s: %s" % (sp, e), file=sys.stderr)


merge(src, dst)
PYEOF
}

is_number() {
  case "$1" in
    ''|*[!0-9]*) return 1 ;;
    *) return 0 ;;
  esac
}

# Print the passwd entry (full line) matching $1, which is a user name or a numeric uid.
passwd_lookup() {
  if has_cmd getent; then
    getent passwd "$1"
    return $?
  fi
  [ -r "$PASSWD_FILE" ] || return 2
  while IFS= read -r _line || [ -n "$_line" ]; do
    _name=${_line%%:*}
    _rest=${_line#*:}; _rest=${_rest#*:}
    _uid=${_rest%%:*}
    if is_number "$1"; then
      [ "$_uid" = "$1" ] || continue
    else
      [ "$_name" = "$1" ] || continue
    fi
    printf '%s\n' "$_line"
    return 0
  done < "$PASSWD_FILE"
  return 2
}

# Print the group entry (full line) matching $1, which is a group name or a numeric gid.
group_lookup() {
  if has_cmd getent; then
    getent group "$1"
    return $?
  fi
  [ -r "$GROUP_FILE" ] || return 2
  while IFS= read -r _line || [ -n "$_line" ]; do
    _name=${_line%%:*}
    _rest=${_line#*:}; _rest=${_rest#*:}
    _gid=${_rest%%:*}
    if is_number "$1"; then
      [ "$_gid" = "$1" ] || continue
    else
      [ "$_name" = "$1" ] || continue
    fi
    printf '%s\n' "$_line"
    return 0
  done < "$GROUP_FILE"
  return 2
}

# Print the name of the user with uid $1, or nothing.
passwd_name_of() {
  _entry=$(passwd_lookup "$1") || return 1
  printf '%s\n' "${_entry%%:*}"
}

# Print the name of the group with gid $1, or nothing.
group_name_of() {
  _entry=$(group_lookup "$1") || return 1
  printf '%s\n' "${_entry%%:*}"
}

# Print "uid:gid" of the user named $1, or nothing.
passwd_ids_of() {
  _entry=$(passwd_lookup "$1") || return 1
  _rest=${_entry#*:}; _rest=${_rest#*:}
  _uid=${_rest%%:*}; _rest=${_rest#*:}
  _gid=${_rest%%:*}
  printf '%s:%s\n' "$_uid" "$_gid"
}

days_since_epoch() {
  _now=$(now_epoch) || _now=""
  if is_number "$_now"; then
    echo $((_now / 86400))
  else
    echo ""
  fi
}

# Rewrite the passwd entry named $1.
# $2: new name  $3: new uid  $4: new gid  $5: new home  $6: new shell  (empty = keep)
passwd_update() {
  [ -r "$PASSWD_FILE" ] || return 1
  _out=""
  _found=1
  while IFS= read -r _line || [ -n "$_line" ]; do
    case "$_line" in
      "$1":*:*:*:*:*:*)
        _found=0
        _rest=${_line#*:}
        _pw=${_rest%%:*}; _rest=${_rest#*:}
        _uid=${_rest%%:*}; _rest=${_rest#*:}
        _gid=${_rest%%:*}; _rest=${_rest#*:}
        _gecos=${_rest%%:*}; _rest=${_rest#*:}
        _home=${_rest%%:*}
        _shell=${_rest#*:}
        _line="${2:-$1}:$_pw:${3:-$_uid}:${4:-$_gid}:$_gecos:${5:-$_home}:${6:-$_shell}"
        ;;
    esac
    _out="$_out$_line
"
  done < "$PASSWD_FILE"
  [ $_found -eq 0 ] || return 1
  printf '%s' "$_out" > "$PASSWD_FILE"
}

# Rename the shadow entry $1 to $2 (no-op when the file or the entry does not exist).
shadow_rename() {
  [ -r "$SHADOW_FILE" ] || return 0
  _out=""
  while IFS= read -r _line || [ -n "$_line" ]; do
    case "$_line" in
      "$1":*) _line="$2:${_line#*:}" ;;
    esac
    _out="$_out$_line
"
  done < "$SHADOW_FILE"
  printf '%s' "$_out" > "$SHADOW_FILE"
}

# Rewrite the group entry named $1.
# $2: new gid (empty = keep)  $3: member to add (empty = none)  $4: member to rename from  $5: to
group_update() {
  [ -r "$GROUP_FILE" ] || return 1
  _out=""
  _found=1
  while IFS= read -r _line || [ -n "$_line" ]; do
    case "$_line" in
      *:*:*:*)
        _name=${_line%%:*}
        _rest=${_line#*:}
        _pw=${_rest%%:*}; _rest=${_rest#*:}
        _gid=${_rest%%:*}
        _members=${_rest#*:}
        if [ -n "$4" ]; then
          _new_members=""
          _saved_ifs=$IFS; IFS=,
          for _m in $_members; do
            [ "$_m" = "$4" ] && _m=$5
            _new_members="${_new_members:+$_new_members,}$_m"
          done
          IFS=$_saved_ifs
          _members=$_new_members
        fi
        if [ "$_name" = "$1" ] || { is_number "$1" && [ "$_gid" = "$1" ]; }; then
          _found=0
          if [ -n "$3" ]; then
            case ",$_members," in
              *",$3,"*) ;;
              *) _members="${_members:+$_members,}$3" ;;
            esac
          fi
          _line="$_name:$_pw:${2:-$_gid}:$_members"
        else
          _line="$_name:$_pw:$_gid:$_members"
        fi
        ;;
    esac
    _out="$_out$_line
"
  done < "$GROUP_FILE"
  if [ -z "$1" ]; then
    _found=0
  fi
  [ $_found -eq 0 ] || return 1
  printf '%s' "$_out" > "$GROUP_FILE"
}

# Create the group $1 with gid $2.
group_create() {
  if has_cmd groupadd; then
    groupadd -g "$2" "$1"
  elif has_cmd addgroup; then
    addgroup -g "$2" "$1"
  else
    printf '%s:x:%s:\n' "$1" "$2" >> "$GROUP_FILE"
  fi
}

# Create the user $1 with uid $2, primary group $3 (name) / $4 (gid), and login shell $5.
# The home directory is /home/$1 and is never created here (it is a bind-mount from the scratch space).
user_create() {
  if has_cmd useradd; then
    useradd -s "$5" -d "/home/$1" -M -r -u "$2" -g "$3" -o -c "User" "$1"
  elif has_cmd adduser; then
    adduser -s "$5" -h "/home/$1" -H -D -u "$2" -G "$3" -g "User" "$1"
  else
    printf '%s:x:%s:%s:User:/home/%s:%s\n' "$1" "$2" "$4" "$1" "$5" >> "$PASSWD_FILE" || return 1
    if [ ! -e "$SHADOW_FILE" ]; then
      # The gid 42 is reserved for "shadow" so that the session user can read this file (see below).
      : > "$SHADOW_FILE" && do_chown 0:42 "$SHADOW_FILE" && do_chmod 0640 "$SHADOW_FILE"
    fi
    printf '%s:!:%s:0:99999:7:::\n' "$1" "$(days_since_epoch)" >> "$SHADOW_FILE"
  fi
}

# Add the user $2 to the supplementary group $1 (name or gid).
group_add_member() {
  if [ -z "$2" ]; then
    echo "WARNING: no user name to add to the group '$1'"
    return 1
  fi
  if has_cmd usermod; then
    usermod -aG "$1" "$2"
  else
    group_update "$1" "" "$2" \
      || { echo "WARNING: group '$1' not found; cannot add the user '$2' to it" >&2; return 1; }
  fi
}

# Rename the user $1 to $2, moving its home to $3 and setting its shell to $4.
user_rename() {
  if has_cmd usermod; then
    usermod -s "$4" -d "$3" -l "$2" "$1"
  else
    passwd_update "$1" "$2" "" "" "$3" "$4" || return 1
    shadow_rename "$1" "$2"
    group_update "" "" "" "$1" "$2"
  fi
}

# Set the password of the user $1 to $2.
user_set_password() {
  if has_cmd chpasswd; then
    echo "$1:$2" | chpasswd -c SHA512
    return $?
  fi
  if ! passwd_lookup "$1" > /dev/null 2>&1; then
    echo "WARNING: cannot set the password of '$1': no such user" >&2
    return 1
  fi
  _hash=$(printf '%s\n' "$2" | /opt/backend.ai/bin/python -s /opt/kernel/sha512_crypt.py) || return 1
  [ -n "$_hash" ] || return 1
  if [ ! -e "$SHADOW_FILE" ]; then
    : > "$SHADOW_FILE" && do_chown 0:42 "$SHADOW_FILE" && do_chmod 0640 "$SHADOW_FILE"
  fi
  _days=$(days_since_epoch)
  _out=""
  _found=1
  while IFS= read -r _line || [ -n "$_line" ]; do
    case "$_line" in
      "$1":*)
        _found=0
        _rest=${_line#*:}      # drop name
        _rest=${_rest#*:}      # drop old hash
        case "$_rest" in
          *:*) _rest=${_rest#*:} ;;  # drop old lastchg
          *) _rest="0:99999:7:::" ;;
        esac
        _line="$1:$_hash:$_days:$_rest"
        ;;
    esac
    _out="$_out$_line
"
  done < "$SHADOW_FILE"
  if [ $_found -ne 0 ]; then
    _out="$_out$1:$_hash:$_days:0:99999:7:::
"
  fi
  printf '%s' "$_out" > "$SHADOW_FILE"
}

write_ld_so_preload() {
  # One entry per line; LD_PRELOAD is colon-separated.
  (IFS=:; set -f; printf '%s\n' $LD_PRELOAD) > /etc/ld.so.preload \
    || echo "WARNING: failed to write /etc/ld.so.preload"
}

# ---------------------------------------------------------------------------------------------

echo "Kernel started at: $(now_iso)"
echo "LOCAL_USER_ID=$LOCAL_USER_ID"
echo "LOCAL_GROUP_ID=$LOCAL_GROUP_ID"
echo "USER_ID=$USER_ID"
echo "GROUP_ID=$GROUP_ID"
if [ -z "$LOCAL_USER_ID" ]; then
  echo "WARNING: \$LOCAL_USER_ID is an empty value. This may be a misbehavior of plugins manipulating the evironment variables of new containers and cause unexpected errors."
fi

# Symlink the scp binary
if [ ! -f "/usr/bin/scp" ]; then
  do_symlink /opt/kernel/dropbearmulti /usr/bin/scp
fi

if [ -f /bin/ash ]; then  # for alpine (busybox)
  export SHELL=/bin/ash
else  # for other distros (ubuntu, centos, etc.)
  export SHELL=/bin/bash
fi

if [ $USER_ID -eq 0 ]; then

  echo "WARNING: Running the user codes as root is not recommended."
  if [ ! -f /bin/ash ]; then
    write_ld_so_preload
    unset LD_PRELOAD
  fi
  group_lookup grpread > /dev/null 2>&1 || group_create grpread 1002
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
    IFS= read -r ALPHA_NUMERIC_VAL < "$HOME/.password" || [ -n "$ALPHA_NUMERIC_VAL" ]
    export ALPHA_NUMERIC_VAL
    do_chmod 0644 "$HOME/.password"
    user_set_password work "$ALPHA_NUMERIC_VAL"
  fi

  echo "Executing the main program..."
  exec "$@"

else

  echo "Setting up uid and gid: $USER_ID:$GROUP_ID"
  USER_NAME=$(passwd_name_of "$USER_ID")
  GROUP_NAME=$(group_name_of "$GROUP_ID")
  if [ ! -f /bin/ash ]; then
    write_ld_so_preload
    unset LD_PRELOAD
  fi
  # NOTE: A committed image may carry a "work" user/group with stale ids. Renumber them by
  #       editing the files directly (see the helper notes above).
  if [ -z "$GROUP_NAME" ]; then
    GROUP_NAME=work
    if group_lookup "$GROUP_NAME" > /dev/null 2>&1; then
      group_update "$GROUP_NAME" "$GROUP_ID"
    else
      group_create "$GROUP_NAME" "$GROUP_ID" \
        || echo "WARNING: failed to create the group '$GROUP_NAME' with gid $GROUP_ID"
    fi
  fi
  if [ -z "$USER_NAME" ]; then
    USER_NAME=work
    if passwd_lookup "$USER_NAME" > /dev/null 2>&1; then
      passwd_update "$USER_NAME" "" "$USER_ID" "$GROUP_ID"
    else
      user_create "$USER_NAME" "$USER_ID" "$GROUP_NAME" "$GROUP_ID" "$SHELL" \
        || echo "WARNING: failed to create the user '$USER_NAME' with uid $USER_ID"
    fi
    group_add_member shadow "$USER_NAME"
    if ! group_lookup grpread > /dev/null 2>&1; then
      group_create grpread 1002
    fi
    group_add_member grpread "$USER_NAME"
  else
    if [ "$USER_NAME" != "work" ]; then
      # The image has an existing user name for the given uid.
      # Merge the image's existing home directory into the bind-mounted "/home/work" from the scratch space.
      # NOTE: Since the image layer and the scratch directory may reside in different filesystems,
      #       we cannot use hard-links to reduce the copy overhead.
      #       It assumes that the number/size of files in the image's home directory is not very large.
      if [ -d "/home/$USER_NAME" ]; then
        merge_dir "/home/$USER_NAME" /home/work
      fi
      # Rename the user to "work" and let it use "/home/work" as the new home directory.
      user_rename "$USER_NAME" work /home/work "$SHELL" \
        || echo "WARNING: failed to rename the user '$USER_NAME' to 'work'"
      USER_NAME=work
    fi
    passwd_update "$USER_NAME" "" "$USER_ID" "$GROUP_ID"
    group_add_member shadow "$USER_NAME"
  fi
  if [ "$(passwd_ids_of "$USER_NAME")" != "$USER_ID:$GROUP_ID" ]; then
    echo "ERROR: /etc/passwd entry for '$USER_NAME' does not match $USER_ID:$GROUP_ID"
    exit 1
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

  # Correct the ownership of agent socket.
  do_chown "$USER_ID:$GROUP_ID" /opt/kernel/agent.sock

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
    IFS= read -r ALPHA_NUMERIC_VAL < "$HOME/.password" || [ -n "$ALPHA_NUMERIC_VAL" ]
    export ALPHA_NUMERIC_VAL
    do_chmod 0644 "$HOME/.password"
    user_set_password "$USER_NAME" "$ALPHA_NUMERIC_VAL"
  fi

  # Create groups for ADDITIONAL_GIDS if they don't exist
  if [ -n "${ADDITIONAL_GIDS}" ]; then
    echo "Processing additional GIDs: ${ADDITIONAL_GIDS}"
    _saved_ifs=$IFS
    IFS=", $(printf '\t')"
    set -f
    for gid in $ADDITIONAL_GIDS; do
      IFS=$_saved_ifs
      [ -n "$gid" ] || continue
      # Check if group exists, create if not
      if ! group_lookup "$gid" > /dev/null 2>&1; then
        echo "Creating group with GID $gid"
        group_create "group$gid" "$gid"
      else
        echo "Group with GID $gid already exists"
      fi
      # Ensure membership even when the group pre-exists (e.g., baked into a committed image)
      if group_add_member "$gid" "$USER_NAME" 2> /dev/null; then
        echo "Added $USER_NAME to group with GID $gid"
      else
        echo "Failed to add $USER_NAME to group with GID $gid"
      fi
    done
    set +f
    IFS=$_saved_ifs
  fi

  # The gid 42 is a reserved gid for "shadow" to allow passwrd-based SSH login. (lablup/backend.ai#751)
  # Note that we also need to use our own patched version of su-exec to support multiple gids.
  echo "Executing the main program: /opt/kernel/su-exec \"$USER_ID:$GROUP_ID${ADDITIONAL_GIDS:+,$ADDITIONAL_GIDS},42\" \"$@\"..."
  exec /opt/kernel/su-exec "$USER_ID:$GROUP_ID${ADDITIONAL_GIDS:+,$ADDITIONAL_GIDS},42" "$@"

fi
