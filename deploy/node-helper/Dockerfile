# The node helper: the kube image plus nerdctl (commit and push of CRI containers) and crane
# (image labels in the registry: `nerdctl commit` has no LABEL change).
ARG BASE
FROM alpine:3.20 AS tools
ARG NERDCTL_VERSION=2.4.2
ARG CRANE_VERSION=0.22.1
RUN wget -qO- "https://github.com/containerd/nerdctl/releases/download/v${NERDCTL_VERSION}/nerdctl-${NERDCTL_VERSION}-linux-amd64.tar.gz" | tar -xz -C /usr/local/bin nerdctl \
 && wget -qO- "https://github.com/google/go-containerregistry/releases/download/v${CRANE_VERSION}/go-containerregistry_Linux_x86_64.tar.gz" | tar -xz -C /usr/local/bin crane

FROM ${BASE}
COPY --from=tools /usr/local/bin/nerdctl /usr/local/bin/crane /usr/local/bin/
