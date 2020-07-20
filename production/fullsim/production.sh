#!/bin/bash

echo "================= CMSRUN starting Step 1 ====================" | tee -a job.log
cmsRun -j step1.log step1.py 

echo "================= CMSRUN starting Step 2 ====================" | tee -a job.log
cmsRun -j step2.log step2.py 

echo "================= CMSRUN starting Step 3 ====================" | tee -a job.log
cmsRun -j step3.log step3.py 


echo "================= CMSRUN starting Step 4 ====================" | tee -a job.log
#cmsRun -j MiniAODSim_Step2.log Step2.py 
cmsRun -e -j FrameworkJobReport.xml step4.py 

echo "================= CMSRUN finished ====================" | tee -a job.log
