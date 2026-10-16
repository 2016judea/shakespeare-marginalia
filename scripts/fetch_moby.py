#!/usr/bin/env python3
"""
Fetch a play's PUBLIC-DOMAIN text from the MIT Moby Shakespeare and write it in the
same plain-text shape as a Folger download, so render_annotated_play.py reads either.

Why this exists: the Folger text is CC BY-NC 3.0, so an edition built on it can never
be sold. MIT's Moby Shakespeare says of itself: "The HTML versions of the plays
provided here are placed in the public domain" (shakespeare.mit.edu, read 2026-10-16).
Build on this text for anything that changes hands for money.

Output shape (the renderer's contract):
    ACT 1            <- arabic numerals, then an "=====" rule
    Scene 1
    [Enter KENT, GLOUCESTER, and EDMUND]
    KENT  I thought the king had more affected the Duke of     <- speaker, two spaces, line one
    Albany than Cornwall.                                       <- continuation lines bare

Usage:
    python3 fetch_moby.py --slug lear --out work/king-lear_moby.txt
--slug is MIT's directory name (lear, hamlet, othello, macbeth, romeo_juliet ...).
"""
import argparse
import html
import re
import urllib.request

ROMAN = {r: i for i, r in enumerate("I II III IV V VI VII VIII IX X XI XII XIII XIV XV".split(), 1)}


def fetch(slug):
    url = f"https://shakespeare.mit.edu/{slug}/full.html"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (shakespeare-marginalia)"})
    return urllib.request.urlopen(req).read().decode("iso-8859-1"), url


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def convert(doc, title, url):
    out = [title, "by William Shakespeare",
           "Text: the Moby Shakespeare, placed in the public domain",
           url, "", ""]
    speaker = None          # set by a <b>NAME</b>, consumed by the next spoken line
    for raw in doc.splitlines():
        line = raw.strip()
        m = re.match(r"(?i)<h3>\s*ACT\s+([IVX]+)", line)
        if m:
            out += ["", f"ACT {ROMAN[m.group(1).upper()]}", "=====", ""]
            continue
        m = re.match(r"(?i)<h3>\s*SCENE\s+([IVX]+)\.?(.*)</h3>", line)
        if m:
            out += [f"Scene {ROMAN[m.group(1).upper()]}", "=======", ""]
            continue
        m = re.search(r"<b>(.*?)</b>", line)
        if m and "NAME=speech" in line:
            out.append("")
            speaker = clean(m.group(1))
            continue
        m = re.search(r"<i>(.*?)</i>", line)
        if m and "NAME=" not in line:
            out.append(f"[{clean(m.group(1))}]")
            continue
        m = re.match(r"<A NAME=\d+\.\d+\.\d+>(.*)</A>", line, re.I)
        if m:
            text = clean(m.group(1))
            if speaker:
                out.append(f"{speaker}  {text}")
                speaker = None
            else:
                out.append(text)
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help='MIT directory, e.g. "lear"')
    ap.add_argument("--title", default="", help="first line of the output file")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    doc, url = fetch(args.slug)
    text = convert(doc, args.title or args.slug, url)
    open(args.out, "w", encoding="utf-8").write(text)
    n = sum(1 for l in text.splitlines() if l and not l.startswith(("[", "ACT", "Scene", "=")))
    print(f"wrote {args.out}: {n} spoken lines from {url}")


if __name__ == "__main__":
    main()
