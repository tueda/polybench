# syntax=docker/dockerfile:1
FROM ubuntu:24.04 AS builder
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# Build tools for the adapters and their native dependencies.
# NOTE: m4 and make are needed for gmp-mpfr-sys
RUN apt-get update -o APT::Update::Error-Mode=any \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    autoconf=2.71* \
    autoconf-archive=20220903* \
    automake=1:1.16.* \
    binutils=2.42* \
    ca-certificates=20260816ubuntu* \
    cmake=3.28.* \
    curl=8.5.* \
    g++=4:13.* \
    gcc=4:13.* \
    git=1:2.43.* \
    libc6-dev=2.39* \
    libtool=2.4.* \
    m4=1.4.* \
    make=4.3* \
    openjdk-21-jdk-headless=21.* \
    pkg-config=1.8.* \
    python3=3.12.* \
    python3-pip=24.0* \
    tar=1.35* \
    unzip=6.0* \
    xz-utils=5.6.1+really5.4.* \
    zip=3.0* \
  && rm -rf /var/lib/apt/lists/*

# Install the pinned Rust toolchain.
RUN curl -fL https://static.rust-lang.org/dist/rust-1.99.1-x86_64-unknown-linux-gnu.tar.xz -o /tmp/rust.tar.xz \
  && echo '231fcae47ee950621374725b5fc3b5441d2fbda2955ac45dd7dc816d8876cfe7  /tmp/rust.tar.xz' | sha256sum -c - \
  && mkdir /tmp/rust \
  && tar -xJf /tmp/rust.tar.xz -C /tmp/rust --strip-components=1 \
  && /tmp/rust/install.sh --prefix=/opt/rust --components=rustc,cargo,rust-std-x86_64-unknown-linux-gnu --disable-ldconfig \
  && rm -rf /tmp/rust /tmp/rust.tar.xz

ENV PATH="/opt/rust/bin:${PATH}" \
  PYTHONPATH=/opt/polybench \
  PYTHONDONTWRITEBYTECODE=1 \
  CARGO_HOME=/cache/cargo GRADLE_USER_HOME=/cache/gradle VCPKG_ROOT=/cache/vcpkg \
  VCPKG_DISABLE_METRICS=1 \
  CFLAGS="-O2 -march=x86-64 -mtune=generic" \
  CXXFLAGS="-O2 -march=x86-64 -mtune=generic" \
  RUSTFLAGS="-C target-cpu=x86-64" \
  POLY_MOJO_PATH=/opt/polymojo/.pixi/envs/default/lib/mojo \
  MOJO_COMMAND=/opt/polybench/containers/mojo.sh \
  MODULAR_HOME=/opt/polymojo/.pixi/envs/default/share/max

# Use Ubuntu's Python; Poetry is only a separate build-time installation.
RUN python3 -m pip install --target=/opt/poetry --no-cache-dir \
  'https://files.pythonhosted.org/packages/63/d5/ee2ab176d0ee8c7f7e80af401812ca750576cf929f64cd9066b90379fd49/poetry-2.4.3-py3-none-any.whl#sha256=79ce90140d0dcded93bab2df97fdd26b433f6949d834b4ac7bb1951aaca65c2f'
WORKDIR /opt/polybench
COPY pyproject.toml poetry.lock ./
RUN PYTHONPATH=/opt/poetry POETRY_VIRTUALENVS_CREATE=false PIP_BREAK_SYSTEM_PACKAGES=1 \
    python3 -m poetry install --only main --no-root --no-interaction \
  && python3 -m pip check

# Keep the locked Mojo compiler and packages for additional variable counts.
RUN curl -fL https://github.com/prefix-dev/pixi/releases/download/v0.83.0/pixi-x86_64-unknown-linux-musl.tar.gz -o /tmp/pixi.tar.gz \
  && echo '064f371e692aaa3400ac581c89da2843c91437f20c2d9155395a5d0037f33551  /tmp/pixi.tar.gz' | sha256sum -c - \
  && tar -xzf /tmp/pixi.tar.gz -C /usr/local/bin pixi \
  && rm /tmp/pixi.tar.gz
COPY polybench/solvers/polymojo/pixi.toml polybench/solvers/polymojo/pixi.lock /opt/polymojo/
RUN pixi install --locked --manifest-path /opt/polymojo/pixi.toml
COPY polybench/ ./polybench/
COPY containers/mojo.sh ./containers/

# Prepare solvers through their existing adapters, at their runtime paths.
ARG BUILD_JOBS
RUN <<'BUILD'
set -eu
jobs=${BUILD_JOBS:-$(nproc)}
case "$jobs" in ''|*[!0-9]*|0) echo 'BUILD_JOBS must be a positive integer' >&2; exit 1 ;; esac
export CARGO_BUILD_JOBS="$jobs" CMAKE_BUILD_PARALLEL_LEVEL="$jobs" VCPKG_MAX_CONCURRENCY="$jobs"
export GRADLE_OPTS="-Dorg.gradle.workers.max=$jobs -Dorg.gradle.daemon=false"
mkdir -p /cache/build /cache/gradle/init.d

# The project manifest owns the vcpkg version and solver versions.
baseline=$(python3 -c 'import json; print(json.load(open("polybench/solvers/flint/vcpkg.json"))["builtin-baseline"])')
git init "$VCPKG_ROOT"
git -C "$VCPKG_ROOT" remote add origin https://github.com/microsoft/vcpkg.git
git -C "$VCPKG_ROOT" fetch --depth 1 origin "$baseline"
git -C "$VCPKG_ROOT" checkout --detach FETCH_HEAD
"$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics
cat >/cache/gradle/init.d/offline.gradle <<'GRADLE'
if (System.getenv('POLYBENCH_OFFLINE') == '1') {
    gradle.startParameter.offline = true
}
GRADLE

python3 -m polybench --build-directory /cache/build --output-directory /tmp/build-output \
  --build-only --fail-on-setup-failure --debug --flint --form --reform --rings --symbolica --polymojo --nvars 5
python3 -m polybench --build-directory /cache/build --output-directory /tmp/build-output \
  --build-only --fail-on-setup-failure --debug --polymojo --nvars 8
# Finish work interrupted by the adapter's timed rustc-version probe.
cargo build --manifest-path /cache/build/symbolica/Cargo.toml --release --locked

# FORM's official binary was downloaded by the adapter; it needs no writable tree.
cp /cache/build/form/*/form /usr/local/bin/form
rm -rf /cache/build/form

# Set permissions in this layer, without duplicating the new build trees.
chmod -R a+rwX /cache
chmod -R a+rX /opt/polybench /opt/polymojo
BUILD

FROM scratch AS singular-packages
# Singular's official packages for Ubuntu 24.04: 4.4.1-1 contains Singular 4.4.1p5 (44105).
ADD --checksum=sha256:c361865b69423e724d6dec372989bcfedff1250e5f857517ac1ff658bc07e06c https://www.singular.uni-kl.de/ftp/repo/ubuntu24/pool/main/s/singular41/singular41-bin_4.4.1-1_amd64.deb /tmp/singular41-bin.deb
ADD --checksum=sha256:7afc4c45a89e45b34cacffec0626b675cc4134ebd42f01f79d4b3bfe8ec4a967 https://www.singular.uni-kl.de/ftp/repo/ubuntu24/pool/main/s/singular41/singular41-common_4.4.1-1_all.deb /tmp/singular41-common.deb

FROM ubuntu:24.04 AS runtime
# Retain tools invoked by the adapters, including the Mojo driver linker.
# Mount Singular's installers so they never enter a runtime layer.
RUN --mount=type=bind,from=singular-packages,source=/tmp,target=/tmp/singular-packages \
  apt-get update -o APT::Update::Error-Mode=any \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    cmake=3.28.* \
    g++=4:13.* \
    git=1:2.43.* \
    make=4.3* \
    openjdk-21-jdk-headless=21.* \
    pkg-config=1.8.* \
    python3=3.12.* \
    /tmp/singular-packages/singular41-bin.deb /tmp/singular-packages/singular41-common.deb \
  && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/rust/bin:${PATH}" \
  PYTHONPATH=/opt/polybench \
  PYTHONDONTWRITEBYTECODE=1 \
  HOME=/home/polybench \
  MODULAR_CACHE_DIR=/home/polybench/.cache/modular \
  CARGO_HOME=/cache/cargo GRADLE_USER_HOME=/cache/gradle VCPKG_ROOT=/cache/vcpkg \
  VCPKG_DISABLE_METRICS=1 \
  CFLAGS="-O2 -march=x86-64 -mtune=generic" \
  CXXFLAGS="-O2 -march=x86-64 -mtune=generic" \
  RUSTFLAGS="-C target-cpu=x86-64" \
  POLY_MOJO_PATH=/opt/polymojo/.pixi/envs/default/lib/mojo \
  MOJO_COMMAND=/opt/polybench/containers/mojo.sh \
  MODULAR_HOME=/opt/polymojo/.pixi/envs/default/share/max

COPY --from=builder --exclude=bin/rustdoc --exclude=bin/rust-* --exclude=libexec /opt/rust /opt/rust
COPY --from=builder --exclude=**/tests /usr/local/lib/ /usr/local/lib/
COPY --from=builder /opt/polybench /opt/polybench
# Keep Mojo's compiler, packages and runtime dependencies for driver compilation.
# Filter directories so shared-library symlinks remain links, not duplicate files.
COPY --from=builder /opt/polymojo/.pixi/envs/default/bin/mojo /opt/polymojo/.pixi/envs/default/bin/mojo
COPY --from=builder --exclude=* --exclude=!mojo --exclude=!lib*Globals.so \
  --exclude=!libKGENCompilerRTShared.so --exclude=!libgcc_s.so* --exclude=!libstdc++.so* \
  /opt/polymojo/.pixi/envs/default/lib /opt/polymojo/.pixi/envs/default/lib
COPY --from=builder --exclude=* --exclude=!max --exclude=!licenses --exclude=max/cache \
  /opt/polymojo/.pixi/envs/default/share /opt/polymojo/.pixi/envs/default/share
# Preserve paths and timestamps for incremental builds. vcpkg's installed
# Release libraries suffice; its package staging trees and native build trees do not.
COPY --from=builder --exclude=flint/build/vcpkg_installed/*/debug /cache/build /cache/build
COPY --from=builder /cache/cargo /cache/cargo
COPY --from=builder --exclude=daemon --exclude=.tmp /cache/gradle /cache/gradle
COPY --from=builder --exclude=buildtrees --exclude=packages --exclude=downloads /cache/vcpkg /cache/vcpkg
# Omit CMake's interactive tools and manuals; keep modules and license notices.
COPY --from=builder --exclude=cmake-*/cmake-*/bin/ccmake --exclude=cmake-*/cmake-*/bin/cmake-gui \
  --exclude=cmake-*/cmake-*/doc/cmake/html --exclude=cmake-*/cmake-*/doc/cmake/CMake.qch \
  --exclude=cmake-*/cmake-*/man \
  /cache/vcpkg/downloads/tools /cache/vcpkg/downloads/tools
COPY --from=builder /usr/local/bin/form /usr/local/bin/form
COPY containers/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY containers/polybench.sh /usr/local/bin/polybench

# Java otherwise uses the passwd home directory when the UID matches an account.
ENV CARGO_NET_OFFLINE=true POLYBENCH_OFFLINE=1 \
  JAVA_TOOL_OPTIONS="-Duser.home=/home/polybench"
WORKDIR /work
# Give arbitrary Docker UIDs a writable HOME outside bind-mounted /work.
# COPY creates its destination directories with mode 755; these roots must
# also accept writes from an arbitrary runtime UID.
RUN mkdir -p "$HOME" \
  && chmod 1777 /work "$HOME" \
  && chmod a+rwx /cache/build /cache/cargo /cache/gradle /cache/vcpkg \
    /cache/vcpkg/downloads /cache/vcpkg/downloads/tools
USER 1000:1000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["polybench"]
