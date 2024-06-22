"""Convert poetry.lock to requirements.txt."""

import sys

import toml
from packaging.specifiers import SpecifierSet
from packaging.version import Version


def is_compatible_version(version: str, specifiers: str) -> bool:
    """Check if the version is compatible with the specifiers."""
    if specifiers == "*":
        return True
    return SpecifierSet(specifiers).contains(version)  # type: ignore[no-any-return]


def poetry_lock_to_requirements(
    python_version: str, poetry_lock_path: str, requirements_path: str
) -> None:
    """Convert poetry.lock to requirements.txt."""
    with open(poetry_lock_path, "r") as f:
        lock_data = toml.load(f)

    latest_versions = {}

    for package in lock_data["package"]:
        name = package["name"]
        version = package["version"]
        python_versions = package.get("python-versions", "*")

        if is_compatible_version(python_version, python_versions):
            if name not in latest_versions:
                latest_versions[name] = version
            else:
                if Version(version) > Version(latest_versions[name]):
                    latest_versions[name] = version

    requirements = [f"{name}=={version}" for name, version in latest_versions.items()]

    with open(requirements_path, "w") as f:
        f.write("\n".join(requirements))


def main() -> None:
    """Entry point."""
    poetry_lock_to_requirements(
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "poetry.lock",
        "requirements.txt",
    )


if __name__ == "__main__":
    main()
