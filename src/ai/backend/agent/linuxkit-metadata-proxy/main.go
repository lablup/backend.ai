package main

import (
	"flag"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"strconv"
)

// Hop-by-hop headers. These are removed when sent to the backend.
// http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html
var hopHeaders = []string{
	"Connection",
	"Keep-Alive",
	"Proxy-Authenticate",
	"Proxy-Authorization",
	"Te", // canonicalized version of "TE"
	"Trailers",
	"Transfer-Encoding",
	"Upgrade",
}

func handleHTTP(w http.ResponseWriter, req *http.Request, remotePort int) {
	req.URL = &url.URL{
		Scheme:      "http",
		Opaque:      req.URL.Opaque,
		User:        req.URL.User,
		Host:        "host.docker.internal:" + strconv.Itoa(remotePort),
		Path:        req.URL.Path,
		RawPath:     req.URL.RawPath,
		ForceQuery:  req.URL.ForceQuery,
		RawQuery:    req.URL.RawQuery,
		Fragment:    req.URL.Fragment,
		RawFragment: req.URL.RawFragment,
	}
	req.Host = "host.docker.internal:" + strconv.Itoa(remotePort)
	log.Printf("%s %s\n", req.Method, req.URL)
	delHopHeaders(req.Header)
	if clientIP, _, err := net.SplitHostPort(req.RemoteAddr); err == nil {
		req.Header.Set("X-Forwarded-For", clientIP)
	}
	resp, err := http.DefaultTransport.RoundTrip(req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()
	copyHeader(w.Header(), resp.Header)
	w.WriteHeader(resp.StatusCode)
	io.Copy(w, resp.Body)
}

func copyHeader(dst, src http.Header) {
	for k, vv := range src {
		for _, v := range vv {
			dst.Add(k, v)
		}
	}
}

func delHopHeaders(header http.Header) {
	for _, h := range hopHeaders {
		header.Del(h)
	}
}

func main() {
	var localPort int
	var remotePort int
	flag.IntVar(&localPort, "port", 50128, "Target port for proxy to listen")
	flag.IntVar(&remotePort, "remote-port", 8000, "Remote metadata server listening port")
	flag.Parse()
	server := &http.Server{
		Addr: ":" + strconv.Itoa(localPort),
		Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			handleHTTP(w, r, remotePort)
		}),
	}
	log.Printf("Listening on 0.0.0.0:%d -> host.docker.internal:%d\n", localPort, remotePort)
	log.Fatal(server.ListenAndServe())
}
