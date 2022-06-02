#!/bin/bash

source s && python AstralTable.py > /home/wetterturnier/cronlog/AstralTable.log && cp AstralTable.txt /var/www/html/ 2>&1
