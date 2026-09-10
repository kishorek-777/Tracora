# PRD: Tracora — Asset Management

| | |
|---|---|
| Version | v0.9 |
| Status | Draft |
| Author | Kishore K |
| Date | 2026-08-31 |
| System | Frappe custom app, installed on the same site as HRMS |
| Approvers | pending |

*This is the flow-level document. It describes what the system does and how work moves through it. It is not the build spec — field types, doctype names and permission internals live in the separate technical PRD, and where the two disagree, this document is the newer decision.*

---

## 1. Summary

Aionion Capital holds hardware and software assets across nine companies, issued to employees across multiple branches. There is no single place that answers two questions reliably: *where is this asset* and *who is holding it*. Tracora is a Frappe application that becomes the one register for every asset and every software licence — recording what exists, who has it, where it sits, everything that has ever happened to it, and what is about to expire.

Tracora also covers assets placed with companies outside the group — clients and partners who hold devices Aionion owns, and devices they own that Aionion manages. Tracora installs on the same site as the existing HRMS and can read companies, branches, departments and employees from there. It does not depend on HRMS: every one of those records can also be created directly in Tracora, so the system runs on its own if HRMS is unavailable, not yet populated, or holds a company Tracora needs before HR does.

The visible change: any asset can be identified from its tag or serial number in seconds from a phone, no employee leaves without their assets being accounted for, and no licence, warranty or payment date passes unnoticed.

## 2. Scope

**Goals**

- One register covering hardware assets and software licences across all companies.
- Custody and location answerable for any asset at any time.
- A complete, unalterable history for every asset.
- Expiry, renewal, warranty, payment and maintenance dates surfaced by email before they lapse.
- An asset identifiable from a phone by scanning its tag or typing its serial number.
- No asset left unaccounted for when an employee exits.
- No hard dependency on HRMS being present or current.
- Assets placed with external companies tracked to the same standard as internal ones, without treating their people as staff.
- Ownership and custody answerable separately, so an asset someone else owns is never counted as ours.

**Non-goals**

- Employees do not log in. They exist as records that assets are assigned to, nothing more.
- No depreciation, book value, or fixed-asset accounting. Tracora is an operational register, not a financial one.
- No procurement, purchase orders or vendor management.
- No separate handover document. An asset moving between two employees is an unassign followed by an assign.

## 3. Users and roles

| Role | Who they are | What they need from this |
|---|---|---|
| Super Admin | Asset team lead | Full access, including deleting records and correcting mistakes that cannot be corrected any other way |
| Admin | Asset team members doing day-to-day issue, return, repair and licence work | Create and edit everything; cannot delete anything |
| Employee | Every person who can hold an asset — staff, and named people at external companies | No login. Appears as the holder of assets, and as the subject of the exit check |

Both roles see all companies. There is no restriction by company or branch — a person who can log in can see the whole register.

## 4. Requirements

### Master records and HRMS

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-01 | Companies can be read from HRMS or created directly in Tracora. A company record holds its name and address. | Must | A company created in Tracora is usable on assets without HRMS involvement |
| FR-02 | Branch and Department can be read from HRMS or created directly in Tracora, and are used to classify both employees and assets. | Must | Both routes produce a branch that can be selected on an asset |
| FR-03 | A Location record holds a place name, a text address, a latitude and a longitude. Locations are created in Tracora only. | Must | A location saves with all four values present |
| FR-04 | The Google Maps link on a location is generated from its latitude and longitude, not typed in and not stored. Opening it shows the location on a map. | Must | Changing the coordinates changes where the link opens, with no separate edit |
| FR-05 | Every hardware asset has exactly one current location at all times. | Must | An asset cannot be saved without a location |
| FR-54 | A company, branch, department or employee created in Tracora behaves identically to one read from HRMS. No screen, report, reminder or flow treats the two differently. | Must | An asset assigned to a Tracora-created employee appears in every report alongside HRMS-sourced ones |
| FR-55 | Tracora continues to function when HRMS is unavailable or uninstalled. No screen fails and no scheduled job errors because an HRMS record cannot be read. | Must | Every flow completes on a site with HRMS disabled |
| FR-56 | Employee code is unique across the whole system regardless of where the record came from. A code that already exists is refused — on manual entry and on HRMS sync alike. Nothing is merged, overwritten or silently linked; the conflict is reported for a person to resolve. | Must | Syncing an employee whose code exists in Tracora produces a named conflict and changes no data |

### Employees

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-06 | An employee record holds employee code, name, mobile, email, date of birth, branch, department, Aadhaar number and permanent address. | Must | All fields present and saved |
| FR-07 | Aadhaar number and permanent address are shown on the employee view for identification at issue and recovery. | Must | Both fields visible to a logged-in Admin |
| FR-08 | The employee view lists every asset currently assigned to that person, hardware and software licence seats alike. | Must | An employee holding three assets shows all three on one screen |
| FR-09 | An employee can be marked exited in Tracora directly. Tracora does not wait for, or depend on, an exit being recorded in HRMS. | Must | An employee is exited in Tracora on a site where HRMS holds no exit record |
| FR-10 | Marking an employee as exited **in Tracora** is blocked while any asset or licence seat remains assigned to them. The block names what is outstanding. | Must | Attempting exit in Tracora with one asset outstanding is refused and the asset is named |
| FR-68 | An exit recorded in HRMS is never blocked by Tracora. HR's action always succeeds. Tracora marks the employee Pending Clearance, lists the outstanding items, and surfaces them for the asset team to clear. | Must | Exiting an employee in HRMS with two assets outstanding succeeds in HRMS and produces a Pending Clearance record in Tracora |
| FR-69 | A Pending Clearance employee cannot receive new assignments, and is cleared to Exited automatically once nothing remains assigned. | Must | Releasing the last asset moves the employee from Pending Clearance to Exited with no further action |
| FR-11 | Each asset released at exit is recorded with a date and remarks stating where it went. | Must | The asset timeline shows the exit release with destination, date and remarks |

### Hardware assets

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-12 | An asset record holds: asset name, brand, model number, serial number, asset ID/tag, status, condition, owning company, holding company, branch, current location, and current holder where assigned. Branch is a property of the asset, not of whoever happens to hold it, so an unassigned asset still belongs to a branch. | Must | An asset with no holder still appears in the branch-wise report |
| FR-13 | An asset ID/tag is unique across the whole register, and no tag may equal any asset's serial number. Serial numbers are unique per brand, since two manufacturers can legitimately issue the same string. A duplicate is rejected on save with the existing asset named. | Must | A tag matching another asset's serial is refused; the same serial under two brands is accepted |
| FR-14 | Asset status is one of: In Store, Assigned, Under Maintenance, Damaged, Lost, Recovered, Released, Retired. | Must | Status list matches exactly, with no free text |
| FR-15 | Asset condition is one of: New, Good, Fair, Poor, Not Working. Condition is set independently of status. | Must | An asset can be In Store and Poor at the same time |
| FR-16 | Moving an asset between locations or between companies is recorded as a dated movement carrying a reason and the person who recorded it. | Must | Each movement produces a timeline entry with reason and recorder |
| FR-17 | Every asset carries a timeline showing every assignment, unassignment, location change, status change, condition change and maintenance event in date order. Timeline entries cannot be edited or deleted. | Must | An attempt to edit a past timeline entry is refused for both roles |
| FR-18 | Maintenance is recorded against an asset with the date sent, the reason, the vendor or handler, the date returned and the condition on return. | Must | An asset returning from maintenance shows both dates and the closing condition |
| FR-19 | Only Super Admin can delete a record. Admin has no delete on any record type. | Must | The delete action is absent for Admin and refused if attempted directly |
| FR-93 | Shared and fixed equipment (e.g., printers, WiFi routers, projectors) can be marked as shared (`is_shared`). Shared assets are held by a location/branch rather than an individual person, and cannot be assigned to an employee while marked shared. An optional point of contact (`point_of_contact`, Link to Tracora Employee) identifies who to contact about the asset without implying custody, appearing in employee custody reports, or blocking exit clearance. | Must | An asset with `is_shared` checked cannot be assigned to an employee; saving a shared asset with an assigned holder is refused; exiting an employee who is a point of contact is not blocked by asset clearance. |

### Assigning and unassigning

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-50 | An asset can be assigned from the asset record by choosing an employee, or from the employee record by choosing one or more assets. Both routes produce the same result and the same timeline entry. | Must | The same assignment, made either way, is indistinguishable afterwards |
| FR-51 | Unassigning an asset requires remarks. The remarks are mandatory, stored on the timeline, and cannot be edited afterwards. | Must | Unassign without remarks is refused; remarks appear on the timeline |
| FR-52 | On unassign, the asset returns to a named location and its status becomes In Store, unless it is being sent to maintenance or marked Damaged or Lost. | Must | An unassigned asset always has a location and a status |
| FR-53 | An asset moving from one employee to another is an unassign followed by an assign. Both events appear separately on the timeline with their own dates and remarks. | Must | A transfer produces two timeline entries, not one |
| FR-57 | Assigning an asset already assigned to someone else is refused, naming the current holder. The asset must be unassigned first. | Must | Direct reassignment is blocked with the holder named |
| FR-58 | An asset that is Under Maintenance, Lost or Retired cannot be assigned. | Must | Assignment is refused for each of the three statuses |

### Asset tags and labels

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-41 | Every asset registration begins with the Admin choosing the tag mode: Auto-generated or Manual entry. The choice is explicit and recorded on the asset. | Must | The asset form cannot be completed without a tag mode selected |
| FR-66 | On Auto-generated, Tracora issues the next number in the series TRC-000001, six running digits. The tag field is filled by the system and cannot be typed into. | Must | Choosing Auto produces the next number and the field is not editable |
| FR-67 | On Manual entry, the tag field opens for typing and Tracora issues nothing. The number typed is the number stored. | Must | Choosing Manual leaves the field empty and editable, and consumes no series number |
| FR-42 | Tags from both modes are held in the same field and share the uniqueness rule in FR-13. Nothing downstream — search, scan, reports, labels — behaves differently by mode. | Must | An auto tag and a manual tag resolve identically in phone search |
| FR-43 | TRC- is reserved for the Auto-generated series. A manually entered tag beginning with TRC- is rejected, so the generated series can never collide with a pre-printed label already stuck to an asset. | Must | Typing a tag starting TRC- is refused with a message naming the reason |
| FR-44 | Tracora produces a printable label for any asset. The label carries a QR code encoding the asset tag number only — no URL, no employee name, no personal data of any kind. | Must | Decoding a printed label with any scanner returns the tag number and nothing else |
| FR-45 | The label shows the tag number as readable text beneath the QR code, so an asset with a damaged or worn code can still be identified and typed into search. | Must | Tag number legible on a printed label without a scanner |
| FR-46 | Labels print at 50 mm × 25 mm with the QR code at least 15 mm square, so it scans from a phone held at arm's length. | Must | A printed label scans from 30 cm on a standard phone camera |
| FR-47 | Labels print as a batch for a selected set of assets, laid out as one sheet or file rather than one file per asset. A single label also prints from the asset record. | Must | Selecting twenty assets produces one printable output containing twenty labels |
| FR-48 | A label can be reprinted at any time. Reprinting does not change the tag number, does not create a new asset, and is recorded on the asset timeline. | Should | Reprinting twice leaves one asset with one unchanged tag and two timeline entries |
| FR-49 | Assets bought with a manufacturer barcode already on them keep their serial number as recorded; the Tracora label is additional and does not replace it. | Should | An asset with both codes resolves to the same record from either scan |

### Software licences

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-20 | A software licence record holds: asset name, software name, licence type, licence expiry date, warranty expiry date, licence renewal date, warranty renewal date, payment date and renewal cycle. | Must | All fields present and saved |
| FR-21 | A licence holds seats. On a user licence a seat names both a user and the device; on a device licence the device is required and the user optional. The same user and device cannot appear twice on one licence. | Must | A user-licence seat missing either is refused; a duplicate pair is refused |
| FR-22 | Each licence has a renewal cycle: one-time, monthly, quarterly, half-yearly or yearly. | Must | Cycle is selectable per licence |
| FR-23 | The next renewal date and next payment date are calculated from the cycle and the last renewal or payment date, and roll forward automatically once a renewal is recorded. | Must | Recording a renewal on a quarterly licence advances the next date by three months |
| FR-24 | A licence whose expiry date has passed is visibly flagged as expired in list views and reports. | Must | An expired licence is distinguishable without opening it |
| FR-59 | Unassigning a hardware asset flags every licence seat installed on that device as needing attention, naming the licence and the user. The seat is not silently released. | Must | Unassigning a laptop with two licence seats surfaces both |
| FR-60 | An employee's licence seats count as outstanding for the exit check in FR-10, alongside their hardware. | Must | Exit is blocked by a licence seat with no hardware assigned |

### External companies and ownership

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-70 | Every company is marked Internal or External. Internal means part of the group, whether or not HRMS knows about it. External means a client or partner. | Must | A company cannot be saved without a type |
| FR-71 | External companies are created in Tracora only. They are never expected in HRMS and no sync or subscriber touches them. | Must | An external company is unaffected by any HRMS activity |
| FR-72 | Branch and department are required when a member of staff is entered by hand. They are optional for an employee of an external company, and optional when a record arrives from HRMS. Nobody invents a branch to register a client's engineer. | Must | An external-company employee saves with neither; an HRMS employee with neither is created and flagged incomplete |
| FR-73 | Every asset records the company that owns it and the company that currently holds it, as two separate facts. For an ordinary internal asset both are the same. | Must | An asset owned by one company and held by another shows both correctly |
| FR-74 | No report mixes owned and merely-held assets without labelling which is which. A count of "our assets" means assets we own. | Must | An asset owned by a client does not appear in an owned-asset total |
| FR-75 | An employee belonging to an external company cannot hold Aadhaar number, date of birth or permanent address. The fields are hidden on their record and refused on save. There is no employment relationship to justify holding them. | Must | Entering an Aadhaar number against an external-company employee is refused |
| FR-76 | An asset can be assigned to any employee, whether they belong to an internal or an external company. There is no second kind of holder. | Must | An external-company employee holds an asset with the same history as a member of staff |
| FR-77 | Employee-wise reporting covers internal-company employees only. Assets held by people at external companies appear in a separate external-custody report, never folded into headcount-based figures. | Must | An externally held asset is absent from the employee report and present in the external one |
| FR-78 | An employee cannot be marked exited or inactive while holding any asset or licence seat, whatever company they belong to. The block names what is outstanding. | Must | Exiting an external-company employee holding one licence seat is refused and the seat is named |
| FR-79 | A licence seat names an employee. On a user licence both the employee and the device are required; on a device licence only the device is. | Must | A user-licence seat missing either is refused |
| FR-80 | The HRMS-driven exit and Pending Clearance process applies to internal employees only. An external-company employee is exited in Tracora directly, by hand. | Must | No HRMS event can change an external-company employee |

### Corrections and lifecycle

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-81 | Every employee field is either HRMS-owned or Tracora-owned. On a synced employee, HRMS-owned fields are read-only and Tracora-owned fields stay editable. Aadhaar number and permanent address are always Tracora-owned. | Must | Aadhaar is editable on an HRMS-sourced employee; name is not |
| FR-82 | A change of owning company is recorded as a dated movement with a reason, in the same way a change of holder is. Ownership is never changed by editing the field. | Must | Selling an asset to a client produces a timeline entry naming both companies |
| FR-83 | An asset that leaves Tracora's care without reaching end of life — a client-owned device we stop managing — is marked Released. Released is distinct from Retired, and history is kept for both. | Must | A Released asset is absent from active reports and its timeline still reads |
| FR-84 | An asset marked Lost that is later found is Recovered by an explicit action carrying remarks and a condition. It cannot be reassigned until that happens. | Must | Assigning a Lost asset is refused until it is recovered |
| FR-85 | Ending a relationship with an external company is blocked while any asset remains with them, and names what is outstanding. | Must | Closing a client holding two assets is refused and both are named |
| FR-86 | When an employee moves between companies, their assets do not move with them. Every asset they hold is flagged for review, naming the employee and both companies. | Must | A company change produces a review flag per held asset |
| FR-87 | An employee who appears anywhere in movement history cannot be deleted, by any role. | Must | Deleting a former holder is refused and the history is named |
| FR-92 | An employee of an external company has no Aionion employee code, so Tracora issues one from a reserved series. A code from that series can never be typed in by hand. | Must | Creating an external-company employee without a code produces one from the series |
| FR-88 | An employee code is never reused. A rehire is a new record with a new code, so old custody history never attaches to a new employment. | Must | Re-creating a code belonging to an exited employee is refused |

### Reminders

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-25 | Reminder emails are sent for: licence expiry, warranty expiry, licence renewal, payment due, and maintenance due. | Must | Each of the five types produces an email in a test run |
| FR-26 | Each reminder is sent 30, 15, 7, 2 and 1 days before the due date, and again on the due date. Nothing is sent after the due date passes. | Must | A due date 40 days out produces exactly six emails on the expected days |
| FR-27 | Reminder recipients are all Super Admin and Admin users. | Must | Both roles receive the test reminder |
| FR-28 | Every reminder sent is logged with its date, recipient and delivery outcome. A failed send is visible without checking the mail server. | Should | A deliberately failed send appears as failed in the log |
| FR-29 | A one-time reminder can be set on a licence with no recurring cycle. | Should | A one-time reminder fires once and does not repeat |
| FR-89 | A date that is already past on an active record produces one overdue notice and a visible flag on the record. An expired licence is never silent. | Must | A licence imported with last year's expiry produces a notice and a flag |
| FR-90 | The daily job records when it last ran. If that is more than 48 hours ago, or if no user holds a role that receives reminders, a warning is shown in the application. | Must | Disabling the scheduler produces a visible warning within two days |
| FR-63 | A reminder stream stops the moment its closing event is recorded, and no further emails in that stream are sent for that date. The closing events are: licence renewal recorded, for licence expiry and licence renewal reminders; warranty renewal recorded, for warranty expiry; payment recorded, for payment due; maintenance closed with a return date, for maintenance due. | Must | Recording payment on day 10 stops the day-7, day-2, day-1 and due-date emails |
| FR-64 | Reminders are evaluated fresh each day against the current state of the record. Emails are never scheduled or queued in advance for future dates. | Must | Recording a payment after the first reminder has gone out prevents every later one with no cancellation step |
| FR-65 | When a closing event rolls a date forward under FR-23, the reminder stream restarts against the new date. A licence renewed with the next date 20 days out receives the 15, 7, 2 and 1 day reminders for that new date. | Must | Renewing a monthly licence produces reminders against the next month's date |

### Mobile app

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-30 | The mobile interface is a PWA installable from the browser. There is no app store submission. | Must | Installed to a phone home screen from a URL |
| FR-31 | Search is a single box. Scanning a barcode or QR code with the phone camera fills it; typing a serial number, asset tag or asset name does the same. No category or type is selected first. | Must | The same box resolves a scanned tag, a typed serial and a name |
| FR-32 | A search hit shows the asset in full: name, brand, model, serial, tag, status, condition, company, branch and location, its maintenance record, and its timeline. | Must | Every field on the desktop asset record is reachable from the phone result |
| FR-33 | The same screen shows who holds it: employee name, code, mobile, email, branch and department, and the date it was assigned. Where the asset carries licence seats, those are listed too. | Must | Asset and holder are on one screen without a second search |
| FR-34 | A search with no match returns a clear "not found" showing what was searched, and creates nothing. | Must | Scanning an unknown tag returns not-found and adds no record |
| FR-91 | An exact tag or serial match opens that asset directly. A partial name match returns a list showing tag, holder and location, and the user chooses. The system never guesses between several matches. | Must | A name matching three assets returns three rows, not one |
| FR-35 | Login is required. Both roles see the same search and the same results. | Must | Search is unreachable when logged out |

### Reports

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-36 | Reports available: company-wise, branch-wise, department-wise, employee-wise, asset-wise, expiry-wise, warranty-wise and payment-wise. | Must | Each report runs and returns rows |
| FR-37 | The department-wise report is what was described as team-wise. Department is the grouping, because it is the only team-shaped field that exists on an employee. | Must | Report groups by department |
| FR-38 | Every report exports to Excel with the same columns shown on screen. | Must | Export opens in Excel with matching rows |
| FR-39 | Aadhaar number and permanent address never appear in any report or export, in any role. | Must | Neither field is selectable as a report column |
| FR-40 | Report access matches record access. No report shows a field a role cannot see on the record itself. | Must | A field hidden on the form does not appear in any report for that role |

### Asset history

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-61 | A history view covering all assets, filterable by asset, employee, location, event type and date range. | Must | Filtering by one employee returns every asset event involving them |
| FR-62 | History is retained when an asset is retired or disposed. Retiring an asset never removes its history. | Must | A retired asset's timeline is still readable |

### Non-functional

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| NFR-01 | A scan or serial search returns a result within two seconds on a normal mobile data connection. | Must | Timed on a phone on 4G against a loaded register |
| NFR-02 | Every create, edit and delete is recorded with the user and the timestamp, for every record type. | Must | A change log is visible on any record |
| NFR-03 | Asset history is retained for the life of the asset and is not purged on any schedule. | Must | No scheduled job deletes history |
| NFR-04 | Tracora runs on the existing HRMS site with one login, but has no code path that requires HRMS to be installed. | Must | The app installs and runs on a site without HRMS |
| NFR-05 | A failed reminder email does not stop the remaining reminders in that run from being sent. | Should | One bad address in a batch of twenty still delivers nineteen |

## 5. Flows

**Flow: Register a new asset**

1. Admin opens New Asset and enters name, brand, model, serial number.
2. Admin selects the company, the branch it belongs to, and the location where the asset physically is.
3. Condition is set; status defaults to In Store.
4. Admin chooses the tag mode. Auto-generated issues the next TRC- number; Manual entry opens the field for the number already printed on the item.
5. Asset is saved and appears in the register, unassigned.
6. Admin prints the label — QR code plus readable tag number — and fixes it to the item.

*Exceptions*

- Serial or tag already exists — save is refused, the existing asset is named, and Admin checks whether this is a duplicate entry or a mislabelled item.
- Manual mode and the typed tag begins with TRC- — save is refused, so a pre-printed label cannot occupy a number the system will later issue itself.
- Many assets arrive together — they are registered as a batch and their labels printed as one sheet.
- The company or branch does not exist yet — Admin creates it in Tracora rather than waiting for HR.

**Flow: Assign an asset**

Two entry points, one result.

*From the asset:*

1. Admin opens the asset and selects Assign.
2. Admin selects the employee. Company, branch, department and code fill in from the record.
3. Admin confirms the date and adds a reference.

*From the employee:*

1. Admin opens the employee and selects Assign Assets.
2. Admin picks one or more assets from those currently In Store.
3. Admin confirms the date and adds a reference.

Either way: status becomes Assigned, the employee becomes the holder, the asset appears on that employee's list, and the timeline records who assigned it, to whom, and when.

*Exceptions*

- Asset is already assigned — assignment is refused and the current holder is named. The asset must be unassigned first.
- Asset is Under Maintenance, Lost or Retired — assignment is refused.
- Employee is exited or pending clearance — assignment is refused.
- Employee is inactive — assignment is refused.
- Asset is owned by one company and going to another — permitted, and both companies are recorded. This is the normal case for a device placed with a client.

**Flow: Unassign an asset**

1. Admin opens the asset, or the employee's asset list, and selects Unassign.
2. Admin enters remarks. This is mandatory — it is the only record of why the asset came back and where it went.
3. Admin selects the location the asset returns to.
4. Status becomes In Store; the employee is no longer the holder.
5. The timeline records the release with the date, the remarks and who recorded it.

*Exceptions*

- Asset comes back damaged — condition is set on the same action and status becomes Damaged rather than In Store.
- Asset is going straight to another employee — unassign first with remarks naming the receiving employee, then assign. Two entries, so the gap between them is visible rather than hidden.
- Asset carries software licence seats — those seats are flagged with the licence and user named, so nobody is left holding a licence on a device they no longer have.

**Flow: Employee exit**

*Exit recorded in Tracora:*

1. Admin marks the employee exited.
2. Tracora checks for assets and licence seats assigned to that person.
3. If any remain, exit is blocked and the outstanding items are listed by name and tag.
4. Admin unassigns each one with remarks stating where it went.
5. Once nothing remains assigned, the exit proceeds.

*Exit recorded in HRMS:*

1. HR marks the employee exited. This always succeeds — Tracora never blocks it.
2. Tracora marks the employee Pending Clearance and lists what is outstanding.
3. The employee can receive no new assignments while pending.
4. Admin unassigns each item with remarks.
5. When nothing remains, the employee moves to Exited automatically.

*Exceptions*

- An asset cannot be found — it is marked Lost with remarks, which clears the block but leaves a permanent record naming the last holder.
- Employee has already left the building — the same flow runs; the date recorded is the actual date the asset was recovered, not the exit date.
- HRMS is unavailable — the exit is recorded in Tracora and the check runs unchanged.
- Employee is cleared and then rehired — a new employee code is a new record. Reusing a code is refused, because the old record carries the old custody history.

**Flow: Maintenance and repair**

1. Admin opens the asset and selects Maintenance, recording the reason, the vendor or handler, and the date sent.
2. Status becomes Under Maintenance. The asset stays associated with its holder but cannot be reassigned.
3. On return, Admin records the return date and the condition.
4. Status returns to its previous value; the timeline holds both ends of the event.

*Exceptions*

- Asset is beyond repair — it is retired instead of returned; history is kept, and the record stays searchable.
- Maintenance runs past the employee's exit — the exit block treats an asset under maintenance as still outstanding, because it has to come back to someone.

**Flow: Software licence renewal and payment**

1. Admin creates the licence with software name, expiry dates, payment date and renewal cycle.
2. Admin adds seats. Each seat names a user and the device the software sits on; neither can be left blank.
3. Reminders go out at 30, 15, 7, 2 and 1 days before each date, and on the day.
4. Admin records the renewal or payment when it is done.
5. The next dates roll forward by the cycle.

*Exceptions*

- Payment or renewal is recorded partway through the reminder run — the remaining reminders for that date stop immediately, and the stream restarts against the new date once it rolls forward.
- Licence is not renewed and expires — it is flagged expired and stays in the register with its seats visible, so it is clear who loses access and on which machines.
- A seat's device is unassigned — the seat is flagged, naming the licence and user, and is treated as outstanding at that employee's exit.
- Users or devices change mid-term — seats are edited on the licence; the change is recorded, not overwritten silently.

**Flow: Find an asset from a phone**

1. Staff member opens the PWA and logs in.
2. Taps scan and points the camera at the tag — or types the serial number, tag or asset name.
3. The asset opens showing everything: full asset detail, maintenance record and timeline, the current holder with their contact details and branch, and any licence seats on the device.

*Exceptions*

- Tag is damaged or unreadable — the tag number printed as text beneath the code is typed into the same box, as is the serial number or asset name.
- Asset is unassigned — the same screen shows its location and status, with no holder.
- No match — a not-found message showing what was searched. Nothing is created; unknown assets are registered from the desktop, not from a failed search.

## 6. What the system holds

Described in business terms. Field-level detail is in the technical PRD.

| Record | Source | What it holds |
|---|---|---|
| Company | HRMS or Tracora | Company name, address, type (Internal / External) |
| Branch | HRMS or Tracora | Branch name, linked to company |
| Department | HRMS or Tracora | Department name |
| Employee | HRMS or Tracora | Employee code, name, designation, mobile, email, branch, department, status. For internal staff only: DOB, Aadhaar, permanent address |
| Location | Tracora | Place name, address text, latitude, longitude; map link generated from coordinates |
| Asset | Tracora | Name, brand, model, serial, tag, status, condition, owning company, holding company, branch, location, current holder |
| Ownership Transfer | Tracora | A dated change of owning company, with reason and recorder |
| Asset Movement | Tracora | Every assignment, unassignment, location change and exit release; dated, with remarks, attributed |
| Maintenance | Tracora | Reason, vendor, date sent, date returned, condition on return |
| Software Licence | Tracora | Software name, expiry and renewal dates, payment date, renewal cycle |
| Licence Seat | Tracora | The user and the device, on a licence |
| Reminder Log | Tracora | What was sent, to whom, when, and whether it delivered |

## 7. Security and compliance

**Permissions**

| Role | View | Create | Edit | Delete |
|---|---|---|---|---|
| Super Admin | All | Yes | Yes | Yes |
| Admin | All | Yes | Yes | No |

No row-level restriction applies. Both roles see all companies, all branches and all employees. This is a deliberate choice recorded in section 8 and not an oversight — if a branch-level restriction is wanted later it is a change to this document, not a configuration tweak.

Timeline and history entries are not editable by either role, including Super Admin. Deleting an asset removes the asset; it does not rewrite what the timeline says happened.

**Personal data held**

| Field | Source | Why it is here |
|---|---|---|
| Employee name, code | HRMS or Tracora | Identifying the holder of an asset |
| Mobile, email | HRMS or Tracora | Contacting the holder to recover or verify an asset |
| Date of birth | HRMS or Tracora | Carried as part of the employee record; no asset process reads it |
| Branch, department | HRMS or Tracora | Grouping and reporting |
| Aadhaar number | HRMS or Tracora | Identity confirmation at issue and recovery |
| Permanent address | HRMS or Tracora | Recovering assets from a departed employee |

Aadhaar number and permanent address are visible on screen to both logged-in roles, and never appear in any report or export (FR-39). This is the boundary that matters: on screen the data is read by one person at a time and leaves no copy; in an export it becomes a spreadsheet on someone's laptop the moment the file is opened.

Employees created in Tracora carry the same fields and the same handling as those read from HRMS. Creating an employee locally does not create a lower standard of protection for their data.

Employees of external companies are covered by none of the three restricted rows. Date of birth, Aadhaar number and permanent address are hidden on their record and refused on save (FR-75). There is no employment relationship to justify holding any of them, and the check is a validation rather than a missing field — which is a weaker control, because a validation can be edited later and an absent field cannot. It is stated here so nobody assumes more protection than exists.

No client data, no KYC data and no money movement is involved. This is employee data, plus business contact details for external custodians.

## 8. Design decisions

| Decision | Alternative considered | Why not |
|---|---|---|
| Two roles: Super Admin (full) and Admin (no delete) | Three roles — Director, Admin, Executive, as in the earlier technical PRD | The three-role split gave two roles the same practical rights. Two roles with one meaningful difference — who can delete — is enforceable and understandable. This supersedes the three-role model |
| Companies, branches, departments and employees can come from HRMS or be created in Tracora | Reading them from HRMS only, as a hard dependency | Tracora needs to run before HRMS is complete, and needs to survive HRMS being down. The cost is the duplicate-record risk, which FR-56 controls by making employee code unique across both sources |
| A code conflict on sync is an error, not a merge | Letting HRMS overwrite, or letting Tracora win | Either automatic rule silently changes data somebody entered deliberately. An error stops and asks; a merge decides on your behalf and tells nobody |
| Tracora never blocks an action inside HRMS | Enforcing the outstanding-asset check against HR's exit too | A block inside HR's save makes HRMS dependent on Tracora, reversing the direction of the whole design. HR could not offboard anyone until the asset team acted. Pending Clearance gets the same outcome without holding HR hostage |
| HRMS changes propagate on document events, not on a schedule or a button | Polling nightly, or a manual sync action | Both systems are on one site and one database. An event fires in the same transaction, so there is no drift window and nothing to remember to press |
| Branch is a field on the asset | Deriving branch from the current holder | Deriving it means an asset sitting in store belongs to no branch and vanishes from branch reporting — which is exactly the stock nobody can account for |
| No handover document; a transfer is unassign then assign | A single handover action recording both ends at once | Two entries make the gap between release and receipt visible. A single handover hides the period where an asset is in transit and nobody is accountable for it |
| Remarks are mandatory on unassign | Optional remarks | Without a handover document, the unassign remark is the only record of why an asset came back and where it went. Optional means empty |
| Licence seats name a user and a device | Naming only the user | A licence with no device cannot be checked at exit, cannot be reclaimed when a laptop is returned, and cannot be audited against what is actually installed |
| Employees have no login | An employee self-service view of their own assets | Employees are the subject of the record, not users of the system. Adding logins for every employee to view a list they can be sent is a large permission surface for a small benefit |
| Google Maps link generated from latitude and longitude | Storing the map URL as its own field alongside the coordinates | Two stored copies of the same fact drift apart. Someone updates the coordinates, the old link keeps opening the old place, and nobody notices until a delivery goes to the wrong branch |
| Renewal cycle set per licence | Four fixed reminder streams with one schedule each | Licences do not share a cycle. A yearly antivirus and a monthly subscription both need reminding, on different rhythms, from the same screen |
| QR code encodes the asset tag number only | Encoding a URL that opens the asset in Tracora | A URL turns every label into a link anyone can scan with a phone camera, pointing at an internal system. A bare tag number is meaningless to a stranger and resolves only inside the app |
| Tag mode is an explicit choice per asset, not inferred from whether the field was left blank | Auto-generating whenever the tag field is empty | Inferring the mode means a distracted Admin who skips the field gets a second number issued for an asset that already carries a label. An explicit choice makes the decision visible at the moment it is made |
| Reminders are evaluated daily against current state, never queued ahead | Scheduling the five emails when the due date is set | A queued email cannot be recalled. Once payment is recorded, the reminders still in the outbox go out anyway, and the person who just paid gets chased four more times |
| Tag numbers may be generated or typed from pre-printed stock, with TRC- reserved for generated ones | Generated only, or pre-printed only | Existing assets already carry labels and reprinting all of them is wasted work; new assets are cheaper to number automatically. The reserved prefix is what stops the two schemes colliding |
| Aadhaar and permanent address visible on screen, never in exports | Hiding them entirely, or allowing them in exports | Hidden entirely, the handover identity check cannot be done. In exports, they leave the system uncontrolled |
| Ownership changes go through a movement, not a field edit | Editing the owning company on the form | The custody chain is protected by making the holder unwritable. Ownership deserves the same protection — a laptop quietly changing owner is exactly the edit nobody would notice |
| A rehire gets a new employee code | Reactivating the old record | The old record carries the old employment's custody history. Reusing it merges two employments into one timeline and makes the first one unauditable |
| Ownership and custody are two fields, not one | A single company field meaning "whose asset is this" | You hold assets you do not own and own assets you do not hold. One field forces a choice that makes every total wrong in one direction or the other |
| One employee record type, internal and external alike | A separate contact record for external people, without the personal fields | The separate type was the stronger data-protection control and the more complex model. One type removes the two-part holder reference from assets, movements, licence seats and every report. The personal fields are blocked by validation instead, which is weaker and stated as such |
| External employees get a reserved code series | Making employee code optional for them | Employee code is the primary key. Optional would mean a second key or a nullable one, and both are worse than issuing a number |
| Assets are deleted only by Super Admin; history is never editable | Allowing Admin to correct mistakes by deleting and re-entering | Delete-and-re-enter destroys the custody chain, which is the one thing this system exists to keep |
