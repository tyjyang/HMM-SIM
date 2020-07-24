#!/bin/bash

echo "================= CMSRUN starting Step 0 ====================" | tee -a job.log
cmsRun -j step0.log step0.py jobNum=1 seed=$(($(date +%s) % 100 + 1)) 

echo "================= CMSRUN starting Step 1_1 ====================" | tee -a job.log
cmsRun -j step1_1.log step1_1.py 

echo "================= CMSRUN starting Step 1_2 ====================" | tee -a job.log
cmsDriver.py --filein file:step1_1.root --fileout file:step1_2.root --mc --eventcontent RAWSIM --datatier GEN-SIM-RAW --conditions 106X_mc2017_realistic_v6 --customise_commands 'process.source.bypassVersionCheck = cms.untracked.bool(True)' --step HLT:@relval2017 --nThreads 8 --geometry DB:Extended --era Run2_2017 --python_filename step1_2.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring -n 500

cmsRun -j step1_2.log step1_2.py

echo "================= CMSRUN starting Step 2 ====================" | tee -a job.log
cmsDriver.py --filein file:step1_2.root --fileout file:step2.root --mc --eventcontent AODSIM --runUnscheduled --datatier AODSIM --conditions 106X_mc2017_realistic_v6 --step RAW2DIGI,L1Reco,RECO,RECOSIM --nThreads 8 --geometry DB:Extended --era Run2_2017 --python_filename step2.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring -n 500

cmsRun -j step2.log step2.py 

echo "================= CMSRUN starting Step 3 ====================" | tee -a job.log
cmsDriver.py --filein file:step2.root --fileout file:step3.root --mc --eventcontent MINIAODSIM --runUnscheduled --datatier MINIAODSIM --conditions 106X_mc2017_realistic_v6 --step PAT --nThreads 8 --geometry DB:Extended --era Run2_2017 --python_filename step3.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring -n 500

#cmsRun -j MiniAODSim_Step2.log Step2.py 
cmsRun -e -j FrameworkJobReport.xml step3.py 

echo "================= CMSRUN finished ====================" | tee -a job.log
