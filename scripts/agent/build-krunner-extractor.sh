#! /bin/sh

# IMPORTANT: this must be executed at the respository root.

docker build -f src/ai/backend/runner/krunner-extractor.dockerfile -t backendai-krunner-extractor:latest src/ai/backend/runner
docker save backendai-krunner-extractor:latest | xz > src/ai/backend/runner/krunner-extractor.img.tar.xz
