#!/bin/bash
python ComputeUserStats.py -c BER -s Moses,Petrus,Schneegewitter,Pfingstochse,GME-MOS,DWD-ICON-MOS -v > plots/BER_sdind"$1".txt
python ComputeUserStats.py -c IBK -s Moses,Petrus,Georg,MOS-Mix -v > plots/IBK_sdind"$1".txt
python ComputeUserStats.py -c LEI -s Moses,Petrus,MOS-Mix,Pfingstochse -v > plots/LEI_sdind"$1".txt
python ComputeUserStats.py -c VIE -s Moses,Petrus,DWD-MOS-Mix,DWD-MOSMixEZGME,GME-MOS,DWD-ICON-MOS,Pfingstochse -v > plots/VIE_sdind"$1".txt
python ComputeUserStats.py -c ZUR -s Moses,Petrus,DWD-MOS-Mix,DWD-MOSMixEZGME,GME-MOS,DWD-ICON-MOS,Pfingstochse -v > plots/ZUR_sdind"$1".txt
