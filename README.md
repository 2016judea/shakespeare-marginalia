# melville-annotated-shakespeare

Turn [Melville's Marginalia Online](https://melvillesmarginalia.org)'s archive of
Herman Melville's real pencil marks in his own copy of Shakespeare into a clean,
print-ready PDF — his underlines, scores, checkmarks, and handwritten comments,
reproduced at the right lines of a modern, readable text.

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
3. Matches each of Melville's marks to its line in the modern text.
4. Renders a print-ready HTML/PDF: his marks shown visually in place (an underline
   is an underline, a "scored" passage gets a vertical line in the margin — that's
   what scoring actually meant physically), and his own handwritten comments shown
   as quoted sidenotes. No invented commentary — if he didn't write it, it doesn't
   appear as text.

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
  --appendix-pages 134 \
  --out work/king_lear_annotated.html

# 4. Print to PDF.
./scripts/print_pdf.sh work/king_lear_annotated.html work/king_lear_annotated.pdf
```

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

## Not a scholarly edition

Footnote placement is approximate wherever Melville's 1837 text departs in wording
from the modern edited text used here (textual variants across editions are real —
e.g. his Lear reads "nothing *can* come of nothing," modern editions read "nothing
*will* come of nothing," a genuine Quarto/Folio-lineage difference, not a bug). This
is built for reading pleasure, not textual-critical precision. If you want the
latter, go to the source: [melvillesmarginalia.org](https://melvillesmarginalia.org).

## Licensing

See [NOTICE.md](NOTICE.md) for the full breakdown. Short version: this repo's code
is MIT; the play text is CC BY-NC 4.0 (so **non-commercial use only**, no exceptions);
the marginalia data has no declared open license and is fetched live rather than
redistributed, per the source project's own citation policy.

## Credits

- **Melville's Marginalia Online** — Steven Olsen-Smith (Boise State, founding
  editor) and Christopher Ohge (University of London, General Editor), for
  preserving and transcribing Melville's actual marginalia.
- **The Folger Shakespeare** — Barbara A. Mowat, Paul Werstine, Michael Poston, and
  Rebecca Niles, Folger Shakespeare Library, for the free modern text.
