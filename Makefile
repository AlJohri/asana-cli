.PHONY: install clean build upload

clean:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf build
	rm -rf dist

install:
	pip install --upgrade -q pipenv
	pipenv install --dev

build:
	pipenv run python setup.py sdist bdist_wheel

upload:
	pipenv run twine upload dist/*
