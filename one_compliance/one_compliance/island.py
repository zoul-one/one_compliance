
from frappe.utils.island import get_ui_islands


def extend_bootinfo(bootinfo):
    bootinfo.ui_islands = get_ui_islands()
