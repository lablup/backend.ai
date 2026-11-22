# Build context: this directory.
FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY *.go ./
RUN CGO_ENABLED=0 go build -trimpath -o /bai-dra-driver .

FROM gcr.io/distroless/static-debian12
COPY --from=build /bai-dra-driver /bai-dra-driver
ENTRYPOINT ["/bai-dra-driver"]
