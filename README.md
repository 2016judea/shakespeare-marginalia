# shakespeare-marginalia

Take the marks a real historical reader left in their own copy of Shakespeare and
set each one beside the line that provoked it, in a clean, print-ready PDF —
underlines, scores, checkmarks and handwritten comments, placed against a modern,
readable text.

It handles **more than one reader at a time**. The worked example here is *King
Lear* carrying the marks of three: Herman Melville, John Milton and John Keats,
each colour-coded and tagged with their initials so you always know whose hand you
are looking at. *(Renamed from `melville-annotated-shakespeare`, 2026-08-15 —
the repo outgrew the name. GitHub redirects the old URL.)*

**Live:** [*King Lear*, Annotated](https://aidanjude.vercel.app/king-lear-annotated) —
124 pages, built by exactly the command in [Quickstart](#quickstart) below.

## Two kinds of reader

Only Melville has a structured transcription database behind him, and that shapes
the whole design:

| | Source | How marks are located |
|---|---|---|
| **Melville** | [Melville's Marginalia Online](https://melvillesmarginalia.org) XML — 52 marks on *Lear* alone | Fetched, then fuzzy-matched to the modern text automatically (~85% clean; the rest need an overrides file) |
| **Everyone else** | Whatever exists — a page facsimile, or the standard scholarship | Found by hand, then declared in an **annotators JSON** and anchored by the *text* of the line |

That second row is the general case, and it's why the pipeline isn't Melville-only.
Milton's marks were located by eye from the Free Library of Philadelphia's
digitization of the First Folio it identified in 2019 as his; Keats's come from
Spurgeon's 1928 study, because the book carrying them isn't freely digitized.

See [`examples/king-lear/annotators.json`](examples/king-lear/annotators.json) for
the full format. Each mark declares the line it sits against **as text**, never as
a line number:

```json
{
  "anchor": "How sharper than a serpent's tooth it is",
  "type": "score",
  "note": "Marked beside Lear's “sharper than a serpent's tooth” line.",
  "citation": "Folio p. 289"
}
```

Anchoring by text rather than by index is deliberate, and learned the hard way: the
play doesn't start at line 1 of the Folger file, so a line number copied out of
`grep -n` is off by the length of the front matter — and it fails *silently*, putting
a real mark on the wrong real line. An anchor string either matches or visibly
doesn't. The renderer prints a score per mark and flags anything below 0.75.

An annotator can also carry a **frontispiece** — a whole page they wrote facing the
play rather than a mark on a line. Keats's sonnet *On Sitting Down to Read King Lear
Once Again* is one, and it prints before Act 1.

## Why

Melville's Marginalia Online did the hard part: they preserved and transcribed
Melville's actual annotated 1837 *Dramatic Works of Shakespeare* (Boston: Hilliard,
Gray), the copy he was reading while he wrote *Moby-Dick*, and made it freely
browsable online. But it's a research archive — a page-by-page viewer, not
something you sit down and read.

This tool exists to close that gap: to turn "here's a scan of a 19th-century book
with pencil marks in it" into "here's a page you can actually read, with his
marginalia sitting next to the line that provoked it." **The goal is accessibility,
not novelty** — more people reading Melville reading Shakespeare, for free, for
their own benefit. See [NOTICE.md](NOTICE.md) for why that's not just a mission
statement but a license requirement: the underlying play text is CC BY-NC, so
non-commercial personal use is the only use this was ever built for.

## What it does

1. Downloads a volume's marginalia data from Melville's Marginalia Online's public
   XML endpoint (live, not bundled — see [NOTICE.md](NOTICE.md)).
2. Downloads the matching play's modern text from Folger Shakespeare (CC BY-NC 4.0).
3. Matches every mark to its line in the modern text — Melville's by fuzzy-matching
   the transcription, any other reader's by their declared anchor string.
4. Renders a print-ready HTML/PDF: marks shown visually in place (an underline is an
   underline, a "scored" passage gets a vertical line in the margin — that's what
   scoring actually meant physically), handwritten comments as sidenotes, and each
   marked line tagged with the initials of who marked it. No invented commentary —
   if a reader didn't write it, it doesn't appear as text. Descriptions of a mark
   are set plainly; only words a reader actually wrote are set in quotes.

## Quickstart

Requires Python 3 and a Chromium-based browser (for the final PDF render — no other
installs needed).

```bash
# 1. Find a play that's actually annotated (not all of them are -- Melville left
#    zero marks on Macbeth, for instance).
python3 scripts/list_plays.py --play "king lear"

# 2. Fetch that play's sources.
python3 scripts/fetch_sources.py --doc-id 31 --folger-slug king-lear --outdir work/

# 3. Match marks to lines and render HTML. Check the printed match report --
#    weak matches need a manual fix, see examples/king-lear/overrides.json for
#    the correction-file format.
python3 scripts/render_annotated_play.py \
  --xml work/vol31_raw.xml --page-start 3 --page-end 134 \
  --folger-text work/king-lear_folger.txt \
  --title "The Tragedy of King Lear" --volume 7 \
  --style antiquarian \
  --overrides examples/king-lear/overrides.json \
  --annotators examples/king-lear/annotators.json \
  --appendix-pages 134 \
  --out work/king_lear_annotated.html

# 4. Print to PDF.
./scripts/print_pdf.sh work/king_lear_annotated.html work/king_lear_annotated.pdf
```

That produces the 124-page three-reader edition. Drop `--annotators` and you get
Melville alone, at 121 pages — the multi-reader front matter and the per-line
initials only appear when there's more than one hand to distinguish.

Three built-in style presets: `antiquarian` (quiet, oxblood ink, hairline margin
rule — closest to a real old-book page), `brutalist` (bold sans headers, thick
vermilion margin bar, high-contrast), `modern_serif` (Hoefler Text, generous
line-height, restrained accent color — the most comfortable for long reads).

## A worked example: King Lear

`examples/king-lear/overrides.json` is the full set of manual corrections needed
to cleanly place all 52 of Melville's marks in *King Lear* (Vol. 7, DocId 31,
pp. 3–134) — a real worked example of the correction-file format, and proof the
pipeline gets ~85% right automatically with the rest needing a human to grep the
play text for context and confirm the line by hand.

One find worth knowing before you pick a play: **Melville left zero marks on
Macbeth, Comedy of Errors, and King John** (Vol. 3, DocId 27) — his heaviest marking
is in Vol. 7 (Lear, Romeo and Juliet, Hamlet, Othello). Run `list_plays.py` before
committing to a play; it'll tell you the mark count before you invest in the rest
of the pipeline.

`examples/king-lear/annotators.json` is the other half: Milton's five marks and
Keats's two, with their sources and citations. Two things fell out of putting all
three readers on one text that none of them showed alone —

- Melville and Milton, two centuries apart, independently marked **the same line**:
  *"Time shall unfold what plighted cunning hides."* It prints with both their
  initials.
- They also both stopped at the same textual crux in Act 5 — the one where the
  Folio's compositor dropped a word from Edmund's line. Milton pencilled the missing
  *"is"* back in above the line. Modern editors, comparing the Quarto centuries
  later, restored the same word, and it's the reading printed here.

## Adding a fourth reader

The Milton route generalizes better than the Melville one. Only Melville has a
pre-built transcription database; for anyone else, expect to survey a facsimile
yourself. That's more tractable than it sounds — check archive.org and university
IIIF endpoints before assuming it's infeasible.

Then it's one more entry in the annotators JSON: a key, a colour, a blurb, a source
line, and the marks. No code changes.

Ruled out so far, for want of a freely accessible personal copy: **Coleridge** (real
marginalia, but only inside a modern in-copyright critical edition), **Tolstoy** (a
standalone essay, not annotations), **Kozintsev** (a director's diary, a different
form entirely), and actor promptbooks (the Folger and the Shakespeare Birthplace
Trust hold real ones; none digitized freely enough to use). Keats's own working
7-volume *Dramatic Works* at Harvard **is** IIIF-digitized — all 104 *Lear* pages
were swept, and they carry no visible marks. His *Lear* marks are in a different
book, the First Folio facsimile associated with Keats House London, which isn't
freely available. Hence the scholarship as the source for his two.

## Not a scholarly edition

Melville's marks are exhaustively transcribed by his editors. Milton's and Keats's
are a first pass, not a complete paleographic inventory — a careful survey of the
Milton Folio would very likely turn up more than five.

Footnote placement is approximate wherever a reader's own edition departs in wording
from the modern edited text used here (textual variants across editions are real —
e.g. his Lear reads "nothing *can* come of nothing," modern editions read "nothing
*will* come of nothing," a genuine Quarto/Folio-lineage difference, not a bug). This
is built for reading pleasure, not textual-critical precision. If you want the
latter, go to the source: [melvillesmarginalia.org](https://melvillesmarginalia.org).

## Licensing

See [NOTICE.md](NOTICE.md) for the full breakdown. Short version: this repo's code
is MIT; the play text is CC BY-NC 4.0 (so **non-commercial use only**, no exceptions);
the marginalia data has no declared open license and is fetched live rather than
redistributed, per the source project's own citation policy. The Milton and Keats
marks in `examples/` are descriptions and citations, not reproduced facsimiles.

## Credits

- **Melville's Marginalia Online** — Steven Olsen-Smith (Boise State, founding
  editor) and Christopher Ohge (University of London, General Editor), for
  preserving and transcribing Melville's actual marginalia.
- **The Folger Shakespeare** — Barbara A. Mowat, Paul Werstine, Michael Poston, and
  Rebecca Niles, Folger Shakespeare Library, for the free modern text.
- **The Free Library of Philadelphia** — for digitizing its 1623 First Folio in full
  and putting it within reach; and **Claire M. L. Bourne** and **Jason Scott-Warren**,
  who identified the hand in it as Milton's in 2019.
- **Caroline F. E. Spurgeon**, *Keats's Shakespeare* (1928), and UVic's
  *Mapping Keats's Progress*, for the record of what Keats wrote and when.
