"""
Filename: shared/models.py
Author: Henry Burgess
Date: 2025-07-29
Description: Shared '@dataclass' models for shared classes between the device and control panel
License: MIT
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from version import VERSION

@dataclass
class Trial:
    """A single trial in the experiment timeline"""
    type: str
    id: str
    parameters: Dict[str, Any]
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert trial to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trial':
        """Create trial from dictionary"""
        return cls(**data)

@dataclass
class Timeline:
    """A sequence of trials that make up an experiment timeline"""
    trials: List[Trial] = None

    def __post_init__(self):
        if self.trials is None:
            self.trials = []

    def add_trial(self, trial_type: str, parameters: Dict[str, Any] = None,
                  trial_id: str = None, description: str = "") -> str:
        """Add a trial to the timeline"""
        trial = Trial(
            type=trial_type,
            id=trial_id,
            parameters=parameters,
            description=description
        )
        self.trials.append(trial)
        return trial_id

    def remove_trial(self, trial_id: str) -> bool:
        """Remove a trial from the timeline"""
        for i, trial in enumerate(self.trials):
            if trial.id == trial_id:
                self.trials.pop(i)
                return True
        return False

    def move_trial(self, trial_id: str, new_index: int) -> bool:
        """Move a trial to a new position"""
        for i, trial in enumerate(self.trials):
            if trial.id == trial_id:
                if 0 <= new_index < len(self.trials):
                    trial = self.trials.pop(i)
                    self.trials.insert(new_index, trial)
                    return True
        return False

    def get_trial(self, trial_id: str) -> Optional[Trial]:
        """Get a trial by ID"""
        for trial in self.trials:
            if trial.id == trial_id:
                return trial
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert timeline to dictionary"""
        return {
            "trials": [trial.to_dict() for trial in self.trials]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Timeline':
        """Create timeline from dictionary"""
        trials = [Trial.from_dict(trial_data) for trial_data in data.get("trials", [])]
        return cls(trials=trials)

@dataclass
class Config:
    """Experiment-wide configuration parameters"""
    iti_minimum: int = 100
    iti_maximum: int = 1000
    response_limit: int = 1000
    cue_minimum: int = 5000
    cue_maximum: int = 10000
    hold_minimum: int = 100
    hold_maximum: int = 1000
    valve_open: int = 100
    punish_time: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary"""
        return cls(**data)

@dataclass
class Experiment:
    """Complete experiment definition with timeline and config"""
    name: str
    timeline: Timeline = None
    config: Config = None
    description: str = ""
    version: str = VERSION
    metadata: Dict[str, Any] = None
    created_at: str = ""
    modified_at: str = ""
    loop: bool = False

    def __post_init__(self):
        if self.timeline is None:
            self.timeline = Timeline()
        if self.config is None:
            self.config = Config()
        if self.metadata is None:
            self.metadata = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = datetime.now().isoformat()

    @property
    def trials(self) -> List[Trial]:
        """Direct access to timeline trials for device compatibility"""
        return self.timeline.trials

    def update_modified_time(self):
        """Update the modified timestamp"""
        self.modified_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert experiment to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "trials": [trial.to_dict() for trial in self.timeline.trials],
            "config": self.config.to_dict(),
            "description": self.description,
            "version": self.version,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "loop": self.loop
        }

    def to_json(self) -> str:
        """Convert experiment to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experiment':
        """Create experiment from dictionary"""
        trials = [Trial.from_dict(trial_data) for trial_data in data.get("trials", [])]
        timeline = Timeline(trials=trials)
        config = Config.from_dict(data.get("config", {}))
        experiment = cls(
            name=data["name"],
            timeline=timeline,
            config=config,
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            loop=data.get("loop", False)
        )

        return experiment

    @classmethod
    def from_json(cls, json_str: str) -> 'Experiment':
        """Create experiment from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate the experiment structure"""
        errors = []

        # Check required fields
        if not self.name.strip():
            errors.append("Experiment name is required")

        if not self.timeline.trials:
            errors.append("Experiment must contain at least one trial")

        # Validate each trial
        trial_ids = set()
        for i, trial in enumerate(self.timeline.trials):
            if not trial.type:
                errors.append(f"Trial {i+1}: Type is required")

            if not trial.id:
                errors.append(f"Trial {i+1}: ID is required")
            elif trial.id in trial_ids:
                errors.append(f"Trial {i+1}: Duplicate trial ID '{trial.id}'")
            else:
                trial_ids.add(trial.id)

        return len(errors) == 0, errors
