package main

import (
	"flag"
	"fmt"
	"os"
	"path"
	"path/filepath"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/spec"
)

func runGenerate(args []string) error {
	fs := flag.NewFlagSet("generate", flag.ContinueOnError)
	root := fs.String("root", ".", "repository root")
	if err := fs.Parse(args); err != nil {
		return err
	}
	loaded, err := spec.Load(*root)
	if err != nil {
		return err
	}
	reg, err := loadRegistry(filepath.Join(*root, loaded.Words.Registry))
	if err != nil {
		return err
	}
	for name, content := range reg.render() {
		if err := os.WriteFile(filepath.Join(*root, name), []byte(content), 0o644); err != nil {
			return err
		}
	}
	return nil
}

// render returns the glossary documents by their path from the root.
func (r *registry) render() map[string]string {
	documents := map[string]string{}
	for _, lang := range languages {
		page := r.rules.Documents[lang]
		documents[page.Path] = r.renderGlossary(lang)
		for _, name := range r.rules.Topics {
			documents[strings.ReplaceAll(page.TermPath, topicPlaceholder, name)] = r.renderTerms(lang, name)
		}
	}
	return documents
}

// markdown joins blocks with a blank line, after the note that the file is generated.
func markdown(note string, blocks []string) string {
	return "<!-- " + note + " -->\n" + strings.Join(blocks, "\n\n") + "\n"
}

func (r *registry) renderGlossary(lang string) string {
	page := r.rules.Documents[lang]
	blocks := []string{"# " + page.Title}
	for _, paragraph := range page.Intro {
		blocks = append(blocks, strings.Join(paragraph, "\n"))
	}
	var index []string
	for _, name := range r.rules.Topics {
		title := r.topics[name].Title[lang]
		link := path.Clean(strings.ReplaceAll(page.TermPath, topicPlaceholder, name))
		index = append(index, fmt.Sprintf("- [%s](%s): %s", title.Link, link, title.Description))
	}
	blocks = append(blocks, "## "+page.Index.Heading, page.Index.Lead, strings.Join(index, "\n"))
	for _, section := range r.rules.Style[lang] {
		blocks = append(blocks, "## "+section.Heading, "- "+strings.Join(section.Rules, "\n- "))
	}
	var rows [][]string
	for _, entry := range r.rules.Expressions {
		if entry.Lang != lang {
			continue
		}
		cell := entry.Word
		if entry.Qualifier != "" {
			cell += " (" + entry.Qualifier + ")"
		}
		rows = append(rows, []string{cell, entry.Instead})
	}
	blocks = append(blocks, "## "+page.Expressions.Heading, page.Expressions.Lead, renderTable(page.Expressions.Columns, rows))
	return markdown(page.GeneratedNote, blocks)
}

func (r *registry) renderTerms(lang, name string) string {
	page := r.rules.Documents[lang]
	topic := r.topics[name]
	var rows [][]string
	for _, entry := range topic.Terms {
		cells := []string{entry.Meaning[lang], strings.Join(entry.Avoid[lang], ", "), entry.Note[lang]}
		// The Korean table leads with both names of a term.
		if lang == spec.Korean {
			rows = append(rows, append([]string{entry.Korean, entry.English}, cells...))
		} else {
			rows = append(rows, append([]string{entry.English}, cells...))
		}
	}
	return markdown(page.GeneratedNote, []string{
		"# " + page.Terms.TitlePrefix + topic.Title[lang].Page,
		strings.ReplaceAll(page.Terms.Lead, topicPlaceholder, name),
		renderTable(page.Terms.Columns, rows),
	})
}

// renderTable renders a Markdown table. An empty cell takes three spaces.
func renderTable(columns []string, rows [][]string) string {
	line := func(cells []string) string {
		var b strings.Builder
		b.WriteString("|")
		for _, cell := range cells {
			if cell == "" {
				b.WriteString("   |")
			} else {
				b.WriteString(" " + cell + " |")
			}
		}
		return b.String()
	}
	lines := []string{line(columns), "|" + strings.Repeat("---|", len(columns))}
	for _, row := range rows {
		lines = append(lines, line(row))
	}
	return strings.Join(lines, "\n")
}
