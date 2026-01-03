import tkinter as tk
from tkinter import ttk


class LicensePlateBlurView:

    def __init__(self, root):
        self.root = root
        self.root.title("Anonymisation de plaques d'immatriculation")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.select_files_btn = None
        self.select_folder_btn = None
        self.process_btn = None
        self.selection_label = None
        self.status_label = None
        self.progress = None

        self.setup_ui()

    def setup_ui(self):
        title_label = tk.Label(
            self.root,
            text="Anonymisation de plaques d'immatriculation",
            font=("Arial", 16, "bold"),
            pady=20
        )
        title_label.pack()

        instructions = tk.Label(
            self.root,
            text="Sélectionnez des images ou un dossier pour flouter les plaques",
            font=("Arial", 10),
            pady=10
        )
        instructions.pack()

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        self.select_files_btn = tk.Button(
            button_frame,
            text="Sélectionner des images",
            width=25,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        self.select_files_btn.grid(row=0, column=0, padx=10)

        self.select_folder_btn = tk.Button(
            button_frame,
            text="Sélectionner un dossier",
            width=25,
            height=2,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        self.select_folder_btn.grid(row=0, column=1, padx=10)

        self.selection_label = tk.Label(
            self.root,
            text="Aucune sélection",
            font=("Arial", 9),
            fg="gray"
        )
        self.selection_label.pack(pady=10)

        self.process_btn = tk.Button(
            self.root,
            text="Lancer le floutage",
            width=30,
            height=2,
            bg="#FF9800",
            fg="white",
            font=("Arial", 12, "bold"),
            cursor="hand2",
            state=tk.DISABLED
        )
        self.process_btn.pack(pady=20)

        self.progress = ttk.Progressbar(
            self.root,
            length=500,
            mode='determinate'
        )
        self.progress.pack(pady=10)

        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 9),
            fg="blue"
        )
        self.status_label.pack(pady=5)

    def set_select_files_command(self, command):
        self.select_files_btn.config(command=command)

    def set_select_folder_command(self, command):
        self.select_folder_btn.config(command=command)

    def set_process_command(self, command):
        self.process_btn.config(command=command)

    def update_selection_label(self, text, color="green"):
        self.selection_label.config(text=text, fg=color)

    def update_status_label(self, text, color="blue"):
        self.status_label.config(text=text, fg=color)

    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()

    def reset_progress(self):
        self.progress['value'] = 0

    def enable_process_button(self):
        self.process_btn.config(state=tk.NORMAL)

    def disable_process_button(self):
        self.process_btn.config(state=tk.DISABLED)

    def enable_selection_buttons(self):
        self.select_files_btn.config(state=tk.NORMAL)
        self.select_folder_btn.config(state=tk.NORMAL)

    def disable_selection_buttons(self):
        self.select_files_btn.config(state=tk.DISABLED)
        self.select_folder_btn.config(state=tk.DISABLED)

    def disable_all_buttons(self):
        self.disable_process_button()
        self.disable_selection_buttons()

    def enable_all_buttons(self):
        self.enable_process_button()
        self.enable_selection_buttons()

    def run(self):
        self.root.mainloop()
