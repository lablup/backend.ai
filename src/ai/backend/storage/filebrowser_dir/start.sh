#!/bin/sh

/bin/filebrowser config init -d /filebrowser_dir/db/filebrowser_$1.db -p $1;
/bin/filebrowser users add admin admin -d /filebrowser_dir/db/filebrowser_$1.db;
/bin/filebrowser config import /filebrowser_dir/config.json -d /filebrowser_dir/db/filebrowser_$1.db;
/bin/filebrowser -c /filebrowser_dir/settings.json -d /filebrowser_dir/db/filebrowser_$1.db -p $1;

exit 0;
