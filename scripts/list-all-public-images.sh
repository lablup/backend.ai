#! /bin/bash

if ! type "curl" > /dev/null; then
  echo "This script requires curl to run."
  exit 1
fi
if ! type "jq" > /dev/null; then
  curl -sSL "https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64" -o jq
  chmod +x ./jq
  jq='./jq'
else
  jq='jq'
fi

org="lablup"
registry="https://registry-1.docker.io"
authBase="https://auth.docker.io"

images=$(curl -s \
  "https://hub.docker.com/v2/repositories/$org/?page_size=100" -o - | $jq -r '.results[].name')
for imageName in $images
do
  if [[ $imageName =~ ^kernel-.*$ ]]; then
    image="$org/$imageName"
    token=$(curl -fsSL "$authBase/token?service=registry.docker.io&scope=repository:$image:pull" | $jq -r '.token')
    imageTags=$(curl -s \
      -H "Authorization: Bearer $token" \
      "$registry/v2/$image/tags/list" -o - | $jq -r '.tags[]')
    for imageTag in $imageTags
    do
      imageDigest=$(curl -s \
        -H "Authorization: Bearer $token" \
        -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
        "$registry/v2/$image/manifests/$imageTag" -o - | $jq -r '.config.digest')
      printf "%-40s %-30s %32s\n" $image $imageTag $imageDigest
    done
  fi
done
exit 0
