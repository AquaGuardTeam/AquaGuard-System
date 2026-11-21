from copy import copy
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

SOURCE = Path(r"C:\Users\xyuku\Downloads\Progress Tracker-Group-9 (1).xlsx")

wb = load_workbook(SOURCE)

NAVY = "173B5C"
PALE = "EDF4F8"
WHITE = "FFFFFF"
THIN = Side(style="thin", color="DDE6EC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def clear_sheet(sheet):
    for merged in list(sheet.merged_cells.ranges):
        sheet.unmerge_cells(str(merged))
    for row in sheet.iter_rows():
        for cell in row:
            cell.value = None
    sheet.sheet_view.showGridLines = False


def style_title(sheet, title, end_column):
    sheet["A1"] = title
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=end_column)
    sheet["A1"].font = Font(name="Calibri", size=15, bold=True, color=WHITE)
    sheet["A1"].fill = PatternFill("solid", fgColor=NAVY)
    sheet["A1"].alignment = Alignment(horizontal="left", vertical="center")
    sheet.row_dimensions[1].height = 32


def section(sheet, row, title):
    sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    cell = sheet.cell(row, 1, title)
    cell.font = Font(bold=True, color=NAVY)
    cell.fill = PatternFill("solid", fgColor=PALE)
    sheet.row_dimensions[row].height = 24


def style_header_row(sheet, row, end_column=6):
    for column in range(1, end_column + 1):
        cell = sheet.cell(row, column)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def style_table(sheet, start_row, end_row, end_column):
    for row in range(start_row, end_row + 1):
        sheet.row_dimensions[row].height = max(sheet.row_dimensions[row].height or 15, 20)
        for column in range(1, end_column + 1):
            cell = sheet.cell(row, column)
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)


scope = wb["Scope & Progress Tracker"]
clear_sheet(scope)
style_title(scope, "AQUAGUARD — SYSTEM SCOPE AND IMPLEMENTATION PROGRESS TRACKER", 6)

section(scope, 3, "I. USER MANAGEMENT AND AUTHORIZATION")
for column, value in enumerate([
    "Role / Function", "Total", "Implemented", "Pending", "Completed", "Remarks"
], 1):
    scope.cell(4, column, value)
style_header_row(scope, 4)

role_rows = [
    ("A. Super Administrator", None),
    ("Create and manage administrator and maintenance accounts", 1, 1, 0, 1, "Secure terminal provisioning and staff-account page"),
    ("Assign super-administrator and protected role scope", 1, 1, 0, 1, "super_admin role implemented"),
    ("Monitor system-wide operations and administration", 1, 1, 0, 1, "Dashboard, accounts, and maintenance access"),
    ("B. Administrator", None),
    ("Review dashboard readings, trends, alerts, and device state", 1, 1, 0, 1, "Implemented"),
    ("Authorize and record valve-control activity", 1, 1, 0, 1, "Protected API and event log implemented"),
    ("Review filter and maintenance records", 1, 1, 0, 1, "Implemented"),
    ("C. Maintenance Personnel", None),
    ("Register or replace filters", 1, 1, 0, 1, "Filter registration implemented"),
    ("Record inspection, service, and replacement events", 1, 1, 0, 1, "Maintenance form implemented"),
    ("Review filter installation and service history", 1, 1, 0, 1, "Implemented"),
    ("D. Students and Faculty", None),
    ("View current readings and operational status", 1, 1, 0, 1, "Kiosk and dashboard views implemented"),
    ("Select Cold or Room Temperature dispensing", 1, 1, 0, 1, "Modal and dispensing API implemented"),
    ("Stop active dispensing immediately", 1, 1, 0, 1, "Stop endpoint and modal control implemented"),
    ("E. ESP32 and System", None),
    ("Collect pH, TDS, and turbidity samples", 1, 1, 0, 1, "Firmware code prepared; hardware verification pending"),
    ("Transmit timestamped readings through HTTPS REST API", 1, 1, 0, 1, "Payload and validation implemented"),
    ("Receive dispensing and stop commands", 1, 1, 0, 1, "Polling logic implemented"),
    ("Fail safe during Critical condition or network loss", 1, 0, 1, 0, "Final actuator and fail-safe behavior require hardware testing"),
]

row = 5
for item in role_rows:
    if item[1] is None:
        scope.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
        scope.cell(row, 1, item[0])
        scope.cell(row, 1).font = Font(bold=True, color=NAVY)
        scope.cell(row, 1).fill = PatternFill("solid", fgColor="F4F7F9")
    else:
        for column, value in enumerate(item, 1):
            scope.cell(row, column, value)
    row += 1

scope.cell(row, 1, "TOTAL USER MANAGEMENT AND CONTROL PROGRESS")
scope.cell(row, 2, 16)
scope.cell(row, 3, 15)
scope.cell(row, 4, 1)
scope.cell(row, 5, 15)
for column in range(1, 7):
    scope.cell(row, column).font = Font(bold=True)
    scope.cell(row, column).fill = PatternFill("solid", fgColor="E8F0F4")
    scope.cell(row, column).border = BORDER

section(scope, 28, "II. FUNCTIONAL COMPONENTS")
for column, value in enumerate(["Module / Component", "Expected", "Implemented", "Pending", "Completed", "Remarks"], 1):
    scope.cell(29, column, value)
style_header_row(scope, 29)

module_rows = [
    ("ESP32 Sensing and Control", 5, 2, 3, 2, "Firmware scaffold and polling logic; sensor acquisition and physical fail-safe testing pending"),
    ("Flask REST API", 7, 6, 1, 6, "Readings, kiosk, dispensing, maintenance, alerts, and control routes"),
    ("External or Local MySQL Database", 6, 5, 1, 5, "Schema and SQLAlchemy models implemented; live deployment and external-MySQL configuration pending"),
    ("Rule-Based Condition Classifier", 5, 5, 0, 5, "TDS/turbidity moving averages and rates of change"),
    ("Authentication and Role Authorization", 5, 5, 0, 5, "Super admin, admin, maintenance; kiosk session; CSRF and login limits"),
    ("Administrative Dashboard", 6, 6, 0, 6, "Overview, readings, alerts, maintenance, accounts, and status cards"),
    ("Filter Maintenance Module", 5, 5, 0, 5, "Filter registration, service history, active status, and date validation"),
    ("Kiosk Dispensing Interface", 5, 4, 1, 4, "Software modal and countdown implemented; physical kiosk hardware and field dispensing not yet built"),
    ("Valve and Pump Safety Control", 5, 2, 3, 2, "Command and event logic implemented; hardware feedback pending"),
]
module_row = 30
for values in module_rows:
    for column, value in enumerate(values, 1):
        scope.cell(module_row, column, value)
    module_row += 1
scope.cell(module_row, 1, "TOTAL FUNCTIONAL COMPONENT PROGRESS")
scope.cell(module_row, 2, 49)
scope.cell(module_row, 3, 43)
scope.cell(module_row, 4, 6)
scope.cell(module_row, 5, 43)
for column in range(1, 7):
    scope.cell(module_row, column).font = Font(bold=True)
    scope.cell(module_row, column).fill = PatternFill("solid", fgColor="E8F0F4")
    scope.cell(module_row, column).border = BORDER

section(scope, 41, "III. DETAILED FEATURE AND SCOPE ALIGNMENT")
scope["A42"] = "Feature / Component"
scope["B42"] = "Status"
scope.merge_cells("C42:F42")
scope["C42"] = "Remarks / Implementation Details"
style_header_row(scope, 42)

feature_rows = [
    ("ESP32 sensor acquisition for pH, TDS, and turbidity", "Pending", "GPIO assignments and firmware scaffold prepared; calibration and field accuracy pending"),
    ("Timestamped JSON transmission over Wi-Fi/HTTPS", "In Progress", "API payload and device authentication implemented; deployment TLS pending"),
    ("Post-filtration sensor reading validation", "Completed", "Range and timestamp freshness validation implemented"),
    ("Moving-average and rate-of-change condition assessment", "Completed", "Normal, Warning, and Critical rule-based classifier implemented"),
    ("pH monitored and displayed without classifier use", "Completed", "Explicitly excluded from current classification rules"),
    ("Filter installation and replacement records", "Completed", "Registration and replacement status supported"),
    ("Maintenance inspection and service history", "Completed", "Recorded by authorized accounts"),
    ("Normal, Warning, and Critical alerts", "Completed", "Assessment-derived alerts and alert page implemented"),
    ("Protected valve-control and event logging", "Pending", "Command and event schema implemented; physical feedback pending"),
    ("Cold and Room Temperature kiosk dispensing", "In Progress", "Only these two modes are supported"),
    ("Ten-second dispensing countdown and immediate stop", "In Progress", "Modal countdown and stop endpoint implemented"),
    ("Super-administrator staff account management", "Completed", "Terminal provisioning and protected staff-account interface"),
    ("Administrator and maintenance role boundaries", "Completed", "Role checks implemented on protected routes"),
    ("Dashboard readings, trends, status, and alerts", "Completed", "Overview and real/empty data states implemented"),
    ("Readings history, alerts, and filter-service views", "Completed", "Dedicated authenticated pages implemented"),
    ("Cloudflare Pages/Workers external-MySQL deployment", "Pending", "Architecture selected; credentials, Hyperdrive/provider, and deployment configuration pending"),
]
feature_row = 43
for name, status, remarks in feature_rows:
    scope.cell(feature_row, 1, name)
    scope.merge_cells(start_row=feature_row, start_column=3, end_row=feature_row, end_column=6)
    scope.cell(feature_row, 2, status)
    scope.cell(feature_row, 3, remarks)
    feature_row += 1

section(scope, 62, "IV. USER INTERFACE AND DESIGN PROGRESS")
for column, value in enumerate(["UI / Design Element", "Expected", "Implemented", "Pending", "Completed", "Remarks / Criteria"], 1):
    scope.cell(63, column, value)
style_header_row(scope, 63)

ui_rows = [
    ("Unique authenticated and kiosk views", 8, 7, 1, 7, "Software screens implemented; physical touchscreen kiosk not purchased or built"),
    ("Maintenance and kiosk interactive controls", 20, 19, 1, 19, "Software controls implemented; hardware dispensing and stop operation pending"),
    ("Data-entry and configuration fields", 15, 15, 0, 15, "Login, staff, filter, maintenance, and dispensing fields"),
    ("Design consistency and responsive layout", 1, 1, 0, 1, "Unified AquaGuard visual system and responsive breakpoints"),
    ("Thin scrollbars and accessible focus states", 1, 1, 0, 1, "Browser scrollbar and focus-visible styling implemented"),
]
ui_row = 64
for values in ui_rows:
    for column, value in enumerate(values, 1):
        scope.cell(ui_row, column, value)
    ui_row += 1
scope.cell(ui_row, 1, "TOTAL UI AND DESIGN PROGRESS")
scope.cell(ui_row, 2, 45)
scope.cell(ui_row, 3, 45)
scope.cell(ui_row, 4, 0)
scope.cell(ui_row, 5, 45)
for column in range(1, 7):
    scope.cell(ui_row, column).font = Font(bold=True)
    scope.cell(ui_row, column).fill = PatternFill("solid", fgColor="E8F0F4")
    scope.cell(ui_row, column).border = BORDER

style_table(scope, 5, max(row, module_row, feature_row, ui_row), 6)
for column, width in enumerate([34, 18, 16, 16, 16, 48], 1):
    scope.column_dimensions[chr(64 + column)].width = width
scope.freeze_panes = "A5"

limitations = wb["System Limitations"]
clear_sheet(limitations)
style_title(limitations, "AQUAGUARD — SYSTEM LIMITATIONS AND BOUNDARIES", 2)
limitations["A3"] = "Category / Domain"
limitations["B3"] = "Identified System Limitation"
style_header_row(limitations, 3, 2)
limitation_rows = [
    ("Water-safety scope", "Selected post-filtration pH, TDS, and turbidity indicators are monitored; formal potability, microbiological, bacterial, and heavy-metal assessment requires appropriate laboratory testing."),
    ("Purification scope", "AquaGuard does not purify untreated water or replace the fountain filtration stage."),
    ("Classifier scope", "The system uses rule-based moving averages and rates of change for TDS and turbidity. It does not use trained machine-learning prediction."),
    ("pH scope", "pH is collected and displayed but is not an input to the current Normal, Warning, or Critical classifier."),
    ("Remaining filter life", "The system identifies condition trends but does not estimate exact remaining filter life or a guaranteed replacement date."),
    ("Dispensing scope", "Only Cold and Room Temperature modes are supported."),
    ("Valve feedback", "Valve events distinguish issued, received, and physically observed states. Closure confirmation depends on feedback hardware or direct observation."),
    ("Physical hardware", "The touchscreen, cooling unit, temperature routing, pump, relay/driver, valve, cable ratings, and datasheets remain to be confirmed before fabrication."),
    ("Cable and installation", "Prototype cable runs between the ESP32 enclosure and sensors, relay/valve, and power connections are limited to 2 meters."),
    ("Electrical safety", "The solenoid valve requires a separate regulated 12 V supply through compatible relay or driver contacts; direct ESP32 GPIO power is prohibited."),
    ("Network operation", "Campus Wi-Fi, HTTPS/REST connectivity, retries, stale readings, network loss, and ESP32 restart behavior require controlled testing."),
    ("Fail-safe operation", "Invalid or stale readings are excluded from normal classification. Critical conditions and fail-safe behavior require final hardware confirmation."),
    ("Data and privacy", "Administrative accounts and protected service/valve actions require secure provisioning, role authorization, and access logging."),
    ("Cloud deployment", "Pages/Workers may use external MySQL through a compatible Worker provider or Hyperdrive; credentials and database host remain deployment tasks."),
    ("Evaluation", "Sensor accuracy, rule-test agreement, API latency, valve response, usability, and ISO/IEC 25010 characteristics require formal tests and reference measurements."),
    ("Claim limitations", "Accuracy and predictive claims must not be reported without independent ground-truth labels and reference measurements."),
]
for row, (category, limitation) in enumerate(limitation_rows, 4):
    limitations.cell(row, 1, category)
    limitations.cell(row, 2, limitation)
style_table(limitations, 4, 3 + len(limitation_rows), 2)
limitations.column_dimensions["A"].width = 30
limitations.column_dimensions["B"].width = 100
limitations.freeze_panes = "A4"

matrix = wb["Role Responsibilities Matrix"]
clear_sheet(matrix)
style_title(matrix, "AQUAGUARD — ROLE-BASED SCOPE AND RESPONSIBILITY MATRIX", 4)
headers = ["User Role", "In-Scope Functions and Responsibilities", "Role Limitations and Out-of-Scope", "Primary Deliverable / Objective"]
for column, value in enumerate(headers, 1):
    matrix.cell(3, column, value)
style_header_row(matrix, 3, 4)

role_matrix = [
    ("Super Administrator", "Provision super-administrator and staff accounts; assign administrator or maintenance roles; oversee account directory and protected system access.", "Does not operate the kiosk as a student/faculty user; cannot bypass device authentication or act outside institutional authorization.", "Secure governance, staff account lifecycle, and role administration"),
    ("Administrator", "Review dashboard readings and trends; monitor alerts and valve events; review maintenance status; authorize protected control actions.", "Cannot certify water safety or exact filter life; protected valve actions require authorization and physical safety procedures.", "Operational oversight, alert review, authorized valve-control access"),
    ("Maintenance Personnel", "Register filter type and installation date; record inspection, service, and replacement events; review filter and maintenance history.", "Cannot interpret condition states as potability certification; cannot bypass role or audit controls.", "Filter lifecycle records and maintenance history"),
    ("Students and Faculty", "Use the kiosk or dashboard to view operational status and monitored readings; select Cold or Room Temperature dispensing.", "No administrative, filter-maintenance, account-management, or protected valve-control functions.", "Fountain status visibility and supported dispensing selections"),
    ("ESP32 System / Device", "Acquire pH, TDS, and turbidity; validate and transmit timestamped readings; poll dispensing commands; execute fail-safe stop behavior.", "Does not perform laboratory testing or potability certification; calibration and actuator feedback depend on tested hardware.", "Sensor telemetry and edge control"),
    ("Facility Personnel", "Review filter-service records, equipment status, alerts, and valve-event history when institutional access is granted.", "Participation is subject to institutional access and authorization; no account or valve authority unless separately assigned.", "Facility maintenance and controlled oversight"),
]
for row, values in enumerate(role_matrix, 4):
    for column, value in enumerate(values, 1):
        matrix.cell(row, column, value)
style_table(matrix, 4, 3 + len(role_matrix), 4)
for column, width in enumerate([24, 62, 62, 44], 1):
    matrix.column_dimensions[chr(64 + column)].width = width
matrix.freeze_panes = "A4"

wb.save(SOURCE)
print(f"Updated {SOURCE}")
