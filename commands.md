docker exec -it viwork_backend /bin/bash

alembic revision --autogenerate -m ""

alembic upgrade head

alembic stamp head

alembic heads

alembic downgrade -1

alembic merge -m "merge multiple heads" <> <>

docker compose run --rm migrations
