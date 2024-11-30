import os
import zipfile
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

class ZipCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zip Creator")

        # Make the window resizable
        self.root.minsize(500, 500)
        self.root.geometry("500x500")

        # Configure the columns to have equal weight
        for i in range(3):
            self.root.grid_columnconfigure(i, weight=1)
        for i in range(7):
            self.root.grid_rowconfigure(i, weight=1)

        # File listbox and scrollbar
        self.files_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)
        self.files_listbox.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

        # Buttons arranged in a single row with equal size
        button_frame = tk.Frame(root)
        button_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        for i in range(4):  # Four buttons
            button_frame.grid_columnconfigure(i, weight=1)

        # Add buttons
        tk.Button(button_frame, text="Add File", command=self.add_file).grid(row=0, column=0, sticky="ew", padx=5, ipadx=50)
        tk.Button(button_frame, text="Add Folder", command=self.add_folder).grid(row=0, column=1, sticky="ew", padx=5, ipadx=50)
        tk.Button(button_frame, text="Replace File", command=self.replace_file).grid(row=0, column=2, sticky="ew", padx=5, ipadx=50)
        tk.Button(button_frame, text="Remove File", command=self.remove_file).grid(row=0, column=3, sticky="ew", padx=5, ipadx=50)

        tk.Button(root, text="Remove All Contents", command=self.remove_all).grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        tk.Button(root, text="Create Archive", command=self.create_archive).grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

        # Stats Label
        self.stats_label = tk.Label(root, text="Stats: 0 items selected")
        self.stats_label.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Archive type radio buttons
        self.archive_type = tk.StringVar(value="zip")
        tk.Radiobutton(root, text="ZIP", variable=self.archive_type, value="zip").grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        tk.Radiobutton(root, text="RAR", variable=self.archive_type, value="rar").grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        tk.Radiobutton(root, text="7Z", variable=self.archive_type, value="7z").grid(row=5, column=2, padx=5, pady=5, sticky="ew")

        # Progress bar
        tk.Label(root, text="Progress:").grid(row=6, column=0, sticky="ew", padx=10, pady=5)
        self.progress = ttk.Progressbar(root, orient="horizontal", length=100, mode="determinate")
        self.progress.grid(row=6, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

        # Internal state
        self.items = []  # Keeps track of full paths (files and folders) with display names

    def update_stats(self):
        total_size = 0  # Total size in bytes
        for item in self.items:
            if os.path.isfile(item[0]):
                total_size += os.path.getsize(item[0])

        # Convert size to KB
        self.total_size_kb = total_size / 1024
        self.stats_label.config(text=f"Stats: {len(self.items)} items selected, Estimated size: {self.total_size_kb:.2f} KB")

    def add_file(self):
        file_paths = filedialog.askopenfilenames()
        if file_paths:
            for file_path in file_paths:
                file_name = os.path.basename(file_path)  # Display file name only
                self.items.append((file_path, file_name))  # Store full path and display name
                self.files_listbox.insert(tk.END, file_name)
            self.update_stats()

    def add_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_name = os.path.basename(folder_path)
            
            # Add the folder itself to the list
            self.items.append((folder_path, folder_name))  # Full path, Display name

            # Add the folder contents
            for root, _, files in os.walk(folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, folder_path)
                    display_name = f"{folder_name}/{relative_path}"  # Display name as {folder_name}/{file}
                    self.items.append((full_path, display_name))  # Full path, Display name
                    self.files_listbox.insert(tk.END, display_name)

            self.update_stats()

    def replace_file(self):
        if not self.items:
            messagebox.showerror("Error", "File list is empty.")
            return
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "No file selected to replace.")
            return
        new_file = filedialog.askopenfilename()
        if new_file:
            new_file_name = os.path.basename(new_file)  # Get the new file's display name
            for index in selected_indices:
                # Replace the selected item with the new file, maintaining the tuple structure
                self.items[index] = (new_file, new_file_name)
                # Update the listbox display
                self.files_listbox.delete(index)
                self.files_listbox.insert(index, new_file_name)
            self.update_stats()

    def remove_file(self):
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "No file selected to remove.")
            return
        for index in reversed(selected_indices):
            del self.items[index]
            self.files_listbox.delete(index)
        self.update_stats()

    def remove_all(self):
        self.items.clear()
        self.files_listbox.delete(0, tk.END)
        self.update_stats()

    def create_archive(self):
        if not self.items:
            messagebox.showerror("Error", "File list is empty.")
            return

        filetypes = [(f"{self.archive_type.get().upper()} Archive", f"*.{self.archive_type.get()}")]
        archive_path = filedialog.asksaveasfilename(filetypes=filetypes, defaultextension=self.archive_type.get())

        if archive_path:
            try:
                # Set progress bar maximum to the number of items
                self.progress["maximum"] = len(self.items)
                self.progress["value"] = 0

                # Simulate compression speed based on file size
                speed_factor = max(0.05, min(1, 100 / self.total_size_kb)) if self.total_size_kb > 0 else 0.1

                with zipfile.ZipFile(archive_path, 'w') as archive:
                    for idx, item in enumerate(self.items, 1):
                        full_path, display_name = item
                        if os.path.isdir(full_path):
                            archive.write(full_path, display_name)
                        else:
                            archive.write(full_path, display_name)

                        # Update progress bar with a delay proportional to the speed factor
                        self.progress["value"] = idx
                        self.root.update_idletasks()
                        self.root.after(int(speed_factor * 100))

                messagebox.showinfo("Success", f"Archive created at {archive_path}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while creating the archive: {e}")
            finally:
                self.progress["value"] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipCreatorApp(root)
    root.mainloop()
