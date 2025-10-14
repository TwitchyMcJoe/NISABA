import tkinter as tk
from utils.ipa_keyboard import open_ipa_keyboard  # <-- shared IPA keyboard utility

def enable_treeview_editing(tree: tk.Widget, save_callback=None, app=None):
    """
    Adds in-place editing to a ttk.Treeview:
    - Double-click a cell to edit
    - Enter or click away to save
    - Escape to cancel
    If save_callback and app are provided, they will be called after each edit.
    """
    edit = {"entry": None, "item": None, "column": None}

    def finish(save: bool):
        if edit["entry"] is None:
            return
        if save:
            newval = edit["entry"].get()
            vals = list(tree.item(edit["item"], "values"))
            col_index = tree["columns"].index(edit["column"])
            vals[col_index] = newval
            tree.item(edit["item"], values=vals)
            # 🔑 auto-save after edit
            if save_callback and app:
                try:
                    save_callback(app)
                except Exception as e:
                    print("Auto-save failed:", e)
        # cleanup
        if hasattr(edit["entry"], "ipa_btn"):
            edit["entry"].ipa_btn.destroy()
        edit["entry"].destroy()
        edit["entry"] = None
        edit["item"] = None
        edit["column"] = None

    def begin_edit(event):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)  # e.g. '#1'
        if not item or not column:
            return
        try:
            col_index = int(column.replace("#", "")) - 1
        except Exception:
            return
        columns = tree["columns"]
        if col_index < 0 or col_index >= len(columns):
            return
        col_name = columns[col_index]

        bbox = tree.bbox(item, column)
        if not bbox:
            return
        x, y, w, h = bbox

        current_vals = tree.item(item, "values")
        current = current_vals[col_index] if col_index < len(current_vals) else ""

        entry = tk.Entry(tree, borderwidth=0)
        entry.insert(0, str(current))
        entry.select_range(0, tk.END)
        entry.focus()
        entry.place(x=x+1, y=y+1, width=w-2, height=h-2)

        # If editing pronunciation or ipa column, add IPA keyboard button
        if col_name == "ipa":
            ipa_btn = tk.Button(tree, text="IPA",
                                    command=lambda e=entry: open_ipa_keyboard(app, e, mode="full"))
            ipa_btn.place(x=x+w+5, y=y)
            entry.ipa_btn = ipa_btn

        if col_name == "pronunciation":
            # Find the loanword value for this row
            vals = tree.item(item, "values")
            try:
                loanword_val = vals[tree["columns"].index("loanword")]
            except Exception:
                loanword_val = "NO"

            # If YES → full keyboard, else → restricted
            if loanword_val.upper() == "YES":
                ipa_btn = tk.Button(tree, text="IPA",
                                    command=lambda e=entry: open_ipa_keyboard(app, e, mode="full"))
            else:
                ipa_btn = tk.Button(tree, text="IPA",
                                    command=lambda e=entry: open_ipa_keyboard(app, e, mode="restricted"))
            ipa_btn.place(x=x+w+5, y=y)
            entry.ipa_btn = ipa_btn

        entry.bind("<Return>", lambda e: finish(True))
        entry.bind("<Escape>", lambda e: finish(False))
        # Clicking elsewhere finalizes (save)
        tree.bind("<Button-1>", lambda e: (finish(True), tree.unbind("<Button-1>")), add="+")
        edit.update({"entry": entry, "item": item, "column": col_name})

    tree.bind("<Double-1>", begin_edit, add="+")
