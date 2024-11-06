// Copyright (c) 2024, Niyaz and contributors
// For license information, please see license.txt

frappe.ui.form.on("WPS", {
    refresh(frm) {
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__("Download"), () => {
                window.location.href = repl(
                    frappe.request.url + "?cmd=%(cmd)s&docname=%(docname)s",
                    {
                        cmd: "teciza.teciza.doctype.wps.wps.get_wps_csv",
                        docname: frm.doc.name
                    },
                );
            })
        }

    },
});
