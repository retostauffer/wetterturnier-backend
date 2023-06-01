#!/bin/bash

pyscript=$1
source venv/bin/activate
alias python="python3"

cd PythonPackage && python setup.py install
cd ..
if [ -n "$pyscript" ]
then
	python ${pyscript}
	ls
else
	which python3
	ls
fi
