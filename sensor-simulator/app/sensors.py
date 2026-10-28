"""Emulated soil-moisture sensor.

`is_up` is the "hardware status" bool of the prototype: True -> the sensor publishes
readings, False -> it goes silent (exactly what a dead sensor looks like from the backend).
"""
import random


class SimulatedSensor:
    def __init__(self, sensor_id: str, rng: random.Random, anomaly_probability: float = 0.0):
        self.sensor_id = sensor_id
        self.is_up = True
        self.value = rng.uniform(25.0, 65.0)   # soil moisture, %
        self._rng = rng
        self._anomaly_probability = anomaly_probability

    def next_value(self) -> float:
        """Mean-reverting random walk around 45% with noise, plus rare spikes."""
        if self._rng.random() < self._anomaly_probability:
            return round(self._rng.choice([3.0, 97.0]), 2)    # injected glitch, not stored in the walk
        self.value += 0.05 * (45.0 - self.value) + self._rng.gauss(0, 2.5)
        self.value = min(100.0, max(0.0, self.value))
        return round(self.value, 2)
