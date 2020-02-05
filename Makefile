.PHONY: install flush

install:
	pip install --upgrade pip
	pip install --upgrade setuptools
	pip install -r requirements.txt

flush:
	pip freeze | xargs pip uninstall -y
