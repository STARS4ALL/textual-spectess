# To install just on a per-project basis
# 1. Activate your virtual environemnt
# 2. uv add --dev rust-just
# 3. Use just within the activated environment


# list all recipes
default:
    just --list

# Install tools globally
tools:
    uv tool install twine
    uv tool install ruff

# Add conveniente development dependencies
dev:
    uv add --dev pytest

# Build the package
build:
    rm -fr dist/*
    uv build

# Publish the package in (pypi|testpypi)
publish repo="pypi" : build
    twine upload --verbose -r {{ repo }} dist/*

# Adds lica source library as dependency version may be a tag or branch
lica version="main":
    #!/bin/env bash
    if [[ "{{ version }}" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]; then
        echo "Adding LICA source library --tag {{ version }}"; 
        uv add git+https://github.com/guaix-ucm/lica --tag {{ version }};
    else
        echo "Adding LICA source library --branch {{ version }}";
        uv add git+https://github.com/guaix-ucm/lica --branch {{ version }};
    fi

