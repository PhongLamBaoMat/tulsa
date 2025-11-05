FROM python:3.13-slim AS requirements

RUN apt update
RUN apt install -y --no-install-recommends build-essential gcc
RUN python -m pip install --no-cache-dir --upgrade uv

WORKDIR /src
COPY pyproject.toml uv.lock ./
RUN uv export --format requirements-txt -o /src/requirements.txt

FROM python:3.13-slim AS app

RUN adduser appuser
WORKDIR /app
USER appuser:appuser

COPY --from=requirements /src/requirements.txt .
COPY . .

RUN pip install --no-cache-dir --user -r requirements.txt

CMD [ "python", "-m", "tulsa" ]