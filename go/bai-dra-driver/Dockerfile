# Build context: this directory.
FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY *.go ./
COPY nvmig/ ./nvmig/
# go-nvml needs cgo; libnvidia-ml is loaded at run time from the node's driver root (dynamic MIG).
RUN CGO_ENABLED=1 CGO_CFLAGS=-Wno-deprecated-declarations go build -trimpath -o /bai-dra-driver .

FROM gcr.io/distroless/base-debian12
COPY --from=build /bai-dra-driver /bai-dra-driver
COPY nvmig/NOTICE /licenses/nvmig-NOTICE
ENTRYPOINT ["/bai-dra-driver"]
