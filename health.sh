#!/usr/bin/env bash

uvx ruff check --fix --unsafe-fixes
uvx ruff format
uvx --with types-requests --with types-beautifulsoup4 mypy .
