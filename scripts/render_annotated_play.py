#!/usr/bin/env python3
"""
Turn a Melville's Marginalia Online volume XML + a Folger play text into a
single annotated HTML file, ready to print to PDF (see print_pdf.sh).

Usage:
    python3 render_annotated_play.py \
        --xml vol31_raw.xml --page-start 3 --page-end 134 \
        --folger-text king-lear_folger.txt \
        --title "The Tragedy of King Lear" --volume 7 \
        --style antiquarian \
        --out king_lear_annotated.html

Then eyeball the printed match report: anything under ~0.55 needs a manual
check (grep the Folger text for a distinctive phrase from the "note=" field,
find its real line, and add it to an --overrides JSON file:
  {"55,2199": 2051, "56,1843": 2085, ...}   -- key is "page,y" from the report
--appendix-pages lets you catch marks that land on editorial back-matter
(this 1837 edition appends Samuel Johnson-style critical notes after some
plays) rather than forcing them onto a real line of the play.

See examples/king-lear/overrides.json in this repo for a complete worked example.
"""
import argparse
import difflib
import html
import json
import re
import xml.etree.ElementTree as ET

MARGIN_TYPES = {"score", "diagonalscore", "crosschecks2", "xmark", "enclosure"}
BARE_SPEAKER_RE = re.compile(r"^[A-Z][A-Z .,\[\]]{0,18}$")

STYLES = {
    "antiquarian": """
@page { size: 8.5in 11in; margin: 0.9in 0.9in; }
body { font-family: 'Palatino', 'Iowan Old Style', Georgia, serif; font-size: 11.5pt; line-height: 1.55; color:#1a1a1a; }
.titlepage { text-align:center; page-break-after: always; padding-top: 2in; }
.titlepage h1 { font-size: 28pt; letter-spacing: 2px; margin-bottom: 0.1em; font-weight:normal; }
.titlepage .sub { font-size: 13pt; font-style: italic; color:#444; margin-bottom: 2.5em; }
.titlepage .credit { font-size: 10pt; color:#555; max-width: 4.6in; margin: 0 auto; line-height:1.6; text-align:left; border-top:1px solid #999; padding-top:1em; margin-top: 3em; }
.actheading { font-size: 19pt; text-align:center; margin-top:1.2em; page-break-before: always; letter-spacing:4px; font-variant: small-caps; }
.sceneheading { font-size: 12.5pt; text-align:center; font-variant: small-caps; margin: 1.2em 0 1em; color:#555; letter-spacing:1px; }
.textcol { width: 4.2in; }
.line { position: relative; white-space: pre-wrap; }
.underlined { text-decoration: underline; text-decoration-skip-ink: none; text-decoration-color:#7a1010; text-decoration-thickness: 1px; }
.checkmark::before { content: "✓"; font-family: Arial, 'Helvetica Neue', sans-serif; color:#7a1010; font-weight:bold; margin-right: 0.35em; }
.line.marked-annotation { background: #f7f0e6; }
.marginbar { position:absolute; left: 100.8%; top: 0; bottom: 0; width: 1.5px; background: #7a1010; }
.sidenote { position:absolute; left: 102%; top: -0.1em; width: 2.2in; font-family: Palatino, Georgia, serif; font-style:italic; font-size: 9pt; line-height:1.4; color:#7a1010; }
.sidenote .tag { font-weight:bold; font-style:normal; border-bottom:1px solid #7a1010; padding:0 2px; margin-right:3px; font-size:7.5pt; letter-spacing:1px; }
""",
    "brutalist": """
@page { size: 8.5in 11in; margin: 0.85in 0.9in; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11.5pt; line-height: 1.5; color:#111; }
.titlepage { text-align:center; page-break-after: always; padding-top: 2in; }
.titlepage h1 { font-family:'Helvetica Neue', Arial, sans-serif; font-weight:800; font-size: 34pt; margin-bottom: 0.15em; }
.titlepage .sub { font-family:'Helvetica Neue', Arial, sans-serif; font-size: 11pt; text-transform:uppercase; letter-spacing:2px; color:#444; margin-bottom: 2.5em; font-style:normal; }
.titlepage .credit { font-size: 10pt; color:#555; max-width: 4.6in; margin: 0 auto; line-height:1.6; text-align:left; border-top:3px solid #e8542b; padding-top:1em; margin-top: 3em; }
.actheading { font-family:'Helvetica Neue', Arial, sans-serif; font-weight:800; font-size: 22pt; text-align:left; margin-top:1.2em; page-break-before: always; border-bottom:4px solid #e8542b; padding-bottom:0.2em; width:4.2in; margin-left:auto; margin-right:auto; }
.sceneheading { font-family:'Helvetica Neue', Arial, sans-serif; font-weight:700; font-size: 11pt; text-align:left; text-transform:uppercase; letter-spacing:2px; margin: 1.4em 0 0.8em; color:#e8542b; width:4.2in; margin-left:auto; margin-right:auto; }
.textcol { width: 4.2in; }
.line { position: relative; white-space: pre-wrap; }
.underlined { text-decoration: underline; text-decoration-skip-ink: none; text-decoration-color:#e8542b; text-decoration-thickness: 2.5px; }
.checkmark::before { content: "✓"; font-family: Arial, 'Helvetica Neue', sans-serif; color:#e8542b; font-weight:bold; margin-right: 0.35em; }
.line.marked-annotation { background: #fdeee7; }
.marginbar { position:absolute; left: 100.8%; top: 0; bottom: 0; width: 5px; background: #e8542b; }
.sidenote { position:absolute; left: 102.5%; top: -0.1em; width: 2.15in; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 8.3pt; line-height:1.35; color:#111; }
.sidenote .tag { font-weight:800; background:#e8542b; color:#fff; border-radius:2px; padding:1px 4px; margin-right:4px; font-size:7.5pt; }
""",
    "modern_serif": """
@page { size: 8.5in 11in; margin: 0.9in 0.9in; }
body { font-family: 'Hoefler Text', 'Athelas', Georgia, serif; font-size: 12pt; line-height: 1.65; color:#1c1c1c; }
.titlepage { text-align:center; page-break-after: always; padding-top: 2in; }
.titlepage h1 { font-size: 27pt; letter-spacing: 1px; margin-bottom: 0.15em; font-weight:normal; }
.titlepage .sub { font-size: 12.5pt; font-style: italic; color:#555; margin-bottom: 2.5em; }
.titlepage .credit { font-size: 9.5pt; color:#555; max-width: 4.6in; margin: 0 auto; line-height:1.6; text-align:left; border-top:2px solid #e8542b; padding-top:1em; margin-top: 3em; }
.actheading { font-size: 20pt; text-align:center; margin-top:1.2em; page-break-before: always; letter-spacing:3px; font-variant: small-caps; }
.actheading::after { content:""; display:block; width:1.2in; height:2px; background:#e8542b; margin:0.35em auto 0; }
.sceneheading { font-size: 12.5pt; text-align:center; font-variant: small-caps; margin: 1.3em 0 1em; color:#555; }
.textcol { width: 4.3in; }
.line { position: relative; white-space: pre-wrap; }
.underlined { text-decoration: underline; text-decoration-skip-ink: none; text-decoration-color:#e8542b; text-decoration-thickness: 1.5px; }
.checkmark::before { content: "✓"; font-family: Arial, 'Helvetica Neue', sans-serif; color:#e8542b; font-weight:bold; margin-right: 0.35em; }
.line.marked-annotation { background: #fdf1ec; }
.marginbar { position:absolute; left: 100.8%; top: 0; bottom: 0; width: 2.5px; background: #e8542b; }
.sidenote { position:absolute; left: 102%; top: -0.1em; width: 2.1in; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 8.3pt; line-height:1.4; color:#a8401f; }
.sidenote .tag { font-weight:bold; border:1px solid #e8542b; border-radius:8px; padding:0 5px; margin-right:4px; font-size:7.3pt; color:#e8542b; }
""",
}


def div_text(div):
    words = []
    for line in div.findall("line"):
        for w in line.findall("w"):
            choice = w.find("choice")
            if choice is not None:
                reg = choice.find("reg")
                txt = reg.text if reg is not None else choice.find("orig").text
            else:
                txt = w.text
            if txt:
                words.append(txt.strip())
    return " ".join(words)


def norm(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9' ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


BARE_SPEAKER = BARE_SPEAKER_RE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", required=True, help="marginalia volume XML from fetch_sources.py")
    ap.add_argument("--page-start", type=int, required=True)
    ap.add_argument("--page-end", type=int, required=True)
    ap.add_argument("--folger-text", required=True, help="the *_folger.txt from fetch_sources.py")
    ap.add_argument("--title", required=True, help='e.g. "The Tragedy of King Lear"')
    ap.add_argument("--volume", type=int, required=True, help="Vol. N of 7, for the credit line")
    ap.add_argument("--sealts", default="460", help="Sealts number of the physical volume (460 for all 7 Dramatic Works vols)")
    ap.add_argument("--style", choices=STYLES.keys(), default="antiquarian")
    ap.add_argument("--overrides", help="JSON file of manual {\"page,y\": line_index} corrections")
    ap.add_argument("--annotators", help="JSON file of ADDITIONAL annotators (Milton, Keats, ...) whose "
                                          "marks are hand-located rather than XML-sourced. See "
                                          "examples/king-lear/annotators.json")
    ap.add_argument("--appendix-pages", nargs="*", type=int, default=[],
                     help="page numbers to treat as trailing editorial notes, not in-text anchors")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    overrides = {}
    if args.overrides:
        raw_overrides = json.load(open(args.overrides))
        for k, v in raw_overrides.items():
            page_s, y_s = k.split(",")
            overrides[(int(page_s), int(y_s))] = v

    # ---------- parse marginalia ----------
    tree = ET.parse(args.xml)
    root = tree.getroot()
    entries = []
    for div in root.iter("div"):
        page = div.get("page")
        if not page:
            continue
        try:
            pnum = int(page.split(".")[-1])
        except ValueError:
            continue
        if not (args.page_start <= pnum <= args.page_end):
            continue
        entries.append({
            "page": pnum, "y": int(div.get("y", 0)),
            "type": div.get("type"), "type2": div.get("type2"),
            "text": div_text(div),
        })
    entries.sort(key=lambda e: (e["page"], e["y"]))
    print(f"Loaded {len(entries)} Melville marks in pp.{args.page_start}-{args.page_end}")
    if not entries:
        raise SystemExit("No marks in this page range -- wrong play/volume, or Melville left it unmarked "
                          "(run list_plays.py first to check).")

    # ---------- parse Folger text ----------
    raw_lines = open(args.folger_text, encoding="utf-8").read().split("\n")
    act_start = next(i for i, l in enumerate(raw_lines) if l.strip() == "ACT 1")
    play_lines = raw_lines[act_start:]
    norm_lines = [norm(l) for l in play_lines]

    # ---------- sequential fuzzy matching ----------
    cursor = 0
    WINDOW = 500
    matches = []
    for e in entries:
        target = norm(e["text"])
        if len(target) < 3:
            matches.append(None)
            continue
        best_score, best_start, best_len = -1, None, 1
        search_end = min(len(play_lines), cursor + WINDOW)
        for start in range(cursor, search_end):
            for span in range(1, 8):
                end = start + span
                if end > len(play_lines):
                    break
                acc = " ".join(norm_lines[start:end])
                if not acc:
                    continue
                ratio = difflib.SequenceMatcher(None, target, acc).ratio()
                score = ratio * min(1.0, len(acc) / max(len(target), 1)) if len(acc) <= len(target) * 1.6 else ratio
                if score > best_score:
                    best_score, best_start, best_len = score, start, span
        matches.append({"start": best_start, "len": best_len, "score": best_score})
        if best_start is not None:
            cursor = best_start

    weak = 0
    for e, m in zip(entries, matches):
        if m is None or m["score"] < 0.55:
            weak += 1
            anchor = play_lines[m["start"]][:60] if m else "???"
            print(f"p.{e['page']:>3} y={e['y']:<5} [{e['type']:<10}] score={(m['score'] if m else 0):.2f} "
                  f"anchor='{anchor}' | note='{e['text'][:60]}'  <-- WEAK, check by hand")
    print(f"\n{weak}/{len(entries)} weak matches -- add corrections to an --overrides JSON if needed, then rerun.\n")

    # ---------- resolve line assignments ----------
    def bump_past_bare_speaker(idx):
        while idx + 1 < len(play_lines) and BARE_SPEAKER.match(play_lines[idx].strip()) and play_lines[idx + 1].strip():
            idx += 1
        return idx

    line_visual = {}
    line_sidenote = {}
    line_authors = {}   # line index -> ordered list of annotator keys who marked it
    appendix_notes = []

    def claim(idx, key):
        """Record that `key` marked line `idx`, so the line can be tagged with whose mark it is."""
        who = line_authors.setdefault(idx, [])
        if key not in who:
            who.append(key)

    # ---------- additional annotators ----------
    # Melville is the only reader with a structured transcription database behind him.
    # Everyone else's marks are located by hand and anchored here by the TEXT of the
    # line they sit against, then resolved with the same fuzzy matcher. Anchoring by
    # text rather than by line index is deliberate: indices move whenever the Folger
    # text is re-fetched, and a hand-typed index that is off by N fails silently.
    def find_line(anchor):
        """Best whole-text match for an anchor string. Returns (index, score)."""
        target = norm(anchor)
        best_score, best_i = -1, None
        for start in range(len(play_lines)):
            for span in range(1, 4):
                acc = " ".join(norm_lines[start:start + span])
                if not acc:
                    continue
                ratio = difflib.SequenceMatcher(None, target, acc).ratio()
                if ratio > best_score:
                    best_score, best_i = ratio, start
        return best_i, best_score

    extra = []
    if args.annotators:
        extra = json.load(open(args.annotators, encoding="utf-8"))["annotators"]
        for a in extra:
            for mk in a["marks"]:
                idx, score = find_line(mk["anchor"])
                mk["_line"], mk["_score"] = idx, score
                flag = "" if score >= 0.75 else "   <-- WEAK, check the rendered page by hand"
                print(f"{a['key']} score={score:.2f} line={idx:<5} "
                      f"anchor='{mk['anchor'][:48]}'{flag}")
            print(f"Loaded {len(a['marks'])} {a['name']} marks")

    for e, m in zip(entries, matches):
        key = (e["page"], e["y"])
        if e["page"] in args.appendix_pages:
            appendix_notes.append(e)
            continue
        if e["type"] == "annotation":
            idx = overrides.get(key)
            if idx is None and m is not None:
                idx = m["start"]
            if idx is None:
                continue
            idx = bump_past_bare_speaker(idx)
            line_sidenote.setdefault(idx, []).append(
                {"tag": "HM", "color": None, "text": e["text"], "citation": None})
            line_visual.setdefault(idx, set()).add("annotation")
            claim(idx, "HM")
        else:
            if key in overrides:
                start_i, span_len = overrides[key], 1
            elif m is not None:
                start_i, span_len = m["start"], m["len"]
            else:
                continue
            for offset in range(span_len):
                li = start_i + offset
                if li < len(play_lines):
                    line_visual.setdefault(li, set()).add(e["type"])
                    claim(li, "HM")

    # Fold the hand-located annotators onto the same line maps Melville's marks use,
    # so from here down the renderer doesn't care where a mark came from.
    for a in extra:
        for mk in a["marks"]:
            idx = mk["_line"]
            if idx is None:
                continue
            idx = bump_past_bare_speaker(idx)
            line_visual.setdefault(idx, set()).add(mk["type"])
            claim(idx, a["key"])
            if mk.get("note"):
                line_sidenote.setdefault(idx, []).append({
                    "tag": a["key"], "color": a["color"],
                    "text": mk["note"], "citation": mk.get("citation"),
                })

    # ---------- build HTML ----------
    def note_html(e, offset_em=0):
        bits = [f"top:{offset_em}em;"] if offset_em else []
        if e.get("color"):
            bits.append(f'color:{e["color"]};')
        style = f' style="{"".join(bits)}"' if bits else ""
        tag_style = f' style="color:{e["color"]};border-color:{e["color"]};"' if e.get("color") else ""
        # Melville's marks are verbatim transcriptions of what he wrote, so they are
        # quoted. Everyone else's are editorial descriptions of a mark, so they are not.
        body = (f'&ldquo;{html.escape(e["text"])}&rdquo;' if e["tag"] == "HM"
                else html.escape(e["text"]))
        cite = f' <span class="cite">({html.escape(e["citation"])})</span>' if e.get("citation") else ""
        return (f'<div class="sidenote"{style}>'
                f'<span class="tag"{tag_style}>{e["tag"]}</span> {body}{cite}</div>')

    def est_note_height_em(e):
        """Rough rendered height of a sidenote, in em, for collision carry-over."""
        chars = len(e["text"]) + (len(e.get("citation") or "") + 3)
        return max(2.6, (chars / 42.0) * 1.4 + 0.8)

    act_re = re.compile(r"^ACT (\d+)$")
    scene_re = re.compile(r"^Scene (\d+)$")

    # ---- title page ----
    readers = [("HM", "Herman Melville", None)] + [(a["key"], a["name"], a["color"]) for a in extra]
    author_color = {a["key"]: a["color"] for a in extra}   # HM keeps the style's own accent
    names_block = "<br>".join(n.upper() for _, n, _ in readers)
    subtitle = "with the marginalia of" if len(readers) == 1 else "with the marginalia of"

    if extra:
        key_line = " &nbsp; ".join(
            f'<span style="font-weight:bold;{"color:" + c + ";" if c else ""}">{k}</span> &middot; {html.escape(n)}'
            for k, n, c in readers)
        intro = (f'<div class="readerkey">{key_line}</div>'
                 f'<div class="readerintro">'
                 f'{len(readers)} readers, two centuries apart, each left a mark on this play. '
                 f'This edition reads {html.escape(args.title)} once, straight through, with every hand '
                 f'visible at the lines that held them &mdash; each tagged so you always know whose.</div>')
        blurbs = ('<div class="blurbs">'
                  '<p><b>HM</b> &mdash; Herman Melville marked his own 1837 <i>Dramatic Works</i> '
                  'obsessively while drafting <i>Moby-Dick</i>; the volume survives at Harvard\'s '
                  'Houghton Library, transcribed in full by Melville\'s Marginalia Online.</p>'
                  + "".join(f'<p><b>{a["key"]}</b> &mdash; {html.escape(a["blurb"])}</p>' for a in extra)
                  + '</div>')
        extra_sources = "".join(
            f'{html.escape(a["name"])}: {html.escape(a["source"])}<br><br>' for a in extra)
        caveat = ("Assembled as a private reading copy, not a scholarly edition. Melville's marks are "
                  "exhaustively transcribed by his editors; the others are a first pass, not a complete "
                  "paleographic inventory. Footnote placement is approximate where a reader's own edition "
                  "departs in wording from the modern edited text.")
        # A multi-reader title page carries a key, an intro and a blurb per reader, which
        # is far more than the single-reader page was spaced for -- without this it pushes
        # the credit block onto a second page.
        titlepage_fit = (".titlepage .sub { margin-bottom: 0; }"
                         ".editionnote { page-break-after: always; padding-top: 0.35in; text-align:center; }"
                         # .credit is styled per-style as `.titlepage .credit`, which no longer
                         # matches once the block moves onto its own page -- restate it here.
                         ".editionnote .credit { font-size:9pt; color:#555; max-width:4.6in; margin:1.6em auto 0;"
                         " line-height:1.5; text-align:left; border-top:1px solid #999; padding-top:0.9em; }")
    else:
        intro, blurbs, extra_sources, titlepage_fit = "", "", "", ""
        caveat = ("Assembled as a private reading copy. Not a scholarly edition &mdash; footnote placement "
                  "is approximate where Melville's 1837 text departs in wording from the modern edited text.")

    out = [f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(args.title)} — annotated</title>
<style>
{STYLES[args.style].strip()}
.readerkey {{ font-size: 11pt; margin: 0.4em 0 1.6em; letter-spacing:0.5px; }}
.readerintro {{ font-size: 10.5pt; font-style:italic; color:#444; max-width:4.6in; margin:0 auto 2em; line-height:1.6; text-align:left; }}
.blurbs {{ font-size: 9.5pt; color:#444; max-width:4.6in; margin:0 auto; text-align:left; line-height:1.55; }}
.blurbs p {{ margin: 0 0 0.7em; }}
.sidenote .cite {{ font-style:normal; font-size:7.5pt; opacity:0.75; white-space:nowrap; }}
.linetag {{ font-family:'Helvetica Neue', Arial, sans-serif; font-size:6.5pt; font-weight:bold; letter-spacing:0.5px; vertical-align:0.35em; margin-left:0.35em; opacity:0.8; }}
.frontispiece {{ page-break-after: always; text-align:center; padding-top:1.2in; }}
.frontispiece .caption {{ font-size:9.5pt; font-style:italic; color:#666; margin-bottom:2.2em; }}
.frontispiece h2 {{ font-size:14pt; font-weight:normal; font-style:italic; margin-bottom:1.4em; }}
.frontispiece .verse {{ display:inline-block; text-align:left; font-size:11.5pt; line-height:2.0; }}
.notesheading {{ font-size:15pt; text-align:center; page-break-before: always; letter-spacing:2px; font-variant:small-caps; margin-bottom:0.4em; }}
.noteslist {{ width:4.4in; font-size:9.5pt; line-height:1.55; }}
.noteslist p {{ margin:0 0 0.7em; }}
.noteslist .tag {{ font-weight:bold; margin-right:4px; }}
{titlepage_fit}
</style></head><body>
<div class="titlepage">
<h1>{html.escape(args.title).upper()}</h1>
<div class="sub">by William Shakespeare<br><br>{subtitle}<br>{names_block}</div>
{'</div><div class="editionnote">' if extra else ''}
{intro}{blurbs}
<div class="credit">Play text: the Folger Shakespeare (ed. Barbara A. Mowat &amp; Paul Werstine), Folger Shakespeare Library, used under CC BY-NC 4.0.<br><br>
Melville: transcribed from his own annotated copy of <i>The Dramatic Works of William Shakespeare</i> (Boston: Hilliard, Gray, 1837), vol. {args.volume}, held at the Houghton Library, Harvard University (Sealts #{args.sealts}). Transcription &amp; digitization by Melville's Marginalia Online (dir. Steven Olsen-Smith, Boise State University), melvillesmarginalia.org.<br><br>
{extra_sources}{caveat}</div>
</div>"""]

    # ---- frontispieces: whole pages a reader wrote facing the play, not line marks ----
    for a in extra:
        fp = a.get("frontispiece")
        if not fp:
            continue
        verse = "<br>".join(html.escape(l) for l in fp["lines"])
        out.append(f'<div class="frontispiece">'
                   f'<div class="caption">{html.escape(fp["caption"])}</div>'
                   f'<h2>{html.escape(fp["title"])}</h2>'
                   f'<div class="verse">{verse}</div>'
                   f'<div style="margin-top:2.4em;font-weight:bold;color:{a["color"]};">{a["key"]}</div>'
                   f'</div>')

    out.append('<div class="textcol">')

    # Body line-height in units of the (smaller) sidenote font — how much vertical room
    # one line of play text buys us before the next sidenote can start.
    LINE_ADVANCE_EM = 2.0
    last_note_bottom_em, last_note_line = 0.0, -999

    i, n = 0, len(play_lines)
    while i < n:
        raw = play_lines[i]
        stripped = raw.strip()
        if stripped == "" or set(stripped) == {"="}:
            i += 1
            continue
        m_act = act_re.match(stripped)
        m_scene = scene_re.match(stripped)
        if m_act:
            out.append(f'<div class="actheading">ACT {m_act.group(1)}</div>')
            i += 1
            continue
        if m_scene:
            out.append(f'<div class="sceneheading">Scene {m_scene.group(1)}</div>')
            i += 1
            continue
        vtypes = line_visual.get(i, set())
        classes = ["line"]
        if "annotation" in vtypes:
            classes.append("marked-annotation")
        has_marginbar = bool(vtypes & MARGIN_TYPES)
        esc = html.escape(raw)
        text_html = f'<span class="underlined">{esc}</span>' if "underline" in vtypes else f'<span class="linetext">{esc}</span>'
        prefix = '<span class="checkmark"></span>' if "checkmark" in vtypes else ""
        line_html = f'<div class="{" ".join(classes)}">{prefix}{text_html}'
        # Whose mark is this? With more than one reader in the book, a margin bar on its
        # own is ambiguous, so every marked line trails the initials of who marked it.
        if len(readers) > 1 and i in line_authors:
            for k in line_authors[i]:
                c = author_color.get(k)
                sty = f' style="color:{c};"' if c else ""
                line_html += f'<span class="linetag"{sty}>{k}</span>'
        if has_marginbar:
            bar_color = author_color.get(line_authors.get(i, ["HM"])[0])
            sty = f' style="background:{bar_color};"' if bar_color else ""
            line_html += f'<div class="marginbar"{sty}></div>'
        # Sidenotes are absolutely positioned inside their own .line, so each one starts
        # its stacking from top:0 and two notes on *nearby but different* lines can
        # overlap. Carry the previous note's bottom edge forward, decayed by how far
        # down the page we've moved since, and start below it.
        notes = line_sidenote.get(i, [])
        if notes:
            decay = (i - last_note_line) * LINE_ADVANCE_EM
            offset = max(0.0, last_note_bottom_em - decay)
            for note in notes:
                line_html += note_html(note, offset_em=round(offset, 2))
                offset += est_note_height_em(note)
            last_note_bottom_em, last_note_line = offset, i
        line_html += "</div>"
        out.append(line_html)
        i += 1

    out.append("</div>")

    # ---- Notes on the Marks: the hand-located readers, listed with their citations ----
    if extra:
        out.append('<div class="notesheading">Notes on the Marks</div>')
        key_line = " &nbsp;&nbsp; ".join(
            f'<span style="font-weight:bold;{"color:" + c + ";" if c else ""}">{k}</span> {html.escape(n)}'
            for k, n, c in readers)
        out.append(f'<div class="noteslist" style="text-align:center;margin-bottom:1.4em;">{key_line}</div>')
        out.append('<div class="noteslist">')
        for a in extra:
            for mk in a["marks"]:
                cite = f' ({html.escape(mk["citation"])})' if mk.get("citation") else ""
                out.append(f'<p><span class="tag" style="color:{a["color"]};">{a["key"]}</span>'
                           f'{html.escape(mk.get("note", ""))}{cite}</p>')
        out.append(f'<p style="margin-top:1.2em;">'
                   f'<span class="tag">HM</span>Melville\'s {len(entries)} marks on '
                   f'{html.escape(args.title)} are individually transcribed at melvillesmarginalia.org '
                   f'and are not re-listed here &mdash; see the marked lines throughout.</p>')
        out.append('</div>')

    if appendix_notes:
        out.append('<div class="actheading" style="font-size:16pt;">EDITOR\'S NOTES, AS MELVILLE READ THEM</div>')
        out.append('<div style="width:4.4in;font-size:10pt;font-style:italic;color:#333;margin-bottom:1em;">'
                    "This 1837 edition appends editorial/critical commentary after the play; Melville marked some "
                    "of it too. Reproduced here as notes rather than pinned to a line of the play itself.</div>")
        for note in appendix_notes:
            out.append(f'<div style="width:4.4in;font-family:Helvetica,Arial,sans-serif;font-size:9.5pt;'
                       f'color:#7a1010;border-left:2px solid #7a1010;padding:0.3em 0 0.3em 0.6em;margin-bottom:0.6em;">'
                       f'<b>HM</b> [{note["type"]}]: &ldquo;{html.escape(note["text"])}&rdquo;</div>')

    out.append("</body></html>")
    open(args.out, "w", encoding="utf-8").write("\n".join(out))
    print("Wrote", args.out)


if __name__ == "__main__":
    main()
