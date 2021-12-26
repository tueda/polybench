FROM ubuntu:focal

# NOTE: m4 and make are needed for gmp-mpfr-sys
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  cargo \
  openjdk-11-jdk-headless=11.0.* \
  form=4.2.* \
  m4=1.4.* \
  make=4.2.* \
  python3-pip=20.0.* \
  singular-ui=1:4.1.* \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --upgrade 'pip<20.4' \
  && pip3 install --no-cache-dir \
  'poetry<2' \
  && poetry config virtualenvs.create false

WORKDIR /polybench

COPY \
  poetry.lock \
  pyproject.toml \
  ./

RUN poetry install --no-dev --no-interaction --no-root \
  && rm -rf ~/.cache/pypoetry/artifacts ~/.cache/pypoetry/cache

COPY run.sh ./
COPY polybench/ ./polybench/
