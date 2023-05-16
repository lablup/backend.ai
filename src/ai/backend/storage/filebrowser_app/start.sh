#!/bin/sh

useradd -r -u $1 -g $2 work
su work
/bin/filebrowser config init -d /filebrowser_app/db/filebrowser_$3.db -p $3
/bin/filebrowser users add admin admin -d /filebrowser_app/db/filebrowser_$3.db
/bin/filebrowser config import /filebrowser_app/config.json -d /filebrowser_app/db/filebrowser_$3.db
/bin/filebrowser -c /filebrowser_app/settings.json -d /filebrowser_app/db/filebrowser_$3.db -p $3

exit 0;
