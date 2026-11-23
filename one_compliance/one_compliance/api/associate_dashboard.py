import frappe

from frappe.utils import (
    getdate,
    nowdate,
    flt,
)

from one_compliance.one_compliance.api.executive_dashboard import (
    get_logged_in_employee,
    get_employee_details,
    get_checkin_data,
    get_working_hours,
    get_effective_hours,
    get_required_hours_for_day,
    get_office_duration,
    get_task_completion,
)


# =========================================================
# HELPER
# =========================================================

def get_associate_executives(associate):
    """
    Return active Employees who report to the Associate.
    """

    return frappe.get_all(
        "Employee",
        filters={
            "reports_to": associate,
            "status": "Active",
        },
        fields=[
            "name",
            "employee_name",
            "user_id",
            "designation",
        ],
        order_by="employee_name asc",
    )


def get_executive_task_records(executives):
    """
    Return Tasks assigned to the given Executives.

    Returns:
        {
            "tasks": [...],
            "task_owners": {...}
        }
    """

    executive_users = [
        employee.user_id
        for employee in executives
        if employee.user_id
    ]

    if not executive_users:
        return {
            "tasks": [],
            "task_owners": {},
        }

    todos = frappe.get_all(
        "ToDo",
        filters={
            "allocated_to": ["in", executive_users],
            "reference_type": "Task",
        },
        fields=[
            "allocated_to",
            "reference_name",
        ],
    )

    task_names = set()
    task_owners = {}

    for todo in todos:

        task_name = todo.reference_name
        owner = todo.allocated_to

        if not task_name:
            continue

        task_names.add(task_name)

        if task_name not in task_owners:
            task_owners[task_name] = set()

        if owner:
            task_owners[task_name].add(owner)

    if not task_names:
        return {
            "tasks": [],
            "task_owners": {},
        }

    tasks = frappe.get_all(
        "Task",
        filters={
            "name": ["in", list(task_names)],
        },
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "project",
            "exp_start_date",
            "exp_end_date",
        ],
    )

    return {
        "tasks": tasks,
        "task_owners": task_owners,
    }


# =========================================================
# BLOCK 1
# MY PERFORMANCE SUMMARY
# =========================================================

@frappe.whitelist()
def get_my_performance(date=None):
    """
    Return personal performance information
    for the logged-in Associate.
    """

    employee = get_logged_in_employee()

    if not employee:
        return {
            "error": "Employee not found for current user"
        }

    date = getdate(date) if date else getdate()

    employee_details = get_employee_details(employee)

    checkin_data = get_checkin_data(
        employee,
        date
    )

    check_in = checkin_data.get("check_in")
    check_out = checkin_data.get("check_out")
    logs = checkin_data.get("logs", [])

    # -----------------------------------------------------
    # Attendance
    # -----------------------------------------------------

    if not check_in:
        attendance_status = "Absent"

    elif check_in and not check_out:
        attendance_status = "Working"

    else:
        attendance_status = "Present"

    # -----------------------------------------------------
    # Hours
    # -----------------------------------------------------

    working_hours = get_working_hours(logs)

    effective_hours = get_effective_hours(
        employee,
        date
    )

    required_hours = get_required_hours_for_day(
        date
    )

    office_hours = get_office_duration(
        check_in,
        check_out,
        date
    )

    break_hours = max(
        0,
        office_hours - working_hours
    )

    gap_hours = max(
        0,
        required_hours - effective_hours
    )

    # -----------------------------------------------------
    # Productivity
    # -----------------------------------------------------

    productivity_percentage = 0

    if required_hours:
        productivity_percentage = (
            effective_hours /
            required_hours
        ) * 100

    productivity_percentage = min(
        100,
        max(
            0,
            productivity_percentage
        )
    )

    # -----------------------------------------------------
    # Task Completion
    # -----------------------------------------------------

    task_data = get_task_completion(
        employee,
        date
    )

    task_completion_percentage = flt(
        task_data.get(
            "completion_percentage",
            0
        ),
        2
    )

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {

        "employee": employee,

        "employee_details": employee_details,

        "date": str(date),

        "attendance": {
            "status": attendance_status,

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
        },

        "hours": {

            "office_duration": flt(
                office_hours,
                2
            ),

            "working_hours": flt(
                working_hours,
                2
            ),

            "break_duration": flt(
                break_hours,
                2
            ),

            "effective_hours": flt(
                effective_hours,
                2
            ),

            "required_hours": flt(
                required_hours,
                2
            ),

            "gap": flt(
                gap_hours,
                2
            ),
        },

        "productivity_percentage": flt(
            productivity_percentage,
            2
        ),

        "task_completion_percentage": flt(
            task_completion_percentage,
            2
        ),

        "tasks": {

            "total": task_data.get(
                "total",
                0
            ),

            "completed": task_data.get(
                "completed",
                0
            ),
        },
    }


# =========================================================
# BLOCK 4 / 5
# EXECUTIVE-WISE PROJECT STATUS
# =========================================================

@frappe.whitelist()
def get_executive_wise_project_status():
    """
    Return project and task status grouped by
    Executives reporting to the logged-in Associate.

    Metrics:
        - Projects
        - High Priority
        - Delayed
        - Blocked
        - Completion
    """

    associate = frappe.db.get_value(
        "Employee",
        {
            "user_id": frappe.session.user
        },
        "name"
    )

    if not associate:
        return {
            "error": "Employee not found for current user"
        }

    executives = get_associate_executives(
        associate
    )

    if not executives:
        return {
            "executives": []
        }

    task_data = get_executive_task_records(
        executives
    )

    tasks = task_data["tasks"]
    task_owners = task_data["task_owners"]

    today = getdate(nowdate())

    # -----------------------------------------------------
    # Initialize summary
    # -----------------------------------------------------

    summary = {}

    user_to_employee = {}

    for executive in executives:

        summary[executive.name] = {
            "employee": executive.name,
            "employee_name": executive.employee_name,
            "designation": executive.designation,

            "projects": set(),

            "total_tasks": 0,
            "completed_tasks": 0,

            "high_priority": 0,
            "delayed": 0,
            "blocked": 0,
        }

        if executive.user_id:
            user_to_employee[
                executive.user_id
            ] = executive.name

    # -----------------------------------------------------
    # Analyze Tasks
    # -----------------------------------------------------

    for task in tasks:

        owners = task_owners.get(
            task.name,
            set()
        )

        if not owners:
            continue

        is_completed = (
            task.status == "Completed"
        )

        is_blocked = (
            task.status == "Blocked"
        )

        is_delayed = False

        if (
            task.exp_end_date
            and not is_completed
        ):

            deadline = getdate(
                task.exp_end_date
            )

            if deadline < today:
                is_delayed = True

        is_high_priority = (
            task.priority == "High"
            and not is_completed
        )

        for owner in owners:

            employee_name = (
                user_to_employee.get(owner)
            )

            if not employee_name:
                continue

            record = summary[
                employee_name
            ]

            # Project
            if task.project:
                record["projects"].add(
                    task.project
                )

            # Total
            record["total_tasks"] += 1

            # Completed
            if is_completed:
                record["completed_tasks"] += 1

            # High priority
            if is_high_priority:
                record["high_priority"] += 1

            # Delayed
            if is_delayed:
                record["delayed"] += 1

            # Blocked
            if is_blocked:
                record["blocked"] += 1

    # -----------------------------------------------------
    # Prepare Response
    # -----------------------------------------------------

    result = []

    for executive in executives:

        record = summary[
            executive.name
        ]

        total_tasks = record[
            "total_tasks"
        ]

        completed_tasks = record[
            "completed_tasks"
        ]

        completion = 0

        if total_tasks:

            completion = (
                completed_tasks /
                total_tasks
            ) * 100

        result.append({

            "employee": record[
                "employee"
            ],

            "employee_name": record[
                "employee_name"
            ],

            "designation": record[
                "designation"
            ],

            "projects": len(
                record["projects"]
            ),

            "total_tasks": total_tasks,

            "completed_tasks": completed_tasks,

            "high_priority": record[
                "high_priority"
            ],

            "delayed": record[
                "delayed"
            ],

            "blocked": record[
                "blocked"
            ],

            "completion": round(
                completion,
                2
            ),
        })

    return {
        "executives": result
    }


# =========================================================
# BLOCK 6
# PROJECT & TASK AGING
# =========================================================

@frappe.whitelist()
def get_project_task_aging():
    """
    Return pending task aging for Executives
    reporting to the logged-in Associate.

    Categories:
        - On Time
        - 1–3 Days Delayed
        - 4–7 Days Delayed
        - 7+ Days Delayed

    Completed tasks are excluded.
    """

    associate = frappe.db.get_value(
        "Employee",
        {
            "user_id": frappe.session.user
        },
        "name"
    )

    if not associate:
        return {
            "error": "Employee not found for current user"
        }

    executives = get_associate_executives(
        associate
    )

    if not executives:
        return {
            "total": 0,
            "on_time": 0,
            "delayed_1_3": 0,
            "delayed_4_7": 0,
            "delayed_7_plus": 0,
        }

    task_data = get_executive_task_records(
        executives
    )

    tasks = task_data["tasks"]

    today = getdate(nowdate())

    # -----------------------------------------------------
    # Counters
    # -----------------------------------------------------

    on_time = 0
    delayed_1_3 = 0
    delayed_4_7 = 0
    delayed_7_plus = 0

    # -----------------------------------------------------
    # Classify Tasks
    # -----------------------------------------------------

    for task in tasks:

        # Completed tasks are not aging
        if task.status == "Completed":
            continue

        # No expected end date
        #
        # We do not know whether the task is delayed,
        # so it is kept under "On Time".
        if not task.exp_end_date:

            on_time += 1
            continue

        deadline = getdate(
            task.exp_end_date
        )

        # Deadline today or in future
        if deadline >= today:

            on_time += 1
            continue

        # -------------------------------------------------
        # Calculate overdue days
        # -------------------------------------------------

        overdue_days = (
            today - deadline
        ).days

        if overdue_days <= 3:

            delayed_1_3 += 1

        elif overdue_days <= 7:

            delayed_4_7 += 1

        else:

            delayed_7_plus += 1

    total = (
        on_time
        + delayed_1_3
        + delayed_4_7
        + delayed_7_plus
    )

    return {

        "total": total,

        "on_time": on_time,

        "delayed_1_3": delayed_1_3,

        "delayed_4_7": delayed_4_7,

        "delayed_7_plus": delayed_7_plus,
    }


@frappe.whitelist()
def get_executive_supervision_summary():
    """Return a supervision summary for the logged-in Associate."""

    associate = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        "name"
    )

    if not associate:
        return {
            "error": "Employee not found for current user",
            "executive_count": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "delayed_tasks": 0,
            "blocked_tasks": 0,
        }

    executives = get_associate_executives(associate)

    if not executives:
        return {
            "executive_count": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "delayed_tasks": 0,
            "blocked_tasks": 0,
            "executives": [],
        }

    task_data = get_executive_task_records(executives)
    tasks = task_data["tasks"]

    from frappe.utils import getdate, nowdate

    today = getdate(nowdate())
    completed = 0
    delayed = 0
    blocked = 0

    for task in tasks:
        if task.status == "Completed":
            completed += 1
        elif task.status == "Blocked":
            blocked += 1

        if (
            task.status != "Completed"
            and task.exp_end_date
            and getdate(task.exp_end_date) < today
        ):
            delayed += 1

    return {
        "executive_count": len(executives),
        "total_tasks": len(tasks),
        "completed_tasks": completed,
        "delayed_tasks": delayed,
        "blocked_tasks": blocked,
        "executives": [
            {
                "employee": employee.name,
                "employee_name": employee.employee_name,
                "designation": employee.designation,
            }
            for employee in executives
        ],
    }


@frappe.whitelist()
def get_my_priority_workboard():
    """Return open Tasks assigned to the logged-in user,
    grouped by priority for the Associate Workboard.
    """

    user = frappe.session.user

    if not user or user == "Guest":
        frappe.throw("Please log in to view your workboard.")

    # Find Tasks assigned to the current user.
    todos = frappe.get_all(
        "ToDo",
        filters={
            "allocated_to": user,
            "reference_type": "Task",
            "status": ["!=", "Cancelled"],
        },
        fields=["reference_name"],
    )

    task_names = list({
        todo.reference_name
        for todo in todos
        if todo.reference_name
    })

    result = {
        "total": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "workboard": {
            "High": [],
            "Medium": [],
            "Low": [],
        },
    }

    if not task_names:
        return result

    # Only show tasks that are still pending.
    tasks = frappe.get_all(
        "Task",
        filters={
            "name": ["in", task_names],
            "status": ["not in", ["Completed", "Cancelled"]],
        },
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "project",
            "exp_end_date",
        ],
        order_by="exp_end_date asc",
    )

    today = getdate(nowdate())

    for task in tasks:
        priority = task.priority or "Medium"

        if priority not in ("High", "Medium", "Low"):
            priority = "Medium"

        deadline = (
            getdate(task.exp_end_date)
            if task.exp_end_date
            else None
        )

        overdue = (
            task.status == "Overdue"
            or bool(deadline and deadline < today)
        )

        aging = (
            (today - deadline).days
            if overdue and deadline
            else None
        )

        project_name = None
        client = None

        if task.project:
            project = frappe.db.get_value(
                "Project",
                task.project,
                ["project_name", "customer"],
                as_dict=True,
            )

            if project:
                project_name = (
                    project.project_name or task.project
                )
                client = project.customer

        result["workboard"][priority].append({
            "name": task.name,
            "subject": task.subject,
            "status": task.status,
            "priority": priority,
            "project": task.project,
            "project_name": project_name,
            "client": client,
            "deadline": str(deadline) if deadline else None,
            "overdue": overdue,
            "aging": aging,
        })

        result[priority.lower()] += 1
        result["total"] += 1

    return result
