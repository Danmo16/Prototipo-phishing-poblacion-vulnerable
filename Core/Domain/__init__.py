"""Top-level package for domain models.

Importing this package will expose the SQLAlchemy base class and the main
ORM models used throughout the application. This helps keep model
definitions centralized and easy to import in other parts of the codebase.
"""

from .models import Base, Campaign, Template, Segment, Target, Event  # noqa: F401