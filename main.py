import os
import shutil
import zipfile
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, simpledialog

class ZipCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zip Creator")
        self.root.minsize(800,500)

        # File listbox and scrollbar
        self.files_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Define button configurations as a dictionary
        buttons = {
            "Add File": self.add_file,
            "Add Folder": self.add_folder,
            "Create File": self.create_file,
            "Create Folder": self.create_folder,
            "Remove File": self.remove_file,
            "Remove Folder": self.remove_folder,
            "Rename File": self.rename_file,
            "Rename Folder": self.rename_folder,
            "Undo": self.undo_action,
            "Redo": self.redo_action,
        }

        for i, (text, command) in enumerate(buttons.items()):
            btn = tk.Button(button_frame, text=text, command=command)
            btn.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)

        # Configure grid columns to have equal weight
        for i in range(len(buttons)):
            button_frame.grid_columnconfigure(i, weight=1)

        # "Create Archive" button
        tk.Button(root, text="Create Archive", command=self.create_archive).pack(fill=tk.X, padx=10, pady=5)

        # "New Archive" button
        tk.Button(root, text="New Archive", command=self.new_archive).pack(fill=tk.X, padx=10, pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        # Stats Label
        self.stats_label = tk.Label(root, text="Stats: 0 items selected")
        self.stats_label.pack(pady=5)

        # Archive Size Label
        self.size_label = tk.Label(root, text="Archive Size: 0 KB")
        self.size_label.pack(pady=5)

        # Internal state
        self.items = []  # List of (path, display_name)
        self.clipboard = []  # Clipboard for copy/paste functionality
        self.undo_stack = []  # Undo stack for changes
        self.redo_stack = []  # Redo stack for changes

        # Bind shortcuts
        self.root.bind("<Control-c>", lambda e: self.copy_selected())
        self.root.bind("<Control-v>", lambda e: self.paste_content())

    def update_stats(self):
        self.stats_label.config(text=f"Stats: {len(self.items)} items selected")

    def update_archive_size(self):
        size = sum(os.path.getsize(item[0]) for item in self.items if item[0] and os.path.isfile(item[0]))
        self.size_label.config(text=f"Archive Size: {size:,} KB")

    def add_file(self):
        # Open the file dialog to select a file to add
        file_path = filedialog.askopenfilename(title="Select a file to add")
        if not file_path:
            return  # If no file was selected, exit the function
        
        # If there are any folders in the archive, prompt the user to place the file in one
        folder_name = self.prompt_folder()

        # Get the file name to display in the list
        file_name = os.path.basename(file_path)
        display_name = f"{folder_name}/{file_name}" if folder_name else file_name

        # Add the selected file to the list of items and display in the listbox
        self.items.append((file_path, display_name))
        self.files_listbox.insert(tk.END, display_name)
        
        self.save_state()
        self.update_stats()
        self.update_archive_size()
        messagebox.showinfo("Success", f"File '{file_name}' added successfully.")

    def add_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_name = os.path.basename(folder_path)
            parent_folder = self.prompt_folder()
            display_name = f"{parent_folder}/{folder_name}" if parent_folder else folder_name
            self.items.append((folder_path, display_name))
            self.files_listbox.insert(tk.END, display_name)
            self.save_state()
            self.update_stats()
            self.update_archive_size()

    def create_file(self):
        # File name input
        filename_label = tk.Label(self.root, text="Filename:")
        filename_label.pack(pady=5)
        
        file_name_entry = tk.Entry(self.root, font=("Arial", 14))
        file_name_entry.insert(0, "example.txt")  # Default filename example
        file_name_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # File content input with ability to change entry size
        content_label = tk.Label(self.root, text="File content:")
        content_label.pack(pady=5)
        
        file_content_text = tk.Text(self.root, wrap=tk.WORD, height=10, font=("Arial", 12))
        file_content_text.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        
        # Function to save the file
        def save_file():
            file_name = file_name_entry.get().strip()
            if not file_name:
                messagebox.showerror("Error", "File name cannot be empty.")
                return

            content = file_content_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showerror("Error", "File content cannot be empty.")
                return

            folder_name = self.prompt_folder()

            file_path = os.path.join(os.getcwd(), file_name)
            try:
                with open(file_path, "w") as f:
                    f.write(content)

                display_name = f"{folder_name}/{file_name}" if folder_name else file_name
                self.items.append((file_path, display_name))
                self.files_listbox.insert(tk.END, display_name)
                self.save_state()
                self.update_stats()
                self.update_archive_size()
                messagebox.showinfo("Success", f"File '{file_name}' created successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create file: {e}")

        # Button to trigger save action
        save_button = tk.Button(self.root, text="Save File", command=save_file)
        save_button.pack(pady=10)

        # Optionally, a button to cancel file creation
        cancel_button = tk.Button(self.root, text="Cancel", command=lambda: self.root.quit())
        cancel_button.pack(pady=5)

    def create_folder(self):
        folder_name = simpledialog.askstring("Folder Name", "Enter folder name:")
        if not folder_name:
            return
        parent_folder = self.prompt_folder()

        display_name = f"{parent_folder}/{folder_name}" if parent_folder else folder_name
        self.items.append((None, display_name))  # Pseudo-path for folder
        self.files_listbox.insert(tk.END, display_name)
        self.save_state()
        self.update_stats()
        self.update_archive_size()

    def rename_file(self):
        # Get the list of files from the items list
        file_names = [display_name for path, display_name in self.items if os.path.isfile(path)]
        
        if not file_names:
            messagebox.showerror("Error", "No files available to rename.")
            return

        # Prompt the user to select a file from the dropdown
        file_to_rename = simpledialog.askstring("Rename File", f"Available files: {', '.join(file_names)}")
        
        if file_to_rename not in file_names:
            messagebox.showerror("Error", "Invalid file selected.")
            return
        
        # Get the new name for the selected file
        new_name = simpledialog.askstring("New Name", "Enter new file name:")
        if not new_name:
            return

        # Find the file and rename it
        for index, (path, display_name) in enumerate(self.items):
            if display_name == file_to_rename:
                try:
                    new_path = os.path.join(os.path.dirname(path), new_name)
                    os.rename(path, new_path)
                    self.items[index] = (new_path, new_name)  # Update the item with new path and name
                    self.update_listbox()  # Update the listbox to reflect the changes
                    messagebox.showinfo("Success", f"File renamed to {new_name}.")
                    self.save_state()  # Save the state for undo
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename file: {e}")
                return

    def rename_folder(self):
        # Get the list of folders from the items list
        folder_names = [display_name for path, display_name in self.items if path is None or os.path.isdir(path)]
        
        if not folder_names:
            messagebox.showerror("Error", "No folders available to rename.")
            return

        # Prompt the user to select a folder from the dropdown
        folder_to_rename = simpledialog.askstring("Rename Folder", f"Available folders: {', '.join(folder_names)}")
        
        if folder_to_rename not in folder_names:
            messagebox.showerror("Error", "Invalid folder selected.")
            return
        
        # Get the new name for the selected folder
        new_name = simpledialog.askstring("New Name", "Enter new folder name:")
        if not new_name:
            return

        # Find the folder and rename it
        for index, (path, display_name) in enumerate(self.items):
            if display_name == folder_to_rename:
                try:
                    # For folders, we can't directly rename None, so we must handle the display name and folder path separately
                    if path is None:
                        new_display_name = new_name
                        self.items[index] = (None, new_display_name)  # Update display name for folders
                    else:
                        new_path = os.path.join(os.path.dirname(path), new_name)
                        os.rename(path, new_path)
                        self.items[index] = (new_path, new_name)  # Update the item with new path and name
                    
                    self.update_listbox()  # Update the listbox to reflect the changes
                    messagebox.showinfo("Success", f"Folder renamed to {new_name}.")
                    self.save_state()  # Save the state for undo
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename folder: {e}")
                return

    def remove_file(self):
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "No items selected.")
            return

        for index in reversed(selected_indices):
            del self.items[index]
            self.files_listbox.delete(index)

        self.save_state()
        self.update_stats()
        self.update_archive_size()

    def remove_folder(self):
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "No items selected.")
            return

        for index in reversed(selected_indices):
            path, display_name = self.items[index]
            if path is None or os.path.isdir(path):
                del self.items[index]
                self.files_listbox.delete(index)
            else:
                messagebox.showerror("Error", f"'{display_name}' is not a folder.")

        self.save_state()
        self.update_stats()
        self.update_archive_size()

    def undo_action(self):
        if not self.undo_stack:
            messagebox.showerror("Error", "Nothing to undo.")
            return
        self.redo_stack.append(list(self.items))
        self.items = self.undo_stack.pop()
        self.update_listbox()
        self.update_stats()
        self.update_archive_size()

    def redo_action(self):
        if not self.redo_stack:
            messagebox.showerror("Error", "Nothing to redo.")
            return
        self.undo_stack.append(list(self.items))
        self.items = self.redo_stack.pop()
        self.update_listbox()
        self.update_stats()
        self.update_archive_size()

    def update_listbox(self):
        self.files_listbox.delete(0, tk.END)
        for _, display_name in self.items:
            self.files_listbox.insert(tk.END, display_name)

    def save_state(self):
        self.undo_stack.append(list(self.items))
        self.redo_stack.clear()

    def new_archive(self):
        if not self.items:
            return

        if messagebox.askyesno("Warning", "This will clear all contents. Continue?"):
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.items.clear()
            self.files_listbox.delete(0, tk.END)
            self.save_state()
            self.update_stats()
            self.update_archive_size()

    def create_archive(self):
        if not self.items:
            messagebox.showerror("Error", "No files or folders to archive.")
            return

        archive_path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")])
        if not archive_path:
            return

        try:
            self.progress["maximum"] = len(self.items)
            self.progress["value"] = 0

            with zipfile.ZipFile(archive_path, "w") as archive:
                for idx, (path, display_name) in enumerate(self.items):
                    if path is None:
                        continue  # Skip pseudo-paths for folders
                    elif os.path.isdir(path):
                        for root, _, files in os.walk(path):
                            for file in files:
                                full_path = os.path.join(root, file)
                                archive.write(full_path, os.path.relpath(full_path, path))
                    else:
                        archive.write(path, display_name)

                    self.progress["value"] += 1
                    self.root.update_idletasks()

            self.progress["value"] = len(self.items)
            archive_size = os.path.getsize(archive_path) // 1024
            messagebox.showinfo("Success", f"Archive created at {archive_path} ({archive_size:,} KB)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create archive: {e}")
        finally:
            self.progress["value"] = 0

    def prompt_folder(self):
        current_folders = [item[1] for item in self.items if item[0] is None or os.path.isdir(item[0])]
        if not current_folders:
            return None

        selected_folder = simpledialog.askstring("Select Folder", f"Available folders: {', '.join(current_folders)}")
        return selected_folder if selected_folder in current_folders else None

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipCreatorApp(root)
    root.mainloop()
