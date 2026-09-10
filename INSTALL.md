# Installing the Tracora agent setup

Bench: `frappe-bench`. Site: `mysite.local` (shared with erpnext, hrms,
hrms_custom, and several unrelated apps — see AGENTS.md for the list
Tracora must never touch).

Copy into `apps/tracora` (already scaffolded via `bench new-app
tracora` and installed via `bench --site mysite.local install-app
tracora`):

    apps/tracora/
    ├── AGENTS.md                          # rules — read by Antigravity AND Claude Code
    ├── .agents/
    │   ├── rules/ui-conventions.md        # design system
    │   └── workflows/p1.md … p15.md       # the fifteen phases, invoked /p1 … /p15
    └── docs/
        ├── PRD.md                         # Tracora-PRD-Flow-v0.9.md, renamed
        ├── HLD.md                         # Tracora-HLD-v0.8.md, renamed
        ├── LLD.md                         # Tracora-LLD-v0.8.md, renamed
        └── EDGE-CASES.md                  # Tracora-Edge-Cases-v0.1.md, renamed

Commands:

    cd ~/frappe-bench/apps/tracora
    cp /path/to/AGENTS.md .
    mkdir -p .agents/rules .agents/workflows docs
    cp /path/to/ui-conventions.md .agents/rules/
    cp /path/to/p*.md .agents/workflows/
    cp Tracora-PRD-Flow-v0.9.md  docs/PRD.md
    cp Tracora-HLD-v0.8.md       docs/HLD.md
    cp Tracora-LLD-v0.8.md       docs/LLD.md
    cp Tracora-Edge-Cases-v0.1.md docs/EDGE-CASES.md

Open `~/frappe-bench` in Antigravity — the bench root, not the app
folder, so the agent can run `bench` commands and read `apps/hrms`.

Then type `/p1` in the Agent Manager.

## Running a phase

1. `/p1` — the agent enters PLANNING and produces an implementation
   plan.
2. **Read the plan. Approve or correct it.** This is the review gate;
   it is worth more than reviewing code afterwards.
3. The agent executes, then verifies and produces a walkthrough with
   screenshots and command output.
4. **Read the walkthrough against the phase's acceptance list.** A
   walkthrough that says "verified" without evidence is not a pass.
5. Only then move to the next phase.

## Do not

- Run phases in parallel. Later phases close gaps earlier ones leave
  open; parallel agents break that chain silently.
- Enable full auto-approval on this bench — it has other apps and
  another site (`event.management`) sharing it. `bench drop-site` and
  `bench migrate` are one typo apart from something expensive.
- Let the agent touch airplane_mode, buzz, event_management,
  library_management, lms, payments, or frappe_whatsapp — see
  AGENTS.md.
- Skip the browser-extension setup — without it there is no visual
  evidence, and the verification loop is the main reason to use this
  tool for this project.
