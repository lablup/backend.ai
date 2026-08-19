from typing import Final

SESSION_PRIORITY_DEFAULT: Final[int] = 10
SESSION_PRIORITY_MIN: Final[int] = 0
SESSION_PRIORITY_MAX: Final[int] = 100

# Scope-local preemption priority ranking a user's own sessions against each
# other, independent of the global scheduler ``priority``. Neutral baseline of
# 0 (Slurm nice / K8s PriorityClass style): higher preempts lower, and users
# may go below 0 to mark background work. No fixed range cap.
JOB_PRIORITY_DEFAULT: Final[int] = 0
