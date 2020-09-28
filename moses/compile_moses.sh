#!/bin/bash

f2py -m moses -c --fcompiler=gfortran general.f moses.f
cp moses.so ../
