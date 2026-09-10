# Flags and Edge Cases: Tracora

| | |
|---|---|
| Version | v0.1 |
| Status | Draft |
| Author | Kishore K |
| Date | 2026-08-31 |
| Covers | Tracora-PRD-Flow-v0.7, Tracora-HLD-v0.4, Tracora-LLD-v0.4 |

*Every situation I can find where the design does something wrong, does nothing, or does something nobody has decided on. Work through it before build, not after.*

**Severity**

- **Blocker** — the design is wrong or silently does nothing. Fix before build.
- **Decide** — the design is coherent but nobody has chosen the behaviour.
- **Accepted** — known, deliberate, documented. No action, but don't be surprised.
- **Handled** — already covered. Listed so nobody re-raises it.

---

## 1. HRMS sync and employees

| # | Situation | What happens today | Severity |
|---|---|---|---|
| 1.1 | Employee code is renamed in HRMS | Frappe allows renaming a document. The subscriber sees an unfamiliar code and creates a **second** Tracora employee. The original keeps the assets; the new one is empty. Nothing flags it. There is no `after_rename` subscriber | **Blocker** |
| 1.2 | HRMS employee has no branch or department | Both are required for internal companies (FR-72). The subscriber cannot build the record, the exception is caught and logged, and the employee **never appears in Tracora**. Silently | **Blocker** |
| 1.3 | HRMS employee is deleted | No `on_trash` subscriber exists. The Tracora record survives with a dangling reference, still holding assets. Probably the right outcome — history should not vanish — but it is unspecified | **Decide** |
| 1.4 | HR reverses an exit entered by mistake | The subscriber sets Pending Clearance or Exited on the way in. Nothing sets it back to Active. The employee is stuck | **Blocker** |
| 1.5 | Employee is rehired under the same code | The old record carries the old custody history and an Exited status. The subscriber reactivates it, silently merging two employments into one asset history | **Decide** |
| 1.6 | Employee moves between group companies in HRMS | Their company, branch and department update. Their assets do not — those belong to the old company and branch. A branch report now shows an asset in Chennai held by someone in Mumbai | **Decide** |
| 1.7 | Exit recorded while an asset is Under Maintenance | Maintenance assets are still assigned, so Pending Clearance counts them. Correct, and worth confirming the query does not filter on status | **Handled** |
| 1.8 | Same person entered twice under two different codes | Undetectable. Tracora has no second identity key, and using Aadhaar as one would mean indexing restricted data | **Accepted** |
| 1.9 | HRMS employee sits under a company Tracora has marked External | Contradiction — external companies are never in HRMS (FR-71). No guard exists | **Blocker** |
| 1.10 | HRMS is installed after Tracora has been running for months | Bulk import hits hundreds of already-created Tracora records. Every value mismatch becomes a conflict, all at once, with nobody having estimated the volume | **Decide** |
| 1.11 | Aadhaar and permanent address are not in your HRMS | On an HRMS-sourced employee those fields are read-only and empty, with no way to ever populate them. FR-06 needs splitting into HRMS-owned fields and Tracora-only fields | **Blocker** |
| 1.12 | Subscriber throws for a reason nobody anticipated | It is caught and logged. HR's save succeeds. The Tracora record is missing and nobody is told | **Decide** |

## 2. Companies, branches, departments

| # | Situation | What happens today | Severity |
|---|---|---|---|
| 2.1 | A branch or department conflicts on sync | `Tracora Sync Conflict` has an `employee_code` field. It cannot record a conflict on any other record type. Company, branch and department conflicts have nowhere to go | **Blocker** |
| 2.2 | A branch is renamed in HRMS | Same shape as 1.1. Tracora creates a second branch; employees and assets still point at the first | **Blocker** |
| 2.3 | Two companies share an abbreviation | Branch and department names are `{name} - {abbr}`. Two companies abbreviated AC put "Chennai - AC" in collision again. Nothing enforces abbreviation uniqueness | **Blocker** |
| 2.4 | HRMS company has no abbreviation | Tracora requires one. The subscriber must derive it or fail, and neither is specified | **Decide** |
| 2.5 | A company is deleted in HRMS while Tracora assets reference it | The Tracora company survives. Correct, and unspecified | **Decide** |
| 2.6 | An external company later becomes a group company | Its type flips to Internal. Its contacts now sit under an internal company, which FR-71 implies should not happen, and their held assets are on contacts rather than employees | **Decide** |
| 2.7 | A location is shared by two companies | `Tracora Location` is named `{name} - {abbr}`, so a genuinely shared building must be entered twice | **Decide** |

## 3. Asset tags and labels

| # | Situation | What happens today | Severity |
|---|---|---|---|
| 3.1 | A manual tag equals another asset's serial number | Uniqueness is enforced per field, not across them. Phone search matches tag on one asset and serial on another, and `find_asset` returns one payload. The wrong asset can be returned | **Blocker** |
| 3.2 | App is reinstalled or the naming series counter is reset | Frappe stores the counter in `tabSeries`. If it is lost, the series restarts at 1 and reissues tags already stuck on assets. Uniqueness rejects the save, so registration simply stops working until someone resets the counter by hand | **Blocker** |
| 3.3 | Two Admins register assets in auto mode at the same moment | Frappe's naming series is atomic. No collision | **Handled** |
| 3.4 | A form is abandoned in auto mode | The number is consumed at insert, not at form open. Nothing is wasted | **Handled** |
| 3.5 | A physical label falls off or is destroyed | Reprint keeps the same tag (FR-48). But an asset whose label is gone and whose serial is worn is unfindable by scan or serial — only by name | **Accepted** |
| 3.6 | Two assets from the same manufacturer share a serial number | Manufacturers do reuse serials across product lines. FR-13 rejects the second asset outright, and the register cannot hold it | **Decide** |

## 4. Assignment and custody

| # | Situation | What happens today | Severity |
|---|---|---|---|
| 4.1 | An asset's owning company changes — sold or transferred to a client | Not modelled. Movement records carry `from_company`/`to_company` for *holding*, not ownership. An ownership change is an invisible field edit | **Blocker** |
| 4.2 | A contact leaves the client company | Nothing tells you. No event, no equivalent of an exit. The asset stays assigned to someone who no longer works there | **Decide** |
| 4.3 | An external company relationship ends entirely | No process recovers the assets placed with them. Deactivating the company is blocked only at the contact level (FR-78) | **Decide** |
| 4.4 | A client-owned asset leaves your management | It must stop counting as yours, but its history must survive. Retiring it is the closest fit and means something different | **Decide** |
| 4.5 | Super Admin deletes an employee or contact who has movement history | Movements point at the deleted record through a dynamic link. History renders with a blank holder | **Blocker** |
| 4.6 | An asset is unassigned twice by two Admins at once | Second unassign finds no holder. Behaviour unspecified — error, or silent no-op | **Decide** |
| 4.7 | An asset is assigned to an employee at a different company from the asset's own | Permitted, and normal for a device placed with a client. Both companies are recorded | **Handled** |
| 4.8 | An asset is marked Lost and later found | Nothing prevents reassigning it — status simply changes. Whether that needs a deliberate "recovered" step is undecided | **Decide** |

## 5. Software licences

| # | Situation | What happens today | Severity |
|---|---|---|---|
| 5.1 | A seat's device is retired or deleted | The seat points at nothing. Only unassignment flags a seat (FR-59); retirement and deletion do not | **Blocker** |
| 5.2 | Every user is removed from a licence | FR-20 requires at least one seat, so a genuinely unused licence cannot be emptied. It must be deleted, which needs Super Admin | **Decide** |
| 5.3 | The same user and device appear on two seats of one licence | Nothing forbids it. Seat counts overstate usage | **Decide** |
| 5.4 | A seat names a contact who is later deactivated | FR-78 blocks deactivation for held *assets*. Whether a licence seat counts is unstated | **Blocker** |
| 5.5 | A licence covers a device with no assigned user — a shared machine | Both fields are mandatory (FR-21), so a shared kiosk licence cannot be recorded without naming someone arbitrary | **Decide** |

## 6. Reminders

| # | Situation | What happens today | Severity |
|---|---|---|---|
| 6.1 | A licence is migrated with a due date already in the past | The day difference is negative, never matches a lead value, and **no reminder ever fires**. The expired licence is silent | **Blocker** |
| 6.2 | The scheduler is disabled or fails | No reminders, no error. The absence of an email is invisible. Already an open item and still unanswered | **Blocker** |
| 6.3 | The scheduler misses a lead day and runs the next | No catch-up. That day's notice is lost | **Accepted** |
| 6.4 | Payment is recorded on the due date itself | Whether the day-0 email goes out depends on the order of the save and the daily run. A race with no stated winner | **Decide** |
| 6.5 | Lead days are changed in Settings mid-cycle | Reminders already logged do not re-fire; newly added lead days fire late. Neither is wrong, neither is specified | **Decide** |
| 6.6 | Every Admin user is deactivated | The run resolves no recipients, sends nothing, and succeeds | **Decide** |
| 6.7 | A due date sits near midnight in a different timezone | `getdate()` uses the site timezone. A date entered from another timezone can shift a day | **Accepted** |
| 6.8 | The job runs twice in one day | The unique constraint on the reminder log makes it idempotent | **Handled** |
| 6.9 | A renewal moves the date forward by less than the shortest lead | A monthly licence renewed the day before its next date gets the day-1 and day-0 notices only | **Accepted** |

## 7. Mobile search

| # | Situation | What happens today | Severity |
|---|---|---|---|
| 7.1 | A search string matches several assets by name | `find_asset` is specified to return one payload. Multi-match behaviour is undefined | **Blocker** |
| 7.2 | A contact-held asset is scanned | The holder block has no branch, no department, no employee code. The screen must render a different shape | **Decide** |
| 7.3 | An unassigned asset is scanned | Location and status only, no holder. Covered in the flow exceptions | **Handled** |
| 7.4 | Someone scans a random product barcode in a shop | Returns not-found naming what was searched, and creates nothing | **Handled** |
| 7.5 | Connectivity drops mid-search | No offline cache by design, so it fails honestly | **Accepted** |

## 8. Access and data

| # | Situation | What happens today | Severity |
|---|---|---|---|
| 8.1 | `report_hide` does not cover list-view export | Aadhaar and permanent address leave the system through a route nobody tested. FR-39 rests entirely on this and it is unverified | **Blocker** |
| 8.2 | Someone holds the stock System Manager role | They can write a script report and read anything. Tracora cannot constrain it | **Accepted** |
| 8.3 | Personal data is typed into a contact's free-text field | No field exists for it, but free text always can be misused | **Accepted** |
| 8.4 | Frappe version is v14, not v15 | Virtual fields, naming and `report_hide` behave differently. The LLD assumes v15 | **Blocker** |
| 8.5 | `hrms_custom` has renamed or wrapped `Employee` | The subscriber keys are wrong and nothing fires — indistinguishable from HRMS being absent | **Blocker** |

---

## The order I would fix them in

**Before writing any code**, because they change the design: 1.1, 1.11, 2.1, 2.3, 4.1, 8.4, 8.5.

**Before the first import**, because they corrupt data: 1.2, 1.9, 2.2, 3.1, 3.2.

**Before go-live**, because they fail silently in production: 1.4, 4.5, 5.1, 6.1, 6.2, 7.1, 8.1.

**Everything marked Decide** can wait, but each one is a question somebody will ask during build and someone will answer by guessing if you haven't.
