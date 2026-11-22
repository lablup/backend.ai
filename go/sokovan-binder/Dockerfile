# Build context: this directory.
FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY *.go ./
RUN CGO_ENABLED=0 go build -trimpath -o /sokovan-binder .

FROM gcr.io/distroless/static-debian12
COPY --from=build /sokovan-binder /sokovan-binder
ENTRYPOINT ["/sokovan-binder"]
