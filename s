#!/bin/bash

pyscript=$1
source venv/bin/activate

cd PythonPackage && python3 setup.py install
cd ..
if [ -n "$pyscript" ]
then
	python ${pyscript}
	ls
else
	which python3
	ls
fi

alias python="python3"
