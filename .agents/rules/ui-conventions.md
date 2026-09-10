# Tracora — UI and UX conventions

Read before building any screen, form, list, report or print format.

## What this product is

A custody register. Two or three asset-team people live in it on a
desktop all day; anyone in the company might open it once on a phone,
standing in a store room, to find out who has a laptop.

The single idea worth designing around: **Tracora is a ledger, not a
CRUD app.** Its value is that history cannot be rewritten. The
provenance of an asset — every hand it has passed through — is the
product. Wherever there is a choice, make history visible and make
custody legible at a glance.

## Colour is state, never decoration

Tracora's palette IS its status system. Asset status is the one thing a
user scans a list for, so status carries the colour and nothing else
does. No gradient washes, no tinted cards, no accent colour applied for
visual interest.

Frappe list-view indicators accept a colour name; use these mappings
consistently in every list, report and dashboard:

| State | Indicator | Reads as |
|---|---|---|
| In Store | blue | available, nothing wrong |
| Assigned | green | in productive use |
| Under Maintenance | orange | temporarily out, expected back |
| Damaged | orange | needs a decision |
| Lost | red | accountability problem |
| Recovered | yellow | needs confirming before reuse |
| Released | grey | no longer ours, deliberately |
| Retired | grey | end of life |

Related state systems reuse the same logic — `Open` conflicts and
`Flagged` seats are orange (needs a person), `Resolved`/`Active` green,
`Expired` red.

Grey for both Released and Retired is deliberate: both mean "out of
scope, on purpose." They differ in meaning, not in urgency.

## Identifiers are read aloud and typed by hand

Asset tags (`TRC-000042`) and serial numbers get transcribed by someone
reading a sticker in bad light. That is a functional constraint, not a
style choice: render identifiers in a face with disambiguated `0/O` and
`1/l/I`, with tabular figures. Use Frappe's monospace utility class in
the desk; specify the font explicitly in the label print format and the
PWA.

Everywhere else, use Frappe's own type stack. Do not fight the desk's
typography — a custom font in a Frappe form is noise, and this app's
users will spend their day moving between Tracora and HRMS.

## Copy rules

- **Buttons say what happens.** "Assign asset", not "Submit". The
  button that says "Unassign" produces a message that says
  "Unassigned".
- **Refusals name the cause and the fix.** Not "Cannot assign." Say
  "TRC-000042 is assigned to Priya Kumar (AC-1204). Unassign it
  first." Rule 14 in `AGENTS.md` is a copy rule as much as a server
  one — the server produces this string, so write it properly there.
- **Empty states invite an action.** An employee holding nothing says
  "No assets assigned" with an Assign button, not "No records found".
- **Never apologise, never blame.** State what happened.
- Sentence case throughout. No ALL-CAPS labels.

## Desk screens — what to configure

Frappe renders forms and lists; your job is to make them legible, not
to restyle them.

**Every doctype needs:** meaningful `list_view` columns (never the
default name + modified), a status indicator where a status exists,
sensible standard filters, and a `title_field` so records read as
something a human recognises.

**Forms need sections.** A twenty-field flat form is a wall. Group into
labelled sections with column breaks; collapse what is rarely touched.
On `Tracora Employee`, the personal-data section is its own collapsed
section AND hidden entirely for External companies (rule 9).

**Actions belong on the form, not in a submenu.** Assign, Unassign,
Print Label, Transfer Ownership, Recover — primary actions are visible
buttons on the Asset form, shown conditionally by status. An action
that cannot apply right now is absent, not present-and-erroring.

**Dialogs collect only what the endpoint needs.** The unassign dialog
has a location and a remarks field, remarks marked required, and it
will not submit empty — the server refuses it anyway (FR-51), but the
user should never get that far.

**Connections/dashboard on Asset** surfaces movements, maintenance and
licence seats. The movement history is the most important thing on that
screen. It is not a footnote.

## The PWA is the one place with real design freedom

`/scan` is a single-purpose tool used one-handed, often in poor light,
by someone who is not a daily user and will not be trained.

- **One input, always focused.** Scan or type, same box. No mode
  toggle, no category picker, no filters.
- **The answer is the screen.** After a scan the result fills the
  viewport: what the asset is, who has it, where it is. Everything
  else is below the fold.
- **Touch targets minimum 44px.** Assume one thumb and a moving hand.
- **High contrast, large type.** This is read at arm's length in a
  store room, not at a desk.
- **Three states must be designed, not defaulted:** no match (naming
  what was searched, offering to search again), no connection (honest,
  not a spinner forever), and camera permission denied (with the typed
  fallback made obvious).
- **No offline data.** The shell may cache; asset data never does. An
  app that confidently shows last week's holder is worse than one that
  says it cannot reach the server.

Spend the design effort here and on the label. Everything else is a
Frappe desk screen and should look like one.

## The label is a physical object

50 × 25 mm, QR at least 15 mm. It gets stuck on a laptop lid and read
by a phone two years later, after a cleaner has wiped it.

- QR encodes the bare tag string. Nothing else. Ever.
- Tag number in readable type beneath it, large enough to type from
  without a scanner — this is the fallback when the code is scratched.
- Asset name truncated, smallest element, purely for human recognition.
- Quiet zone around the QR respected. No logo inside it, no decoration
  on the label. This is equipment, not stationery.

## Accessibility floor

Visible keyboard focus. Colour never the only signal — every status
indicator carries its text label too, because the whole status system
above is colour-coded and roughly one in twelve men reads it
differently. Respect reduced-motion. The PWA must work at 200% zoom.

## What not to do

No dashboard of decorative number cards on the workspace. No animated
transitions between desk screens. No rounded-card grid treatment
applied to content that is not a set of peers. No icon without a label.
No colour that does not encode a state.
