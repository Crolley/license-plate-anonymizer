import os
import threading
import shutil
from tkinter import filedialog, messagebox


class LicensePlateBlurController:

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.selected_files = []
        self.selected_folder = None
        self.processing = False
        self.setup_event_handlers()

    def setup_event_handlers(self):
        self.view.set_select_files_command(self.on_select_files)
        self.view.set_select_folder_command(self.on_select_folder)
        self.view.set_process_command(self.on_start_processing)

    def on_select_files(self):
        files = filedialog.askopenfilenames(
            title="Sélectionnez des images",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png"),
                ("Tous les fichiers", "*.*")
            ]
        )

        if files:
            self.selected_files = list(files)
            self.selected_folder = None
            count = len(self.selected_files)
            self.view.update_selection_label(f"{count} image(s) sélectionnée(s)", color="green")
            self.view.enable_process_button()

    def on_select_folder(self):
        folder = filedialog.askdirectory(title="Sélectionnez un dossier")

        if folder:
            self.selected_folder = folder
            self.selected_files = []
            image_count = sum(1 for _, _, files in os.walk(folder)
                            for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png')))
            folder_name = os.path.basename(folder)
            self.view.update_selection_label(f"Dossier: {folder_name} ({image_count} images)", color="green")
            self.view.enable_process_button()

    def on_start_processing(self):
        if self.processing:
            return

        if not self.selected_files and not self.selected_folder:
            messagebox.showwarning("Attention", "Veuillez sélectionner des images ou un dossier")
            return

        self.processing = True
        self.view.disable_all_buttons()

        thread = threading.Thread(target=self.process_images)
        thread.daemon = True
        thread.start()

    def progress_callback(self, current, total, filename):
        self.view.update_status_label(f"Traitement: {filename} ({current}/{total})", color="blue")
        progress_value = (current / total) * 100
        self.view.update_progress(progress_value)

    def process_images(self):
        try:
            self.view.update_status_label("Chargement du modèle...", color="blue")
            self.model.load_model()

            if self.selected_files:
                images = self.model.collect_images_from_files(self.selected_files)
            elif self.selected_folder:
                images = self.model.collect_images_from_folder(self.selected_folder)
            else:
                raise ValueError("Aucune sélection")

            if not images:
                raise ValueError("Aucune image trouvée")

            output_dir = "temp_output"
            success_count = self.model.process_batch(images, output_dir, progress_callback=self.progress_callback)

            self.view.update_status_label("Création du fichier ZIP...", color="blue")

            zip_path = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip")],
                initialfile="images_floutees.zip"
            )

            if zip_path:
                self.model.create_zip(output_dir, zip_path)
                shutil.rmtree(output_dir)
                self.view.update_status_label(f"✅ Terminé! {success_count} image(s) traitée(s)", color="green")
                self.view.reset_progress()
                messagebox.showinfo("Succès", f"Traitement terminé!\n\n{success_count} image(s) traitée(s)\nFichier: {zip_path}")
            else:
                shutil.rmtree(output_dir)
                self.view.update_status_label("Annulé", color="gray")
                self.view.reset_progress()

        except Exception as e:
            self.view.update_status_label(f"❌ Erreur: {str(e)}", color="red")
            self.view.reset_progress()
            messagebox.showerror("Erreur", f"Une erreur est survenue:\n{str(e)}")

        finally:
            self.processing = False
            self.view.enable_all_buttons()

    def run(self):
        self.view.run()
