"""
Timeline management for bbox_controller project
"""

import json
import os
from typing import List, Optional
from ..models import ExperimentTimeline


class TimelineManager:
    """Manages timeline storage and retrieval"""

    def __init__(self, timelines_dir: str = "timelines"):
        self.timelines_dir = timelines_dir
        self._ensure_timelines_dir()
        self._load_timelines()

    def _ensure_timelines_dir(self):
        """Ensure the timelines directory exists"""
        if not os.path.exists(self.timelines_dir):
            os.makedirs(self.timelines_dir)

    def _load_timelines(self):
        """Load all timelines from the directory"""
        self.timelines = {}
        if os.path.exists(self.timelines_dir):
            for filename in os.listdir(self.timelines_dir):
                if filename.endswith('.json'):
                    name = filename[:-5]  # Remove .json extension
                    try:
                        with open(os.path.join(self.timelines_dir, filename), 'r') as f:
                            timeline_data = json.load(f)
                            self.timelines[name] = ExperimentTimeline.from_dict(timeline_data)
                    except Exception as e:
                        print(f"Error loading timeline {name}: {e}")

    def save_timeline(self, timeline: ExperimentTimeline) -> bool:
        """Save a timeline to disk"""
        try:
            filename = os.path.join(self.timelines_dir, f"{timeline.name}.json")
            with open(filename, 'w') as f:
                f.write(timeline.to_json())
            self.timelines[timeline.name] = timeline
            return True
        except Exception as e:
            print(f"Error saving timeline {timeline.name}: {e}")
            return False

    def load_timeline(self, name: str) -> Optional[ExperimentTimeline]:
        """Load a timeline by name"""
        return self.timelines.get(name)

    def delete_timeline(self, name: str) -> bool:
        """Delete a timeline from disk and memory"""
        try:
            filename = os.path.join(self.timelines_dir, f"{name}.json")
            if os.path.exists(filename):
                os.remove(filename)
            if name in self.timelines:
                del self.timelines[name]
            return True
        except Exception as e:
            print(f"Error deleting timeline {name}: {e}")
            return False

    def list_timelines(self) -> List[str]:
        """List all available timeline names"""
        return list(self.timelines.keys())

    def create_timeline(self, name: str, description: str = "") -> ExperimentTimeline:
        """Create a new timeline"""
        timeline = ExperimentTimeline(name=name, description=description)
        self.timelines[name] = timeline
        return timeline
