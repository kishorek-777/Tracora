# Tracora — User Acceptance Testing (UAT) Guide & Test Cases

This document is the authoritative testing and operational manual for Tracora. It covers all 10 core functional areas, system invariants, step-by-step user execution instructions, and 30 exhaustive test cases designed for UAT sign-off.

---

## 1. Architecture & System Roles

| Role | Access Level | Responsibilities |
| :--- | :--- | :--- |
| **Tracora Super Admin** | Full access | System configuration, settings, company/branch setup, all asset actions, licence overrides. |
| **Tracora Admin** | Operational access | Asset creation, assignment, returns, maintenance logs, licence allocations, viewing reports. |
| **Tracora User** | Read-only | Views assigned assets, personal custody receipts, and licence allocations. |

---

## 2. Core Modules & Operational Guide

### Module 1: Organizational Masters
* **DocTypes**: `Tracora Company`, `Tracora Branch`, `Tracora Department`, `Tracora Location`, `Tracora Employee`.
* **Key Rules**:
  - `Company`: Categorized as **Internal** (holding internal custody) or **External** (client, vendor, third-party site).
  - `Branch` & `Department`: Naming convention enforced by system: `{Name} - {Company Abbr}` (e.g., `HQ - TIC`).
  - `Location`: Physical sites (warehouses, office floors, server rooms). Locations are **shared across companies** and do not carry company abbreviations.
  - `Employee`: Primary key is `employee_code` (e.g., `EMP-1001`). Rehires get new codes; codes are never recycled. Statuses: `Active`, `Pending Clearance`, `Exited`, `On Leave`.

### Module 2: Asset Management (`Tracora Asset`)
* **Key Rules**:
  - **Asset Tag**: Generated automatically as `TRC-XXXXXX` (or manual if legacy pre-printed).
  - **Single Source of Truth**: The fields `status`, `assigned_to`, `holding_company`, and `owner_company` **CANNOT be edited directly in form edit mode**. They can only be modified through validated server actions (**Assign**, **Unassign**, **Transfer**, **Send to Maintenance**).
  - **QR Code**: Bare string payload containing only the exact asset tag (e.g., `TRC-000288`) for high-speed offline scanning.

### Module 3: Asset Movements & Chain of Custody (`Tracora Asset Movement`)
* **Key Rules**:
  - **Strictly Append-Only**: Records are permanent audit events. No user (including Administrator) can edit or delete an existing movement record.
  - Every physical transition (Assign, Return, Location Transfer, Repair Dispatch, Lost Recovery) writes an immutable record recording timestamp, actor, prior state, and new state.

### Module 4: Maintenance Logs (`Tracora Maintenance Log`)
* **Key Rules**:
  - Assets in maintenance have status `Under Maintenance` and cannot be assigned to employees.
  - Tracks service vendor, maintenance type (Preventive, Breakdown, Calibration), cost, out date, return date, and service report notes.

### Module 5: Software Licences & Seat Allocation (`Tracora Software Licence`)
* **Key Rules**:
  - Tracks seat counts: Total Seats, Assigned Seats, and Remaining Seats.
  - Licence types: **User licence** (tied to Employee) or **Device licence** (tied to Asset).
  - Tracks expiration (`licence_expiry_date`) and recurring billing schedule (`next_renewal_date`).

### Module 6: Reminders & Notifications (`Tracora Reminder Log`)
* **Key Rules**:
  - Daily scheduler monitors upcoming licence expirations (30-day, 15-day, 7-day, overdue) and pending employee exit clearance.
  - Append-only log preventing duplicate reminder spam.

### Module 7: Reports & Analytics (`Tracora Report`)
* **Key Rules**:
  - Consolidated single-entry reporting dashboard with 8 canonical views:
    1. *Assets Owned* (Ownership register + company distribution chart)
    2. *Assets Held* (Physical custody breakdown)
    3. *Assets by Branch* (Branch inventory + in-store stock)
    4. *Assets by Department* (Department allocation + unassigned stock)
    5. *Assets by Employee* (Surfaces exited staff with red custody alert pills)
    6. *External Custody* (Assets deployed at external clients/vendors)
    7. *Licence Expiry* (Chronological expiration schedule with proximity coloring)
    8. *Licence Renewal Due* (Upcoming payment timetable)
  - Strict PII Gate: Zero exposure of `aadhaar_number` or `permanent_address`.
  - Native Excel export parity matching on-screen column selection.

---

## 3. UAT Test Cases

### Category A: Master Data & Constraints

| Test ID | Test Scenario | Steps to Execute | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **TC-MST-01** | Create Internal & External Companies | 1. Go to **Companies** → **Add Tracora Company**.<br>2. Create "Alpha Internal" (Internal, Abbr: AI).<br>3. Create "Beta Client" (External, Abbr: BC). | Both companies save successfully with correct company type badges. | [ ] |
| **TC-MST-02** | Branch & Department Auto-Naming | 1. Go to **Branches** → Create branch "Chennai HQ" under "Alpha Internal".<br>2. Check record name. | Record name is automatically generated as `Chennai HQ - AI`. | [ ] |
| **TC-MST-03** | Location Creation (Global/Shared) | 1. Go to **Locations** → Create "Central Store Floor 2".<br>2. Provide address & optional GPS coords. | Location saves without company abbreviation suffix. | [ ] |
| **TC-MST-04** | Employee Creation & Code Uniqueness | 1. Go to **Employees** → Add `EMP-9001` (Active, Email, Dept).<br>2. Try adding a second employee with identical code `EMP-9001`. | First employee succeeds; second attempt throws duplicate primary key error. | [ ] |
| **TC-MST-05** | Employee Exit & Clearance Flagging | 1. Open `EMP-9001` holding an asset.<br>2. Change status to `Exited` or `Pending Clearance`. | System prevents direct `Exited` status without clearing custody, or marks `Pending Clearance`. | [ ] |

---

### Category B: Asset Invariants & Direct Modification Blocking

| Test ID | Test Scenario | Steps to Execute | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **TC-AST-01** | Auto-Generated Asset Tag Creation | 1. Go to **Assets** → **Add Tracora Asset**.<br>2. Select Tag Mode: `Auto-generated`.<br>3. Fill Name, Brand (Dell), Model, Owner Company, Branch, Location.<br>4. Save. | Asset tag `TRC-XXXXXX` is automatically allocated; Status starts as `In Store`. | [ ] |
| **TC-AST-02** | Manual Asset Tag Creation | 1. Create asset with Tag Mode: `Manual`.<br>2. Enter tag `LEGACY-8801`. Save. | System accepts pre-printed custom tag format without collision. | [ ] |
| **TC-AST-03** | Direct Form Modification Block (Crucial) | 1. Open an existing asset.<br>2. Attempt to manually edit `Status` from `In Store` to `Assigned` or type an employee into `Assigned To`.<br>3. Save. | Fields are read-only in the UI. Server API rejects any direct write bypassing the assign endpoint. | [ ] |
| **TC-AST-04** | QR Code Print Format Verification | 1. On Asset form, click **Print Label**.<br>2. Inspect print preview. | Shows clean thermal label with Asset Name, Brand, Tag, and QR code with bare tag string. | [ ] |

---

### Category C: Asset Movements (Chain of Custody)

| Test ID | Test Scenario | Steps to Execute | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **TC-MOV-01** | Standard Asset Assignment | 1. Open asset with status `In Store`.<br>2. Click **Actions** → **Assign Asset** (or sidebar Assign button).<br>3. Select active employee, target location, and remarks.<br>4. Submit. | 1. Asset status transitions to `Assigned`.<br>2. `Assigned To` updates to employee.<br>3. Movement record created in timeline. | [ ] |
| **TC-MOV-02** | Refuse Assigning Already Assigned Asset | 1. Take asset already assigned to Employee A.<br>2. Attempt to assign to Employee B without unassigning. | System throws validation error: Asset is already assigned; must be unassigned first. | [ ] |
| **TC-MOV-03** | Unassign Asset with Mandatory Remarks | 1. Open assigned asset.<br>2. Click **Actions** → **Unassign Asset**.<br>3. Leave Remarks empty and submit.<br>4. Fill Remarks ("Project completed, returned in good shape") and submit. | 1. Empty remarks is blocked with validation error.<br>2. Valid remarks sets status to `In Store` and clears `Assigned To`. | [ ] |
| **TC-MOV-04** | Auto-Clearance on Last Unassignment | 1. Assign asset to Employee with status `Pending Clearance`.<br>2. Unassign the last asset held by this employee. | Employee status automatically updates from `Pending Clearance` to `Cleared`. | [ ] |
| **TC-MOV-05** | Location Change Movement | 1. Open `In Store` asset.<br>2. Click **Actions** → **Change Location**.<br>3. Select new Location ("Warehouse B") and submit. | Asset location updates; `Tracora Asset Movement` records type `Location Change`. | [ ] |
| **TC-MOV-06** | Transfer Company Ownership | 1. Click **Actions** → **Transfer Ownership**.<br>2. Select new owning internal company and reason.<br>3. Submit. | `owner_company` updates cleanly with audit movement logged. | [ ] |
| **TC-MOV-07** | Mark Asset Lost & Recovery | 1. Click **Actions** → **Mark as Lost** with investigation notes.<br>2. Verify status is `Lost`.<br>3. Attempt to assign lost asset (must fail).<br>4. Click **Actions** → **Recover Asset** back to store. | Asset correctly blocks assignment while `Lost`, and restores to `In Store` upon recovery. | [ ] |
| **TC-MOV-08** | Append-Only Enforcement (Security) | 1. Go to **Asset Movements** list view.<br>2. Open any movement record (e.g. `TAM-2026-000128`).<br>3. Attempt to edit remarks and save, or delete from Menu. | System refuses save and delete with explicit permission/invariant exception. | [ ] |

---

### Category D: Maintenance Workflow

| Test ID | Test Scenario | Steps to Execute | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **TC-MNT-01** | Send Asset to Maintenance | 1. Open an `In Store` asset.<br>2. Click **Actions** → **Send to Maintenance**.<br>3. Enter vendor name, issue description, expected return date.<br>4. Submit. | Asset status transitions to `Under Maintenance`; `Tracora Maintenance Log` created. | [ ] |
| **TC-MNT-02** | Prevent Assignment While In Maintenance | 1. Open asset with status `Under Maintenance`.<br>2. Attempt to trigger Assign action. | System blocks action: Assets under maintenance cannot be assigned. | [ ] |
| **TC-MNT-03** | Return Asset from Maintenance | 1. Open `Tracora Maintenance Log` or Asset form.<br>2. Click **Complete Maintenance / Return to Store**.<br>3. Enter cost, repair notes, and condition rating. | Asset status returns to `In Store`; updated condition reflected on Asset. | [ ] |

---

### Category E: Software Licences & Seat Allocations

| Test ID | Test Scenario | Steps to Execute | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **TC-LIC-01** | Create User Licence with Seat Limits | 1. Go to **Software Licences** → **Add Tracora Software Licence**.<br>2. Name: "Figma Enterprise", Seats: 5, Type: `User licence`.<br>3. Expiry: 6 months future, Renewal: 1 year future.<br>4. Save. | Licence created with Total Seats: 5, Assigned: 0, Remaining: 5. Status: `Active`. | [ ] |
| **TC-LIC-02** | Allocate Licence Seat to Employee | 1. Open "Figma Enterprise" licence.<br>2. In Seats table, add Row with Employee `EMP-1001`.<br>3. Save. | Assigned Seats increments to 1; Remaining Seats decrements to 4. | [ ] |
| **TC-LIC-03** | Depleted Licence Seat Cap Enforcement | 1. Allocate all remaining seats until Remaining = 0.<br>2. Status automatically flips to `Depleted`.<br>3. Attempt to allocate one additional seat beyond cap. | System blocks over-allocation with error: No seats available. | [ ] |
| **TC-LIC-04** | Revoke / Unassign Licence Seat | 1. Remove an employee from the seat allocation table.<br>2. Save. | Assigned Seats decrements; Remaining Seats increments; status flips back to `Active`. | [ ] |

---

### Category F: Unified Reports & Excel Export

| Test ID | Test Scenario | Steps to Execute | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **TC-REP-01** | Single-Click Reports Navigation | 1. In Desk left sidebar, click **Reports**.<br>2. Verify destination. | Directly opens `Tracora Report` without intermediate clicks or empty workspaces. | [ ] |
| **TC-REP-02** | Primary View Switcher | 1. Switch dropdown between **Assets Owned**, **Assets by Branch**, **Assets by Employee**, and **Licence Expiry**. | Report dynamically updates table columns, summary cards, and charts in real time. | [ ] |
| **TC-REP-03** | Multi-Select Filtering | 1. In **Assets Owned**, select multiple companies in the `Company` filter.<br>2. In **Status** filter, select `Assigned` and `In Store`. | Table filters rows matching ANY selected company and status simultaneously. | [ ] |
| **TC-REP-04** | Exited Employee Custody Alert | 1. Switch view to **Assets by Employee**.<br>2. Find an asset held by an employee with status `Exited`. | Row displays red indicator pill: **`Exited (Custody Alert)`**. | [ ] |
| **TC-REP-05** | Dynamic Column Selection | 1. In `Filter Columns` multi-select list, uncheck 3 non-essential columns.<br>2. Observe table. | Table re-renders immediately hiding the unchecked columns. | [ ] |
| **TC-REP-06** | Excel (.xlsx) Export Parity | 1. Configure custom filters and column visibility.<br>2. Click Menu (**...**) → **Export** → **Excel**.<br>3. Open downloaded file. | Spreadsheet columns, headers, and rows match the visible on-screen table exactly. | [ ] |

---

## 4. UAT Sign-off Checklist

- [ ] All Master Doctypes configured without duplicate violations.
- [ ] Asset tags auto-generate properly with zero sequence collisions.
- [ ] Direct form tampering of custody/status is strictly blocked.
- [ ] Complete chain of custody is recorded in `Tracora Asset Movement` (append-only).
- [ ] Maintenance dispatches and returns update asset condition and availability.
- [ ] Software licence seat pools enforce capacity limits.
- [ ] Unified Report executes all 8 views with zero PII exposure and exact Excel export parity.
