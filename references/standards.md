# Standards: what is applied and how far to trust it

ISO, ABNT and most other drawing standards are paid documents. This project does not reproduce their text. It applies general conventions as taught in open teaching material, and records where the source is secondary. **Nothing here is a certificate of conformity.** When a contract requires conformity, the drawing must be checked against the purchased standard.

## Conventions applied in v0.1

| Convention | Value here | Related standards | Basis |
|---|---|---|---|
| Sheet sizes | A0 to A4 | ISO 5457, ABNT NBR 16752 | Open teaching material |
| Margins | 20 mm left, 10 mm others | ISO 5457, ABNT NBR 16752:2020 | Secondary source below. Older NBR 10068:1987 used 25 and 7 (available as `frame="nbr-1987"`) |
| Title block position and width | Bottom right, up to 180 mm | ISO 7200, ABNT NBR 16752 | General practice. **Doubt:** NBR 10068:1987 used 178 mm; the current figure was not verified |
| Line weights | Thick 0.5, thin 0.25 (2:1) | ISO 128 series, ABNT NBR 16861 | General practice. Other weight series not offered yet |
| Line types | Continuous, dashed, chain | ISO 128 series, ABNT NBR 16861 | General practice. Dash lengths are approximate |
| Lettering heights | 2.5, 3.5, 5, 7 mm | ISO 3098, ABNT NBR 16861 | General practice. **The font is not standard lettering**: Overpass is an open substitute |
| Scales | 1:1, 1:2, 1:5, 1:10 ... and 2:1, 5:1 ... | ISO 5455, ABNT NBR 8196 | General practice. 1:25 is common in building work and is not in this list: it is allowed but warns |
| Dimensions | Value above the line; vertical reads from the right; closed arrows; 1 mm gap and 1.5 mm overrun on extension lines | ISO 129-1, ABNT NBR 17068 | General practice. Exact sizes unverified |
| Not-to-scale value | Underlined | ISO 129-1 | Widely taught. **Doubt:** check the current edition's wording |
| Decimal comma | In Portuguese | ABNT practice | General practice |
| Section hatching | Thin lines at 45° | ISO 128 series, ABNT NBR 17067 | General hatching only. Material-specific patterns not implemented |
| Thin sections solid | Black fill | ISO 128 series | General practice |
| First-angle symbol | Frustum left, circles right | ISO 5456-2, ABNT NBR 17006 | Widely published. Default, as Brazil uses first angle |
| Process symbols | Simplified | ISA-5.1, ISO 10628-2 | Style only, not verified |

## Brazilian standards that have been replaced

Several ABNT standards still cited everywhere were superseded in 2020 to 2022. This mapping comes from university teaching material, **not from ABNT**. Check the status in the ABNT catalogue before citing.

| Older | Newer | Subject |
|---|---|---|
| NBR 8403:1984 | NBR 16861:2020 | Lines (and lettering) |
| NBR 10067:1995 | NBR 17006:2021 | Projection methods, views and sections |
| NBR 10068:1987 | NBR 16752:2020 | Sheet layout |
| NBR 10126:1998 | NBR 17068:2022 | Dimensions and tolerances |
| NBR 12298 | NBR 17067:2022 | Hatching |

**Doubts:** whether NBR 8402 (lettering) was absorbed into NBR 16861, and whether NBR 8196 (scales) has been replaced. No source found either way. Sources also disagree about the title of NBR 17068.

## Open sources consulted

- [UFRN, Normas](https://www.vetorial.design.ufrn.br/src/pdfs/Normas.pdf): list of replacements.
- [UFRGS, Folha de desenho técnico e linhas](https://www.ufrgs.br/destec/wp-content/uploads/2020/07/7-FOLHA-DE-DESENHO-TÉCNICO-E-LINHAS-Geísa.pdf): margins in the newer standard.
- [IFSC, material on the NBR 10068](https://docente.ifsc.edu.br/gianpaulo.medeiros/MaterialDidatico/Desenho%20Mecatr%c3%b4nica%20/aula%202/NBR%2010068-Folha%20de%20desenho%20-%20Leiaute%20e%20dimensoes.pdf): the older layout.

## Rules for this project

- Never reproduce text, tables or figures from a paid standard, here or in a drawing's notes. Naming a standard and applying a convention is fine.
- A convention without an open source goes in as a recorded doubt, not as a fact.
- Do not print "according to ISO ..." on a drawing unless someone has checked it against that standard.
