# Creating a new version

>[!WARNING]
> Make sure that `pyproject.toml` and `__init__.py` match. The version bump script is not very resilient

```bash
uv run scripts/bump_version.py [major|minor|patch]
```

## TODO

- Make the bump script resilient to failures, and ideally atomic
    - Possibly use [bumpver](https://github.com/mbarkhau/bumpver) instead
