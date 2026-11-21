import calendar
import frappe
from frappe.utils import (
    getdate,
    get_datetime,
    flt,
    add_days,
)
from hrms.hr.doctype.employee_checkin.employee_checkin import (
    calculate_working_hours,
    add_log_based_on_employee_field,
)
# ============================================================
# EMPLOYEE HELPERS
# ============================================================
def get_logged_in_employee():
    """
    Return the Employee linked to the currently logged-in user.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return None
    return frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name",
    )
def get_employee_user(employee):
    """
    Return the user_id linked to an Employee.
    """
    if not employee:
        return None
    return frappe.db.get_value(
        "Employee",
        employee,
        "user_id",
    )
def get_employee_details(employee):
    """
    Return basic employee information.
    """
    if not employee:
        return {}
    employee_data = frappe.db.get_value(
        "Employee",
        employee,
        [
            "name",
            "employee_name",
            "department",
            "designation",
            "image",
        ],
        as_dict=True,
    )
    if not employee_data:
        return {}
    return {
        "employee_id": employee_data.name,
        "employee_name": employee_data.employee_name,
        "department": employee_data.department,
        "designation": employee_data.designation,
        "avatar": employee_data.image,
    }
# ============================================================
# STANDARD WORKING HOURS
# ============================================================
def get_standard_working_hours():
    """
    Get Standard Working Hours from HR Settings.
    HR Settings field:
        standard_working_hours
    Falls back to 9 hours if the setting is empty.
    """
    standard_hours = frappe.db.get_single_value(
        "HR Settings",
        "standard_working_hours",
    )
    standard_hours = flt(
        standard_hours
    )
    if standard_hours <= 0:
        standard_hours = 9
    return standard_hours
# ============================================================
# WORKING HOURS
# ============================================================
def get_working_hours(logs):
    """
    Calculate working hours from Employee Checkin
    IN / OUT records.
    """
    if not logs:
        return 0
    try:
        total_hours, _, _ = calculate_working_hours(
            logs,
            "Alternating entries as IN and OUT during the same shift",
            "Every Valid Check-in and Check-out",
        )
        return flt(
            total_hours,
            2,
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Executive Dashboard - Working Hours",
        )
        return 0
# ============================================================
# TIMESHEET AND EFFECTIVE HOURS
# ============================================================
def get_timesheet_hour_totals(employee, date):
    """
    Return gross Timesheet hours and recorded lag time
    for submitted Timesheet Detail records on the given date.

    Timesheet Detail.hours is stored in hours.
    Timesheet Detail.lag_time is a Duration stored in seconds.
    """
    if not employee or not date:
        return {
            "timesheet_working_hours": 0,
            "effective_hours": 0,
        }

    next_date = add_days(date, 1)
    totals = frappe.db.sql(
        """
        SELECT
            COALESCE(SUM(tsd.hours), 0) AS timesheet_hours,
            COALESCE(SUM(tsd.lag_time), 0) AS lag_seconds
        FROM `tabTimesheet` ts
        INNER JOIN `tabTimesheet Detail` tsd
            ON tsd.parent = ts.name
        WHERE
            ts.employee = %s
            AND ts.docstatus = 1
            AND tsd.from_time >= %s
            AND tsd.from_time < %s
        """,
        (
            employee,
            f"{date} 00:00:00",
            f"{next_date} 00:00:00",
        ),
        as_dict=True,
    )

    timesheet_hours = flt(totals[0].timesheet_hours)
    lag_hours = flt(totals[0].lag_seconds) / 3600
    effective_hours = max(0, timesheet_hours - lag_hours)

    return {
        "timesheet_working_hours": flt(timesheet_hours, 2),
        "effective_hours": flt(effective_hours, 2),
    }


def get_effective_hours(employee, date):
    """
    Backward-compatible helper returning Timesheet hours
    after subtracting recorded lag time.
    """
    return get_timesheet_hour_totals(employee, date)["effective_hours"]


def get_timesheet_working_hours(employee, date):
    """
    Return gross submitted Timesheet hours, before lag deduction.
    """
    return get_timesheet_hour_totals(employee, date)["timesheet_working_hours"]
# ============================================================
# CHECK-IN DATA
# ============================================================
def get_checkin_data(employee, date):
    """
    Return Employee Checkin records for the given date.
    Returns:
        check_in
        check_out
        logs
    """
    logs = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": [
                "between",
                [
                    f"{date} 00:00:00",
                    f"{date} 23:59:59",
                ],
            ],
        },
        fields=[
            "name",
            "log_type",
            "time",
        ],
        order_by="time asc",
    )
    check_in = None
    check_out = None
    for log in logs:
        if (
            log.log_type == "IN"
            and not check_in
        ):
            check_in = log.time
        elif log.log_type == "OUT":
            check_out = log.time
    return {
        "check_in": check_in,
        "check_out": check_out,
        "logs": logs,
    }
def get_latest_checkin_log(employee):
    """
    Return the latest Employee Checkin record for an employee.
    """
    if not employee:
        return None
    logs = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
        },
        fields=[
            "name",
            "log_type",
            "time",
        ],
        order_by="time desc",
        page_length=1,
    )
    return logs[0] if logs else None
# ============================================================
# EMPLOYEE CHECK-IN / CHECK-OUT
# ============================================================
@frappe.whitelist(methods=["POST"])
def record_attendance(log_type):
    """
    Record Check In or Check Out for the logged-in employee.
    Uses HRMS standard Employee Checkin creation and validation.
    """
    # Only accept valid attendance actions.
    log_type = (log_type or "").strip().upper()
    if log_type not in ("IN", "OUT"):
        frappe.throw("Invalid attendance action.")
    # Identify the employee from the logged-in session.
    employee = get_logged_in_employee()
    if not employee:
        frappe.throw(
            "No Employee record is linked to your user account."
        )
    # Find the latest attendance record.
    latest_log = get_latest_checkin_log(employee)
    # Prevent duplicate consecutive actions.
    if log_type == "IN":
        if latest_log and latest_log.log_type == "IN":
            frappe.throw(
                "You are already checked in. Please check out first."
            )
    elif log_type == "OUT":
        if not latest_log or latest_log.log_type != "IN":
            frappe.throw(
                "You are not currently checked in."
            )
    # Create the actual Employee Checkin through HRMS.
    checkin = add_log_based_on_employee_field(
        employee_field_value=employee,
        employee_fieldname="name",
        timestamp=frappe.utils.now_datetime(),
        log_type=log_type,
    )
    return {
        "success": True,
        "message": (
            "Check In recorded successfully."
            if log_type == "IN"
            else "Check Out recorded successfully."
        ),
        "employee": employee,
        "log_name": checkin.name,
        "log_type": checkin.log_type,
        "time": checkin.time,
    }
# ============================================================
# OFFICE DURATION
# ============================================================
def get_office_duration(
    check_in,
    check_out,
    current_date,
):
    """
    Calculate office duration.
    First IN -> Last OUT.
    If today is still in progress and there is no OUT,
    use the current time.
    """
    if not check_in:
        return 0
    try:
        start_time = get_datetime(
            check_in
        )
        if check_out:
            end_time = get_datetime(
                check_out
            )
        elif current_date == getdate():
            end_time = get_datetime()
        else:
            return 0
        duration_seconds = (
            end_time - start_time
        ).total_seconds()
        if duration_seconds <= 0:
            return 0
        return flt(
            duration_seconds / 3600,
            2,
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Executive Dashboard - Office Duration",
        )
        return 0
# ============================================================
# REQUIRED HOURS FOR A DAY
# ============================================================
def get_required_hours_for_day(date):
    """
    Return required working hours for a given date.
    Monday-Friday:
        Standard Working Hours
    Saturday-Sunday:
        0
    """
    if date.weekday() < 5:
        return get_standard_working_hours()
    return 0
# ============================================================
# 1. MY DAY SUMMARY
# ============================================================
@frappe.whitelist()
def get_my_day_summary(date=None):
    """
    Return My Day Summary for the logged-in employee.
    Includes:
    - Employee details
    - Check-in
    - Check-out
    - Required working hours
    - Working hours
    - Effective hours
    - Productivity
    - Task completion
    """
    employee = get_logged_in_employee()
    if not employee:
        return {
            "error": "Employee not found for current user",
        }
    employee_details = get_employee_details(
        employee
    )
    date = (
        getdate(date)
        if date
        else getdate()
    )
    checkin_data = get_checkin_data(
        employee,
        date,
    )
    latest_log = get_latest_checkin_log(employee)
    is_checked_in = bool(
        latest_log and latest_log.log_type == "IN"
    )
    working_hours = get_working_hours(
        checkin_data["logs"],
    )
    timesheet_totals = get_timesheet_hour_totals(
        employee,
        date,
    )
    effective_hours = timesheet_totals["effective_hours"]
    timesheet_working_hours = timesheet_totals["timesheet_working_hours"]
    required_hours = get_required_hours_for_day(
        date
    )
    productivity_percentage = 0
    if required_hours:
        # Preserve the existing productivity calculation using gross
        # Timesheet hours; effective hours are exposed separately.
        productivity_percentage = (
            timesheet_working_hours
            / required_hours
        ) * 100
    productivity_percentage = min(
        100,
        max(
            0,
            productivity_percentage,
        ),
    )
    task_data = get_task_completion(
        employee,
        date,
    )
    return {
        "employee": employee,
        "employee_details": employee_details,
        "date": str(date),
        "check_in": checkin_data.get(
            "check_in"
        ),
        "check_out": checkin_data.get(
            "check_out"
        ),
        "last_log_type": (
            latest_log.log_type
            if latest_log
            else None
        ),
        "is_checked_in": is_checked_in,
        "required_hours": flt(
            required_hours,
            2,
        ),
        "working_hours": flt(
            working_hours,
            2,
        ),
        "effective_hours": flt(
            effective_hours,
            2,
        ),
        "timesheet_working_hours": flt(
            timesheet_working_hours,
            2,
        ),
        "productivity_percentage": flt(
            productivity_percentage,
            2,
        ),
        "task_completion_percentage": flt(
            task_data.get(
                "completion_percentage",
                0,
            ),
            2,
        ),
        "total_tasks": task_data.get(
            "total",
            0,
        ),
        "completed_tasks": task_data.get(
            "completed",
            0,
        ),
    }
# ============================================================
# 2. WEEKLY WORKING HOURS ANALYSIS
# ============================================================
@frappe.whitelist()
def get_weekly_working_hours_analysis():
    """
    Return current-week working-hour analysis.
    IMPORTANT:
    Only elapsed days are returned.
    Example:
    Monday:
        Monday
    Tuesday:
        Monday + Tuesday
    Wednesday:
        Monday + Tuesday + Wednesday
    Future days are never returned.
    Required hours come from:
        HR Settings -> Standard Working Hours
    Weekends have 0 required hours.
    """
    employee = get_logged_in_employee()
    if not employee:
        return {
            "error": "Employee not found for current user",
            "week": [],
        }
    today = getdate()
    week_start = add_days(
        today,
        -today.weekday(),
    )
    week_end = today
    standard_working_hours = (
        get_standard_working_hours()
    )
    total_working_hours = 0
    total_effective_hours = 0
    total_office_hours = 0
    total_break_hours = 0
    total_required_hours = 0
    total_timesheet_working_hours = 0
    daily_data = []
    current_date = week_start
    while current_date <= week_end:
        checkin_data = get_checkin_data(
            employee,
            current_date,
        )
        logs = checkin_data.get(
            "logs",
            [],
        )
        # ----------------------------------------------------
        # WORKING HOURS
        # ----------------------------------------------------
        working_hours = get_working_hours(
            logs,
        )
        # ----------------------------------------------------
        # EFFECTIVE HOURS
        # ----------------------------------------------------
        timesheet_totals = get_timesheet_hour_totals(
            employee,
            current_date,
        )
        effective_hours = timesheet_totals["effective_hours"]
        timesheet_working_hours = timesheet_totals["timesheet_working_hours"]
        # ----------------------------------------------------
        # OFFICE DURATION
        # ----------------------------------------------------
        check_in = checkin_data.get(
            "check_in"
        )
        check_out = checkin_data.get(
            "check_out"
        )
        office_hours = get_office_duration(
            check_in,
            check_out,
            current_date,
        )
        # ----------------------------------------------------
        # BREAK HOURS
        # ----------------------------------------------------
        break_hours = max(
            0,
            office_hours - working_hours,
        )
        # ----------------------------------------------------
        # REQUIRED HOURS
        # ----------------------------------------------------
        if current_date.weekday() < 5:
            required_hours = (
                standard_working_hours
            )
        else:
            required_hours = 0
        # ----------------------------------------------------
        # DAILY GAP
        # ----------------------------------------------------
        gap_hours = max(
            0,
            required_hours - timesheet_working_hours,
        )
        # ----------------------------------------------------
        # DAILY CONSISTENCY
        # ----------------------------------------------------
        consistency_percentage = 0
        if required_hours:
            consistency_percentage = (
                timesheet_working_hours
                / required_hours
            ) * 100
        consistency_percentage = min(
            100,
            max(
                0,
                consistency_percentage,
            ),
        )
        # ----------------------------------------------------
        # WEEKLY TOTALS
        # ----------------------------------------------------
        total_working_hours += working_hours
        total_effective_hours += effective_hours
        total_timesheet_working_hours += timesheet_working_hours
        total_office_hours += office_hours
        total_break_hours += break_hours
        total_required_hours += required_hours
        # ----------------------------------------------------
        # DAILY DATA
        # ----------------------------------------------------
        daily_data.append(
            {
                "date": str(
                    current_date
                ),
                "day": current_date.strftime(
                    "%a"
                ),
                "working_hours": flt(
                    working_hours,
                    2,
                ),
                "effective_hours": flt(
                    effective_hours,
                    2,
                ),
                "timesheet_working_hours": flt(
                    timesheet_working_hours,
                    2,
                ),
                "office_hours": flt(
                    office_hours,
                    2,
                ),
                "break_hours": flt(
                    break_hours,
                    2,
                ),
                "required_hours": flt(
                    required_hours,
                    2,
                ),
                "gap_hours": flt(
                    gap_hours,
                    2,
                ),
                "consistency_percentage": flt(
                    consistency_percentage,
                    2,
                ),
                "check_in": (
                    str(check_in)
                    if check_in
                    else None
                ),
                "check_out": (
                    str(check_out)
                    if check_out
                    else None
                ),
                "is_today": (
                    current_date == today
                ),
            }
        )
        current_date = add_days(
            current_date,
            1,
        )
    # --------------------------------------------------------
    # WEEKLY GAP
    # --------------------------------------------------------
    weekly_gap = max(
        0,
        total_required_hours
        - total_timesheet_working_hours,
    )
    # --------------------------------------------------------
    # WEEKLY CONSISTENCY
    # --------------------------------------------------------
    weekly_consistency = 0
    if total_required_hours:
        weekly_consistency = (
            total_timesheet_working_hours
            / total_required_hours
        ) * 100
    weekly_consistency = min(
        100,
        max(
            0,
            weekly_consistency,
        ),
    )
    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------
    return {
        "employee": employee,
        "week_start": str(
            week_start
        ),
        "week_end": str(
            week_end
        ),
        "today": str(
            today
        ),
        "standard_working_hours": flt(
            standard_working_hours,
            2,
        ),
        "totals": {
            "working_hours": flt(
                total_working_hours,
                2,
            ),
            "effective_hours": flt(
                total_effective_hours,
                2,
            ),
            "timesheet_working_hours": flt(
                total_timesheet_working_hours,
                2,
            ),
            "break_hours": flt(
                total_break_hours,
                2,
            ),
            "required_hours": flt(
                total_required_hours,
                2,
            ),
            "gap_hours": flt(
                weekly_gap,
                2,
            ),
            "consistency_percentage": flt(
                weekly_consistency,
                2,
            ),
        },
        "daily": daily_data,
    }
# ============================================================
# 3. TASK COMPLETION
# ============================================================
def get_task_completion(
    employee,
    date=None,
):
    """
    Return task completion information.
    """
    user = get_employee_user(
        employee
    )
    if not user:
        return {
            "total": 0,
            "completed": 0,
            "completion_percentage": 0,
        }
    tasks = frappe.db.sql(
        """
        SELECT DISTINCT
            t.name,
            t.status
        FROM `tabTask` t
        INNER JOIN `tabToDo` td
            ON td.reference_type = 'Task'
            AND td.reference_name = t.name
        WHERE td.allocated_to = %s
        """,
        user,
        as_dict=True,
    )
    total = len(tasks)
    completed = sum(
        1
        for task in tasks
        if task.status == "Completed"
    )
    completion_percentage = 0
    if total:
        completion_percentage = (
            completed / total
        ) * 100
    completion_percentage = min(
        100,
        completion_percentage,
    )
    return {
        "total": total,
        "completed": completed,
        "completion_percentage": flt(
            completion_percentage,
            2,
        ),
    }
# ============================================================
# 4. TASK MANAGEMENT
# ============================================================
import frappe
from frappe.utils import getdate, add_days, flt
# ============================================================
# TASK MANAGEMENT DASHBOARD
# ============================================================
def get_logged_in_employee():
    """
    Return the Employee linked to the currently logged-in user.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return None
    return frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name",
    )
def get_employee_user(employee):
    """
    Return the user_id linked to an Employee.
    """
    if not employee:
        return None
    return frappe.db.get_value(
        "Employee",
        employee,
        "user_id",
    )
def get_executive_tasks(user):
    """
    Return all tasks assigned to the logged-in executive.
    Assignment is determined through ToDo.allocated_to.
    """
    if not user or user == "Guest":
        return []
    tasks = frappe.db.sql(
        """
        SELECT DISTINCT
            t.name,
            t.subject,
            t.status,
            t.priority,
            t.exp_start_date,
            t.exp_end_date,
            t.project,
            p.project_name,
            p.customer,
            p.customer_name,
            t.progress
        FROM `tabTask` t
        INNER JOIN `tabToDo` td
            ON td.reference_type = 'Task'
            AND td.reference_name = t.name
        LEFT JOIN `tabProject` p
            ON p.name = t.project
        WHERE
            td.allocated_to = %s
        ORDER BY
            CASE
                WHEN t.status = 'Completed' THEN 1
                ELSE 0
            END ASC,
            CASE
                WHEN t.priority = 'Urgent' THEN 1
                WHEN t.priority = 'High' THEN 2
                WHEN t.priority = 'Medium' THEN 3
                WHEN t.priority = 'Low' THEN 4
                ELSE 5
            END ASC,
            t.exp_end_date ASC
        """,
        user,
        as_dict=True,
    )
    return tasks
def prepare_task_data(task, today):
    """
    Convert a Task document into dashboard-friendly data.
    """
    status = task.status or ""
    priority = task.priority or ""
    start_date = (
        getdate(task.exp_start_date)
        if task.exp_start_date
        else None
    )
    deadline = (
        getdate(task.exp_end_date)
        if task.exp_end_date
        else None
    )
    is_completed = status == "Completed"
    is_cancelled = status == "Cancelled"
    is_pending = (
        not is_completed
        and not is_cancelled
    )
    is_assigned_today = (
        start_date == today
    )
    is_overdue = (
        is_pending
        and deadline is not None
        and deadline < today
    )
    is_high_priority = (
        priority in ("High", "Urgent")
    )
    if is_overdue:
        deadline_state = "Overdue"
    elif deadline == today:
        deadline_state = "Due Today"
    elif deadline and deadline > today:
        deadline_state = "Upcoming"
    else:
        deadline_state = "No Deadline"
    return {
        "name": task.name,
        "subject": task.subject or task.name,
        "status": status,
        "priority": priority,
        "start_date": (
            str(start_date)
            if start_date
            else None
        ),
        "deadline": (
            str(deadline)
            if deadline
            else None
        ),
        "deadline_state": deadline_state,
        "project": task.project,
        "project_name": task.project_name,
        "customer": task.customer,
        "customer_name": task.customer_name,
        "compliance_sub_category": task.compliance_sub_category,
        "progress": flt(
            task.progress or 0,
            2,
        ),
        "is_completed": is_completed,
        "is_cancelled": is_cancelled,
        "is_pending": is_pending,
        "is_assigned_today": is_assigned_today,
        "is_overdue": is_overdue,
        "is_high_priority": is_high_priority,
    }
def filter_executive_tasks(
    tasks,
    filter_name,
):
    """
    Apply dashboard filter to the executive's
    already-assigned task list.
    Supported filters:
    all
    today
    pending
    completed
    overdue
    high_priority
    """
    if filter_name == "today":
        return [
            task
            for task in tasks
            if task["is_assigned_today"]
        ]
    if filter_name == "pending":
        return [
            task
            for task in tasks
            if task["is_pending"]
        ]
    if filter_name == "completed":
        return [
            task
            for task in tasks
            if task["is_completed"]
        ]
    if filter_name == "overdue":
        return [
            task
            for task in tasks
            if task["is_overdue"]
        ]
    if filter_name == "high_priority":
        return [
            task
            for task in tasks
            if (
                task["is_high_priority"]
                and task["is_pending"]
            )
        ]
    return tasks
@frappe.whitelist()
def get_my_tasks(filter_name="all"):
    """
    Task Management Dashboard API.
    Returns tasks assigned to the logged-in executive.
    Filters:
        all
        today
        pending
        completed
        overdue
        high_priority
    The task list and summary counts are calculated
    from the same employee-specific task dataset.
    """
    # ========================================================
    # USER
    # ========================================================
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "error": "User not logged in",
            "total": 0,
            "assigned_today": 0,
            "pending": 0,
            "completed": 0,
            "overdue": 0,
            "high_priority": 0,
            "active_filter": filter_name,
            "tasks": [],
        }
    # ========================================================
    # EMPLOYEE
    # ========================================================
    employee = get_logged_in_employee()
    if not employee:
        return {
            "error": "Employee not found for current user",
            "total": 0,
            "assigned_today": 0,
            "pending": 0,
            "completed": 0,
            "overdue": 0,
            "high_priority": 0,
            "active_filter": filter_name,
            "tasks": [],
        }
    # ========================================================
    # GET ASSIGNED TASKS
    # ========================================================
    raw_tasks = get_executive_tasks(user)
    today = getdate()
    prepared_tasks = []
    for task in raw_tasks:
        prepared_tasks.append(
            prepare_task_data(
                task,
                today,
            )
        )
    # ========================================================
    # SUMMARY COUNTS
    # ========================================================
    total_tasks = len(
        prepared_tasks
    )
    assigned_today = sum(
        1
        for task in prepared_tasks
        if task["is_assigned_today"]
    )
    pending_tasks = sum(
        1
        for task in prepared_tasks
        if task["is_pending"]
    )
    completed_tasks = sum(
        1
        for task in prepared_tasks
        if task["is_completed"]
    )
    overdue_tasks = sum(
        1
        for task in prepared_tasks
        if task["is_overdue"]
    )
    high_priority_tasks = sum(
        1
        for task in prepared_tasks
        if (
            task["is_high_priority"]
            and task["is_pending"]
        )
    )
    # ========================================================
    # VALIDATE FILTER
    # ========================================================
    valid_filters = {
        "all",
        "today",
        "pending",
        "completed",
        "overdue",
        "high_priority",
    }
    if filter_name not in valid_filters:
        filter_name = "all"
    # ========================================================
    # FILTER TASKS
    # ========================================================
    filtered_tasks = filter_executive_tasks(
        prepared_tasks,
        filter_name,
    )
    return {
        "employee": employee,
        "user": user,
        "date": str(today),
        "active_filter": filter_name,
        "summary": {
            "total": total_tasks,
            "assigned_today": assigned_today,
            "pending": pending_tasks,
            "completed": completed_tasks,
            "overdue": overdue_tasks,
            "high_priority": high_priority_tasks,
        },
        "tasks": filtered_tasks,
    }
# ============================================================
# 5. PROJECT RESPONSIBILITY
# ============================================================
@frappe.whitelist()
def get_project_responsibility():
    """
    Return active projects related to the logged-in user.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "error": "User not logged in",
            "projects": [],
        }
    project_names = frappe.db.sql(
        """
        SELECT DISTINCT
            t.project
        FROM `tabTask` t
        INNER JOIN `tabToDo` td
            ON td.reference_type = 'Task'
            AND td.reference_name = t.name
        WHERE td.allocated_to = %s
            AND t.project IS NOT NULL
            AND t.project != ''
        """,
        user,
        pluck="project",
    )
    if not project_names:
        return {
            "projects": [],
        }
    projects = frappe.db.get_all(
        "Project",
        filters={
            "name": ["in", project_names],
            "status": [
                "not in",
                [
                    "Completed",
                    "Cancelled",
                ],
            ],
            "is_active": "Yes",
        },
        fields=[
            "name",
            "project_name",
            "customer",
            "customer_name",
            "percent_complete",
            "expected_end_date",
        ],
        order_by="modified desc",
    )
    result = []
    for project in projects:
        pending_tasks = frappe.db.sql(
            """
            SELECT
                t.name,
                t.subject,
                t.status,
                t.exp_end_date,
                t.priority,
                t.progress
            FROM `tabTask` t
            INNER JOIN `tabToDo` td
                ON td.reference_type = 'Task'
                AND td.reference_name = t.name
            WHERE td.allocated_to = %s
                AND t.project = %s
                AND t.status NOT IN (
                    'Completed',
                    'Cancelled'
                )
            ORDER BY
                t.exp_end_date ASC
            """,
            (
                user,
                project.name,
            ),
            as_dict=True,
        )
        pending_count = len(
            pending_tasks
        )
        if not pending_count:
            continue
        next_deadline = None
        for task in pending_tasks:
            if not task.exp_end_date:
                continue
            task_deadline = getdate(
                task.exp_end_date
            )
            if (
                next_deadline is None
                or task_deadline < next_deadline
            ):
                next_deadline = task_deadline
        result.append(
            {
                "project": project.name,
                "project_name": project.project_name,
                "customer": project.customer,
                "customer_name": project.customer_name,
                "pending_tasks": pending_count,
                "next_deadline": (
                    str(next_deadline)
                    if next_deadline
                    else None
                ),
                "progress": flt(
                    project.percent_complete or 0,
                    2,
                ),
            }
        )
    return {
        "projects": result,
    }
# ============================================================
# 6. ACTION REQUIRED
# ============================================================
@frappe.whitelist()
def get_action_required():
    """
    Return tasks requiring attention.
    Categories:
    - Overdue
    - Due Today
    - Upcoming - next 7 days
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "error": "User not logged in",
            "overdue": [],
            "due_today": [],
            "upcoming": [],
        }
    tasks = frappe.db.sql(
        """
        SELECT DISTINCT
            t.name,
            t.subject,
            t.status,
            t.priority,
            t.exp_start_date,
            t.exp_end_date,
            t.project,
            p.project_name,
            p.customer,
            p.customer_name
        FROM `tabTask` t
        INNER JOIN `tabToDo` td
            ON td.reference_type = 'Task'
            AND td.reference_name = t.name
        LEFT JOIN `tabProject` p
            ON p.name = t.project
        WHERE td.allocated_to = %s
            AND t.status NOT IN (
                'Completed',
                'Cancelled'
            )
            AND t.exp_end_date IS NOT NULL
        ORDER BY
            t.exp_end_date ASC
        """,
        user,
        as_dict=True,
    )
    today = getdate()
    upcoming_date = add_days(
        today,
        7,
    )
    overdue = []
    due_today = []
    upcoming = []
    for task in tasks:
        deadline = getdate(
            task.exp_end_date
        )
        task_data = {
            "name": task.name,
            "subject": task.subject,
            "status": task.status,
            "priority": task.priority,
            "start_date": (
                str(task.exp_start_date)
                if task.exp_start_date
                else None
            ),
            "deadline": str(deadline),
            "project": task.project,
            "project_name": task.project_name,
            "customer": task.customer,
            "customer_name": task.customer_name,
        }
        if deadline < today:
            overdue.append(
                task_data
            )
        elif deadline == today:
            due_today.append(
                task_data
            )
        elif deadline <= upcoming_date:
            upcoming.append(
                task_data
            )
    return {
        "overdue": overdue,
        "due_today": due_today,
        "upcoming": upcoming,
        "total": (
            len(overdue)
            + len(due_today)
            + len(upcoming)
        ),
    }
# ============================================================
# 7. CAPABILITY / PERFORMANCE
# ============================================================
@frappe.whitelist()
def get_capability_performance():
    """
    Return performance metrics for the logged-in employee.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "error": "User not logged in",
        }
    employee = get_logged_in_employee()
    if not employee:
        return {
            "error": "Employee not found for current user",
        }
    tasks = frappe.db.sql(
        """
        SELECT DISTINCT
            t.name,
            t.status,
            t.exp_end_date
        FROM `tabTask` t
        INNER JOIN `tabToDo` td
            ON td.reference_type = 'Task'
            AND td.reference_name = t.name
        WHERE td.allocated_to = %s
        """,
        user,
        as_dict=True,
    )
    total_tasks = len(tasks)
    completed_tasks = sum(
        1
        for task in tasks
        if task.status == "Completed"
    )
    task_completion = 0
    if total_tasks:
        task_completion = (
            completed_tasks / total_tasks
        ) * 100
    task_completion = min(
        100,
        task_completion,
    )
    today = getdate()
    completed_with_deadline = 0
    completed_on_time = 0
    overdue_tasks = 0
    for task in tasks:
        if not task.exp_end_date:
            continue
        deadline = getdate(
            task.exp_end_date
        )
        if task.status == "Completed":
            completed_with_deadline += 1
            completed_on_time += 1
        elif deadline < today:
            overdue_tasks += 1
    deadline_adherence = 0
    if completed_with_deadline:
        deadline_adherence = (
            completed_on_time
            / completed_with_deadline
        ) * 100
    elif completed_tasks:
        deadline_adherence = 100
    deadline_adherence = min(
        100,
        deadline_adherence,
    )
    checkin_data = get_checkin_data(
        employee,
        today,
    )
    working_hours = get_working_hours(
        checkin_data["logs"],
    )
    timesheet_totals = get_timesheet_hour_totals(
        employee,
        today,
    )
    effective_hours = timesheet_totals["effective_hours"]
    timesheet_working_hours = timesheet_totals["timesheet_working_hours"]
    required_hours = get_required_hours_for_day(
        today
    )
    working_hours_percentage = 0
    if required_hours:
        working_hours_percentage = (
            working_hours
            / required_hours
        ) * 100
    working_hours_percentage = min(
        100,
        working_hours_percentage,
    )
    productivity = 0
    if required_hours:
        productivity = (
            timesheet_working_hours
            / required_hours
        ) * 100
    productivity = min(
        100,
        productivity,
    )
    improvement_focus = []
    if task_completion < 70:
        improvement_focus.append(
            "Improve task completion by closing pending responsibilities."
        )
    if productivity < 70:
        improvement_focus.append(
            "Increase focused working time to improve productivity."
        )
    if deadline_adherence < 80:
        improvement_focus.append(
            "Reduce overdue tasks and improve deadline adherence."
        )
    if overdue_tasks > 0:
        improvement_focus.append(
            f"Focus on {overdue_tasks} overdue "
            f"{'task' if overdue_tasks == 1 else 'tasks'}."
        )
    if not improvement_focus:
        improvement_focus.append(
            "Performance is on track. Continue maintaining consistency."
        )
    return {
        "employee": employee,
        "metrics": {
            "task_completion": flt(
                task_completion,
                2,
            ),
            "productivity": flt(
                productivity,
                2,
            ),
            "deadline_adherence": flt(
                deadline_adherence,
                2,
            ),
            "working_hours": flt(
                working_hours_percentage,
                2,
            ),
        },
        "details": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "working_hours": flt(
                working_hours,
                2,
            ),
            "effective_hours": flt(
                effective_hours,
                2,
            ),
            "timesheet_working_hours": flt(
                timesheet_working_hours,
                2,
            ),
            "required_hours": flt(
                required_hours,
                2,
            ),
            "overdue_tasks": overdue_tasks,
        },
        "improvement_focus": improvement_focus,
    }
# ============================================================
# 8. ACTIONS REQUIRING ATTENTION
# ============================================================
@frappe.whitelist()
def get_actions_requiring_attention():
    """
    Return tasks requiring immediate attention.
    Includes:
    - Overdue
    - Due Today
    - High Priority
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "error": "User not logged in",
            "total": 0,
            "overdue": 0,
            "due_today": 0,
            "high_priority": 0,
            "tasks": [],
        }
    tasks = frappe.db.sql(
        """
        SELECT DISTINCT
            t.name,
            t.subject,
            t.status,
            t.priority,
            t.exp_start_date,
            t.exp_end_date,
            t.project
        FROM `tabTask` t
        INNER JOIN `tabToDo` td
            ON td.reference_type = 'Task'
            AND td.reference_name = t.name
        WHERE td.allocated_to = %s
            AND t.status NOT IN (
                'Completed',
                'Cancelled'
            )
            AND (
                t.exp_end_date IS NOT NULL
                OR t.priority IN (
                    'High',
                    'Urgent'
                )
            )
        ORDER BY
            t.exp_end_date ASC
        """,
        user,
        as_dict=True,
    )
    today = getdate()
    overdue = 0
    due_today = 0
    high_priority = 0
    result = []
    for task in tasks:
        due_date = (
            getdate(
                task.exp_end_date
            )
            if task.exp_end_date
            else None
        )
        is_overdue = (
            due_date is not None
            and due_date < today
        )
        is_due_today = (
            due_date is not None
            and due_date == today
        )
        is_high_priority = (
            task.priority
            in (
                "High",
                "Urgent",
            )
        )
        if is_overdue:
            overdue += 1
        if is_due_today:
            due_today += 1
        if is_high_priority:
            high_priority += 1
        if not (
            is_overdue
            or is_due_today
            or is_high_priority
        ):
            continue
        if is_overdue:
            attention_type = "Overdue"
        elif is_due_today:
            attention_type = "Due Today"
        elif task.priority == "Urgent":
            attention_type = "Urgent"
        else:
            attention_type = "High Priority"
        result.append(
            {
                "name": task.name,
                "subject": task.subject,
                "status": task.status,
                "priority": task.priority,
                "project": task.project,
                "due_date": (
                    str(due_date)
                    if due_date
                    else None
                ),
                "attention_type": attention_type,
            }
        )
    return {
        "total": len(result),
        "overdue": overdue,
        "due_today": due_today,
        "high_priority": high_priority,
        "tasks": result,
    }
@frappe.whitelist()
def get_project_status_cards():
    """
    Return project statistics for the Employee Associate Dashboard.
    Total Projects:
        Projects where is_active = Yes, excluding Cancelled projects.
    Assigned Projects:
        Projects containing at least one non-template, non-group,
        non-cancelled Task assigned to the logged-in user through
        a Task-linked ToDo.
    Progress:
        Completed eligible Tasks / Total eligible Tasks * 100.
    Completed Tasks remain eligible for project assignment detection,
    so projects do not disappear when the employee completes their work.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Please log in to view project information.")
    if not frappe.has_permission("Project", "read"):
        frappe.throw("You do not have permission to view projects.")
    # --------------------------------------------------------
    # TOTAL ORGANIZATION PROJECTS
    # --------------------------------------------------------
    total_projects = frappe.db.count(
        "Project",
        filters={
            "is_active": "Yes",
            "status": ["!=", "Cancelled"],
        },
    )
    # --------------------------------------------------------
    # PROJECTS ASSIGNED THROUGH TASK-LINKED TODOS
    # --------------------------------------------------------
    projects = frappe.db.sql(
        """
        SELECT
            p.name,
            p.project_name,
            p.customer_name,
            p.expected_end_date,
            p.status,
            p.creation,
            COUNT(t.name) AS total_tasks,
            SUM(
                CASE
                    WHEN t.status = 'Completed' THEN 1
                    ELSE 0
                END
            ) AS completed_tasks
        FROM `tabProject` p
        LEFT JOIN `tabTask` t
            ON t.project = p.name
            AND IFNULL(t.is_template, 0) = 0
            AND IFNULL(t.is_group, 0) = 0
            AND IFNULL(t.status, '') NOT IN (
                'Template',
                'Cancelled'
            )
        WHERE
            p.is_active = 'Yes'
            AND p.status != 'Cancelled'
            AND EXISTS (
                SELECT 1
                FROM `tabTask` assigned_task
                INNER JOIN `tabToDo` td
                    ON td.reference_type = 'Task'
                    AND td.reference_name = assigned_task.name
                WHERE
                    assigned_task.project = p.name
                    AND td.allocated_to = %s
                    AND IFNULL(td.status, 'Open') != 'Cancelled'
                    AND IFNULL(assigned_task.is_template, 0) = 0
                    AND IFNULL(assigned_task.is_group, 0) = 0
                    AND IFNULL(assigned_task.status, '') NOT IN (
                        'Template',
                        'Cancelled'
                    )
            )
        GROUP BY
            p.name,
            p.project_name,
            p.customer_name,
            p.expected_end_date,
            p.status,
            p.creation,
            p.modified
        ORDER BY
            p.modified DESC
        """,
        (user,),
        as_dict=True,
    )
    # --------------------------------------------------------
    # CALCULATE WHOLE-PROJECT PROGRESS
    # --------------------------------------------------------
    result = []
    for project in projects:
        total_tasks = int(project.total_tasks or 0)
        completed_tasks = int(project.completed_tasks or 0)
        if total_tasks:
            progress = flt(
                (completed_tasks / total_tasks) * 100,
                2,
            )
        else:
            progress = 0
        result.append({
            "name": project.name,
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "expected_end_date": project.expected_end_date,
            "status": project.status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress": progress,
            "creation": project.creation,
        })
    return {
        "total_projects": total_projects,
        "assigned_projects_count": len(result),
        "projects": result,
    }
@frappe.whitelist()
def get_associate_project_workspace():
    """
    Return projects assigned to the logged-in user, together
    with all eligible Tasks belonging to those projects.
    Existing functions reused:
        get_project_status_cards()
        prepare_task_data()
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Please log in to view project information.")
    # --------------------------------------------------------
    # 1. REUSE EXISTING PROJECT SELECTION
    # --------------------------------------------------------
    project_summary = get_project_status_cards()
    assigned_projects = project_summary.get("projects", [])
    if not assigned_projects:
        return {
            "projects": [],
            "total_projects": 0,
        }
    project_names = [
        project["name"]
        for project in assigned_projects
    ]
    # --------------------------------------------------------
    # 2. FETCH PROJECT DETAILS
    # --------------------------------------------------------
    project_details = frappe.db.get_all(
        "Project",
        filters={
            "name": ["in", project_names],
        },
        fields=[
            "name",
            "project_name",
            "customer",
            "customer_name",
            "expected_end_date",
            "status",
            "is_active",
        ],
    )
    project_details_by_name = {
        project.name: project
        for project in project_details
    }
    # --------------------------------------------------------
    # 3. FETCH ALL ELIGIBLE TASKS FOR THESE PROJECTS
    # --------------------------------------------------------
    placeholders = ", ".join(
        ["%s"] * len(project_names)
    )
    task_rows = frappe.db.sql(
        f"""
        SELECT
            t.name,
            t.subject,
            t.status,
            t.priority,
            t.exp_start_date,
            t.exp_end_date,
            t.progress,
            t.project,
            t.compliance_sub_category,
            p.project_name,
            p.customer,
            p.customer_name,
            td.allocated_to,
            u.full_name AS assignee_name
        FROM `tabTask` t
        INNER JOIN `tabProject` p
            ON p.name = t.project
        LEFT JOIN `tabToDo` td
            ON td.reference_type = 'Task'
            AND td.reference_name = t.name
            AND IFNULL(td.status, 'Open') != 'Cancelled'
        LEFT JOIN `tabUser` u
            ON u.name = td.allocated_to
        WHERE
            t.project IN ({placeholders})
            AND IFNULL(t.is_template, 0) = 0
            AND IFNULL(t.is_group, 0) = 0
            AND IFNULL(t.status, '') NOT IN (
                'Template',
                'Cancelled'
            )
        ORDER BY
            t.project ASC,
            t.exp_end_date ASC,
            t.creation ASC
        """,
        tuple(project_names),
        as_dict=True,
    )
    # --------------------------------------------------------
    # 4. PREPARE TASKS AND COLLECT ASSIGNEES
    # --------------------------------------------------------
    today = getdate()
    task_data_by_name = {}
    tasks_by_project = {
        name: []
        for name in project_names
    }
    project_assignees = {
        name: set()
        for name in project_names
    }
    for row in task_rows:
        # Create each Task only once, even if it has
        # multiple ToDo assignment records.
        if row.name not in task_data_by_name:
            task_data = prepare_task_data(
                row,
                today,
            )
            task_data["assignees"] = []
            task_data_by_name[row.name] = task_data
            tasks_by_project[row.project].append(
                task_data
            )
        # Collect all non-cancelled Task assignees.
        if row.allocated_to:
            assignee_name = (
                row.assignee_name
                or row.allocated_to
            )
            task_assignees = task_data_by_name[
                row.name
            ]["assignees"]
            if assignee_name not in task_assignees:
                task_assignees.append(assignee_name)
            project_assignees[row.project].add(
                assignee_name
            )
    # --------------------------------------------------------
    # 5. BUILD PROJECT RESPONSE
    # --------------------------------------------------------
    result = []
    for summary in assigned_projects:
        project_name = summary["name"]
        project = project_details_by_name.get(
            project_name
        )
        if not project:
            continue
        result.append({
            "name": project.name,
            "project_name": project.project_name,
            "customer": project.customer,
            "customer_name": project.customer_name,
            "expected_end_date": project.expected_end_date,
            "status": project.status,
            "is_active": project.is_active,
            "progress": summary.get("progress", 0),
            "total_tasks": summary.get("total_tasks", 0),
            "completed_tasks": summary.get("completed_tasks", 0),
            "assignees": sorted(
                project_assignees[project_name]
            ),
            "tasks": tasks_by_project[project_name],
        })
    return {
        "total_projects": len(result),
        "projects": result,
    }
# ============================================================
# EMPLOYEE NOTIFICATIONS
# ============================================================
@frappe.whitelist()
def get_my_notifications():
    """
    Return Notification Log records belonging to the
    currently logged-in user.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Please log in to view notifications.")
    notifications = frappe.get_all(
        "Notification Log",
        filters={
            "for_user": user,
        },
        fields=[
            "name",
            "title",
            "description",
            "read",
            "creation",
            "type",
            "document_type",
            "document_name",
            "source_doctype",
            "link",
        ],
        order_by="creation desc",
        limit_page_length=50,
    )
    return notifications
@frappe.whitelist(methods=["POST"])
def mark_notification_as_read(notification_name):
    """
    Mark a notification as read after verifying ownership.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Please log in to update notifications.")
    notification_user = frappe.db.get_value(
        "Notification Log",
        notification_name,
        "for_user",
    )
    if notification_user != user:
        frappe.throw("You are not authorized to update this notification.")
    frappe.db.set_value(
        "Notification Log",
        notification_name,
        "read",
        1,
    )
    return {"success": True}
@frappe.whitelist(methods=["POST"])
def mark_all_notifications_as_read():
    """
    Mark all unread notifications belonging to the
    currently logged-in user as read.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Please log in to update notifications.")
    frappe.db.set_value(
        "Notification Log",
        {
            "for_user": user,
            "read": 0,
        },
        "read",
        1,
    )
    return {"success": True}
# ============================================================
# EMPLOYEE TO-DO
# ============================================================
@frappe.whitelist()
def get_my_todos():
    """
    Return ToDo records assigned to the currently logged-in user.
    Includes Task-linked, Project-linked and other ToDo records.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Please log in to view your tasks.")
    todos = frappe.get_all(
        "ToDo",
        filters={
            "allocated_to": user,
        },
        fields=[
            "name",
            "description",
            "date",
            "priority",
            "status",
            "reference_type",
            "reference_name",
            "creation",
        ],
        order_by="date asc, creation desc",
        limit_page_length=100,
    )
    return todos
def get_my_todo_document(todo_name):
    """
    Fetch a ToDo only if it belongs to the logged-in user.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Please log in to update your tasks.")
    if not todo_name:
        frappe.throw("ToDo name is required.")
    todo = frappe.get_doc("ToDo", todo_name)
    if todo.allocated_to != user:
        frappe.throw("You are not authorized to update this task.")
    return todo
@frappe.whitelist(methods=["POST"])
def update_my_todo_status(todo_name, status):
    """
    Update the status of an employee's own ToDo.
    Supports Open and Closed for the checkbox interaction.
    """
    if status not in ["Open", "Closed"]:
        frappe.throw("Invalid ToDo status.")
    todo = get_my_todo_document(todo_name)
    todo.status = status
    todo.save(ignore_permissions=True)
    return {
        "success": True,
        "status": todo.status,
    }
@frappe.whitelist(methods=["POST"])
def update_my_todo_details(
    todo_name,
    description,
    date,
    priority,
):
    """
    Update the description, deadline and priority
    of an employee's own ToDo.
    """
    todo = get_my_todo_document(todo_name)
    description = (description or "").strip()
    if not description:
        frappe.throw("Task description is required.")
    if not date:
        frappe.throw("Deadline is required.")
    if priority not in ["High", "Medium", "Low"]:
        frappe.throw("Invalid task priority.")
    todo.description = description
    todo.date = frappe.utils.getdate(date)
    todo.priority = priority
    todo.save(ignore_permissions=True)
    return {
        "success": True,
        "name": todo.name,
    }
# ============================================================
# TEAM UPDATES: LEAVE, BIRTHDAYS, ANNIVERSARIES AND EVENTS
# ============================================================
@frappe.whitelist()
def get_team_updates():
    """
    Return current team leave and important dates for the employee's company.
    Important dates include:
    - Employee birthdays
    - Employee work anniversaries
    - Public Frappe Events scheduled in the next 30 days
    Leave details intentionally exclude leave descriptions and leave reasons.
    """
    employee = get_logged_in_employee()
    if not employee:
        return {
            "team_leaves": [],
            "important_dates": [],
        }
    today = getdate()
    end_date = add_days(today, 30)
    company = frappe.db.get_value(
        "Employee",
        employee,
        "company",
    )
    employee_filters = {
        "status": "Active",
    }
    if company:
        employee_filters["company"] = company
    employees = frappe.get_all(
        "Employee",
        filters=employee_filters,
        fields=[
            "name",
            "employee_name",
            "designation",
            "date_of_birth",
            "date_of_joining",
        ],
    )
    employee_map = {
        row.name: row
        for row in employees
    }
    # --------------------------------------------------------
    # 1. EMPLOYEES CURRENTLY ON APPROVED LEAVE
    # --------------------------------------------------------
    leave_filters = {
        "status": "Approved",
        "docstatus": 1,
        "from_date": ["<=", today],
        "to_date": [">=", today],
    }
    if company:
        leave_filters["company"] = company
    leave_applications = frappe.get_all(
        "Leave Application",
        filters=leave_filters,
        fields=[
            "name",
            "employee",
            "employee_name",
            "from_date",
            "to_date",
        ],
        order_by="from_date asc",
    )
    team_leaves = []
    for leave in leave_applications:
        employee_data = employee_map.get(leave.employee)
        # Do not show inactive or out-of-company employees.
        if not employee_data:
            continue
        team_leaves.append({
            "id": leave.name,
            "name": leave.employee_name or employee_data.employee_name,
            "designation": employee_data.designation or "",
            "from": str(leave.from_date),
            "to": str(leave.to_date),
        })
    # --------------------------------------------------------
    # 2. NEXT OCCURRENCE OF BIRTHDAYS AND WORK ANNIVERSARIES
    # --------------------------------------------------------
    def next_annual_occurrence(value):
        if not value:
            return None
        original_date = getdate(value)
        year = today.year
        def build_date(target_year):
            # Handles 29 February birthdays in non-leap years.
            day = min(
                original_date.day,
                calendar.monthrange(target_year, original_date.month)[1],
            )
            return getdate(
                f"{target_year}-{original_date.month:02d}-{day:02d}"
            )
        occurrence = build_date(year)
        if occurrence < today:
            occurrence = build_date(year + 1)
        if occurrence > end_date:
            return None
        return occurrence
    important_dates = []
    for employee_data in employees:
        if employee_data.date_of_birth:
            birthday = next_annual_occurrence(
                employee_data.date_of_birth
            )
            if birthday:
                important_dates.append({
                    "id": f"birthday-{employee_data.name}",
                    "name": employee_data.employee_name,
                    "description": "Birthday",
                    "date": str(birthday),
                    "type": "Birthday",
                    "icon": "lucide-cake",
                })
        if employee_data.date_of_joining:
            joining_date = getdate(
                employee_data.date_of_joining
            )
            if joining_date <= today:
                anniversary = next_annual_occurrence(
                    joining_date
                )
                if anniversary:
                    years = anniversary.year - joining_date.year
                    important_dates.append({
                        "id": f"anniversary-{employee_data.name}",
                        "name": employee_data.employee_name,
                        "description": (
                            f"Work Anniversary · {years} "
                            f"{'year' if years == 1 else 'years'}"
                        ),
                        "date": str(anniversary),
                        "type": "Anniversary",
                        "icon": "lucide-award",
                    })
    # --------------------------------------------------------
    # 3. PUBLIC COMPANY EVENTS IN THE NEXT 30 DAYS
    # --------------------------------------------------------
    event_filters = {
        "event_type": "Public",
        "status": "Open",
        "starts_on": [
            "between",
            [
                f"{today} 00:00:00",
                f"{end_date} 23:59:59",
            ],
        ],
    }
    if company:
        event_filters["company"] = company
    events = frappe.get_all(
        "Event",
        filters=event_filters,
        fields=[
            "name",
            "subject",
            "event_category",
            "starts_on",
        ],
        order_by="starts_on asc",
    )
    for event in events:
        event_date = getdate(event.starts_on)
        important_dates.append({
            "id": f"event-{event.name}",
            "name": event.subject or "Company Event",
            "description": event.event_category or "Company Event",
            "date": str(event_date),
            "type": "Event",
            "icon": "lucide-calendar-days",
        })
    important_dates.sort(
        key=lambda item: (item["date"], item["name"].lower())
    )
    return {
        "team_leaves": team_leaves,
        "important_dates": important_dates,
    }
