PYTHON=python

test:
	${PYTHON} -m pytest

lint:
	${PYTHON} -m pylint potemkin

dist: clean
	${PYTHON} setup.py sdist bdist_wheel

clean:
	rm -rf dist build potemkin_decorator.egg-info

pypi: dist
	${PYTHON} -m twine upload dist/*
