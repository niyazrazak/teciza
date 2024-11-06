
import frappe
import uuid

def check_mac_address(doc, method=None):
    # if frappe.session.user != "Admiistartor":
        # allowed_mac = frappe.db.get_value("User", frappe.session.user, "allowed_mac_address")
        # allowed_mac = "teysj"

    mac = uuid.getnode()
    mac_address = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
    frappe.msgprint(str(mac_address))