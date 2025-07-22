"""
Filename: timeline_models.py
Author: Henry Burgess
Date: 2025-03-07
Description: Timeline models for device-side experiment execution
License: MIT
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class TrialConfig:
    """Configuration for a single trial"""
    type: str
    id: str
    parameters: Dict[str, Any]
    description: str = ""

@dataclass
class ExperimentConfig:
    """Configuration for the entire experiment"""
    iti_minimum: int = 100
    iti_maximum: int = 1000
    response_limit: int = 1000
    cue_minimum: int = 5000
    cue_maximum: int = 10000
    hold_minimum: int = 100
    hold_maximum: int = 1000
    valve_open: int = 100
    punish_time: int = 1000

@dataclass
class ExperimentTimeline:
    """Complete experiment timeline definition"""
    name: str
    version: str = "1.0"
    description: str = ""
    trials: List[TrialConfig] = None
    config: ExperimentConfig = None
    metadata: Dict[str, Any] = None
    created_at: str = ""
    modified_at: str = ""

    def __post_init__(self):
        if self.trials is None:
            self.trials = []
        if self.config is None:
            self.config = ExperimentConfig()
        if self.metadata is None:
            self.metadata = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert timeline to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "trials": [asdict(trial) for trial in self.trials],
            "config": asdict(self.config),
            "metadata": self.metadata,
            "created_at": self.created_at,
            "modified_at": self.modified_at
        }

    def to_json(self) -> str:
        """Convert timeline to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentTimeline':
        """Create timeline from dictionary"""
        # Convert trial data back to TrialConfig objects
        trials = []
        for trial_data in data.get("trials", []):
            trial = TrialConfig(**trial_data)
            trials.append(trial)

        # Convert config data back to ExperimentConfig object
        config_data = data.get("config", {})
        config = ExperimentConfig(**config_data)

        timeline = cls(
            name=data["name"],
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            trials=trials,
            config=config,
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", "")
        )
        return timeline

    @classmethod
    def from_json(cls, json_str: str) -> 'ExperimentTimeline':
        """Create timeline from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate the timeline structure"""
        errors = []

        # Check required fields
        if not self.name.strip():
            errors.append("Timeline name is required")

        if not self.trials:
            errors.append("Timeline must contain at least one trial")

        # Validate each trial
        trial_ids = set()
        for i, trial in enumerate(self.trials):
            if not trial.type:
                errors.append(f"Trial {i+1}: Type is required")

            if not trial.id:
                errors.append(f"Trial {i+1}: ID is required")
            elif trial.id in trial_ids:
                errors.append(f"Trial {i+1}: Duplicate trial ID '{trial.id}'")
            else:
                trial_ids.add(trial.id)

        return len(errors) == 0, errors

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
            from device.trials import Stage1
            return Stage1(**parameters, **kwargs)
        elif trial_type == "Stage2":
            from device.trials import Stage2
            return Stage2(**parameters, **kwargs)
        elif trial_type == "Stage3":
            from device.trials import Stage3
            return Stage3(**parameters, **kwargs)
        elif trial_type == "Interval":
            from device.trials import Interval
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
            for trial_data in self.current_timeline.trials:
                trial = self.trial_factory.create_trial(
                    trial_data.type,
                    trial_data.parameters,
                    screen=self.device.screen,
                    font=self.device.font,
                    width=self.device.width,
                    height=self.device.height,
                    io=self.device.io,
                    display=self.device.display
                )
                trials.append(trial)

            # Start experiment with timeline
            self.device.start_experiment_with_timeline(animal_id, trials, self.current_timeline.config)
            return True, f"Timeline '{self.current_timeline.name}' started successfully"

        except Exception as e:
            return False, f"Timeline execution error: {str(e)}"

    def get_current_timeline(self) -> Optional[ExperimentTimeline]:
        """Get the current timeline"""
        return self.current_timeline

    def clear_timeline(self):
        """Clear the current timeline"""
        self.current_timeline = None

# Available trial types for validation
AVAILABLE_TRIAL_TYPES = {
    "Stage1": {
        "description": "Basic lever press training stage",
        "default_parameters": {
            "cue_duration": 5000,
            "response_limit": 1000,
            "water_delivery_duration": 2000
        }
    },
    "Stage2": {
        "description": "Advanced lever press stage with visual cues",
        "default_parameters": {
            "cue_duration": 5000,
            "response_limit": 1000,
            "water_delivery_duration": 2000
        }
    },
    "Stage3": {
        "description": "Complex decision-making stage",
        "default_parameters": {
            "cue_duration": 5000,
            "response_limit": 1000,
            "water_delivery_duration": 2000
        }
    },
    "Interval": {
        "description": "Inter-trial interval",
        "default_parameters": {
            "duration": 800
        }
    }
}
