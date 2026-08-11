import frappe
from frappe.utils import getdate, add_days


@frappe.whitelist()
def get_dashboard_data(
    compliance_category=None,
    compliance_sub_category=None
):

    today = getdate()


    # ========================================================
    # PROJECT FILTERS
    #
    # Compliance filters apply ONLY to Project /
    # Compliance-related data.
    # ========================================================

    project_filters = {
        "status": "Open"
    }


    if compliance_category:

        project_filters[
            "compliance_category"
        ] = compliance_category


    if compliance_sub_category:

        project_filters[
            "compliance_sub_category"
        ] = compliance_sub_category


    # ========================================================
    # KPI CARDS
    # ========================================================

    # --------------------------------------------------------
    # Active Leads
    #
    # Compliance filters are NOT applied because Lead
    # does not participate in the dashboard filter logic.
    # --------------------------------------------------------

    active_leads = frappe.db.count(
        "Lead",
        filters={
            "status": [
                "not in",
                [
                    "Lost",
                    "Do Not Contact",
                    "Converted"
                ]
            ]
        }
    )


    # --------------------------------------------------------
    # Open Projects
    # --------------------------------------------------------

    open_projects = frappe.db.count(
        "Project",
        filters=project_filters
    )


    # --------------------------------------------------------
    # Pending Tasks
    #
    # Not globally filtered by compliance category.
    # --------------------------------------------------------

    pending_tasks = frappe.db.count(
        "Task",
        filters={
            "status": [
                "not in",
                [
                    "Completed",
                    "Cancelled"
                ]
            ]
        }
    )


    # --------------------------------------------------------
    # Due Today
    # --------------------------------------------------------

    due_today = frappe.db.count(
        "Task",
        filters={
            "exp_end_date": today,
            "status": [
                "not in",
                [
                    "Completed",
                    "Cancelled"
                ]
            ]
        }
    )


    # --------------------------------------------------------
    # Overdue Tasks
    # --------------------------------------------------------

    overdue_tasks = frappe.db.count(
        "Task",
        filters={
            "exp_end_date": [
                "<",
                today
            ],
            "status": [
                "not in",
                [
                    "Completed",
                    "Cancelled"
                ]
            ]
        }
    )


    # --------------------------------------------------------
    # Completed Projects
    # --------------------------------------------------------

    completed_project_filters = {
        "status": "Completed"
    }


    if compliance_category:

        completed_project_filters[
            "compliance_category"
        ] = compliance_category


    if compliance_sub_category:

        completed_project_filters[
            "compliance_sub_category"
        ] = compliance_sub_category


    completed_projects = frappe.db.count(
        "Project",
        filters=completed_project_filters
    )


    # --------------------------------------------------------
    # Customers
    # --------------------------------------------------------

    customers = frappe.db.count(
        "Customer",
        filters={
            "disabled": 0
        }
    )


    # --------------------------------------------------------
    # Active Compliance Agreements
    # --------------------------------------------------------

    active_agreements = frappe.db.count(
        "Compliance Agreement",
        filters={
            "status": "Active"
        }
    )


    # ========================================================
    # LEAD STATUS DISTRIBUTION
    # ========================================================

    lead_status_distribution = frappe.db.sql(
        """
        SELECT
            status,
            COUNT(name) AS count
        FROM `tabLead`
        WHERE
            status IS NOT NULL
            AND status != ''
        GROUP BY status
        ORDER BY count DESC
        """,
        as_dict=True
    )


    # ========================================================
    # PROJECT STATUS DISTRIBUTION
    #
    # Compliance filters ARE applied here.
    # ========================================================

    project_conditions = [
        "status IS NOT NULL",
        "status != ''"
    ]

    project_values = []


    if compliance_category:

        project_conditions.append(
            "compliance_category = %s"
        )

        project_values.append(
            compliance_category
        )


    if compliance_sub_category:

        project_conditions.append(
            "compliance_sub_category = %s"
        )

        project_values.append(
            compliance_sub_category
        )


    projects_by_status = frappe.db.sql(
        f"""
        SELECT
            status,
            COUNT(name) AS count
        FROM `tabProject`
        WHERE
            {" AND ".join(project_conditions)}
        GROUP BY status
        ORDER BY count DESC
        """,
        project_values,
        as_dict=True
    )


    # ========================================================
    # UPCOMING COMPLIANCE DEADLINES
    # ========================================================

    compliance_conditions = [
        "next_compliance_date BETWEEN %s AND %s"
    ]

    compliance_values = [
        today,
        add_days(today, 30)
    ]


    if compliance_category:

        compliance_conditions.append(
            "compliance_category = %s"
        )

        compliance_values.append(
            compliance_category
        )


    if compliance_sub_category:

        compliance_conditions.append(
            """
            (
                compliance_sub_category = %s
                OR sub_category_name = %s
            )
            """
        )

        compliance_values.extend([
            compliance_sub_category,
            compliance_sub_category
        ])


    compliance_due = frappe.db.sql(
        f"""
        SELECT
            name,
            compliance_category,
            compliance_sub_category,
            sub_category_name,
            next_compliance_date
        FROM `tabCompliance Category Details`
        WHERE
            {" AND ".join(compliance_conditions)}
        ORDER BY next_compliance_date ASC
        LIMIT 100
        """,
        compliance_values,
        as_dict=True
    )


    # ========================================================
    # DEADLINES BY WEEK
    # ========================================================

    upcoming_compliance_deadlines = []


    week_ranges = [
        (
            today,
            add_days(today, 6),
            "This Week"
        ),

        (
            add_days(today, 7),
            add_days(today, 13),
            "Next Week"
        ),

        (
            add_days(today, 14),
            add_days(today, 20),
            "Week 3"
        ),

        (
            add_days(today, 21),
            add_days(today, 30),
            "Week 4"
        )
    ]


    for start_date, end_date, label in week_ranges:

        count = 0


        for item in compliance_due:

            compliance_date = getdate(
                item.next_compliance_date
            )


            if (
                start_date
                <= compliance_date
                <= end_date
            ):

                count += 1


        upcoming_compliance_deadlines.append({
            "label": label,
            "count": count
        })


    # ========================================================
    # TOP CUSTOMERS
    #
    # Contextual because the list is based on Projects.
    # ========================================================

    customer_conditions = [
        "customer IS NOT NULL",
        "customer != ''"
    ]

    customer_values = []


    if compliance_category:

        customer_conditions.append(
            "compliance_category = %s"
        )

        customer_values.append(
            compliance_category
        )


    if compliance_sub_category:

        customer_conditions.append(
            "compliance_sub_category = %s"
        )

        customer_values.append(
            compliance_sub_category
        )


    top_customers = frappe.db.sql(
        f"""
        SELECT
            customer,
            COUNT(name) AS count
        FROM `tabProject`
        WHERE
            {" AND ".join(customer_conditions)}
        GROUP BY customer
        ORDER BY count DESC
        LIMIT 5
        """,
        customer_values,
        as_dict=True
    )


    # ========================================================
    # UPCOMING TASKS
    #
    # Tasks themselves are not globally filtered.
    # ========================================================

    upcoming_tasks = frappe.get_all(
        "Task",
        filters={
            "exp_end_date": [
                ">=",
                today
            ],

            "status": [
                "not in",
                [
                    "Completed",
                    "Cancelled"
                ]
            ]
        },

        fields=[
            "name",
            "subject",
            "project",
            "exp_end_date",
            "assigned_to",
            "priority",
            "status"
        ],

        order_by="exp_end_date asc",

        limit_page_length=10
    )


    # ========================================================
    # ACTIVE PROJECTS
    #
    # Compliance filters apply here.
    # ========================================================

    projects = frappe.get_all(
        "Project",

        filters=project_filters,

        fields=[
            "name",
            "project_name",
            "customer",
            "status",
            "percent_complete",
            "expected_end_date",
            "compliance_category",
            "compliance_sub_category"
        ],

        order_by="expected_end_date asc",

        limit_page_length=10
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        # ----------------------------------------------------
        # KPI
        # ----------------------------------------------------

        "active_leads":
            active_leads,

        "open_projects":
            open_projects,

        "pending_tasks":
            pending_tasks,

        "due_today":
            due_today,

        "overdue_tasks":
            overdue_tasks,

        "completed_projects":
            completed_projects,

        "customers":
            customers,

        "active_agreements":
            active_agreements,


        # ----------------------------------------------------
        # CHARTS
        # ----------------------------------------------------

        "lead_status_distribution":
            lead_status_distribution,

        "projects_by_status":
            projects_by_status,

        "upcoming_compliance_deadlines":
            upcoming_compliance_deadlines,


        # ----------------------------------------------------
        # TABLES
        # ----------------------------------------------------

        "top_customers":
            top_customers,

        "upcoming_tasks":
            upcoming_tasks,

        "projects":
            projects,

        "compliance_due":
            compliance_due
    }


# ============================================================
# DASHBOARD FILTER OPTIONS
# ============================================================

@frappe.whitelist()
def get_dashboard_filters():

    categories = frappe.get_all(
        "Project",

        filters={
            "compliance_category": [
                "is",
                "set"
            ]
        },

        fields=[
            "compliance_category"
        ],

        group_by="compliance_category",

        order_by="compliance_category asc"
    )


    return {
        "categories": [
            row.compliance_category
            for row in categories
            if row.compliance_category
        ]
    }


# ============================================================
# DASHBOARD SUB CATEGORIES
# ============================================================

@frappe.whitelist()
def get_dashboard_sub_categories(
    compliance_category=None
):

    if not compliance_category:

        return []


    sub_categories = frappe.get_all(
        "Project",

        filters={
            "compliance_category":
                compliance_category,

            "compliance_sub_category": [
                "is",
                "set"
            ]
        },

        fields=[
            "compliance_sub_category"
        ],

        group_by="compliance_sub_category",

        order_by="compliance_sub_category asc"
    )


    return [
        row.compliance_sub_category
        for row in sub_categories
        if row.compliance_sub_category
    ]