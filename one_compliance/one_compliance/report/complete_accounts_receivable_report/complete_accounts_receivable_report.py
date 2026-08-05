# Copyright (c) 2026, Zoul Technologies Private Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, nowdate

def execute(filters: dict | None = None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_columns() -> list[dict]:
	return [
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
		{"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 150},
		{"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
		{"label": "Voucher No", "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 200},
		{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
		{"label": "Amount", "fieldname": "grand_total", "fieldtype": "Currency", "width": 150},
		{"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 150},
		{"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 180},
	]

def get_data(filters: dict) -> list[dict]:
	result = []

	# 1. Fetch Sales Invoices
	si_conditions = []
	si_vals = []

	if filters.get("company"):
		si_conditions.append("si.company = %s")
		si_vals.append(filters.get("company"))

	if filters.get("customer"):
		si_conditions.append("si.customer = %s")
		si_vals.append(filters.get("customer"))

	if filters.get("customer_group"):
		si_conditions.append("cust.customer_group = %s")
		si_vals.append(filters.get("customer_group"))

	if filters.get("from_date") and filters.get("to_date"):
		si_conditions.append("si.posting_date BETWEEN %s AND %s")
		si_vals.extend([filters.get("from_date"), filters.get("to_date")])

	si_where = " AND ".join(si_conditions)
	if si_where:
		si_where = "AND " + si_where

	sales_invoices = frappe.db.sql(f"""
		SELECT
			si.posting_date AS posting_date,
			si.customer,
			si.due_date AS due_date,
			'Sales Invoice' AS voucher_type,
			si.name AS voucher_no,
			COALESCE(NULLIF(si.rounded_total, 0), si.grand_total) AS grand_total,
			si.paid_amount AS paid_amount,
			si.outstanding_amount AS outstanding_amount,
			cust.customer_group
		FROM `tabSales Invoice` si
		LEFT JOIN `tabCustomer` cust ON cust.name = si.customer
		WHERE si.docstatus = 1
		  AND si.outstanding_amount != 0
		  {si_where}
	""", si_vals, as_dict=True)

	result.extend(sales_invoices)

	# 2. Fetch Sales Orders (Proforma Invoice only, without any submitted Sales Invoice)
	so_conditions = []
	so_vals = []

	if filters.get("company"):
		so_conditions.append("so.company = %s")
		so_vals.append(filters.get("company"))

	if filters.get("customer"):
		so_conditions.append("so.customer = %s")
		so_vals.append(filters.get("customer"))

	if filters.get("customer_group"):
		so_conditions.append("cust.customer_group = %s")
		so_vals.append(filters.get("customer_group"))

	if filters.get("from_date") and filters.get("to_date"):
		so_conditions.append("so.transaction_date BETWEEN %s AND %s")
		so_vals.extend([filters.get("from_date"), filters.get("to_date")])

	so_where = " AND ".join(so_conditions)
	if so_where:
		so_where = "AND " + so_where

	sales_orders = frappe.db.sql(f"""
		SELECT
			so.transaction_date AS posting_date,
			so.customer,
			MIN(ps.due_date) AS due_date,
			'Sales Order' AS voucher_type,
			so.name AS voucher_no,
			COALESCE(NULLIF(so.rounded_total, 0), so.grand_total) AS grand_total,
			so.advance_paid AS paid_amount,
			(COALESCE(NULLIF(so.rounded_total, 0), so.grand_total) - so.advance_paid) AS outstanding_amount,
			cust.customer_group
		FROM `tabSales Order` so
		LEFT JOIN `tabCustomer` cust ON cust.name = so.customer
		LEFT JOIN `tabPayment Schedule` ps ON ps.parent = so.name
		WHERE so.docstatus = 1
		  AND (so.workflow_state = 'Proforma Invoice' OR so.status = 'Proforma Invoice')
		  AND NOT EXISTS (
		  	SELECT 1
		  	FROM `tabSales Invoice Item` sii
		  	JOIN `tabSales Invoice` si ON si.name = sii.parent
		  	WHERE sii.sales_order = so.name
		  	  AND si.docstatus = 1
		  )
		  {so_where}
		GROUP BY so.name
		HAVING outstanding_amount != 0
	""", so_vals, as_dict=True)

	result.extend(sales_orders)

	# 3. Fetch Journal Entries
	journal_entries = get_journal_entries(filters)
	result.extend(journal_entries)

	# Sort by posting date descending, and fallback to voucher_no
	result.sort(key=lambda x: (getdate(x.get("posting_date")) if x.get("posting_date") else getdate("1900-01-01"), x.get("voucher_no")), reverse=True)
	return result

def get_journal_entries(filters):
	"""
	Returns filtered Journal Entry records linked to customers.
	Includes Draft Journal Entries if checkbox is enabled.
	Excludes fully paid Journal Entries.
	Shows paid amount if partially paid.
	"""
	conditions = []
	vals = []
	if filters.get("include_draft_journal_entries"):
		docstatus_condition = "je.docstatus IN (0, 1)"
	else:
		docstatus_condition = "je.docstatus = 1"

	if filters.get("company"):
		conditions.append("je.company = %s")
		vals.append(filters["company"])

	if filters.get("customer"):
		conditions.append("jel.party = %s")
		vals.append(filters["customer"])

	if filters.get("customer_group"):
		conditions.append("cust.customer_group = %s")
		vals.append(filters["customer_group"])

	if filters.get("from_date") and filters.get("to_date"):
		conditions.append("je.posting_date BETWEEN %s AND %s")
		vals.append(filters["from_date"])
		vals.append(filters["to_date"])

	where = " AND ".join(conditions)
	if where:
		where = "AND " + where

	return frappe.db.sql(f"""
		SELECT
			je.posting_date,
			jel.party AS customer,
			cust.customer_group,
			'Journal Entry' AS voucher_type,
			je.name AS voucher_no,

			SUM(jel.debit - jel.credit) AS grand_total,

			COALESCE((
				SELECT SUM(per.allocated_amount)
				FROM `tabPayment Entry Reference` per
				JOIN `tabPayment Entry` pe ON pe.name = per.parent
				WHERE per.reference_doctype = 'Journal Entry'
				  AND per.reference_name = je.name
				  AND pe.party_type = 'Customer'
				  AND pe.party = jel.party
				  AND pe.docstatus = 1
			), 0) AS paid_amount,

			SUM(jel.debit - jel.credit) -
			COALESCE((
				SELECT SUM(per.allocated_amount)
				FROM `tabPayment Entry Reference` per
				JOIN `tabPayment Entry` pe ON pe.name = per.parent
				WHERE per.reference_doctype = 'Journal Entry'
				  AND per.reference_name = je.name
				  AND pe.party_type = 'Customer'
				  AND pe.party = jel.party
				  AND pe.docstatus = 1
			), 0) AS outstanding_amount,

			NULL AS due_date

		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jel
			ON jel.parent = je.name
		LEFT JOIN `tabCustomer` cust
			ON cust.name = jel.party

		WHERE {docstatus_condition}
		  AND jel.party_type = 'Customer'
		  {where}

		GROUP BY je.name, jel.party
		HAVING outstanding_amount != 0
	""", vals, as_dict=True)