FROM python:3.10-alpine3.16
LABEL org.opencontainers.image.source="https://github.com/DataDog/guarddog/"
RUN apk add --update gcc musl-dev  # gcc and musl-dev needed for the pip install
RUN pip install poetry  # poetry is used for python package management
WORKDIR /app
ADD . .
RUN poetry config virtualenvs.create false  # no need for a virtual env in a docker container
RUN poetry install --no-interaction  # install dependencies listed in pyproject.toml
RUN rm -rf /root/.cache/pypoetry  # slim down final container
ENTRYPOINT ["python", "-m", "guarddog"]