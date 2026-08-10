// Copyright (c) 2026, Zoul Technologies Private Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Missing Project Summary"] = {
	"filters": [
		{
			"fieldname": "customer",
			"label": __("Client"),
			"fieldtype": "Link",
			"options": "Customer",
		},
		{
			"fieldname": "compliance_sub_category",
			"label": __("Compliance Sub Category"),
			"fieldtype": "Link",
			"options": "Compliance Sub Category",
		},
		{
			"fieldname": "date_basis",
			"label": "Date Basis",
			"fieldtype": "Select",
			"options": ["Posting Date", "Valid Upto", "Valid From", "Expected Start Date"],
		},
		{
			"fieldname": "from",
			"label": __("From"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "to",
			"label": __("To"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "include_expired",
			"label": __("Include Expired"),
			"fieldtype": "Check",
		},
	],
};
