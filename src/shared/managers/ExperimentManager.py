"""
Filename: shared/managers/ExperimentManager.py
Author: Henry Burgess
Date: 2025-07-29
Description: Manager for experiments, handles saving and loading experiments from the 'experiments' directory
License: MIT
"""

import json
import os
from typing import List, Optional
from ..models import Experiment

class ExperimentManager:
    """Manages experiment storage and retrieval"""

    def __init__(self, experiments_dir: str = "experiments"):
        self.experiments_dir = experiments_dir
        self._check_experiments_dir()
        self._load_experiments()

    def _check_experiments_dir(self):
        """Ensure the 'experiments' directory exists"""
        if not os.path.exists(self.experiments_dir):
            os.makedirs(self.experiments_dir)

    def _load_experiments(self):
        """Load all experiments from the directory"""
        self.experiments = {}
        if os.path.exists(self.experiments_dir):
            for filename in os.listdir(self.experiments_dir):
                if filename.endswith('.json'):
                    name = filename[:-5]
                    try:
                        with open(os.path.join(self.experiments_dir, filename), 'r') as f:
                            experiment_data = json.load(f)
                            self.experiments[name] = Experiment.from_dict(experiment_data)
                    except Exception as e:
                        print(f"Error loading experiment {name}: {e}")

    def save_experiment(self, experiment: Experiment) -> bool:
        """Save an experiment to disk"""
        try:
            # Update modified time
            experiment.update_modified_time()

            filename = os.path.join(self.experiments_dir, f"{experiment.name}.json")
            with open(filename, 'w') as f:
                f.write(experiment.to_json())
            self.experiments[experiment.name] = experiment
            return True
        except Exception as e:
            print(f"Error saving experiment {experiment.name}: {e}")
            return False

    def load_experiment(self, name: str) -> Optional[Experiment]:
        """Load an experiment by name"""
        return self.experiments.get(name)

    def list_experiments(self) -> List[str]:
        """List all available experiment names"""
        return list(self.experiments.keys())

    def create_experiment(self, name: str, description: str = "") -> Experiment:
        """Create a new experiment"""
        experiment = Experiment(name=name, description=description)
        self.experiments[name] = experiment
        return experiment
