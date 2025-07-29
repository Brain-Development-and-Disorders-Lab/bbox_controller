"""
Filename: timeline_models.py
Author: Henry Burgess
Date: 2025-03-07
Description: Timeline models for device-side experiment execution
License: MIT
"""

from typing import Dict, Any, Optional
from shared.models import TrialConfig, ExperimentConfig, ExperimentTimeline

class TrialFactory:
    """Factory for creating trial objects from timeline data"""

    def __init__(self):
        self.trial_types = {
            "Stage1": "Stage1",
            "Stage2": "Stage2",
            "Stage3": "Stage3",
            "Interval": "Interval"
        }

    def create_trial(self, trial_type: str, parameters: Dict[str, Any], **kwargs):
        """Create a trial object from type and parameters"""
        if trial_type not in self.trial_types:
            raise ValueError(f"Unknown trial type: {trial_type}")

        # Import trial classes dynamically to avoid circular imports
        if trial_type == "Stage1":
            from device.core.trials import Stage1
            return Stage1(**parameters, **kwargs)
        elif trial_type == "Stage2":
            from device.core.trials import Stage2
            return Stage2(**parameters, **kwargs)
        elif trial_type == "Stage3":
            from device.core.trials import Stage3
            return Stage3(**parameters, **kwargs)
        elif trial_type == "Interval":
            from device.core.trials import Interval
            return Interval(**parameters, **kwargs)
        else:
            raise ValueError(f"Unsupported trial type: {trial_type}")

    def is_valid_trial_type(self, trial_type: str) -> bool:
        """Check if a trial type is valid"""
        return trial_type in self.trial_types

class TimelineProcessor:
    """Processor for handling timeline operations on the device"""

    def __init__(self, device):
        self.device = device
        self.current_timeline: Optional[ExperimentTimeline] = None
        self.trial_factory = TrialFactory()

    def process_timeline_upload(self, timeline_data: Dict[str, Any]) -> tuple[bool, str]:
        """Process a timeline upload from the control panel"""
        try:
            # Create timeline from data
            timeline = ExperimentTimeline.from_dict(timeline_data)

            # Validate timeline
            is_valid, errors = timeline.validate()
            if not is_valid:
                error_msg = "Timeline validation failed: " + "; ".join(errors)
                return False, error_msg

            # Store timeline
            self.current_timeline = timeline
            return True, "Timeline validated and stored successfully"

        except Exception as e:
            return False, f"Timeline processing error: {str(e)}"

    def execute_timeline(self, animal_id: str) -> tuple[bool, str]:
        """Execute the current timeline with the given animal ID"""
        if not self.current_timeline:
            return False, "No timeline available for execution"

        try:
            # Convert timeline to trial objects
            trials = []
            trial_configs = []  # Store configurations for looping
            for trial_data in self.current_timeline.trials:
                trial = self.trial_factory.create_trial(
                    trial_data.type,
                    trial_data.parameters,
                    screen=self.device.screen,
                    font=self.device.font,
                    width=self.device.width,
                    height=self.device.height,
                    io=self.device.io,
                    display=self.device.display,
                    statistics=self.device.statistics_controller
                )
                trials.append(trial)

                # Store configuration for looping
                trial_configs.append({
                    "type": trial_data.type,
                    "kwargs": trial_data.parameters
                })

            # Start experiment with timeline
            self.device.start_experiment_with_timeline(animal_id, trials, self.current_timeline.config, self.current_timeline.loop, trial_configs)
            return True, f"Timeline '{self.current_timeline.name}' started successfully"

        except Exception as e:
            return False, f"Timeline execution error: {str(e)}"

    def get_current_timeline(self) -> Optional[ExperimentTimeline]:
        """Get the current timeline"""
        return self.current_timeline

    def clear_timeline(self):
        """Clear the current timeline"""
        self.current_timeline = None
