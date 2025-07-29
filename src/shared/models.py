"""
Shared dataclass models for bbox_controller project
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

    def __post_init__(self):
        """Load configuration from file if not explicitly set"""
        # Only load from global config if all values are still the original defaults
        # This prevents overwriting values that were explicitly set (e.g., from JSON)
        if (self.iti_minimum == 100 and self.iti_maximum == 1000 and
            self.response_limit == 1000 and self.cue_minimum == 5000 and
            self.cue_maximum == 10000 and self.hold_minimum == 100 and
            self.hold_maximum == 1000 and self.valve_open == 100 and
            self.punish_time == 1000):

            # Import config_manager locally to avoid circular imports
            from .managers.config_manager import config_manager
            config = config_manager.load_config()
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)


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
    loop: bool = False  # Whether to loop the timeline when completed

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

    def add_trial(self, trial_type: str, parameters: Dict[str, Any] = None,
                  trial_id: str = None, description: str = "") -> str:
        """Add a trial to the timeline"""
        if trial_id is None:
            trial_id = f"{trial_type}_{len(self.trials)}"

        if parameters is None:
            parameters = {}

        trial = TrialConfig(
            type=trial_type,
            id=trial_id,
            parameters=parameters,
            description=description
        )
        self.trials.append(trial)
        self.modified_at = datetime.now().isoformat()
        return trial_id

    def remove_trial(self, trial_id: str) -> bool:
        """Remove a trial from the timeline"""
        for i, trial in enumerate(self.trials):
            if trial.id == trial_id:
                self.trials.pop(i)
                self.modified_at = datetime.now().isoformat()
                return True
        return False

    def move_trial(self, trial_id: str, new_index: int) -> bool:
        """Move a trial to a new position"""
        for i, trial in enumerate(self.trials):
            if trial.id == trial_id:
                if 0 <= new_index < len(self.trials):
                    trial = self.trials.pop(i)
                    self.trials.insert(new_index, trial)
                    self.modified_at = datetime.now().isoformat()
                    return True
        return False

    def get_trial(self, trial_id: str) -> Optional[TrialConfig]:
        """Get a trial by ID"""
        for trial in self.trials:
            if trial.id == trial_id:
                return trial
        return None

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
            "modified_at": self.modified_at,
            "loop": self.loop
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
            modified_at=data.get("modified_at", ""),
            loop=data.get("loop", False)
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
