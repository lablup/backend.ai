from sphinx.writers.html import HTMLTranslator


class NewTabLinkHTMLTranslator(HTMLTranslator):
    """Patched translator to open an external link in a new tab of the browser.

    ref: https://stackoverflow.com/a/67153583
    """

    def starttag(self, node, tagname, *args, **atts):
        match = (
            tagname == "a"
            and "target" not in atts
            and (
                "external" in atts.get("class", "")
                or "external" in atts.get("classes", [])
            )
        )
        if match:
            atts["target"] = "_blank"
            atts["rel"] = "noopener noreferrer"
        tag = super().starttag(node, tagname, *args, **atts)
        if match:
            tag += '<img class="external-link-icon" src="/_static/icons/icon-external.svg" />'
        return tag


def setup(app):
    app.set_translator("html", NewTabLinkHTMLTranslator)
    app.set_translator("dirhtml", NewTabLinkHTMLTranslator)
    app.set_translator("singlehtml", NewTabLinkHTMLTranslator)