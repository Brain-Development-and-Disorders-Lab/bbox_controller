from enum import Enum
import random
from typing import Optional

import numpy as np


class ExitStatus(str, Enum):
  """
  Exit codes for trials.
  """
  SUCCESS = "success"
  FAILURE_NOSEPORT = "failure_noseport"
  FAILURE_NOLEVER = "failure_nolever"
  FAILURE_TIMEOUT = "failure_timeout"
  FAILURE_OTHER = "failure_other"
  CANCELLED = "cancelled"

class Randomness:
  """
  A class for generating reproducible random values with configurable seeds.
  Supports exponential distribution for ITI generation.
  """

  def __init__(self, seed: Optional[int] = None):
    """
    Initialize the random generator with an optional seed.

    Args:
        seed: Optional seed for reproducible random sequences
    """
    self.seed = seed
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    self._random_state = random.Random(seed)
    self._np_random_state = np.random.RandomState(seed)

  def set_seed(self, seed: int):
    """
    Set a new seed for the random generator.

    Args:
        seed: New seed value
    """
    self.seed = seed
    self._random_state.seed(seed)
    self._np_random_state.seed(seed)

  def generate_iti(self, min: float = 1000, max: float = 10000,
                          decay: float = 0.001) -> float:
    """
    Generate a random inter-trial interval (ITI) using exponential distribution.

    Args:
        min: Minimum ITI duration in milliseconds
        max: Maximum ITI duration in milliseconds
        decay: Decay constant for exponential distribution (lambda)
                        Higher values = faster decay, more values near min
                        Lower values = slower decay, more uniform distribution

    Returns:
        Random ITI duration in milliseconds
    """
    # Generate uniform random value between 0 and 1
    u = self._np_random_state.uniform(0, 1)

    # Use inverse transform sampling for truncated exponential distribution
    # We want an exponential distribution truncated to [min, max]
    # The CDF of truncated exponential is: F(x) = (1 - exp(-lambda * (x - min))) / (1 - exp(-lambda * (max - min)))
    # The inverse is: x = min - ln(1 - u * (1 - exp(-lambda * (max - min)))) / lambda

    # Calculate the normalization factor
    normalization = 1 - np.exp(-decay * (max - min))

    # Generate the truncated exponential value
    mapped_value = min - np.log(1 - u * normalization) / decay
    mapped_value = int(mapped_value)

    return mapped_value
