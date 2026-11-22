# The node helper: the kube image plus nerdctl (commit and push of CRI containers) and crane
# (image labels in the registry: `nerdctl commit` has no LABEL change).
# A version bump changes its checksum too (the release's SHA256SUMS / checksums.txt).
ARG BASE
FROM alpine:3.20 AS tools
ARG NERDCTL_VERSION=2.4.2
ARG NERDCTL_SHA256=41a66995888043c0ba05f8061574eaba1b9e06b9b21c2a238215179df2728d3f
ARG CRANE_VERSION=0.22.1
ARG CRANE_SHA256=0ab7a1d6932a213aed964ce97666c3077fe691c8606413674a8b3e0b9ec4cda0
RUN wget -qO /tmp/nerdctl.tar.gz "https://github.com/containerd/nerdctl/releases/download/v${NERDCTL_VERSION}/nerdctl-${NERDCTL_VERSION}-linux-amd64.tar.gz" \
 && echo "${NERDCTL_SHA256}  /tmp/nerdctl.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/nerdctl.tar.gz -C /usr/local/bin nerdctl \
 && wget -qO /tmp/crane.tar.gz "https://github.com/google/go-containerregistry/releases/download/v${CRANE_VERSION}/go-containerregistry_Linux_x86_64.tar.gz" \
 && echo "${CRANE_SHA256}  /tmp/crane.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/crane.tar.gz -C /usr/local/bin crane \
 && rm /tmp/nerdctl.tar.gz /tmp/crane.tar.gz

FROM ${BASE}
COPY --from=tools /usr/local/bin/nerdctl /usr/local/bin/crane /usr/local/bin/
