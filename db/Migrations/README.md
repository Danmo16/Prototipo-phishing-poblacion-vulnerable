# **Database migrations**

This directory will contain Alembic migration scripts. Once you configure
Alembic in your project (via **alembic init**), the versioned migration
files will live here. To create your first migration after defining the
models in **core/domain/models.py**, run the following command from the
project root:

> alembic init db/migrations


Then edit the **alembic.ini** to point at your database URL and the
**env.py** file to import the SQLAlchemy **Base** and your models. You can
generate an initial migration with:

> alembic revision --autogenerate -m "initial schema"


For more information, see Alembic's documentation.