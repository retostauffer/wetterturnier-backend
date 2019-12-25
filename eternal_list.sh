#!/bin/bash
python ComputeUserStats.py -c BER -s Moses,Petrus,Schneegewitter,Pfingstochse -v > plots/BER_sdfit.txt
python ComputeUserStats.py -c IBK -s Moses,Petrus,Georg,MOS-Mix -v > plots/IBK_sdfit.txt
python ComputeUserStats.py -c LEI -s Moses,Petrus,MOS-Mix,Pfingstochse -v > plots/LEI_sdfit.txt
python ComputeUserStats.py -c VIE -s Moses,Petrus,DWD-MOS-Mix,DWD-MOSMixEZGME,Pfingstochse -v > plots/VIE_sdfit.txt
python ComputeUserStats.py -c ZUR -s Moses,Petrus,DWD-MOS-Mix,DWD-MOSMixEZGME,Pfingstochse -v > plots/ZUR_sdfit.txt

