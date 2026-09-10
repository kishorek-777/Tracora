# Frappe framework conventions

Read before writing any doctype, controller, whitelisted method, query,
client script, or test. This is general Frappe craft — where a Tracora
rule in `AGENTS.md` and something here overlap, `AGENTS.md` wins; it is
more specific to this app.

## Whitelisted methods — the most common source of real bugs

**`frappe.get_doc()` does not check permissions.** `doc.save()`,
`doc.insert()`, `doc.submit()` do — but a whitelisted method that
fetches a document with `get_doc` and returns it, or fields from it,
bypasses the permission system entirely unless you call
`doc.check_permission("read")` yourself. This applies directly to
`api.lookup.find_asset` (P11) and anywhere a subscriber or endpoint
reads a document to hand data back to the client. Do not assume a
whitelisted decorator alone means the caller was authorized to see
what comes back.

**Use `frappe.get_list`, not `frappe.get_all`, for anything read on a
user's behalf.** `get_list` respects the calling user's permissions;
`get_all` does not (`ignore_permissions=True` implicitly). Reports and
the PWA lookup are user-facing reads — `get_list`. A background job
running as the system (P9's reminder scheduler) may legitimately use
`get_all`, because it has to see every record regardless of who is
logged in — that is a deliberate exception, not a default.

**Never accept a doctype or field list from the client and act on it
generically.** No `frappe.get_doc(request_body).insert()`, no
`frappe.get_attr(method_name)()`. Every whitelisted method in this app
names its target doctype and fields in the code, not from user input.

**Type-hint whitelisted method parameters.** Frappe validates against
the hint before your code runs:
```python
@frappe.whitelist()
def assign_asset(asset: str, employee: str, reference: str | None = None):
```
Not a substitute for `validate()` on the doctype — a second layer, at
the boundary.

**State-changing methods take `POST`, reads take `GET`.**
`@frappe.whitelist(methods=["POST"])` on anything that writes. A GET
that mutates data breaks caching assumptions and is a CSRF surface.

**A refusal is `frappe.throw()`, not a silently-ignored return.**
`frappe.throw(_("TRC-000042 is assigned to Priya Kumar (AC-1204). "
"Unassign it first."))` — this is also how CLAUDE.md rule 14's
copy-with-a-reason actually reaches the client; a `return {"ok":
False}` does not surface as an error dialog the same way.

## Queries

**`frappe.qb`, not string-built SQL.** If a report or a check genuinely
needs raw SQL, use `frappe.db.sql(query, values)` with parameterized
values — never an f-string or `.format()` building the query. This is
the framework's own guidance, and it is where a generic AI habit of
`f"WHERE name = '{name}'"` becomes a real vulnerability.

**No `SELECT *`.** Name the fields — this is also how P11's rule
against leaking `aadhaar_number` is actually enforced in code, not just
stated in the workflow.

**Every list-returning method has a limit.** An unbounded query against
a growing asset register is a P10 problem waiting to happen; page it or
cap it explicitly.

## DocType and controller conventions

- One controller class per doctype, in `<app>/<module>/doctype/
  <doctype_snake_case>/<doctype_snake_case>.py`, extending
  `frappe.model.document.Document`. This is created automatically by
  `bench new-doctype` — use it rather than hand-rolling the folder
  structure.
- Controller hooks run in a fixed order relative to the database write:
  `before_insert` and `before_naming` run before the row exists;
  `validate` runs before every save, insert or update; `on_trash` runs
  before deletion completes. Rules 1 and 2 in `AGENTS.md` depend on
  knowing exactly which hook fires when — do not guess.
- `autoname()` sets `self.name` directly; it runs before `validate()`.
  Rule 7's company-qualified branch/department naming and P4's tag
  series both live here.
- Frappe auto-generates type-annotation stubs above the
  `# end: auto-generated types` comment in newer controllers. Never
  hand-edit that block — it is regenerated from the doctype JSON.

## hooks.py

- `doc_events` is for hooking doctypes the app does NOT own (P3's HRMS
  subscribers — see `AGENTS.md` rule 13). For doctypes Tracora owns,
  the logic goes in the controller class, not in `doc_events`.
- `scheduler_events` keys are `"daily"`, `"hourly"`, `"weekly"`,
  `"monthly"`, or a cron string under `"cron"` — P9's reminder job is
  `"daily"`.
- `fixtures` entries always carry an explicit filter (`AGENTS.md`
  covers why — an unfiltered `Role` fixture exports every role on the
  site).

## Developer mode and schema changes

- Doctype and workspace changes made through the desk UI write straight
  into the owning app's files on disk when `developer_mode` is on. This
  is exactly how the stray edits in `apps/hrms` happened on a previous
  bench, before this project's build even started. When building
  Tracora's own doctypes, prefer writing the JSON and controller
  directly and committing them, per `AGENTS.md` rule 13 — do not rely
  on UI-driven scaffolding as the source of truth.
- After any doctype JSON change made outside the running app (a direct
  file edit), the database needs `bench --site mysite.local migrate`
  or a targeted `frappe.reload_doc()` to pick it up. Per `AGENTS.md`,
  ask before running either on this bench.

## Testing

Use `FrappeTestCase` from `frappe.tests.utils`, not bare `unittest`
against a live site by hand — it wraps each test in a transaction that
rolls back, so test data never pollutes `mysite.local`'s real content.

```python
from frappe.tests.utils import FrappeTestCase

class TestTracoraAsset(FrappeTestCase):
    def test_duplicate_serial_within_brand_refused(self):
        ...
```

Where a phase's acceptance list asks for something a screenshot can't
show cleanly — "as Administrator, editing a movement is refused" — a
`FrappeTestCase` asserting `frappe.exceptions.ValidationError` is
better evidence than a screenshot of an error toast, and it becomes a
regression test for every phase after it. Prefer this for the
code-level checks in P3, P5, P9, P12; keep screenshots for what's
genuinely a UI concern.

## Client scripts and desk customisation

- A client script changes form behaviour without a new doctype field —
  conditional visibility beyond what `depends_on` alone can express,
  a confirm dialog before a destructive button, a computed display-only
  value. Prefer `depends_on` and standard doctype properties first;
  reach for a client script only when the JSON can't express it.
- `frappe.ui.form.on("Tracora Asset", { ... })` is the standard shape.
  Keep Tracora's client scripts in `public/js/<doctype>.js`, referenced
  from `hooks.py`'s `doctype_js`, not pasted into Customize Form (same
  reasoning as rule 13 — it belongs in git, not in the database).
- Report Builder and the workflow builder are for end users configuring
  their own view of data Tracora already exposes — not for defining
  Tracora's own doctypes, permissions, or business logic.
