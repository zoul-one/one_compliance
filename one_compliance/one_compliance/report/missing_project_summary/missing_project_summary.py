# Copyright (c) 2026, Zoul Technologies Private Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, today, add_months, add_years
from datetime import date
import calendar


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_missing_projects(filters)
	return columns, data

def get_columns():
	return [
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
		{"label": "Compliance Agreement", "fieldname": "compliance_agreement", "fieldtype": "Link", "options": "Compliance Agreement","width": 200},
		{"label": "Compliance Sub Category", "fieldname": "compliance_sub_category", "fieldtype": "Data", "width": 250},
		{"label": "Compliance Date", "fieldname": "expected_start_date", "fieldtype": "Date", "width": 120},
	]


def get_missing_projects(filters):
	results = []
	params = {"today": today()}
	if filters.get("include_expired"):
		conditions = "(ca.status = 'Expired' OR (ca.status != 'Expired' AND (ca.valid_upto IS NULL OR ca.valid_upto <= %(today)s))) AND ca.docstatus != 2"
	else:
		conditions = "ca.status != 'Expired' AND (ca.valid_upto IS NULL OR ca.valid_upto <= %(today)s) AND ca.docstatus != 2"
	if filters.get("customer"):
		conditions += " AND ca.customer = %(customer)s"
		params["customer"] = filters["customer"]
	if filters.get("compliance_sub_category"):
		conditions += " AND cad.compliance_sub_category = %(compliance_sub_category)s"
		params["compliance_sub_category"] = filters["compliance_sub_category"]
	from_date = filters.get("from")
	to_date = filters.get("to")
	date_basis = filters.get("date_basis")
	valid_date_fields = {
		"Valid From": "ca.valid_from",
		"Valid Upto": "ca.valid_upto",
		"Posting Date": "ca.posting_date"
	}
	date_basis_field = valid_date_fields.get(date_basis)
	if from_date and to_date and date_basis_field:
		conditions += f" AND {date_basis_field} BETWEEN %(from_date)s AND %(to_date)s"
		params["from_date"] = from_date
		params["to_date"] = to_date
	else:
		pass
	agreements = frappe.db.sql(f"""
		SELECT
			ca.name AS compliance_agreement,
			ca.customer,
			ca.valid_from,
			ca.valid_upto,
			cad.compliance_sub_category
		FROM `tabCompliance Agreement` ca
		JOIN `tabCompliance Category Details` cad ON cad.parent = ca.name
		WHERE {conditions}
	""", params, as_dict=True)
	for agreement in agreements:
		sub_cat = frappe.db.get_value("Compliance Sub Category", agreement.compliance_sub_category,
									  ["allow_repeat", "repeat_on", "month", "day"], as_dict=True)
		if not sub_cat or not sub_cat.allow_repeat:
			continue
		frequency = sub_cat.repeat_on
		month = None
		day = None
		if sub_cat.month:
			try:
				month = int(sub_cat.month) if isinstance(sub_cat.month, int) else list(calendar.month_name).index(sub_cat.month)
				if month == 0:
					month = None
			except Exception:
				month = None
		if sub_cat.day:
			try:
				day = int(sub_cat.day)
			except Exception:
				day = None
		valid_from = getdate(agreement.valid_from)
		if agreement.valid_upto:
			valid_upto = getdate(agreement.valid_upto)
		else:
			valid_upto = getdate(today())
		expected_dates = get_repeat_dates(valid_from, valid_upto, frequency, month, day)
		for compliance_date in expected_dates:
			project_exists = frappe.db.exists("Project", {
				"compliance_agreement": agreement.compliance_agreement,
				"compliance_sub_category": agreement.compliance_sub_category,
				"expected_start_date": compliance_date
			})
			if not project_exists:
				results.append({
					"customer": agreement.customer,
					"compliance_agreement": agreement.compliance_agreement,
					"compliance_sub_category": agreement.compliance_sub_category,
					"expected_start_date": compliance_date
				})
	return results


def get_repeat_dates(start_date, valid_upto, frequency, month=None, day=None):
	dates = []
	limit_date = min(getdate(today()), valid_upto)
	if frequency == "Quarterly" and month and day:
		quarterly_months = [(month + 3*i - 1) % 12 + 1 for i in range(4)]
		year = start_date.year
		while year <= limit_date.year:
			for m in quarterly_months:
				max_day = calendar.monthrange(year, m)[1]
				day_to_use = day if day <= max_day else max_day
				candidate = date(year, m, day_to_use)
				if candidate < start_date:
					continue
				if candidate > limit_date:
					return dates
				dates.append(candidate)
			year += 1

	else:
		current = start_date
		while current <= limit_date:
			candidate_day = day if day else current.day
			max_day = calendar.monthrange(current.year, current.month)[1]
			candidate_day = min(candidate_day, max_day)
			candidate_date = date(current.year, current.month, candidate_day)
			if candidate_date < start_date:
				current = add_months(current, 1 if frequency == "Monthly" else
											3 if frequency == "Quarterly" else
											6 if frequency == "Half Yearly" else
											12)
				continue
			if candidate_date > limit_date:
				break
			dates.append(candidate_date)
			current = add_months(current, 1 if frequency == "Monthly" else
										3 if frequency == "Quarterly" else
										6 if frequency == "Half Yearly" else
										12)
	return dates
