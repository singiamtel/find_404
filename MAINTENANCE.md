# Creating a new version

```bash
uv version --bump [major|minor|patch]
NEW_VERSION="$(uv version | cut -d" " -f2)"
git tag v$NEW_VERSION
git push --tags
gh release create v$NEW_VERSION -t "Release $NEW_VERSION" --notes-from-tag
```
