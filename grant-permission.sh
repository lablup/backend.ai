#!/bin/sh
sudo chown -R jopemachine ./tmp ./volumes/
sudo chgrp -R jopemachine ./volumes/ ./tmp
sudo chmod -R 777 ./volumes/ ./tmp/
