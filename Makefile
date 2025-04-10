
default:
	@echo "Call a specific subcommand:"
	@echo
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null\
	| awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}'\
	| sort\
	| egrep -v -e '^[^[:alnum:]]' -e '^$@$$'
	@echo
	@exit 1

.state/docker-build-base: Dockerfile requirements.txt
	# Build our base container for this project.
	docker compose build --force-rm base

	# Collect static assets
	docker compose run --rm web python manage.py collectstatic --noinput

	# Mark the state so we don't rebuild this needlessly.
	mkdir -p .state
	touch .state/docker-build-base

.state/db-migrated:
	make migrate
	mkdir -p .state && touch .state/db-migrated

.state/db-initialized: .state/docker-build-base .state/db-migrated
        # Do anything you might need to after the DB is built/migrated here (like fixtures)

	# Mark the state so we don't reload after first launch.
	mkdir -p .state
	touch .state/db-initialized

serve: .state/db-initialized
	docker compose up --remove-orphans -d

shell: .state/db-initialized
	docker compose run --rm web /bin/bash

dbshell: .state/db-initialized
	docker compose exec postgres psql -U clabot clabot

manage: .state/db-initialized
	# Run Django manage to accept arbitrary arguments
	docker compose run --rm web ./manage.py $(filter-out $@,$(MAKECMDGOALS))

migrations: .state/db-initialized
	# Run Django makemigrations
	docker compose run --rm web ./manage.py makemigrations

migrate: .state/docker-build-base
	# Run Django migrate
	docker compose run --rm web ./manage.py migrate $(filter-out $@,$(MAKECMDGOALS))

lint: .state/docker-build-base
	docker compose run --rm base isort --check-only .
	docker compose run --rm base black --check .
	docker compose run --rm base flake8

reformat: .state/docker-build-base
	docker compose run --rm base isort .
	docker compose run --rm base black .

test: .state/docker-build-base
	docker compose run --rm web pytest --cov --reuse-db --no-migrations
	docker compose run --rm web python -m coverage html --show-contexts
	docker compose run --rm web python -m coverage report -m

check: test lint

clean:
	docker compose down -v
	rm -rf staticroot
	rm -f .state/docker-build-base
	rm -f .state/db-initialized
	rm -f .state/db-migrated
