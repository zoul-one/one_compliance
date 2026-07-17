import frappe

def execute():
	"""Set custom_is_billable for existing Projects based on Compliance Sub Category or Project Template."""
	frappe.db.sql(
		"""
		UPDATE `tabProject` p
		LEFT JOIN `tabProject Template` pt ON p.project_template = pt.name
		LEFT JOIN `tabCompliance Sub Category` csc ON COALESCE(p.compliance_sub_category, pt.compliance_sub_category) = csc.name
		SET p.custom_is_billable = COALESCE(csc.is_billable, 0)
		"""
	)
	frappe.db.commit()
