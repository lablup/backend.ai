#!/bin/sh
useradd -r -u $1 -g $2 work
su work
/bin/filebrowser config init -d /filebrowser_dir/db/filebrowser_$3.db -p $3
/bin/filebrowser users add admin admin -d /filebrowser_dir/db/filebrowser_$3.db
/bin/filebrowser config import /filebrowser_dir/config.json -d /filebrowser_dir/db/filebrowser_$3.db
/bin/filebrowser -c /filebrowser_dir/settings.json -d /filebrowser_dir/db/filebrowser_$3.db -p $3

exit 0