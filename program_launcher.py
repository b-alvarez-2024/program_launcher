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

        self.buttons_data = []  # Lista para [{name, program_path, icon_path, tk_icon_ref}]
        self.current_config_file = None
        self.max_cols_buttons = 10  # Número máximo de botones por fila

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

        # --- Frame para los botones ---
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.update_buttons_display()
        self.root.minsize(150, 100) # Tamaño mínimo inicial

    def _launch_program(self, program_path):
        """Lanza el programa especificado."""
        try:
            subprocess.Popen(program_path)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Programa no encontrado: {program_path}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo lanzar el programa: {program_path}\nDetalles: {e}", parent=self.root)

    def _load_and_prepare_icon(self, icon_path):
        """Carga, redimensiona un icono y devuelve un objeto PhotoImage."""
        if not icon_path or not os.path.exists(icon_path):
            return None
        try:
            img = Image.open(icon_path)
            # Para GIFs animados, usar el primer frame. Pillow < 10.0.0 .is_animated, >= 10.0.0 .n_frames > 1
            if getattr(img, 'is_animated', False) or (hasattr(img, 'n_frames') and img.n_frames > 1):
                img.seek(0) # Usar el primer frame
            img = img.resize((32, 32), Image.LANCZOS) # Image.Resampling.LANCZOS en Pillow >= 9.1.0
            return ImageTk.PhotoImage(img)
        except Exception as e:
            # messagebox.showwarning("Error de Icono", f"No se pudo cargar o procesar el icono: {icon_path}\n{e}", parent=self.root)
            print(f"Advertencia: No se pudo cargar o procesar el icono: {icon_path}\n{e}")
            return None

    def update_buttons_display(self):
        """Limpia y redibuja todos los botones en la interfaz."""
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        if not self.buttons_data:
            self.root.geometry("") # Permitir que la ventana se encoja
            self.root.minsize(150, 100)
            # Podría mostrarse un Label indicando que no hay botones.
            # empty_label = tk.Label(self.buttons_frame, text="Añada botones desde el menú 'Editar'.")
            # empty_label.pack(pady=20)
            return
        
        self.root.minsize(0,0) # Resetear minsize para que se ajuste al contenido

        row, col = 0, 0
        for i, button_data in enumerate(self.buttons_data):
            tk_icon = button_data.get('tk_icon_ref') # El PhotoImage ya está almacenado

            if tk_icon:
                button = tk.Button(self.buttons_frame, image=tk_icon, width=32, height=32,
                                   command=lambda p=button_data['program_path']: self._launch_program(p))
                button.image = tk_icon  # Mantener referencia para evitar garbage collection
            else:
                # Botón con texto si no hay icono o falla la carga
                button_text = button_data['name'][0].upper() if button_data['name'] else "?"
                button = tk.Button(self.buttons_frame, text=button_text, width=4, height=2, # Aprox. 32x32 para una letra
                                   font=("Arial", 10, "bold"),
                                   command=lambda p=button_data['program_path']: self._launch_program(p))
            
            button.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            self.buttons_frame.grid_columnconfigure(col, weight=1) # Distribuir espacio
            
            col += 1
            if col >= self.max_cols_buttons:
                self.buttons_frame.grid_rowconfigure(row, weight=1) # Distribuir espacio
                col = 0
                row += 1
        if self.buttons_data: # Asegurar que la última fila también se expande si es necesario
            self.buttons_frame.grid_rowconfigure(row, weight=1)

        self.root.geometry("") # Forzar a Tkinter a recalcular el tamaño


    def add_button_dialog(self):
        """Muestra diálogos para añadir un nuevo botón."""
        name = simpledialog.askstring("Nombre del Botón", "Introduce un nombre para el botón (ej: Navegador):", parent=self.root)
        if name is None: # El usuario canceló el nombre
            return

        program_path = filedialog.askopenfilename(
            title="Seleccionar Programa a Ejecutar",
            filetypes=(("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")),
            parent=self.root
        )
        if not program_path: # El usuario canceló la selección de programa
            return

        icon_path = filedialog.askopenfilename(
            title="Seleccionar Icono (PNG, GIF, JPG, ICO)",
            filetypes=(("Imágenes", "*.png *.gif *.jpg *.jpeg *.ico"), ("Todos los archivos", "*.*")),
            parent=self.root
        )
        # icon_path puede ser None o una cadena vacía si el usuario cancela o no selecciona

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
        """Crea una nueva configuración vacía."""
        if self.buttons_data: # Si hay datos, preguntar si se quieren guardar
             if messagebox.askyesno("Guardar Cambios", "¿Desea guardar la configuración actual antes de crear una nueva?", parent=self.root):
                if self.current_config_file:
                    self.save_config()
                else:
                    self.save_config_as() # Si es una config nueva sin nombre, pedir dónde guardarla

        self.buttons_data = []
        self.current_config_file = None
        self.root.title("Lanzador de Aplicaciones - Nueva Configuración")
        self.update_buttons_display()


    def _load_config_from_file(self, filepath):
        """Carga la configuración desde un archivo JSON y actualiza `buttons_data`."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data_from_file = json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Archivo de configuración no encontrado: {filepath}", parent=self.root)
            return False
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Error al decodificar el archivo JSON: {filepath}. El archivo podría estar corrupto.", parent=self.root)
            return False
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo de configuración: {filepath}\n{e}", parent=self.root)
            return False

        temp_buttons_data = []
        for item in config_data_from_file:
            if not isinstance(item, dict) or "program_path" not in item:
                messagebox.showwarning("Formato Incorrecto", "Se encontró un elemento con formato incorrecto en el archivo de configuración y será omitido.", parent=self.root)
                continue
            
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
        """Abre un diálogo para seleccionar y cargar un archivo de configuración."""
        if self.buttons_data: # Si hay datos, preguntar si se quieren guardar
             if messagebox.askyesno("Guardar Cambios", "¿Desea guardar la configuración actual antes de abrir otra?", parent=self.root):
                if self.current_config_file:
                    self.save_config()
                else:
                    self.save_config_as()

        filepath = filedialog.askopenfilename(
            title="Abrir Configuración",
            filetypes=(("Archivos JSON de Configuración", "*.json"), ("Todos los archivos", "*.*")),
            defaultextension=".json",
            parent=self.root
        )
        if not filepath:
            return

        if self._load_config_from_file(filepath):
            self.current_config_file = filepath
            self.root.title(f"Lanzador de Aplicaciones - {os.path.basename(filepath)}")
            self.update_buttons_display()

    def _prepare_data_for_saving(self):
        """Prepara los datos de `buttons_data` para ser guardados en JSON (sin objetos Tkinter)."""
        return [
            {
                "name": btn_data["name"],
                "program_path": btn_data["program_path"],
                "icon_path": btn_data["icon_path"]
            }
            for btn_data in self.buttons_data
        ]

    def save_config(self):
        """Guarda la configuración actual en el archivo `current_config_file`."""
        if self.current_config_file:
            try:
                data_to_save = self._prepare_data_for_saving()
                with open(self.current_config_file, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=2)
                # messagebox.showinfo("Guardado", f"Configuración guardada en {self.current_config_file}", parent=self.root)
            except Exception as e:
                messagebox.showerror("Error al Guardar", f"No se pudo guardar la configuración en {self.current_config_file}:\n{e}", parent=self.root)
        else:
            self.save_config_as() # Si no hay archivo actual, pedir uno.

    def save_config_as(self):
        """Pide una ubicación y guarda la configuración actual en un nuevo archivo."""
        filepath = filedialog.asksaveasfilename(
            title="Guardar Configuración Como...",
            filetypes=(("Archivos JSON de Configuración", "*.json"), ("Todos los archivos", "*.*")),
            defaultextension=".json",
            initialfile="lanzador_config.json",
            parent=self.root
        )
        if not filepath:
            return

        try:
            data_to_save = self._prepare_data_for_saving()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2)
            self.current_config_file = filepath
            self.root.title(f"Lanzador de Aplicaciones - {os.path.basename(filepath)}")
            # messagebox.showinfo("Guardado", f"Configuración guardada en {filepath}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar la configuración en {filepath}:\n{e}", parent=self.root)

def check_and_install_pillow():
    try:
        from PIL import Image, ImageTk
        return True
    except ImportError:
        print("El módulo Pillow (PIL) no está instalado.")
        try:
            import pip
            print("Intentando instalar Pillow usando pip...")
            if hasattr(pip, 'main'):
                pip.main(['install', 'Pillow'])
            else: # Para versiones más nuevas de pip (pip >= 10)
                from pip._internal.cli.main import main as pip_main
                pip_main(['install', 'Pillow'])
            
            print("\nPillow debería estar instalado ahora.")
            print("Por favor, REINICIE la aplicación para que los cambios surtan efecto.")
            # Crear una ventana temporal para mostrar el mensaje si Tkinter ya está disponible
            temp_root = tk.Tk()
            temp_root.withdraw() # Ocultar la ventana principal temporal
            messagebox.showinfo("Instalación Completada", "Pillow ha sido instalado. Por favor, reinicie la aplicación.", parent=temp_root)
            temp_root.destroy()
            return False # Indicar que se necesita reinicio
        except ImportError:
            print("pip no está disponible. No se pudo instalar Pillow automáticamente.")
            messagebox.showerror("Error de Dependencia", "El módulo Pillow es necesario y pip no está disponible para instalarlo automáticamente.\nPor favor, instálelo manualmente ejecutando: pip install Pillow")
            return False
        except Exception as e:
            print(f"Error durante la instalación de Pillow: {e}")
            messagebox.showerror("Error de Dependencia", f"El módulo Pillow es necesario y no se pudo instalar automáticamente.\nError: {e}\nPor favor, instálelo manualmente ejecutando: pip install Pillow")
            return False

if __name__ == "__main__":
    if not check_and_install_pillow():
        # Si check_and_install_pillow devuelve False, significa que Pillow
        # no estaba o se acaba de instalar (y se necesita reiniciar) o no se pudo instalar.
        # En cualquier caso, no se debe continuar con la ejecución de la app principal
        # si la instalación fue necesaria y se mostró el mensaje de reinicio.
        exit() # Salir para que el usuario reinicie si es necesario.

    main_root_window = tk.Tk()
    app = AppLauncher(main_root_window)
    main_root_window.mainloop()