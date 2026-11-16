"""Semantic formatting supported by Facebook, independent of editor-specific CSS."""

import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse


def article_html(html, tags=""):
    if "</body>" in html:
        return html.replace("</body>", f"<p>{escape(tags.strip())}</p></body>" if tags.strip() else "</body>")
    return html + (f"<p>{escape(tags.strip())}</p>" if tags.strip() else "")


class SemanticHTML(HTMLParser):
    allowed = {
        "p",
        "div",
        "b",
        "strong",
        "i",
        "em",
        "u",
        "s",
        "br",
        "ul",
        "ol",
        "li",
        "blockquote",
        "h1",
        "h2",
        "h3",
        "a",
        "table",
        "tr",
        "td",
        "th",
        "tbody",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.stack = [], []
        self.blocked = None

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "title"}:
            self.blocked = tag
            return
        if self.blocked:
            return
        attrs = dict(attrs)
        closers = []
        if tag in self.allowed:
            extra = ""
            href = attrs.get("href", "") or ""
            if tag == "a" and urlparse(href).scheme.lower() in {"http", "https", "mailto", "tel"}:
                extra = f' href="{escape(href, quote=True)}"'
            if tag == "ol" and str(attrs.get("start", "")).isdigit():
                extra += f' start="{attrs["start"]}"'
            self.parts.append(f"<{tag}{extra}>")
            if tag != "br":
                closers.append(tag)
        style = attrs.get("style", "") or ""
        for condition, wrapper in [
            (r"font-weight\s*:\s*(?:bold|[6-9]00)", "b"),
            (r"font-style\s*:\s*italic", "i"),
            (r"text-decoration[^;]*underline", "u"),
        ]:
            if re.search(condition, style, re.I):
                self.parts.append(f"<{wrapper}>")
                closers.append(wrapper)
        if tag not in {"br", "hr", "img", "meta", "link", "input"}:
            self.stack.append((tag, closers))

    def handle_endtag(self, tag):
        if self.blocked:
            if tag == self.blocked:
                self.blocked = None
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                for _, closers in reversed(self.stack[index:]):
                    self.parts.extend(f"</{name}>" for name in reversed(closers))
                del self.stack[index:]
                break

    def handle_data(self, data):
        if not self.blocked:
            self.parts.append(escape(data))


def facebook_html(html):
    parser = SemanticHTML()
    parser.feed(html)
    parser.close()
    for _, closers in reversed(parser.stack):
        parser.parts.extend(f"</{name}>" for name in reversed(closers))
    return "".join(parser.parts)
