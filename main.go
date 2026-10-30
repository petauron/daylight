// Daylight is a versioned, self-contained website served by the bundled Caddy.
package main

import (
	"bytes"
	_ "embed"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
)

//go:embed site/index.html
var page string

var version = "dev"

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "daylight:", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 1 && args[0] == "version" {
		fmt.Println("Daylight", version)
		return nil
	}
	if len(args) == 0 || (args[0] != "run" && args[0] != "validate") {
		return errors.New("usage: daylight run|validate --config site.json; daylight version")
	}
	flags := flag.NewFlagSet(args[0], flag.ContinueOnError)
	configPath := flags.String("config", "", "Caddy JSON with an exact-host root HTML response")
	if err := flags.Parse(args[1:]); err != nil {
		return err
	}
	if *configPath == "" || flags.NArg() != 0 {
		return errors.New("one --config path is required")
	}
	file, err := os.Open(*configPath)
	if err != nil {
		return errors.New("cannot read site configuration")
	}
	raw, err := io.ReadAll(io.LimitReader(file, (1<<20)+1))
	file.Close()
	if err != nil || len(raw) > 1<<20 {
		return errors.New("site configuration is unreadable or exceeds 1 MiB")
	}
	rendered, err := render(raw)
	if err != nil {
		return err
	}
	executable, err := os.Executable()
	if err != nil {
		return err
	}
	// The release ships the same digest-pinned Caddy used by the managed gateway.
	// No PATH lookup, downloaded startup code, shell command or admin API is used.
	command := exec.Command(filepath.Join(filepath.Dir(executable), "caddy"), args[0], "--config", "-")
	command.Stdin = bytes.NewReader(rendered)
	command.Stdout, command.Stderr = os.Stdout, os.Stderr
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(signals)
	if err := command.Start(); err != nil {
		return errors.New("cannot start bundled Caddy")
	}
	done := make(chan error, 1)
	go func() { done <- command.Wait() }()
	for {
		select {
		case sig := <-signals:
			_ = command.Process.Signal(sig)
		case err := <-done:
			if err != nil {
				return fmt.Errorf("Caddy exited: %w", err)
			}
			return nil
		}
	}
}

// The package owns the root document. Deployment configuration owns listeners,
// hostname matching, TLS, certificates, headers and health checks. This single
// rendering path replaces only exact-host root HTML bodies; it never edits the
// source configuration or certificate store and never falls back to old content.
func render(raw []byte) ([]byte, error) {
	var config map[string]any
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if err := decoder.Decode(&config); err != nil {
		return nil, errors.New("invalid Caddy JSON")
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return nil, errors.New("configuration must contain one JSON document")
	}
	apps, _ := config["apps"].(map[string]any)
	httpApp, _ := apps["http"].(map[string]any)
	servers, _ := httpApp["servers"].(map[string]any)
	updated := 0
	for _, value := range servers {
		server, _ := value.(map[string]any)
		routes, _ := server["routes"].([]any)
		for _, value := range routes {
			route, _ := value.(map[string]any)
			matches, _ := route["match"].([]any)
			if len(matches) != 1 {
				continue
			}
			match, _ := matches[0].(map[string]any)
			paths, _ := match["path"].([]any)
			hosts, _ := match["host"].([]any)
			if len(paths) != 1 || paths[0] != "/" || len(hosts) != 1 {
				continue
			}
			host, ok := hosts[0].(string)
			if !ok || host == "" || strings.ContainsAny(host, "*/ ") {
				return nil, errors.New("the website requires an exact hostname")
			}
			handlers, _ := route["handle"].([]any)
			if len(handlers) != 1 {
				return nil, errors.New("the root route must have one HTML response")
			}
			handler, _ := handlers[0].(map[string]any)
			headers, _ := handler["headers"].(map[string]any)
			types, _ := headers["Content-Type"].([]any)
			if handler["handler"] != "static_response" || len(types) != 1 || types[0] != "text/html; charset=utf-8" {
				return nil, errors.New("the root route must be a UTF-8 HTML response")
			}
			handler["body"] = page
			updated++
		}
	}
	if updated == 0 {
		return nil, errors.New("no exact-host root HTML response is configured")
	}
	return json.Marshal(config)
}
