"""Irrigation Planner (FR-4, FR-8, TNF-1.3, TNF-2.2).

  rules.py     the if/else decision (stand-in for the PID / rule engine)
  anomaly.py   flags implausible readings (FR-8)
  planner.py   periodic cycle: collect inputs (with last-valid-value fallback) -> decide
"""
