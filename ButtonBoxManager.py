import json
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import subprocess
import threading
import time
import pyautogui
import serial
import os
import sys
import serial.tools.list_ports
import queue

CONFIG_FILE = "config.json"

KEYS_LAYOUT = [
    ["F21", "F22", "F23", "F24"],
    ["F17", "F18", "F19", "F20"],
    ["F13", "F14", "F15", "F16"]
]
# Limite de pages
MAX_PAGES = 6


# === Thèmes centralisés ===
THEMES = {
    "dark": {"bg": "#2F3136", "fg": "white", "entry_bg": "#202225", "active_bg": "#5c5f66"},
    "light": {"bg": "white", "fg": "black", "entry_bg": "#f0f0f0", "active_bg": "#e0e0e0"}
}

# Références globales aux barres personnalisées
title_bar = None
option_bar = None
theme_button = None

def get_available_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# load configuration file
def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "serial": {"port": "COM3", "baudrate": 9600},
            # Pour la compatibilité, on initialise la première page dans "macros"
            "macros": {"page_0": {f"F{13+i}": {"type": "hotkey", "value": "", "description": ""} for i in range(12)}},
            "dark_mode": True,
            "start_daemon_on_launch": False
        }

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def apply_theme(style, is_dark):
    theme = THEMES["dark"] if is_dark else THEMES["light"]
    style.theme_use("clam" if is_dark else "default")
    style.configure('.', background=theme["bg"], foreground=theme["fg"])
    style.configure('TFrame', background=theme["bg"])
    style.configure('TLabel', background=theme["bg"], foreground=theme["fg"])
    style.configure('TButton', background=theme["entry_bg"], foreground=theme["fg"])
    style.map('TButton', background=[('active', theme["active_bg"])])
    style.configure('TEntry', fieldbackground=theme["entry_bg"], foreground=theme["fg"], background=theme["entry_bg"])
    style.configure('TCombobox', fieldbackground=theme["entry_bg"], background=theme["entry_bg"], foreground=theme["fg"])
    style.configure('TCheckbutton', background=theme["bg"], foreground=theme["fg"])

def update_custom_bars(is_dark):
    theme = THEMES["dark"] if is_dark else THEMES["light"]
    for bar in [title_bar, option_bar]:
        if bar:
            bar.config(bg=theme["bg"])
            for widget in bar.winfo_children():
                widget.config(bg=theme["bg"], fg=theme["fg"])

def restart_gui():
    python_exe = sys.executable
    os.execl(python_exe, python_exe, *sys.argv)

def execute_action(action):
    if action["type"] == "hotkey":
        pyautogui.hotkey(*action["value"].split("+"))
    elif action["type"] == "command":
        subprocess.Popen(action["value"], shell=True)

def switch_theme(is_dark):
    config = load_config()
    config["dark_mode"] = is_dark
    save_config(config)
    restart_gui()

def create_gui():
    global title_bar, option_bar, theme_button

    # Créer la fenêtre principale (root) avant d'utiliser des variables Tkinter
    root = tk.Tk()  # Création de la fenêtre principale
    root.iconphoto(True, PhotoImage(file="icon.png"))
    root.title("ButtonBoxManager")
    root.resizable(False, False)

    # Charger la configuration après avoir créé la fenêtre
    config = load_config()  # Charger la configuration à ce moment-là

    # Initialiser le style pour ttk
    style = ttk.Style()

    # Maintenant vous pouvez créer des variables liées à Tkinter
    multipage_var = tk.BooleanVar(value=config.get("multipage_mode", False))

    max_pages = config.get("max_pages", 6)
    current_page = 0
    if multipage_var.get():
        current_page = 1  # Si en mode multipage, on commence par la page 1

    serial_config = config["serial"]
    dark_mode = config["dark_mode"]
    window_size = config.get("window_size", {"width": 670, "height": 728})

    stop_event = threading.Event()

    # File pour transmettre les commandes au démon
    serial_cmd_queue = queue.Queue()

    # Appliquer le thème après avoir défini 'style'
    apply_theme(style, dark_mode)
    
    def get_macros_for_page(page):
        return config["macros"].get(f"page_{page}", {
            f"F{13+i}": {"type": "hotkey", "value": ""} for i in range(12)
        })

    def save_macros_for_page(page, type_vars, value_vars, desc_vars):
        config["macros"][f"page_{page}"] = {
            key: {
                "type": type_vars[key].get(),
                "value": value_vars[key].get(),
                "description": desc_vars[key].get()
            }
            for row in KEYS_LAYOUT for key in row
    }
    # apply_theme(style, dark_mode)
    update_custom_bars(dark_mode)
    root.geometry(f"{window_size['width']}x{window_size['height']}")
    root.configure(bg=THEMES["dark" if dark_mode else "light"]["bg"])

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    def on_closing():
        stop_daemon()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Config COM & Baudrate
    port_var = tk.StringVar(value=serial_config.get("port", "COM3"))
    baud_var = tk.StringVar(value=str(serial_config.get("baudrate", 9600)))
    ttk.Label(frame, text="Port COM:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    ttk.Label(frame, text="Baudrate:").grid(row=0, column=2, sticky="e")

    if dark_mode:
        port_entry = tk.Entry(
            frame,
            textvariable=port_var,
            width=10,
            bg=THEMES["dark"]["entry_bg"],
            fg=THEMES["dark"]["fg"],
            insertbackground=THEMES["dark"]["fg"]
        )
        port_entry.grid(row=0, column=1, sticky="w")
        baud_entry = tk.Entry(
            frame,
            textvariable=baud_var,
            width=10,
            bg=THEMES["dark"]["entry_bg"],
            fg=THEMES["dark"]["fg"],
            insertbackground=THEMES["dark"]["fg"]
        )
        baud_entry.grid(row=0, column=3, sticky="w")
    else:
        ttk.Entry(frame, textvariable=port_var, width=10).grid(row=0, column=1, sticky="w")
        ttk.Entry(frame, textvariable=baud_var, width=10).grid(row=0, column=3, sticky="w")

    ttk.Separator(frame).grid(row=1, column=0, columnspan=4, sticky="ew", pady=2)

    # Zone d'affichage des macros
    macro_frame = ttk.Frame(frame)
    macro_frame.grid(row=2, column=0, columnspan=4)
    
    type_vars = {}
    value_vars = {}
    desc_vars = {}
    def draw_macro_page(page):
        nonlocal type_vars, value_vars, desc_vars
        for widget in macro_frame.winfo_children():
            widget.destroy()
        type_vars.clear()
        value_vars.clear()
        desc_vars.clear()

        macros = get_macros_for_page(page)
        colors = {
            "F13": "red", "F14": "green", "F15": "red", "F16": "green",
            "F17": "black", "F18": "#DCDCDC", "F19": "blue", "F20": "yellow",
            "F21": "black", "F22": "#DCDCDC", "F23": "blue", "F24": "yellow"
        }

        row_offset = 0
        for i, row_keys in enumerate(KEYS_LAYOUT):
            for j, key in enumerate(row_keys):
                color = colors.get(key, "black")

                btn = tk.Button(
                    macro_frame,
                    text=f"↓{key}↓",
                    width=5,
                    fg=color,
                    font=("Arial", 15, "bold"),
                    bg=THEMES["dark" if dark_mode else "light"]["entry_bg"],
                    activebackground=THEMES["dark" if dark_mode else "light"]["active_bg"],
                    command=lambda k=key: send_serial_command(k)
                )
                btn.grid(row=row_offset + i * 5, column=j, padx=1, pady=2)

                if multipage_var.get() and key in ["F13", "F14"]:
                    text_color = "white" if dark_mode else "black"  # Texte en blanc en mode sombre et noir en mode clair
                    if key == "F13":
                        big_button = tk.Button(
                            macro_frame,
                            text="Page Prèc.",
                            width=14,
                            height=3,
                            font=("Arial", 12, "bold"),
                            bg=THEMES["dark" if dark_mode else "light"]["entry_bg"],
                            activebackground=THEMES["dark" if dark_mode else "light"]["active_bg"],
                            fg=text_color,  # Appliquer la couleur du texte
                            command=lambda: change_page(-1)
                        )
                        big_button.grid(row=row_offset + i * 5 + 1, column=j, padx=0, pady=0, rowspan=3)
                    elif key == "F14":
                        big_button = tk.Button(
                            macro_frame,
                            text="Page Suiv.",
                            width=14,
                            height=3,
                            font=("Arial", 12, "bold"),
                            bg=THEMES["dark" if dark_mode else "light"]["entry_bg"],
                            activebackground=THEMES["dark" if dark_mode else "light"]["active_bg"],
                            fg=text_color,  # Appliquer la couleur du texte
                            command=lambda: change_page(1)
                        )
                        big_button.grid(row=row_offset + i * 5 + 1, column=j, padx=0, pady=0, rowspan=3)
                else:
                    type_var = tk.StringVar(value=macros[key]["type"])
                    ttk.Combobox(macro_frame, textvariable=type_var, values=["hotkey", "command"], width=22)\
                        .grid(row=row_offset + i * 5 + 1, column=j, padx=1, pady=2)

                    ttk.Label(macro_frame, text="cmd:", width=4).grid(row=row_offset + i * 5 + 2, column=j, sticky="w", padx=(1, 0))
                    value_var = tk.StringVar(value=macros[key]["value"])
                    tk.Entry(macro_frame, textvariable=value_var, width=17,
                            bg=THEMES["dark" if dark_mode else "light"]["entry_bg"],
                            fg=THEMES["dark" if dark_mode else "light"]["fg"],
                            insertbackground=THEMES["dark" if dark_mode else "light"]["fg"])\
                        .grid(row=row_offset + i * 5 + 2, column=j, padx=(40, 1), pady=2)

                    ttk.Label(macro_frame, text="desc:", width=4).grid(row=row_offset + i * 5 + 3, column=j, sticky="w", padx=(1, 0))
                    desc_var = tk.StringVar(value=macros[key].get("description", ""))
                    tk.Entry(macro_frame, textvariable=desc_var, width=17,
                            bg=THEMES["dark" if dark_mode else "light"]["entry_bg"],
                            fg=THEMES["dark" if dark_mode else "light"]["fg"],
                            insertbackground=THEMES["dark" if dark_mode else "light"]["fg"])\
                        .grid(row=row_offset + i * 5 + 3, column=j, padx=(40, 1), pady=(2, 5))

                type_vars[key] = type_var
                value_vars[key] = value_var
                desc_vars[key] = desc_var

            row_offset += 1

    # Toggle mode multipage

    def on_mode_toggle():
        if multipage_var.get():
            page_nav_frame.grid()
            update_page_label()
            change_page(1)
        else:
            page_nav_frame.grid_remove()
            page_label.config(text="Page 0")
            change_page(0)

        # 🔥 Sauvegarde immédiate du mode multipage dans le fichier de config
        config["multipage_mode"] = multipage_var.get()
        save_config(config)
        #log("Mode multipage mis à jour et sauvegardé.")

        draw_macro_page(current_page)

    ttk.Checkbutton(
        frame,
        text="Mode multipage",
        variable=multipage_var,
        command=lambda: on_mode_toggle()
    ).grid(row=16, column=0, columnspan=4, pady=(5, 0), sticky="w")

    # Zone pour la console
    console = tk.Text(frame, height=15, bg="black", fg="lime", insertbackground="white")
    console.grid(row=18, column=0, columnspan=4, padx=2, pady=2, sticky="nsew")

    def log(text):
        console.insert(tk.END, text + "\n")
        console.see(tk.END)

    # Fonction pour envoyer une commande via la file (qui sera traitée par le démon)
    def send_serial_command(command):
        if command.strip() == "":
            log("Commande vide, rien à envoyer.")
            return
        serial_cmd_queue.put(command)
        log(f"Commande en file : {command}")

    # Le démon va ouvrir le port série et vérifier périodiquement la file pour envoyer des commandes
    def listen_serial(console):
        try:
            with serial.Serial(port_var.get(), int(baud_var.get()), timeout=1) as arduino:
                log(f"Connecté à {port_var.get()} @ {baud_var.get()}")
                time.sleep(2)
                while not stop_event.is_set():  # 🔧 Ajoute cette condition
                    # Vérifier si une commande doit être envoyée
                    try:
                        cmd = serial_cmd_queue.get_nowait()
                    except queue.Empty:
                        cmd = None
                    if cmd:
                        arduino.write((cmd + "\n").encode())
                        log(f"[SERIAL] Commande envoyée : {cmd}")
                    # Lecture des données entrantes
                    line = arduino.readline().decode().strip()
                    if line:
                        log(f"[SERIAL] {line}")
                        current_macros = config["macros"].get(f"page_{current_page}", {})
                        if multipage_var.get():
                            if line == "F13":
                                change_page(-1)
                                continue
                            elif line == "F14":
                                change_page(1)
                                continue
                        if line in current_macros:
                            execute_action(current_macros[line])
                    time.sleep(0.05)
        except Exception as e:
            log(f"[ERREUR] {e}")


    def launch_daemon():
        log("Lancement du démon série...")
        stop_event.clear()  # Assurez-vous que stop_event est dans un état non déclenché
        threading.Thread(target=lambda: listen_serial(console), daemon=True).start()

    def stop_daemon():
        log("[*] Arrêt du démon série.")
        stop_event.set()  # Signale au thread du démon de s'arrêter

    def on_save():
        save_macros_for_page(current_page, type_vars, value_vars, desc_vars)
        config["serial"] = {"port": port_var.get(), "baudrate": int(baud_var.get())}
        config["start_daemon_on_launch"] = daemon_var.get()
        config["multipage_mode"] = multipage_var.get()

        save_config(config)
        log("Configuration sauvegardée.")

    #=== Pagination placée juste au-dessus de la console ===
    page_nav_frame = ttk.Frame(frame)
    page_nav_frame.grid(row=16, column=0, columnspan=4, pady=(0, 0))

    # ttk.Button(page_nav_frame, text="← Page Préc.", command=lambda: change_page(-1), width=15)\
    #     .pack(side="left")
    page_label = ttk.Label(page_nav_frame, text="Page 0", font=("Arial", 12, "bold"))
    page_label.pack(side="left", padx=1)
    # ttk.Button(page_nav_frame, text="Page Suiv. →", command=lambda: change_page(1), width=15)\
    #     .pack(side="left")

    def update_page_label():
        page_label.config(text=f"Page {current_page}")

    def change_page(delta):
        nonlocal current_page, max_pages
        save_macros_for_page(current_page, type_vars, value_vars, desc_vars)

        if multipage_var.get():  # Si en mode multipage
            current_page = (current_page + delta - 1) % max_pages + 1
        else:  # Si en mode mono-page
            current_page = 0  # On reste sur la page 0 pour mono-page

        # Attendre quelques millisecondes pour réduire le clignotement fix  pour la fluidité sinon voir chat gpt 
        # "Oui, ce comportement de "clignotement" ou de rafraîchissement brutal vient du fait que tous les widgets de la page
        #  des macros sont détruits puis recréés à chaque changement de page avec draw_macro_page."
        macro_frame.after(100, lambda: draw_macro_page(current_page))
        update_page_label()

    # === Boutons actions (sauvegarder, lancer, arrêter, thème) ===
    button_frame = ttk.Frame(frame)
    button_frame.grid(row=19, column=0, columnspan=4, sticky="e", pady=(10, 0))

    right_buttons = ttk.Frame(button_frame)
    right_buttons.pack(side="right")

    theme_button = tk.Button(right_buttons, borderwidth=0)

    def toggle_theme():
        current_config = load_config()
        new_mode = not current_config["dark_mode"]
        current_config["dark_mode"] = new_mode
        save_config(current_config)
        restart_gui()
    def update_theme_button(is_dark):
        theme_button.config(text="☀️ Mode Clair" if is_dark else "🌙 Mode Sombre")

    theme_button.config(command=toggle_theme, width=15)
    theme_button.grid(row=0, column=0, padx=2)
    update_theme_button(dark_mode)

    ttk.Button(right_buttons, text="Sauvegarder", command=on_save, width=15)\
        .grid(row=0, column=1, padx=2)
    ttk.Button(right_buttons, text="Lancer le démon", command=launch_daemon, width=15)\
        .grid(row=0, column=2, padx=2)
    ttk.Button(right_buttons, text="Arrêter le démon", command=stop_daemon, width=15)\
        .grid(row=0, column=3, padx=2)

    daemon_var = tk.BooleanVar(value=config.get("start_daemon_on_launch", False))
    tk.Checkbutton(
        frame,
        text="Lancer le démon au démarrage",
        variable=daemon_var,
        bg=style.lookup("TFrame", "background"),
        fg=style.lookup("TLabel", "foreground"),
        selectcolor=style.lookup("TFrame", "background")
    ).grid(row=19, column=0, columnspan=4, sticky="w", pady=(5, 0))

    draw_macro_page(current_page)
    update_page_label()

    if not multipage_var.get():
        page_nav_frame.grid_remove()
        page_label.config(text="")

    if config.get("start_daemon_on_launch", False):
        launch_daemon()

    root.mainloop()

if __name__ == "__main__":
    create_gui()
