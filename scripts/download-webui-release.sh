#! /bin/sh

if [ $# -ne 1 ]; then
    echo "Usage: $0 <webui-version>"
    exit 1
fi

BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)
TARGET_VERSION=$1

cd $BASE_PATH/src/ai/backend/web
curl --fail -sL https://github.com/lablup/backend.ai-webui/releases/download/v$TARGET_VERSION/backend.ai-webui-bundle-$TARGET_VERSION.zip > /tmp/bai-webui.zip
if [ $? -ne 0 ]; then
    echo "Failed to download the webui bundle."
    exit 1
fi
rm -rf static
mkdir static
cd static
unzip /tmp/bai-webui.zip
cd $BASE_PATH
git add src/ai/backend/web/static

echo "Updated built-in static webui to $TARGET_VERSION"
