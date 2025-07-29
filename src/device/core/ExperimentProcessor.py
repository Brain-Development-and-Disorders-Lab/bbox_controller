from typing import Any, Dict, Optional

from device.core.TrialFactory import TrialFactory
from shared.models import Experiment


class ExperimentProcessor:
    """Processor for receiving an experiment file and executing the timeline on the device"""

    def __init__(self, device):
        self.device = device
        self.current_experiment: Optional[Experiment] = None
        self.trial_factory = TrialFactory()

    def process_experiment_upload(self, experiment_data: Dict[str, Any]) -> tuple[bool, str]:
        """Process an experiment upload from the control panel"""
        try:
            # Create experiment from data
            experiment = Experiment.from_dict(experiment_data)

            # Validate experiment
            is_valid, errors = experiment.validate()
            if not is_valid:
                error_msg = "Experiment validation failed: " + "; ".join(errors)
                return False, error_msg

            # Store experiment
            self.current_experiment = experiment

            # Update device's experiment config to match the new experiment
            self.device.config = experiment.config

            return True, "Experiment validated and stored successfully"

        except Exception as e:
            return False, f"Experiment processing error: {str(e)}"

    def execute_experiment(self, animal_id: str) -> tuple[bool, str]:
        """Execute the current experiment with the given animal ID"""
        if not self.current_experiment:
            return False, "No experiment available for execution"

        try:
            # Convert experiment to trial objects
            trials = []
            trial_configs = []
            for trial_data in self.current_experiment.trials:
                trial = self.trial_factory.create_trial(
                    trial_data.type,
                    trial_data.parameters,
                    screen=self.device.screen,
                    font=self.device.font,
                    width=self.device.width,
                    height=self.device.height,
                    io=self.device.io,
                    display=self.device.display,
                    statistics=self.device.statistics_controller,
                    config=self.current_experiment.config
                )
                trials.append(trial)

                trial_configs.append({
                    "type": trial_data.type,
                    "kwargs": trial_data.parameters
                })

            # Start experiment with experiment
            self.device.start_experiment_with_timeline(animal_id, trials, self.current_experiment.config, self.current_experiment.loop, trial_configs)
            return True, f"Experiment '{self.current_experiment.name}' started successfully"

        except Exception as e:
            return False, f"Experiment execution error: {str(e)}"
