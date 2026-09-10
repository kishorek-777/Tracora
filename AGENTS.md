# Tracora — agent rules

Asset custody register for Aionion Capital. Frappe custom app.
Specs: `docs/PRD.md` (92 FRs), `docs/HLD.md`, `docs/LLD.md`,
`docs/EDGE-CASES.md`. UI rules: `.agents/rules/ui-conventions.md`.
Frappe framework conventions and security patterns — permission
checks on whitelisted methods, query patterns, testing framework:
`.agents/rules/frappe-framework.md`. Read both rule files before
writing code; `ui-conventions.md` for anything user-facing,
`frappe-framework.md` for anything server-side.

Build one phase at a time via `/p1` … `/p15` in `.agents/workflows/`.
Read only the spec sections a phase names. Do not read the whole LLD
for a single phase — these rules dilute across sixty pages, and that
is the main way generated code drifts from the design.

## Working mode

Use PLANNING → EXECUTION → VERIFICATION. Always produce an
implementation plan and wait for approval before writing code. Always
produce a walkthrough with real evidence — screenshots of the actual
screen, actual command output — never a self-reported "verified."

Run ONE phase at a time. Do not dispatch parallel agents across
phases. Phases share invariants and later phases close gaps earlier
ones leave open; parallel work breaks that chain silently.

## Fifteen rules that are not negotiable

1. **Nothing that matters changes by editing a field.** An asset's
   holder (`assigned_to`), owning company (`owner_company`) and status
   change ONLY through server methods in `api/assign.py` that write a
   `Tracora Asset Movement` in the same transaction. If you are
   setting `doc.assigned_to = x` outside `api/assign.py`, stop.

2. **History is append-only, enforced in code, for every role
   including Administrator.** `Tracora Asset Movement` and
   `Tracora Reminder Log` throw in `validate()` when
   `self.get_doc_before_save()` is not None, and throw
   unconditionally in `on_trash()`. Permission settings are not
   sufficient — they can be edited from the UI, code cannot.

3. **HRMS subscribers never throw.** Every function in
   `integrations/hrms.py` wraps its body in try/except and calls
   `frappe.log_error()`. A subscriber that raises aborts an HR user's
   save in an app they never touched.

4. **No HRMS or ERPNext import at file scope.** Detect with
   `frappe.db.exists("DocType", "Employee")` at call time. A top-level
   import of an absent app breaks every page load.

5. **Every doctype is prefixed `Tracora `.** ERPNext and HRMS own
   `Asset`, `Company`, `Employee`, `Branch`, `Department`, `Location`.

6. **Employee code is the primary key and is never reused.** A rehire
   gets a new code. Reactivating an old record attaches old custody
   history to a new employment.

7. **Branch and Department are named `{name} - {company_abbr}`.
   Location is not** — a building can be shared. `company_abbr`
   carries a unique index.

8. **Tag and serial share one uniqueness namespace.** A tag must not
   equal any asset's serial, and vice versa. Check both fields.
   Serial is unique per brand, not globally.

9. **External-company employees carry no personal fields.**
   `date_of_birth`, `aadhaar_number`, `permanent_address` are hidden by
   `depends_on` and refused in `validate()` when the employee's company
   is `External`. This is a validation standing in for an absent field
   — treat it as load-bearing.

9a. **`aadhaar_number` is always Tracora-owned, even when
    `source = HRMS`.** HRMS holds its own `custom_aadhaar_number` field
    (confirmed present on the live Employee doctype). Tracora's copy is
    entered independently for asset handover and is deliberately never
    read from or written to HRMS — the two values are expected to
    diverge over time. Do not add Aadhaar to the P3 subscriber's field
    list, and do not "fix" this by syncing it. `permanent_address` is a
    stock HRMS field and IS synced normally, following rule 6's
    HRMS-owned behaviour like any other field.

10. **Owning company and holding company are separate, both
    mandatory.** Never assume they are equal, even though they usually
    are.

11. **Reminders compute daily against current state, never queue
    ahead.** No email is ever scheduled for a future date.

12. **A conflict is a record, not a log line.** `Tracora Sync Conflict`
    is generic: `reference_doctype` + `reference_key`.

13. **Tracora's own doctypes are built as committed JSON and
    controllers** — never through Customize Form or the workflow
    builder. (Property Setters ARE correct for customising doctypes
    Tracora does not own — that is how `hrms_custom` works — but that
    is not this app.)

14. **Every refusal names its reason.** "Already assigned to Priya K
    (AC-1204)", never "cannot assign." This is a UI rule as much as a
    server one — see `ui-conventions.md`.

15. **A phase is done when its FRs are demonstrated, not when the code
    runs.** Each workflow lists what proves each FR. Evidence goes in
    the walkthrough.

## Environment

- Frappe `version-16`. ERPNext and HRMS are on `develop`, NOT
  `version-16` — a known mismatch against production, accepted
  deliberately. Re-verify HRMS `Employee` fields against production
  before P15 installs there (see the field-ownership note above).
- Bench `frappe-bench`, site `mysite.local`. This site's HRMS/company/
  employee data is test data — safe to create, edit and delete freely
  as part of build and verification.
- This bench also runs `airplane_mode`, `buzz`, `event_management`,
  `library_management`, `lms`, `payments`, `frappe_whatsapp` —
  unrelated to Tracora, installed on `mysite.local` and/or
  `event.management`. Never read, modify, or run commands against
  these apps, their doctypes, or their data. If a search or a fix
  seems to need touching one of them, stop and report instead.
- Work only in `apps/tracora`. Read `apps/hrms` and `apps/erpnext` for
  reference; never modify them. Never edit files inside `apps/hrms` —
  a previous bench had stray doctype-editor writes there and it cost a
  day to untangle.
- `hrms_custom` customises HRMS via Property Setter fixtures. Read it
  to understand precedent; do not change it.
- Ask before any `bench migrate`, `bench update`, or
  `switch-to-branch`. Never run `bench drop-site`.

## Verification standard

A walkthrough that says "tested and working" is not evidence. For each
FR in the phase's acceptance list, show one of:

- a screenshot of the actual screen, including refusal messages with
  their real wording
- console output of the actual command and its actual result
- a browser recording of the interaction
- a `FrappeTestCase` (see `.agents/rules/frappe-framework.md`) that
  fails on the old code and passes now — preferred for code-level
  checks (append-only guards, permission refusals, subscriber
  behaviour) since it becomes a regression test, not just a moment-in-
  time screenshot

If a check cannot be demonstrated, say so plainly and mark it
untested. An honest gap is worth more than a confident claim — the
whole design rests on rules that look fine until something proves
otherwise.
