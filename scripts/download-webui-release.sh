#! /bin/sh
BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)
TARGET_VERSION=$1

cd $BASE_PATH/src/ai/backend/web
curl -sL https://github.com/lablup/backend.ai-webui/releases/download/v$TARGET_VERSION/backend.ai-webui-bundle-$TARGET_VERSION.zip > /tmp/bai-webui.zip
rm -rf static
mkdir static
cd static
unzip /tmp/bai-webui.zip
cd $BASE_PATH
git add src/ai/backend/web/static

echo "Updated built-in static webui to $TARGET_VERSION"
