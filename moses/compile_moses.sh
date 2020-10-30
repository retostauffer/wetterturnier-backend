#!/bin/bash

f2py -m moses -c --fcompiler=gfortran general.f90 moses.f90
cp moses.so ../
