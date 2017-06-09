#!/bin/bash

EXTPC='admin@prognose.met.fu-berlin.de'

extra="1[6-7]"


# - Innsbruck
if [ ! -d 'wert_i' ] ; then mkdir wert_i ; fi
rsync -vart admin@prognose.met.fu-berlin.de:/home/innsbruck/auswertung/wert/wert${extra}*.txt wert_i

# - Berlin
if [ ! -d 'wert_b' ] ; then mkdir wert_b ; fi
rsync -vart admin@prognose.met.fu-berlin.de:/home/berlin/auswertung/wert/wert${extra}*.txt wert_b

# - Leipzig
if [ ! -d 'wert_l' ] ; then mkdir wert_l ; fi
rsync -vart admin@prognose.met.fu-berlin.de:/home/leipzig/auswertung/wert/wert${extra}*.txt wert_l

# - Zuerich 
if [ ! -d 'wert_z' ] ; then mkdir wert_z ; fi
rsync -vart admin@prognose.met.fu-berlin.de:/home/zuerich/auswertung/wert/wert${extra}*.txt wert_z

# - Wien
if [ ! -d 'wert_w' ] ; then mkdir wert_w ; fi
rsync -vart admin@prognose.met.fu-berlin.de:/home/wien/auswertung/wert/wert${extra}*.txt wert_w

# - Kill data of current tournament (can crash if there is everything full of x)
today=`date -u '+%y%m%d'`
rm wert_*/wert${today}.txt
