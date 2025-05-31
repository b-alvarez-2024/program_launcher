
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import subprocess
import json
import os


class AppLauncher:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Lanzador de Aplicaciones")
        self.root.minsize(200, 100) # Ancho mínimo para asegurar visibilidad de la barra de título

        self.buttons_data = []
        self.current_config_file = None
        self.max_cols_buttons = 10

        self.always_on_top_var = tk.BooleanVar()
        self.always_on_top_var.set(False)

        # --- Menú ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Nueva Configuración", command=self.new_config)
        file_menu.add_command(label="Abrir Configuración...", command=self.open_config)
        file_menu.add_command(label="Guardar Configuración", command=self.save_config)
        file_menu.add_command(label="Guardar Como...", command=self.save_config_as)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Añadir Botón...", command=self.add_button_dialog)
        edit_menu.add_command(label="Modificar Botón...", command=self.modify_button_dialog)
        edit_menu.add_command(label="Eliminar Botón...", command=self.delete_button_dialog)

        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ventana", menu=window_menu)
        window_menu.add_checkbutton(label="Siempre Encima",
                                    onvalue=True, offvalue=False,
                                    variable=self.always_on_top_var,
                                    command=self.toggle_always_on_top)

        # --- Frame para los botones ---
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.update_buttons_display()

    def toggle_always_on_top(self):
        self.root.attributes('-topmost', self.always_on_top_var.get())

    def _launch_program(self, program_path):
        try:
            subprocess.Popen(program_path)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Programa no encontrado: {program_path}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo lanzar el programa: {program_path}\nDetalles: {e}", parent=self.root)

    def _load_and_prepare_icon(self, icon_path):
        if not icon_path or not os.path.exists(icon_path):
            return None
        try:
            img = Image.open(icon_path)
            if getattr(img, 'is_animated', False) or (hasattr(img, 'n_frames') and img.n_frames > 1):
                img.seek(0)
            img = img.resize((32, 32), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Advertencia: No se pudo cargar o procesar el icono: {icon_path}\n{e}")
            return None

    def update_buttons_display(self):
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        if not self.buttons_data:
            self.root.geometry("")
            self.root.minsize(200, 100) # Asegurar minsize si está vacío
            return
        
        self.root.minsize(0,0) # Resetear minsize para que se ajuste al contenido

        row, col = 0, 0
        for i, button_data in enumerate(self.buttons_data):
            tk_icon = button_data.get('tk_icon_ref')
            if tk_icon:
                button = tk.Button(self.buttons_frame, image=tk_icon, width=32, height=32,
                                   command=lambda p=button_data['program_path']: self._launch_program(p))
                button.image = tk_icon
            else:
                button_text = button_data['name'][0].upper() if button_data['name'] else "?"
                button = tk.Button(self.buttons_frame, text=button_text, width=4, height=2,
                                   font=("Arial", 10, "bold"),
                                   command=lambda p=button_data['program_path']: self._launch_program(p))
            
            button.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            self.buttons_frame.grid_columnconfigure(col, weight=1)
            col += 1
            if col >= self.max_cols_buttons:
                self.buttons_frame.grid_rowconfigure(row, weight=1)
                col = 0
                row += 1
        if self.buttons_data:
            self.buttons_frame.grid_rowconfigure(row, weight=1)
        self.root.geometry("")

    def add_button_dialog(self):
        name = simpledialog.askstring("Nombre del Botón", "Introduce un nombre para el botón (ej: Navegador):", parent=self.root)
        if name is None: return

        program_path = filedialog.askopenfilename(
            title="Seleccionar Programa a Ejecutar",
            filetypes=(("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")),
            parent=self.root)
        if not program_path: return

        icon_path = filedialog.askopenfilename(
            title="Seleccionar Icono (PNG, GIF, JPG, ICO)",
            filetypes=(("Imágenes", "*.png *.gif *.jpg *.jpeg *.ico"), ("Todos los archivos", "*.*")),
            parent=self.root)

        tk_icon_ref = self._load_and_prepare_icon(icon_path)
        new_button_data = {
            "name": name if name else os.path.splitext(os.path.basename(program_path))[0],
            "program_path": program_path,
            "icon_path": icon_path if icon_path else "",
            "tk_icon_ref": tk_icon_ref
        }
        self.buttons_data.append(new_button_data)
        self.update_buttons_display()

    def new_config(self):
        if self.buttons_data:
             if messagebox.askyesno("Guardar Cambios", "¿Desea guardar la configuración actual antes de crear una nueva?", parent=self.root):
                if self.current_config_file: self.save_config()
                else: self.save_config_as()
        self.buttons_data = []
        self.current_config_file = None
        self.root.title("Lanzador de Aplicaciones - Nueva Configuración")
        self.update_buttons_display()
        self.root.minsize(200, 100) # Asegurar minsize para configs vacías

    def _load_config_from_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data_from_file = json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Archivo de configuración no encontrado: {filepath}", parent=self.root); return False
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Error al decodificar el archivo JSON: {filepath}.", parent=self.root); return False
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {filepath}\n{e}", parent=self.root); return False

        temp_buttons_data = []
        for item in config_data_from_file:
            if not isinstance(item, dict) or "program_path" not in item:
                messagebox.showwarning("Formato Incorrecto", "Elemento con formato incorrecto en config omitido.", parent=self.root); continue
            tk_icon_ref = self._load_and_prepare_icon(item.get("icon_path"))
            temp_buttons_data.append({
                "name": item.get("name", os.path.splitext(os.path.basename(item["program_path"]))[0]),
                "program_path": item["program_path"],
                "icon_path": item.get("icon_path", ""),
                "tk_icon_ref": tk_icon_ref
            })
        self.buttons_data = temp_buttons_data
        return True

    def open_config(self):
        if self.buttons_data:
             if messagebox.askyesno("Guardar Cambios", "¿Desea guardar la configuración actual antes de abrir otra?", parent=self.root):
                if self.current_config_file: self.save_config()
                else: self.save_config_as()
        filepath = filedialog.askopenfilename(
            title="Abrir Configuración",
            filetypes=(("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")),
            defaultextension=".json", parent=self.root)
        if not filepath: return
        if self._load_config_from_file(filepath):
            self.current_config_file = filepath
            self.root.title(f"Lanzador de Aplicaciones - {os.path.basename(filepath)}")
            self.update_buttons_display()

    def _prepare_data_for_saving(self):
        return [{"name": b["name"], "program_path": b["program_path"], "icon_path": b["icon_path"]} for b in self.buttons_data]

    def save_config(self):
        if self.current_config_file:
            try:
                with open(self.current_config_file, 'w', encoding='utf-8') as f:
                    json.dump(self._prepare_data_for_saving(), f, indent=2)
            except Exception as e:
                messagebox.showerror("Error al Guardar", f"No se pudo guardar: {self.current_config_file}\n{e}", parent=self.root)
        else: self.save_config_as()

    def save_config_as(self):
        filepath = filedialog.asksaveasfilename(
            title="Guardar Configuración Como...",
            filetypes=(("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")),
            defaultextension=".json", initialfile="lanzador_config.json", parent=self.root)
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._prepare_data_for_saving(), f, indent=2)
            self.current_config_file = filepath
            self.root.title(f"Lanzador de Aplicaciones - {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar en {filepath}:\n{e}", parent=self.root)

    def _get_button_list_for_dialog(self):
        return "\n".join([f"{i+1}. {data['name']}" for i, data in enumerate(self.buttons_data)])

    def _select_file_for_entry(self, entry_var, title_suffix, file_type_pattern, dialog_parent):
        filetypes_map = {
            "Ejecutables": ((title_suffix, file_type_pattern), ("Todos los archivos", "*.*")),
            "Imágenes": ((title_suffix, file_type_pattern), ("Todos los archivos", "*.*"))
        }
        filepath = filedialog.askopenfilename(
            title=f"Seleccionar {title_suffix}",
            filetypes=filetypes_map.get(title_suffix, (("Todos los archivos", "*.*"),)),
            parent=dialog_parent)
        if filepath: entry_var.set(filepath)

    def _open_actual_edit_dialog(self, button_index):
        original_data = self.buttons_data[button_index]
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Modificar Botón")
        edit_win.transient(self.root); edit_win.grab_set(); edit_win.resizable(False, False)

        name_var = tk.StringVar(value=original_data['name'])
        prog_var = tk.StringVar(value=original_data['program_path'])
        icon_var = tk.StringVar(value=original_data['icon_path'])

        form = tk.Frame(edit_win, padx=10, pady=10); form.pack(fill=tk.BOTH, expand=True)
        tk.Label(form, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=2)
        name_e = tk.Entry(form, textvariable=name_var, width=50); name_e.grid(row=0, column=1, sticky=tk.EW, pady=2)
        tk.Label(form, text="Programa:").grid(row=1, column=0, sticky=tk.W, pady=2)
        prog_e = tk.Entry(form, textvariable=prog_var, width=40); prog_e.grid(row=1, column=1, sticky=tk.EW, pady=2)
        tk.Button(form, text="...", command=lambda: self._select_file_for_entry(prog_var, "Ejecutables", "*.exe", edit_win)).grid(row=1, column=2, padx=(5,0))
        tk.Label(form, text="Icono:").grid(row=2, column=0, sticky=tk.W, pady=2)
        icon_e = tk.Entry(form, textvariable=icon_var, width=40); icon_e.grid(row=2, column=1, sticky=tk.EW, pady=2)
        tk.Button(form, text="...", command=lambda: self._select_file_for_entry(icon_var, "Imágenes", "*.png *.gif *.jpg *.jpeg *.ico", edit_win)).grid(row=2, column=2, padx=(5,0))

        btn_frame = tk.Frame(edit_win, pady=5); btn_frame.pack(fill=tk.X)
        def on_save():
            new_name, new_prog, new_icon = name_var.get().strip(), prog_var.get().strip(), icon_var.get().strip()
            if not new_name or not new_prog:
                messagebox.showerror("Error", "Nombre y programa no pueden estar vacíos.", parent=edit_win); return
            
            self.buttons_data[button_index]['name'] = new_name
            self.buttons_data[button_index]['program_path'] = new_prog
            if self.buttons_data[button_index]['icon_path'] != new_icon or \
               (new_icon and not self.buttons_data[button_index]['tk_icon_ref']) or \
               (not new_icon and self.buttons_data[button_index]['tk_icon_ref']):
                self.buttons_data[button_index]['icon_path'] = new_icon
                self.buttons_data[button_index]['tk_icon_ref'] = self._load_and_prepare_icon(new_icon)
            self.update_buttons_display(); edit_win.destroy()

        tk.Button(btn_frame, text="Guardar Cambios", command=on_save, width=15).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancelar", command=edit_win.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        
        edit_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()//2) - (edit_win.winfo_width()//2)
        y = self.root.winfo_y() + (self.root.winfo_height()//2) - (edit_win.winfo_height()//2)
        edit_win.geometry(f"+{x}+{y}"); name_e.focus_set()

    def modify_button_dialog(self):
        if not self.buttons_data: messagebox.showinfo("Modificar", "No hay botones para modificar.", parent=self.root); return
        prompt = f"Introduce el número del botón a modificar:\n\n{self._get_button_list_for_dialog()}"
        num = simpledialog.askinteger("Modificar Botón", prompt, parent=self.root, minvalue=1, maxvalue=len(self.buttons_data))
        if num is not None: self._open_actual_edit_dialog(num - 1)

    def delete_button_dialog(self):
        if not self.buttons_data: messagebox.showinfo("Eliminar", "No hay botones para eliminar.", parent=self.root); return
        prompt = f"Introduce el número del botón a eliminar:\n\n{self._get_button_list_for_dialog()}"
        num = simpledialog.askinteger("Eliminar Botón", prompt, parent=self.root, minvalue=1, maxvalue=len(self.buttons_data))
        if num is not None:
            idx = num - 1
            name = self.buttons_data[idx]['name']
            if messagebox.askyesno("Confirmar", f"¿Eliminar el botón '{name}'?", parent=self.root):
                del self.buttons_data[idx]; self.update_buttons_display()

def check_and_install_pillow():
    try:
        from PIL import Image, ImageTk; return True
    except ImportError:
        print("Pillow (PIL) no instalado.")
        try:
            import pip; print("Intentando instalar Pillow...")
            if hasattr(pip, 'main'): pip.main(['install', 'Pillow'])
            else: from pip._internal.cli.main import main as pip_main; pip_main(['install', 'Pillow'])
            print("\nPillow debería estar instalado. REINICIE la aplicación.");
            temp_root = tk.Tk(); temp_root.withdraw()
            messagebox.showinfo("Instalación", "Pillow instalado. Reinicie la aplicación.", parent=temp_root)
            temp_root.destroy(); return False
        except ImportError: print("pip no disponible."); messagebox.showerror("Error", "Pillow necesario. pip no disponible."); return False
        except Exception as e: print(f"Error instalando Pillow: {e}"); messagebox.showerror("Error", f"Pillow necesario. Error: {e}"); return False

if __name__ == "__main__":
    if not check_and_install_pillow(): exit()
    main_root_window = tk.Tk()
    app = AppLauncher(main_root_window)
    main_root_window.mainloop()
