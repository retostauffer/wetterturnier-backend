#!/bin/bash

pyscript=$1
source venv/bin/activate

cd PythonPackage && python setup.py install
cd ..
if [ -n "$pyscript" ]
then
	python ${pyscript}
	ls
else
	which python
	ls
fi
