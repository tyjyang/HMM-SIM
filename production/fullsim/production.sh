#!/bin/bash
export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
if [ -r CMSSW_10_6_0/src ] ; then 
	echo release CMSSW_10_6_0 already exists
 else
	scram p CMSSW CMSSW_10_6_0
fi
eval `scram runtime -sh`

echo "================= CMSRUN starting Step 0 ====================" | tee -a job.log
cmsRun -j step0.log step0.py jobNum=1 seed=$(($(date +%s) % 100 + 1))

echo "================= CMSRUN starting Step 1_1 ====================" | tee -a job.log
cmsRun -j step1_1.log step1_1.py

echo "================= CMSRUN starting Step 1_2 ====================" | tee -a job.log
cmsRun -j step1_2.log step1_2.py

echo "================= CMSRUN starting Step 2 ====================" | tee -a job.log
cmsRun -j step2.log step2.py

echo "================= CMSRUN starting Step 3 ====================" | tee -a job.log
cmsRun -e -j FrameworkJobReport.xml step3.py

echo "================= CMSRUN finished ====================" | tee -a job.log
