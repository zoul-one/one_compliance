import frappe
from frappe import _
from frappe.email.doctype.notification.notification import get_context
from frappe.utils import add_days, getdate, today
from one_compliance.one_compliance.utils import create_todo
from one_compliance.one_compliance.doc_events.task import (
	create_sales_order,
	get_rate_from_compliance_agreement,
	update_expected_dates_in_task,
)
from one_compliance.one_compliance.utils import (
	create_project_completion_todos,
	send_notification,
)

def validate(doc, method=None):
	set_is_billable(doc)

def after_insert(doc, method=None):
	if not doc.sales_order and doc.custom_is_billable and doc.compliance_agreement:
		create_sales_order_for_project(doc)

def set_is_billable(doc):
	sub_cat = doc.compliance_sub_category
	if not sub_cat and doc.project_template:
		sub_cat = frappe.db.get_value("Project Template", doc.project_template, "compliance_sub_category")

	if sub_cat:
		is_billable = frappe.db.get_value("Compliance Sub Category", sub_cat, "is_billable")
		doc.custom_is_billable = 1 if is_billable else 0
	else:
		doc.custom_is_billable = 0

@frappe.whitelist()
def project_on_update(doc, method):
	is_not_rework = doc.sales_order and not frappe.db.get_value("Sales Order", doc.sales_order, "custom_is_rework")

	if doc.status == 'Completed':
		if is_not_rework:
			create_project_completion_todos(doc.sales_order, doc.project_name)

		send_project_completion_mail = frappe.db.get_value('Customer', doc.customer, 'send_project_completion_mail')
		if send_project_completion_mail:
			email_id = frappe.db.get_value('Customer', doc.customer, 'email_id')
			if email_id and frappe.db.get_single_value('Compliance Settings', 'enable_project_complete_notification_for_customer'):
				project_complete_notification_for_customer(doc, email_id)

	if is_not_rework:
		update_sales_order_billing_instruction(doc.sales_order, doc.custom_billing_instruction)
	if doc.status == 'Completed' and doc.custom_is_billable:
		create_commission_purchase_invoice(doc)

def update_sales_order_billing_instruction(sales_order, custom_billing_instruction):
	"""
	Updates the 'Billing Instruction' field in the Sales Order.
	"""
	if not frappe.db.exists("Sales Order", sales_order):
		frappe.throw(_("Sales Order does not exist"))

	frappe.db.set_value(
		"Sales Order", sales_order, "custom_billing_instruction", custom_billing_instruction
	)


@frappe.whitelist()
def project_complete_notification_for_customer(doc, email_id):
	context = get_context(doc)
	send_notification(doc, email_id, context, 'project_complete_notification_for_customer')

@frappe.whitelist()
def set_project_status(project, status, comment=None):
	"""
	set status for project and all related tasks
	"""
	if status not in ("Open","Completed", "Cancelled", "Hold"):
		frappe.throw(_("Status must be or Open or Hold Cancelled or Completed"))

	project = frappe.get_doc("Project", project)
	frappe.has_permission(doc=project, throw=True)
	if status == "Cancelled" and project.sales_order:
		if frappe.db.exists("Sales Order", project.sales_order):
			so = frappe.get_doc("Sales Order", project.sales_order)
			if so.docstatus == 1:
				so.cancel()

	tasks = frappe.get_all("Task", filters={"project": project.name}, fields=["name", "status"])

	for task in tasks:
		if task.status == "Completed":
			continue

		frappe.db.set_value("Task", task.name, "status", status)
		if status == "Hold":
			frappe.db.set_value("Task", task.name, "hold", 1)
		else:
			frappe.db.set_value("Task", task.name, "hold", 0)
			task_doc = frappe.get_doc('Task', task.name)
			update_expected_dates_in_task(task_doc)
	frappe.db.set_value("Project", project.name, "status", status)
	if status == "Hold":
		frappe.db.set_value("Project", project.name, "hold", 1)
	elif status == "Open":
		frappe.db.set_value("Project", project.name, "hold", 0)
	if comment:
		project.add_comment('Comment', comment)

@frappe.whitelist()
def set_status_to_overdue():

    projects = frappe.get_all(
        "Project",
        filters={
            "status": ["not in", ["Cancelled", "Hold", "Completed", "Invoiced", "Partially Paid", "Paid"]]
        },
        fields=["name", "expected_end_date", "project_template"],
    )

    today_date = getdate(today())
    settings = frappe.get_single("Compliance Settings")

    for project in projects:
        if not project.expected_end_date or today_date <= getdate(project.expected_end_date):
            continue

        if not frappe.db.exists(
            "Task",
            {
                "project": project.name,
                "status": ["not in", ["Completed", "Cancelled", "Hold"]],
            },
        ):
            continue

        try:
            doc = frappe.get_doc("Project", project.name)
            extension_days = 0
            project_template = doc.project_template

            if not project_template and doc.compliance_sub_category:
                project_template = frappe.db.get_value(
                    "Compliance Sub Category",
                    doc.compliance_sub_category,
                    "project_template",
                )

            if project_template:
                template = frappe.get_doc("Project Template", project_template)

                if template.overdue_extension_days and template.overdue_extension_days > 0:
                    extension_days = template.overdue_extension_days
                elif template.enable_project_extension:
                    if (
                        settings.enable_common_project_extension
                        and settings.overdue_extension_days
                        and settings.overdue_extension_days > 0
                    ):
                        extension_days = settings.overdue_extension_days

            if extension_days:
                old_date = doc.expected_end_date
                new_date = add_days(old_date, extension_days)
                frappe.db.set_value("Project", doc.name, "expected_end_date", new_date)
                frappe.db.set_value("Project", doc.name, "status", "Open")
                frappe.db.set_value("Project", doc.name, "is_overdue", 1)
                doc.add_comment(
                    "Comment",
                    text=f"Expected End Date was automatically changed from {old_date} to {new_date} based on the configured Overdue Extension Days.",
                )
            else:
                frappe.db.set_value("Project", doc.name, "status", "Overdue")
                frappe.db.set_value("Project", doc.name, "is_overdue", 1)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"set_status_to_overdue failed for project {project.name}")
            continue

@frappe.whitelist()
def get_permission_query_conditions(user=None):
	"""
	Method used to set the permission to get the list of docs (Example: list view query)
	Called from the permission_query_conditions of hooks for the DocType Issue
	args:
		user: name of User object or current user
	return conditions query
	"""
	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)
	if "Administrator" in user_roles:
		return None

	if "Manager" in user_roles or "Executive" in user_roles:
		if frappe.db.has_column("Project", "_assign"):
			return "(`tabProject`.`_assign` LIKE '%{}%')".format(user)
		else:
			return "1=0"
	else:
		return None


@frappe.whitelist()
def convert_project_to_premium(project):
	"""
	Convert Project to Premium by adding its associated Premium Tasks.
	"""
	try:
		project_doc = frappe.get_doc("Project", project)

		if not project_doc.compliance_sub_category:
			return "no_sub_category"

		sub_category_doc = frappe.get_doc("Compliance Sub Category", project_doc.compliance_sub_category)

		if not sub_category_doc.project_template:
			return "no_template"

		template_doc = frappe.get_doc("Project Template", sub_category_doc.project_template)
		for premium_task in template_doc.premium_tasks:
			existing_task = frappe.db.exists("Task", {
				"project": project_doc.name,
				"subject": premium_task.subject
			})
			if existing_task:
				continue
			task = frappe.new_doc("Task")
			task.subject = premium_task.subject
			task.project = project_doc.name
			task.expected_time = premium_task.task_duration or 0
			task.task_weightage = premium_task.task_weightage or 0
			task.save()

		project_doc.is_premium = 1
		project_doc.save()

		return "success"

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Convert Project to Premium Error")
		return "failed"

@frappe.whitelist()
def create_tasks_from_template(project):
	"""Create tasks in a Project from its Sub Category's Project Template"""
	project_doc = frappe.get_doc("Project", project)

	if not project_doc.compliance_sub_category:
		frappe.throw("No Compliance Sub Category linked with this Project")

	sub_category_doc = frappe.get_doc("Compliance Sub Category", project_doc.compliance_sub_category)
	if not sub_category_doc.project_template:
		frappe.throw("No Project Template linked with this Sub Category")

	template_doc = frappe.get_doc("Project Template", sub_category_doc.project_template)

	created_tasks = []

	for template_task in template_doc.tasks:
		template_task_doc = None
		if template_task.task:
			template_task_doc = frappe.get_doc("Task", template_task.task)

		task = frappe.new_doc("Task")
		task.compliance_sub_category = project_doc.compliance_sub_category
		task.subject = template_task.subject
		task.task_weightage = template_task.task_weightage or 0
		task.project = project_doc.name
		task.company = project_doc.company
		task.project_name = project_doc.project_name
		task.category_type = project_doc.category_type
		task.custom_serial_number = template_task.idx

		task.status = "Open"
		task.save(ignore_permissions=True)

		if template_task.type and template_task.employee_or_group:
			frappe.db.set_value("Task", task.name, "assigned_to", template_task.employee_or_group)

			if template_task.type == "Employee":
				user_id = frappe.db.get_value("Employee", template_task.employee_or_group, "user_id")
				if user_id:
					create_todo("Task", task.name, user_id, user_id, f"Task {task.name} Assigned Successfully")

			elif template_task.type == "Employee Group":
				employee_group = frappe.get_doc("Employee Group", template_task.employee_or_group)
				if employee_group.employee_list:
					for emp in employee_group.employee_list:
						if emp.user_id:
							create_todo("Task", task.name, emp.user_id, emp.user_id, f"Task {task.name} Assigned Successfully")

		created_tasks.append(task.name)

	return created_tasks


@frappe.whitelist()
def get_project_tasks(project):
	""" 
	Fetch tasks related to a project and determine if any are completed.
	"""
	tasks = frappe.get_all(
		"Task",
		filters={"project": project},
		fields=["name", "subject", "status", "completed_by", "completed_on"],
		order_by="modified desc"
	)

	has_completed = any(t.status == "Completed" for t in tasks)

	return {
		"show": has_completed,
		"tasks": tasks
	}

def create_commission_purchase_invoice(doc):
	"""
	Creates a Purchase Invoice for referral commission when a Project is marked as Completed.
	"""
	settings = frappe.get_single("Compliance Settings")

	if not settings.enable_referral_commission:
		return
	customer = frappe.get_doc("Customer", doc.customer)
	if customer.disable_referral_commission:
		return
	if customer.reference_completed:
		return
	if doc.compliance_sub_category:
		billable = frappe.db.get_value(
			"Compliance Sub Category",
			doc.compliance_sub_category,
			"is_billable"
		)

		if not billable:
			return
	sales_order = frappe.db.get_value(
		"Sales Order",
		{"project": doc.name},
		["name", "grand_total"],
		as_dict=True
	)

	if not sales_order:
		return

	sales_order_amount = sales_order.grand_total
	rate = 0

	if customer.commission_amount:
		rate = customer.commission_amount
	else:
		if customer.commission_percentage:
			rate = (sales_order_amount * customer.commission_percentage) / 100

	if not rate:
		return
	pi = frappe.new_doc("Purchase Invoice")
	pi.company = doc.company
	pi.supplier = customer.supplier
	pi.is_commission_invoice = 1
	pi.customer = customer.name
	pi.compliance_sub_category = doc.compliance_sub_category
	pi.project = doc.name
	pi.append("items", {
		"item_code": settings.service_item,
		"qty": 1,
		"rate": rate
	})

	pi.set_missing_values()
	pi.insert(ignore_permissions=True)
	frappe.get_doc({
		"doctype": "Reference Detail",
		"parent": customer.name,
		"parenttype": "Customer",
		"parentfield": "reference_details",
		"purchase_invoice": pi.name,
		"rate": rate,
		"status": pi.status
	}).insert(ignore_permissions=True)

	if customer.one_time:
		frappe.db.set_value("Customer", customer.name, "reference_completed", 1)

def create_sales_order_for_project(doc):
	try:
		if doc.compliance_sub_category:
			item_code = frappe.db.get_value("Compliance Sub Category", doc.compliance_sub_category, "item_code")
			item_name = frappe.db.get_value("Item", item_code, "item_name") if item_code else None
			if not item_code:
				frappe.throw(_("Item Code not found for Compliance Sub Category: {0}").format(doc.compliance_sub_category))
		rate, compliance_date = frappe.db.get_value(
			"Compliance Category Details",
			{
				"parent": doc.compliance_agreement,
				"compliance_sub_category": doc.compliance_sub_category,
		},
			["rate", "compliance_date"]
		)
		so = frappe.new_doc("Sales Order")
		so.customer = doc.customer
		so.company = doc.company
		so.compliance_agreement = doc.compliance_agreement
		so.compliance_sub_category = doc.compliance_sub_category
		so.transaction_date = compliance_date or today()
		so.delivery_date = compliance_date or today()
		so.project = doc.name

		item_row = {
			"item_code": item_code,
			"item_name": item_name,
			"qty": 1,
			"rate": rate or 0,
			"project": doc.name if doc else None
		}
		if frappe.db.get_single_value("Compliance Settings", "automatically_set_so_item_desc"):
			item_row["description"] = doc.custom_project_service if doc.custom_project_service else item_name

		so.append("items", item_row)
		so.set_missing_values()
		so.insert(ignore_permissions=True)
		so.submit()
		doc.db_set("sales_order", so.name)


	except Exception:
		frappe.log_error(frappe.get_traceback(), f"SO Creation Failed - {doc.name}")