"""
Monster Editor avanzado para MU Online
- Diseño: panel izquierdo (lista con checkboxes + buscador), centro (formulario de edición),
  derecha (aplicar porcentaje a monsters seleccionados).
- Opción A: seleccionar monsters mediante checkboxes en una ventana/columna.
- Lee y guarda Monster.txt con formato parecido al original.
- Dependencias: ttkbootstrap
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *

FILE_PATH = "Monster.txt"

# Columnas esperadas (según tu encabezado)
COLUMNS = [
    "Index","Rate","Name","Level","MaxLife","MaxMana","DamageMin","DamageMax",
    "Defense","MagicDefense","AttackRate","DefenseRate","MoveRange","AttackType",
    "AttackRange","ViewRange","MoveSpeed","AttackSpeed","RegenTime","Attribute",
    "ItemRate","MoneyRate","MaxItemLevel","MonsterSkill","Resistance1","Resistance2",
    "Resistance3","Resistance4"
]

# ---------- UTIL: parse / format ----------
def parse_monster_line(line: str):
    """
    Parsea una línea de monster y devuelve lista de campos o None si no cumple.
    Formato esperado: index rate "Name" rest_of_numbers...
    """
    line = line.strip()
    if not line or line.startswith("//") or line.lower().startswith("end"):
        return None

    # regex: index rate "Name" then the rest of fields separated by spaces
    m = re.match(r'^\s*(\d+)\s+(\d+)\s+"([^"]+)"\s+(.*)$', line)
    if not m:
        return None

    index, rate, name, rest = m.groups()
    rest_parts = re.split(r'\s+', rest.strip())
    row = [index, rate, name] + rest_parts
    # Ensure the row has same number of columns as COLUMNS (pad with zeros if needed)
    if len(row) < len(COLUMNS):
        row += ["0"] * (len(COLUMNS) - len(row))
    return row[:len(COLUMNS)]

def format_monster_line(row):
    """Formatea una fila (lista) a línea para guardar en el archivo"""
    # Name in quotes, align spaces similar to original
    name = f"\"{row[2]}\""
    left = f"{row[0]:<8}{row[1]:<8}{name:<35}"
    right = " ".join(str(x) for x in row[3:])
    return left + right

def load_file(path=FILE_PATH):
    """Carga el archivo entero, devuelve (header_lines, monsters_list, footer_lines)"""
    header = []
    monsters = []
    footer = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_monsters = True
    for ln in lines:
        if ln.strip().lower() == "end":
            footer.append(ln.rstrip("\n"))
            in_monsters = False
            continue

        parsed = parse_monster_line(ln)
        if parsed:
            monsters.append(parsed)
        else:
            # if it's non-data and we haven't reached "end", treat as header
            if in_monsters:
                header.append(ln.rstrip("\n"))
            else:
                footer.append(ln.rstrip("\n"))

    return header, monsters, footer

def save_file(monsters, header, footer, path=FILE_PATH):
    """Guarda todo preservando header/footer (aprox)."""
    with open(path, "w", encoding="utf-8") as f:
        # write header lines (or a standard header if none)
        if header:
            for h in header:
                f.write(h + "\n")
        else:
            f.write("//Index   Rate   Name                                 Level ...\n")

        for m in monsters:
            f.write(format_monster_line(m) + "\n")

        # write footer if exists, else write 'end'
        if footer:
            for ft in footer:
                f.write(ft + "\n")
        else:
            f.write("end\n")

# ---------- GUI ----------
class MonsterEditorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("🐉 Monster Editor - TuServerMU.com.ve by Azzlaer")
        self.master.geometry("1200x720")

        # Load initial data
        self.header, self.monsters, self.footer = load_file()

        # Map index->monster for quick find (Index as string)
        self.index_map = {m[0]: m for m in self.monsters}

        # Top bar
        self._build_topbar()

        # Body: left / center / right
        body = ttk.Frame(self.master, padding=10)
        body.pack(fill="both", expand=True)

        left_frame = ttk.Frame(body, width=320)
        left_frame.pack(side="left", fill="y", padx=(0,10))
        center_frame = ttk.Frame(body)
        center_frame.pack(side="left", fill="both", expand=True, padx=(0,10))
        right_frame = ttk.Frame(body, width=320)
        right_frame.pack(side="right", fill="y")

        # Left: buscador + lista de checkboxes
        self._build_left(left_frame)

        # Center: formulario de edición
        self._build_center(center_frame)

        # Right: controles para aplicar porcentaje
        self._build_right(right_frame)

        # Status bar
        self.status_var = tk.StringVar(value=f"Monsters cargados: {len(self.monsters)}")
        status = ttk.Label(self.master, textvariable=self.status_var, anchor="w")
        status.pack(fill="x", side="bottom")

    def _build_topbar(self):
        top = ttk.Frame(self.master, padding=8)
        top.pack(fill="x")

        title = ttk.Label(top, text="🐲 Monster Editor", font=("Segoe UI", 16, "bold"))
        title.pack(side="left")

        subtitle = ttk.Label(top, text="  — Edita y aplica porcentajes a tus monsters", foreground="#9aa")
        subtitle.pack(side="left", padx=(8,0))

        btn_save = ttk.Button(top, text="💾 Guardar Todo", bootstyle="success", command=self.save_all)
        btn_save.pack(side="right", padx=6)

        btn_reload = ttk.Button(top, text="🔄 Recargar", bootstyle="secondary", command=self.reload_file)
        btn_reload.pack(side="right", padx=6)

    # ---------------- left: buscador + list of checkboxes ----------------
    def _build_left(self, parent):
        # Buscador
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill="x", pady=(0,8))
        ttk.Label(search_frame, text="🔎 Buscar:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(6,0))
        search_entry.bind("<KeyRelease>", lambda e: self._refresh_monster_list())

        # Scrollable container for checkboxes
        box_frame = ttk.Frame(parent)
        box_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(box_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(box_frame, orient="vertical", command=canvas.yview)
        self.checks_container = ttk.Frame(canvas)

        self.checks_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=self.checks_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons: seleccionar todo / ninguno / invertir
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="✅ Seleccionar todo", bootstyle="info", command=self.select_all).pack(side="left", expand=True, padx=2)
        ttk.Button(btn_frame, text="❌ Deseleccionar", bootstyle="light", command=self.clear_all).pack(side="left", expand=True, padx=2)
        ttk.Button(btn_frame, text="🔁 Invertir", bootstyle="outline", command=self.invert_selection).pack(side="left", expand=True, padx=2)

        # Build checkbuttons initially
        self.checkbox_vars = []  # list of (var,index)
        self._refresh_monster_list()

    def _refresh_monster_list(self):
        # clear container
        for widget in self.checks_container.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()

        query = self.search_var.get().lower().strip()
        for i, m in enumerate(self.monsters):
            display = f"[{m[0]}] {m[2]} (Lv {m[3]})"
            if query and query not in display.lower():
                continue
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(self.checks_container, text=display, variable=var)
            cb.pack(anchor="w", pady=1, padx=4)
            # bind left click to open editor on double-click (simulated)
            cb.bind("<Double-Button-1>", lambda e, idx=i: self.open_editor_window(idx))
            self.checkbox_vars.append((var, i))

    def select_all(self):
        for var, _ in self.checkbox_vars:
            var.set(True)

    def clear_all(self):
        for var, _ in self.checkbox_vars:
            var.set(False)

    def invert_selection(self):
        for var, _ in self.checkbox_vars:
            var.set(not var.get())

    # ---------------- center: formulario de edición ----------------
    def _build_center(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill="x")
        ttk.Label(header, text="✏️ Editor de Monster", font=("Segoe UI", 14, "bold")).pack(side="left")

        # info label
        self.current_index_var = tk.StringVar(value="Ninguno seleccionado")
        ttk.Label(header, textvariable=self.current_index_var).pack(side="left", padx=12)

        # form area
        form_frame = ttk.Frame(parent, padding=8)
        form_frame.pack(fill="both", expand=True, pady=(8,0))

        # Two-column layout for form fields (scrollable)
        canvas = tk.Canvas(form_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.form_entries = {}  # col_name -> entry widget
        # create entries
        for i, col in enumerate(COLUMNS):
            row = ttk.Frame(inner, padding=(4,4))
            row.pack(fill="x")
            label = ttk.Label(row, text=col, width=18, anchor="w")
            label.pack(side="left")
            ent = ttk.Entry(row)
            ent.pack(side="left", fill="x", expand=True)
            self.form_entries[col] = ent

        # Buttons under form
        btns = ttk.Frame(parent, padding=8)
        btns.pack(fill="x")
        ttk.Button(btns, text="🧾 Cargar seleccionado", bootstyle="secondary", command=self.load_selected_into_form).pack(side="left", padx=6)
        ttk.Button(btns, text="💾 Guardar cambios (único)", bootstyle="success", command=self.save_form_to_monster).pack(side="left", padx=6)
        ttk.Button(btns, text="➕ Agregar nuevo monster", bootstyle="primary", command=self.add_new_monster).pack(side="left", padx=6)
        ttk.Button(btns, text="🗑 Eliminar seleccionado", bootstyle="danger", command=self.delete_selected_monster).pack(side="left", padx=6)

    def _get_first_checked_index(self):
        for var, idx in self.checkbox_vars:
            if var.get():
                return idx
        return None

    def load_selected_into_form(self):
        idx = self._get_first_checked_index()
        if idx is None:
            messagebox.showwarning("Selecciona uno", "Selecciona al menos un monster (el primero seleccionado se cargará).")
            return
        self.open_editor_window(idx)

    def open_editor_window(self, monster_idx):
        # monster_idx is index in self.monsters
        try:
            m = self.monsters[monster_idx]
        except IndexError:
            messagebox.showerror("Error", "Monster no encontrado.")
            return

        # populate form entries in center with the monster data
        for i, col in enumerate(COLUMNS):
            self.form_entries[col].delete(0, "end")
            self.form_entries[col].insert(0, str(m[i]))

        self.current_edit_idx = monster_idx
        self.current_index_var.set(f"Editando: [{m[0]}] {m[2]}")

    def save_form_to_monster(self):
        if not hasattr(self, "current_edit_idx") or self.current_edit_idx is None:
            messagebox.showwarning("Nada para guardar", "No hay monster cargado en el formulario.")
            return

        # read entries and update monster
        newrow = []
        for col in COLUMNS:
            val = self.form_entries[col].get().strip()
            # basic sanitation for Name to remove quotes if present
            if col == "Name":
                val = val.strip('"')
            newrow.append(val if val != "" else "0")
        # replace
        self.monsters[self.current_edit_idx] = newrow
        # refresh left list display (names/levels might have changed)
        self._refresh_monster_list()
        self.status_var.set(f"Guardado monster [{newrow[0]}] {newrow[2]}")
        messagebox.showinfo("Guardado", "Cambios guardados para el monster en memoria. Recuerda 'Guardar Todo' para escribir el archivo.")

    def add_new_monster(self):
        # Create a new monster with default values and open in form
        new_index = 0
        if self.monsters:
            # compute next index as max existing + 1
            try:
                existing = [int(m[0]) for m in self.monsters]
                new_index = max(existing) + 1
            except:
                new_index = len(self.monsters)
        newrow = [str(new_index), "1", f"New Monster {new_index}"] + ["0"] * (len(COLUMNS)-3)
        self.monsters.append(newrow)
        self._refresh_monster_list()
        # select the new one
        # set its checkbox var to True if present
        for var, idx in self.checkbox_vars:
            if idx == len(self.monsters)-1:
                var.set(True)
        messagebox.showinfo("Nuevo", f"Monster creado con Index {new_index}. Selecciónalo y edítalo en el formulario.")

    def delete_selected_monster(self):
        idx = self._get_first_checked_index()
        if idx is None:
            messagebox.showwarning("Selecciona uno", "Selecciona al menos un monster para eliminar.")
            return
        m = self.monsters[idx]
        if messagebox.askyesno("Confirmar eliminación", f"¿Eliminar [{m[0]}] {m[2]}?"):
            del self.monsters[idx]
            # refresh map and lists
            self._refresh_monster_list()
            self.status_var.set(f"Monster [{m[0]}] eliminado (aún no guardado en archivo).")

    # ---------------- right: porcentaje / select fields ----------------
    def _build_right(self, parent):
        ttk.Label(parent, text="📈 Aplicar porcentaje", font=("Segoe UI", 13, "bold")).pack(pady=(0,6))
        ttk.Label(parent, text="Porcentaje (ej: 20 para +20%)").pack(anchor="w")
        self.pct_var = tk.StringVar(value="10")
        pct_entry = ttk.Entry(parent, textvariable=self.pct_var)
        pct_entry.pack(fill="x", pady=4)

        ttk.Label(parent, text="Seleccionar atributos a aumentar:").pack(anchor="w", pady=(8,4))
        # scrollable list of attribute checkboxes (omit Index/Rate/Name as non-numeric)
        attrs_frame = ttk.Frame(parent)
        attrs_frame.pack(fill="both", expand=False)

        canvas = tk.Canvas(attrs_frame, borderwidth=0, highlightthickness=0, height=220)
        sb = ttk.Scrollbar(attrs_frame, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.attr_vars = {}
        numeric_cols = COLUMNS[3:]  # treat columns from Level onward as numeric
        for col in numeric_cols:
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(inner, text=col, variable=var)
            cb.pack(anchor="w", pady=1, padx=3)
            self.attr_vars[col] = var

        # Quick-select buttons for attributes
        attr_buttons = ttk.Frame(parent)
        attr_buttons.pack(fill="x", pady=6)
        ttk.Button(attr_buttons, text="Seleccionar todos", bootstyle="outline", command=lambda: self._set_all_attrs(True)).pack(side="left", padx=3)
        ttk.Button(attr_buttons, text="Deseleccionar", bootstyle="outline", command=lambda: self._set_all_attrs(False)).pack(side="left", padx=3)

        # Apply to selected monsters button
        ttk.Button(parent, text="▶ Aplicar a monsters seleccionados", bootstyle="primary", command=self.apply_percentage_to_selected).pack(fill="x", pady=(8,4))
        ttk.Button(parent, text="▶ Aplicar a todos los monsters", bootstyle="warning", command=self.apply_percentage_to_all).pack(fill="x", pady=(2,4))

        ttk.Separator(parent).pack(fill="x", pady=8)
        ttk.Label(parent, text="Vista rápida (monster seleccionado):").pack(anchor="w")
        self.preview_txt = scrolledtext.ScrolledText(parent, height=8, state="disabled")
        self.preview_txt.pack(fill="both", pady=(6,0), expand=False)

    def _set_all_attrs(self, val: bool):
        for v in self.attr_vars.values():
            v.set(val)

    def _get_checked_monster_indices(self):
        return [idx for var, idx in self.checkbox_vars if var.get()]

    def apply_percentage_to_selected(self):
        checked = self._get_checked_monster_indices()
        if not checked:
            messagebox.showwarning("Sin selection", "Debes seleccionar al menos un monster en la columna izquierda.")
            return
        self._apply_percentage_to_indices(checked)

    def apply_percentage_to_all(self):
        indices = list(range(len(self.monsters)))
        self._apply_percentage_to_indices(indices)

    def _apply_percentage_to_indices(self, indices):
        # Get percentage
        try:
            pct = float(self.pct_var.get())
        except:
            messagebox.showerror("Error", "Porcentaje inválido. Usa un número, p.ej. 20")
            return
        factor = 1 + pct / 100.0

        # get selected attributes as column names
        selected_attrs = [col for col, var in self.attr_vars.items() if var.get()]
        if not selected_attrs:
            messagebox.showwarning("Selecciona atributos", "Selecciona al menos un atributo para aplicar el porcentaje.")
            return

        # map col -> index in COLUMNS
        attr_indices = [COLUMNS.index(col) for col in selected_attrs]

        # apply
        affected = 0
        for i in indices:
            row = self.monsters[i]
            changed = False
            for ci in attr_indices:
                try:
                    # try parse as float/int; preserve integer if original integer
                    orig = row[ci]
                    # If it's name-like, skip
                    if ci == 2:
                        continue
                    # allow integers and floats
                    val = float(orig)
                    newval = val * factor
                    # round: if original had no decimal, store int
                    if float(int(val)) == val:
                        newstr = str(int(round(newval)))
                    else:
                        # keep two decimals for floats
                        newstr = f"{newval:.2f}"
                    row[ci] = newstr
                    changed = True
                except Exception:
                    # ignore non-numeric fields
                    continue
            if changed:
                affected += 1

        self._refresh_monster_list()
        self.status_var.set(f"Ajustado {pct}% a {affected} monsters en {', '.join(selected_attrs)}")
        messagebox.showinfo("Aplicado", f"Se aplicó {pct}% a {affected} monsters en {len(selected_attrs)} atributos.\nRecuerda guardar para persistir en archivo.")

        # update preview if any one selected for preview
        first_idx = indices[0] if indices else None
        if first_idx is not None:
            self._show_preview(first_idx)

    def _show_preview(self, idx):
        self.preview_txt.configure(state="normal")
        self.preview_txt.delete("1.0", "end")
        try:
            row = self.monsters[idx]
            lines = [f"{col}: {row[i]}" for i, col in enumerate(COLUMNS)]
            self.preview_txt.insert("end", "\n".join(lines))
        except Exception:
            self.preview_txt.insert("end", "No hay preview disponible")
        self.preview_txt.configure(state="disabled")

    # ---------------- file ops ----------------
    def save_all(self):
        save_file(self.monsters, self.header, self.footer)
        messagebox.showinfo("Guardado", f"Archivo '{FILE_PATH}' actualizado correctamente.")
        self.status_var.set("Guardado en archivo.")

    def reload_file(self):
        if messagebox.askyesno("Recargar", "Recargará el archivo desde disco y perderás cambios no guardados. ¿Continuar?"):
            self.header, self.monsters, self.footer = load_file()
            self._refresh_monster_list()
            self.status_var.set("Recargado desde archivo.")

# ---------- RUN ----------
if __name__ == "__main__":
    app = tb.Window(themename="superhero")
    MonsterEditorApp(app)
    app.mainloop()
