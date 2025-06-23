# define an alias for the specific python version used in this file.
FROM docker.io/python:3.12.11-slim-bookworm AS python

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=local

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg dependencies
  libpq-dev

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN pip wheel --wheel-dir /usr/src/app/wheels \
  -r ${BUILD_ENVIRONMENT}.txt


# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}


# devcontainer dependencies and playwright requirements
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential libpq-dev sudo git bash-completion nano ssh \
    wait-for-it gettext \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxcb1 libxkbcommon0 libatspi2.0-0 libx11-6 \
    libxcomposite1 libxdamage1 libxext6 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 \
  && rm -rf /var/lib/apt/lists/*

# Create devcontainer user and add it to sudoers
RUN groupadd --gid 1000 dev-user \
  && useradd --uid 1000 --gid dev-user --shell /bin/bash --create-home dev-user \
  && echo "dev-user ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/dev-user \
  && chmod 0440 /etc/sudoers.d/dev-user

# Install Python dependencies
COPY --from=python-build-stage /usr/src/app/wheels /wheels

# Permissions for the wheels directory to dev-user
RUN chown -R dev-user:dev-user /wheels

# Install Python dependencies from wheels
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
 && rm -rf /wheels

# Copy entrypoint and start scripts
COPY ./compose/production/django/entrypoint /entrypoint
COPY ./compose/local/django/start      /start
RUN sed -i 's/\r$//g' /entrypoint /start \
  && chmod +x /entrypoint /start

# Set the user to dev-user
USER dev-user

# Install playwright and playwright browsers
RUN pip install --no-cache-dir pytest-playwright playwright \
  && python -m playwright install --with-deps

# copy application code to WORKDIR
COPY . ${APP_HOME}

ENTRYPOINT ["/entrypoint"]
