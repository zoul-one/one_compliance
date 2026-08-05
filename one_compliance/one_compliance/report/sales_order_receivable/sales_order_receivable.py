# # Copyright (c) 2026, Zoul Technologies Private Limited and contributors
# # For license information, please see license.txt

import frappe
from frappe.utils import getdate, nowdate

DEFAULT_RANGES = [30, 60, 90, 120]


def parse_ageing_ranges(filters: dict | None) -> list[int]:
	"""
	Turn the comma‑separated text in filters['range'] into a sorted list[int].
	Falls back to DEFAULT_RANGES on empty/bad input.
	"""
	raw = (filters or {}).get("range", "")
	try:
		edges = [int(x.strip()) for x in raw.split(",")]
		edges = sorted({edge for edge in edges if edge > 0})
		return edges or DEFAULT_RANGES
	except Exception:
		return DEFAULT_RANGES


def make_bucket_labels(edges: list[int]) -> list[str]:
	"""
	For edges [30, 60] ⇒ ["0‑30", "31‑60", "61‑Above"].
	"""
	if not edges:
		return ["0‑Above"]

	labels = [f"0‑{edges[0]}"]
	labels += [f"{edges[i-1] + 1}‑{edges[i]}" for i in range(1, len(edges))]
	labels.append(f"{edges[-1] + 1}‑Above")
	return labels


# ---------------------------------------------------------------------------
# Report entry point
# ---------------------------------------------------------------------------

def execute(filters: dict | None = None):
	if not filters:
		filters = {}

	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart_data(data, filters)

	# third return value (“message”) left as None intentionally
	return columns, data, None, chart


# ---------------------------------------------------------------------------
# Column builder
# ---------------------------------------------------------------------------

def get_columns(filters: dict) -> list[dict]:
	edges = parse_ageing_ranges(filters)
	labels = make_bucket_labels(edges)

	columns = [
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Party Type", "fieldname": "party_type", "fieldtype": "Data", "width": 90},
		{"label": "Party", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
		{"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 120},
		{"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 100},
		{"label": "Voucher No", "fieldname": "voucher_no", "fieldtype": "Link", "options": "Sales Order", "width": 150},
		{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
		{"label": "Sales Order Amount", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
		{"label": "Received Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 140},
		{"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 130},
		{"label": "Age (Days)", "fieldname": "age", "fieldtype": "Int", "width": 70},
	]

	# dynamic ageing buckets
	for idx, lbl in enumerate(labels, 1):
		columns.append({
			"label": lbl,
			"fieldname": f"range{idx}",
			"fieldtype": "Currency",
			"width": 100
		})

	columns.extend([
		{"label": "Currency", "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80},
		{"label": "Territory", "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 110},
		{"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 130},
		{"label": "Customer Contact", "fieldname": "customer_contact", "fieldtype": "Link", "options": "Contact", "width": 140},
	])
	return columns


# ---------------------------------------------------------------------------
# Data fetch & processing
# ---------------------------------------------------------------------------

def get_conditions(filters: dict) -> tuple[str, list]:
	"""
	Builds SQL WHERE snippets for customer, company, territory, customer group.
	Returns (condition_sql, bind_values)
	"""
	conditions, vals = [], []

	if cust := filters.get("customer"):
		conditions.append("so.customer = %s")
		vals.append(cust)

	if company := filters.get("company"):
		conditions.append("so.company = %s")
		vals.append(company)

	if terr := filters.get("territory"):
		terr_doc = frappe.get_doc("Territory", terr)
		terr_list = [terr]
		if terr_doc.is_group:
			terr_list = [d.name for d in frappe.get_all("Territory",
							filters={"lft": [">=", terr_doc.lft], "rgt": ["<=", terr_doc.rgt]})]
		conditions.append("cust.territory IN ({})".format(", ".join(["%s"] * len(terr_list))))
		vals.extend(terr_list)

	if cgrp := filters.get("customer_group"):
		cgrp_doc = frappe.get_doc("Customer Group", cgrp)
		cgrp_list = [cgrp]
		if cgrp_doc.is_group:
			cgrp_list = [d.name for d in frappe.get_all("Customer Group",
							filters={"lft": [">=", cgrp_doc.lft], "rgt": ["<=", cgrp_doc.rgt]})]
		conditions.append("cust.customer_group IN ({})".format(", ".join(["%s"] * len(cgrp_list))))
		vals.extend(cgrp_list)

	return " AND ".join(conditions), vals


def get_data(filters: dict) -> list[dict]:
	today = getdate(filters.get("report_date") or nowdate())
	edges = parse_ageing_ranges(filters)
	bucket_count = len(edges) + 1  # final “above” bucket

	# date filtering
	date_cond, date_vals = "", []
	fd, td = filters.get("from_date"), filters.get("to_date")

	if filters.get("ageing_based_on") == "Posting Date" and fd and td:
		date_cond = "AND so.transaction_date BETWEEN %s AND %s"
		date_vals.extend([fd, td])
	elif filters.get("ageing_based_on") == "Due Date" and fd and td:
		date_cond = "AND ps.due_date BETWEEN %s AND %s"
		date_vals.extend([fd, td])

	# other filters
	extra_cond, extra_vals = get_conditions(filters)

	# workflow states
	w_states = ["Proforma Invoice"]
	if filters.get("include_invoiced"):
		w_states.append("Invoiced")
	if filters.get("include_paid"):
		w_states.append("Paid")

	wf_cond = "AND so.workflow_state IN ({})".format(", ".join(["%s"] * len(w_states)))

	# placeholder order: today / workflow / date / others
	bind_vals = [today] + w_states + date_vals + extra_vals

	results = frappe.db.sql(f"""
		SELECT
			so.transaction_date AS posting_date,
			'Customer'            AS party_type,
			so.customer,
			soi.cost_center,
			ps.due_date           AS due_date,
			'Sales Order'         AS voucher_type,
			so.name               AS voucher_no,
			so.grand_total,
			so.advance_paid       AS paid_amount,
			(so.grand_total - so.advance_paid) AS outstanding_amount,
			DATEDIFF(%s, so.transaction_date)  AS age,
			so.currency,
			cust.territory,
			cust.customer_group,
			cust.customer_primary_contact AS customer_contact
		FROM `tabSales Order` so
		LEFT JOIN `tabSales Order Item` soi ON soi.parent = so.name
		LEFT JOIN `tabCustomer` cust        ON cust.name  = so.customer
		LEFT JOIN `tabPayment Schedule` ps  ON ps.parent  = so.name
		WHERE so.docstatus = 1
		  {wf_cond}
		  {date_cond}
		  {"AND " + extra_cond if extra_cond else ""}
		GROUP BY so.name
	""", bind_vals, as_dict=True)

	# bucket allocation
	for r in results:
		age = r.age or 0
		# init buckets
		for i in range(bucket_count):
			r[f"range{i+1}"] = 0

		placed = False
		for i, edge in enumerate(edges):
			if age <= edge:
				r[f"range{i+1}"] = r.outstanding_amount
				placed = True
				break
		if not placed:
			r[f"range{bucket_count}"] = r.outstanding_amount

	return results

def get_chart_data(data: list[dict], filters: dict) -> dict:
	edges = parse_ageing_ranges(filters)
	labels = make_bucket_labels(edges)
	bucket_count = len(labels)

	totals = [0] * bucket_count
	for row in data:
		for i in range(bucket_count):
			totals[i] += row.get(f"range{i+1}", 0)

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "Outstanding Amount", "values": totals}
			]
		},
		"type": "percentage"
	}
