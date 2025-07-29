"""
Filename: experiment_editor.py
Author: Henry Burgess
Date: 2025-03-07
Description: Experiment editor UI component
License: MIT
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional
try:
    from shared.models import Experiment, Config
    from shared.managers import ExperimentManager
    from shared.constants import AVAILABLE_TRIAL_TYPES
except ImportError:
    # Fallback for when running as standalone script
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from shared.models import Experiment, Config
    from shared.managers import ExperimentManager
    from shared.constants import AVAILABLE_TRIAL_TYPES

class ExperimentEditor(tk.Toplevel):
    """Experiment editor window for creating and editing experiments"""

    def __init__(self, parent, experiment_manager: ExperimentManager,
                 on_experiment_save: Optional[Callable] = None):
        super().__init__(parent)
        self.parent = parent
        self.experiment_manager = experiment_manager
        self.on_experiment_save = on_experiment_save
        self.current_experiment: Optional[Experiment] = None

        # Configure window
        self.title("Experiment Editor")
        self.geometry("640x600")
        self.resizable(False, False)

        # Center window on parent
        self.transient(parent)
        self.grab_set()

        # Configure consistent styling
        self.configure(bg="#f0f0f0")

        # Create UI
        self.create_widgets()
        self.create_layout()

        # Bind events
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self, padding="10")

        # Experiment info section
        self.info_frame = ttk.LabelFrame(self.main_frame, text="Experiment Information", padding="10")

        # Name and description
        ttk.Label(self.info_frame, text="Name:", font="Arial 10").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self.info_frame, textvariable=self.name_var, width=30, font="Arial 10")
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=5)

        ttk.Label(self.info_frame, text="Description:", font="Arial 10").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(self.info_frame, textvariable=self.description_var, width=45, font="Arial 10")
        self.description_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=5)

        # Loop checkbox
        self.loop_var = tk.BooleanVar()
        self.loop_checkbox = ttk.Checkbutton(
            self.info_frame,
            text="Loop experiment when completed",
            variable=self.loop_var
        )
        self.loop_checkbox.grid(row=2, column=0, columnspan=2, sticky="w", padx=(0, 10), pady=5)

        # Left column - Trial management
        self.left_frame = ttk.LabelFrame(self.main_frame, text="Timeline Management", padding="10")

        # Trial list
        ttk.Label(self.left_frame, text="Trials:", font="Arial 10 bold").pack(anchor="w", pady=(0, 5))

        # Trial listbox with scrollbar
        listbox_frame = ttk.Frame(self.left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.trial_listbox = tk.Listbox(listbox_frame, height=12, font="Arial 10", selectmode=tk.SINGLE)
        self.trial_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.trial_listbox.yview)
        self.trial_listbox.configure(yscrollcommand=self.trial_scrollbar.set)

        self.trial_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.trial_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind trial selection
        self.trial_listbox.bind('<<ListboxSelect>>', self.on_trial_selected)

        # Trial control buttons
        ttk.Label(self.left_frame, text="Controls:", font="Arial 10 bold").pack(anchor="w", pady=(0, 5))

        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.add_trial_button = tk.Button(button_frame, text="Add Trial", font="Arial 10", command=self.add_trial, width=10)
        self.add_trial_button.grid(row=0, column=0, padx=(0, 5), pady=(0, 5))

        self.remove_trial_button = tk.Button(button_frame, text="Remove Trial", font="Arial 10", command=self.remove_trial, width=10)
        self.remove_trial_button.grid(row=0, column=1, padx=(5, 0), pady=(0, 5))

        self.move_up_button = tk.Button(button_frame, text="Move Up", font="Arial 10", command=self.move_trial_up, width=10)
        self.move_up_button.grid(row=1, column=0, padx=(0, 5), pady=(5, 0))

        self.move_down_button = tk.Button(button_frame, text="Move Down", font="Arial 10", command=self.move_trial_down, width=10)
        self.move_down_button.grid(row=1, column=1, padx=(5, 0), pady=(5, 0))

        # Right column - Experiment configuration
        self.right_frame = ttk.LabelFrame(self.main_frame, text="Experiment Configuration", padding="10")

        # Create config widgets
        self.config_widgets = {}
        config_fields = [
            ("iti_minimum", "ITI Minimum (ms):", 100),
            ("iti_maximum", "ITI Maximum (ms):", 1000),
            ("response_limit", "Response Limit (ms):", 1000),
            ("cue_minimum", "Cue Minimum (ms):", 5000),
            ("cue_maximum", "Cue Maximum (ms):", 10000),
            ("hold_minimum", "Hold Minimum (ms):", 100),
            ("hold_maximum", "Hold Maximum (ms):", 1000),
            ("valve_open", "Valve Open (ms):", 100),
            ("punish_time", "Punishment Time (ms):", 1000)
        ]

        for i, (field, label, default) in enumerate(config_fields):
            ttk.Label(self.right_frame, text=label, font="Arial 10").grid(row=i, column=0, sticky="w", padx=(0, 10), pady=3)
            var = tk.StringVar(value=str(default))
            entry = ttk.Entry(self.right_frame, textvariable=var, width=15, font="Arial 10")
            entry.grid(row=i, column=1, sticky="w", padx=(0, 10), pady=3)
            self.config_widgets[field] = var

        # Add reset config button
        ttk.Label(self.right_frame, text="", font="Arial 10").grid(row=len(config_fields), column=0, sticky="w", pady=(5, 0))
        self.reset_config_button = tk.Button(self.right_frame, text="Reset to Defaults", font="Arial 10", command=self.reset_config_to_defaults, width=15)
        self.reset_config_button.grid(row=len(config_fields), column=1, sticky="w", padx=(0, 10), pady=(5, 0))

        # Validation section
        ttk.Label(self.right_frame, text="Validation:", font="Arial 10 bold").grid(row=len(config_fields)+1, column=0, sticky="w", pady=(10, 5))
        self.validation_text = tk.Text(self.right_frame, height=4, wrap=tk.WORD, font="Arial 10")
        self.validation_text.grid(row=len(config_fields)+2, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        # Bottom action buttons
        self.action_frame = ttk.Frame(self.main_frame)

        self.new_button = tk.Button(self.action_frame, text="New", font="Arial 10", command=self.new_experiment, width=8)
        self.new_button.pack(side=tk.LEFT, padx=(0, 5))

        self.load_button = tk.Button(self.action_frame, text="Load", font="Arial 10", command=self.load_experiment, width=8)
        self.load_button.pack(side=tk.LEFT, padx=(0, 5))

        self.save_button = tk.Button(self.action_frame, text="Save", font="Arial 10", command=self.save_experiment, width=8)
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))

        self.export_button = tk.Button(self.action_frame, text="Export", font="Arial 10", command=self.export_experiment, width=8)
        self.export_button.pack(side=tk.LEFT, padx=(0, 5))

    def create_layout(self):
        """Create the layout of the UI"""
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=0)  # Fixed width for trial management
        self.main_frame.columnconfigure(1, weight=1)  # Expandable for experiment parameters
        self.main_frame.rowconfigure(1, weight=1)

        # Info frame (spans both columns)
        self.info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.info_frame.columnconfigure(1, weight=1)

        # Left column
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.left_frame.configure(width=250)  # Set fixed width for trial management

        # Right column
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        self.right_frame.columnconfigure(1, weight=1)

        # Action buttons at bottom (spans both columns)
        self.action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # Initialize with empty experiment
        self.new_experiment()

    def new_experiment(self):
        """Create a new experiment"""
        # Create experiment with default config
        config = Config()
        self.current_experiment = Experiment(name="New Experiment", config=config)
        self.update_ui()

    def load_experiment(self):
        """Load an existing experiment"""
        experiment_names = self.experiment_manager.list_experiments()
        if not experiment_names:
            messagebox.showinfo("No Experiments", "No saved experiments found.")
            return

        # Create a simple dialog to select experiment
        dialog = tk.Toplevel(self)
        dialog.title("Load Experiment")
        dialog.geometry("260x180")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Select an experiment to load:", font="Arial 9").pack(pady=8)

        listbox = tk.Listbox(dialog, height=8, font="Arial 9")
        listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        for name in experiment_names:
            listbox.insert(tk.END, name)

        def on_load():
            selection = listbox.curselection()
            if selection:
                experiment_name = listbox.get(selection[0])
                experiment = self.experiment_manager.load_experiment(experiment_name)
                if experiment:
                    self.current_experiment = experiment
                    self.update_ui()
                    dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=8, pady=8)

        tk.Button(button_frame, text="Load", font="Arial 9", command=on_load, width=8).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Cancel", font="Arial 9", command=on_cancel, width=8).pack(side=tk.RIGHT, padx=4)

    def save_experiment(self):
        """Save the current experiment"""
        if not self.current_experiment:
            return

        # Update experiment from UI
        self.update_experiment_from_ui()

        # Validate experiment
        is_valid, errors = self.current_experiment.validate()
        if not is_valid:
            error_msg = "Experiment validation failed:\n" + "\n".join(errors)
            messagebox.showerror("Validation Error", error_msg)
            return

        # Save experiment
        if self.experiment_manager.save_experiment(self.current_experiment):
            messagebox.showinfo("Success", f"Experiment '{self.current_experiment.name}' saved successfully.")
            if self.on_experiment_save:
                self.on_experiment_save(self.current_experiment)
        else:
            messagebox.showerror("Error", "Failed to save experiment.")

    def export_experiment(self):
        """Export experiment to a file"""
        if not self.current_experiment:
            return

        # Update experiment from UI
        self.update_experiment_from_ui()

        # Validate experiment
        is_valid, errors = self.current_experiment.validate()
        if not is_valid:
            error_msg = "Experiment validation failed:\n" + "\n".join(errors)
            messagebox.showerror("Validation Error", error_msg)
            return

        # Get save file path
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Experiment"
        )

        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(self.current_experiment.to_json())
                messagebox.showinfo("Success", f"Experiment exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export experiment: {str(e)}")

    def add_trial(self):
        """Add a new trial to the timeline"""
        if not self.current_experiment:
            return

        # Create dialog to select trial type
        dialog = tk.Toplevel(self)
        dialog.title("Add Trial")
        dialog.geometry("340x220")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg="#f0f0f0")

        # Main frame with reduced padding
        main_frame = ttk.Frame(dialog, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Select trial type:", font="Arial 10 bold").pack(pady=(0, 6))

        # Trial type selection
        ttk.Label(main_frame, text="Trial Type:", font="Arial 9").pack(anchor="w", pady=(0, 2))
        trial_type_var = tk.StringVar()
        trial_type_combo = ttk.Combobox(main_frame, textvariable=trial_type_var,
                                       values=list(AVAILABLE_TRIAL_TYPES.keys()), state="readonly", font="Arial 9")
        trial_type_combo.pack(fill=tk.X, pady=(0, 8))

        # Trial ID entry
        ttk.Label(main_frame, text="Trial ID:", font="Arial 9").pack(anchor="w", pady=(0, 2))
        trial_id_var = tk.StringVar()
        trial_id_entry = ttk.Entry(main_frame, textvariable=trial_id_var, font="Arial 9")
        trial_id_entry.pack(fill=tk.X, pady=(0, 8))

        # Auto-generate trial ID when trial type changes
        def on_trial_type_change(event=None):
            trial_type = trial_type_var.get()
            if trial_type:
                # Generate a unique ID based on trial type and count
                existing_trials = [t for t in self.current_experiment.timeline.trials if t.type == trial_type]
                trial_id = f"{trial_type}_{len(existing_trials)}"
                trial_id_var.set(trial_id)

        trial_type_combo.bind('<<ComboboxSelected>>', on_trial_type_change)

        # Trial description entry
        ttk.Label(main_frame, text="Description (optional):", font="Arial 9").pack(anchor="w", pady=(0, 2))
        trial_desc_var = tk.StringVar()
        trial_desc_entry = ttk.Entry(main_frame, textvariable=trial_desc_var, font="Arial 9")
        trial_desc_entry.pack(fill=tk.X, pady=(0, 12))

        def on_add():
            trial_type = trial_type_var.get()
            if not trial_type:
                messagebox.showerror("Error", "Please select a trial type.")
                return

            trial_id = trial_id_var.get().strip()
            if not trial_id:
                messagebox.showerror("Error", "Trial ID is required.")
                return

            description = trial_desc_var.get().strip()

            # Get default parameters for the trial type
            default_params = AVAILABLE_TRIAL_TYPES[trial_type]["default_parameters"].copy()

            # Add trial to timeline
            self.current_experiment.timeline.add_trial(trial_type, default_params, trial_id, description)
            # Update UI to reflect the new trial
            self.update_ui()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(8, 0))

        tk.Button(button_frame, text="Add", font="Arial 9", command=on_add, width=8).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(button_frame, text="Cancel", font="Arial 9", command=on_cancel, width=8).pack(side=tk.RIGHT, padx=(5, 0))

    def remove_trial(self):
        """Remove the selected trial"""
        if not self.current_experiment:
            return

        selection = self.trial_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a trial to remove.")
            return

        index = selection[0]
        if 0 <= index < len(self.current_experiment.timeline.trials):
            trial = self.current_experiment.timeline.trials[index]
            if messagebox.askyesno("Confirm", f"Remove trial '{trial.id}'?"):
                self.current_experiment.timeline.remove_trial(trial.id)
                # Update UI to reflect the removed trial
                self.update_ui()

    def move_trial_up(self):
        """Move the selected trial up"""
        if not self.current_experiment:
            return

        selection = self.trial_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index > 0:
            trial = self.current_experiment.timeline.trials[index]
            self.current_experiment.timeline.move_trial(trial.id, index - 1)
            # Update UI to reflect the moved trial
            self.update_ui()
            self.trial_listbox.selection_set(index - 1)

    def move_trial_down(self):
        """Move the selected trial down"""
        if not self.current_experiment:
            return

        selection = self.trial_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self.current_experiment.timeline.trials) - 1:
            trial = self.current_experiment.timeline.trials[index]
            self.current_experiment.timeline.move_trial(trial.id, index + 1)
            # Update UI to reflect the moved trial
            self.update_ui()
            self.trial_listbox.selection_set(index + 1)

    def on_trial_selected(self, event=None):
        """Handle trial selection in listbox"""
        # For now, just update validation
        self.update_validation()

    def update_ui(self):
        """Update the UI to reflect the current experiment"""
        if not self.current_experiment:
            return

        # Update experiment info
        self.name_var.set(self.current_experiment.name)
        self.description_var.set(self.current_experiment.description)
        self.loop_var.set(self.current_experiment.loop)

        # Update trial list
        self.trial_listbox.delete(0, tk.END)
        for trial in self.current_experiment.timeline.trials:
            self.trial_listbox.insert(tk.END, f"{trial.id} ({trial.type})")

        # Update configuration - use experiment's own config values
        for field, var in self.config_widgets.items():
            value = getattr(self.current_experiment.config, field, 0)
            var.set(str(value))

        # Update validation
        self.update_validation()

    def update_experiment_from_ui(self):
        """Update the experiment from UI values"""
        if not self.current_experiment:
            return

        # Update experiment info
        self.current_experiment.name = self.name_var.get().strip()
        self.current_experiment.description = self.description_var.get().strip()
        self.current_experiment.loop = self.loop_var.get()

        # Update configuration - save UI values to experiment config
        for field, var in self.config_widgets.items():
            try:
                value = int(var.get())
                setattr(self.current_experiment.config, field, value)
            except ValueError:
                # Keep existing value if invalid
                pass

    def reset_config_to_defaults(self):
        """Reset all configuration fields to their default values"""
        default_config = Config()
        for field, var in self.config_widgets.items():
            value = getattr(default_config, field, 0)
            var.set(str(value))
        messagebox.showinfo("Configuration Reset", "All configuration fields have been reset to their default values.")
        self.update_validation() # Re-validate after reset

    def update_validation(self):
        """Update the validation display"""
        if not self.current_experiment:
            self.validation_text.delete(1.0, tk.END)
            return

        # Validate experiment
        is_valid, errors = self.current_experiment.validate()

        self.validation_text.delete(1.0, tk.END)
        if is_valid:
            self.validation_text.insert(tk.END, "✔ Experiment is valid")
        else:
            self.validation_text.insert(tk.END, "✗ Experiment validation failed:\n")
            for error in errors:
                self.validation_text.insert(tk.END, f"• {error}\n")

    def on_close(self):
        """Handle window close"""
        self.destroy()
