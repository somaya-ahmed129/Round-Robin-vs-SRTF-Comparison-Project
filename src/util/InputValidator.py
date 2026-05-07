"""
InputValidator.py
-----------------
Validates all user input before it reaches the schedulers.
Raises ValidationError with a human-readable message on failure.
"""


class ValidationError(Exception):
    pass


def validate_processes(processes: list) -> list:
    if not processes:
        raise ValidationError("Please add at least one process.")

    seen_ids = set()
    for i, p in enumerate(processes):
        for key in ("pid", "arrival", "burst"):
            if key not in p:
                raise ValidationError(f"Process {i+1}: field '{key}' is missing.")

        pid     = str(p["pid"]).strip()
        arrival = p["arrival"]
        burst   = p["burst"]

        # PID validation
        if not pid.isdigit():
          raise ValidationError( f"Process {i+1}: PID must be a positive integer.")

        if int(pid) <= 0:
           raise ValidationError(f"Process {i+1}: PID must be greater than zero." )

        if not pid:
            raise ValidationError(f"Process {i+1}: PID cannot be empty.")
        if pid in seen_ids:
            raise ValidationError(f"Duplicate PID '{pid}'. Each process must have a unique ID.")
        seen_ids.add(pid)

        if not isinstance(arrival, (int, float)):
            raise ValidationError(f"Process '{pid}': arrival time must be a number.")
        if arrival < 0:
            raise ValidationError(f"Process '{pid}': arrival time cannot be negative.")
        if arrival != int(arrival):
            raise ValidationError(f"Process '{pid}': arrival time must be a whole number.")

        if not isinstance(burst, (int, float)):
            raise ValidationError(f"Process '{pid}': burst time must be a number.")
        if burst <= 0:
            raise ValidationError(f"Process '{pid}': burst time must be greater than zero.")
        if burst != int(burst):
            raise ValidationError(f"Process '{pid}': burst time must be a whole number.")

    return [{"pid": str(p["pid"]).strip(),
             "arrival": int(p["arrival"]),
             "burst":   int(p["burst"])} for p in processes]


def validate_quantum(quantum) -> int:
    if quantum is None or str(quantum).strip() == "":
        raise ValidationError("Time quantum is required for Round Robin.")
    try:
        q = float(quantum)
    except (ValueError, TypeError):
        raise ValidationError("Time quantum must be a number.")
    if q <= 0:
        raise ValidationError("Time quantum must be greater than zero.")
    if q != int(q):
        raise ValidationError("Time quantum must be a whole number.")
    return int(q)