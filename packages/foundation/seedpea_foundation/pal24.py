"""Public PAL 2.4 finite-adaptation entry points."""

from .pal24_profile import (
    PROFILE,
    RESOURCE_PROFILE,
    RESUME_PROFILE,
    review_pal24_resources,
    review_pal24_resume,
)

__all__ = [
    "PROFILE",
    "RESOURCE_PROFILE",
    "RESUME_PROFILE",
    "review_pal24_resources",
    "review_pal24_resume",
]
