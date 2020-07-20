import FWCore.ParameterSet.Config as cms

externalLHEProducer = cms.EDProducer("ExternalLHEProducer",
    args = cms.vstring('/cvmfs/cms.cern.ch/phys_generator/gridpacks/UL/13TeV/powheg/V2/gg_H_quark-mass-effects_slc7_amd64_gcc700_CMSSW_10_6_0_ggh125_13TeV_PDF316200/v1/gg_H_quark-mass-effects_slc7_amd64_gcc700_CMSSW_10_6_0_ggh125_13TeV_PDF316200.tgz'),
    nEvents = cms.untracked.uint32(5000),
    numberOfParameters = cms.uint32(1),
    outputFile = cms.string('cmsgrid_final.lhe'),
    scriptName = cms.FileInPath('GeneratorInterface/LHEInterface/data/run_generic_tarball_cvmfs.sh')
)

import FWCore.ParameterSet.Config as cms
from Configuration.Generator.Pythia8CommonSettings_cfi import *
from Configuration.Generator.Pythia8CUEP8M1Settings_cfi import *
from Configuration.Generator.Pythia8PowhegEmissionVetoSettings_cfi import *

generator = cms.EDFilter("Pythia8HadronizerFilter",
	maxEventsToPrint = cms.untracked.int32(1),
	pythiaPylistVerbosity = cms.untracked.int32(1),
	filterEfficiency = cms.untracked.double(1.0),
	pythiaHepMCVerbosity = cms.untracked.bool(False),
	comEnergy = cms.double(13000.),
	PythiaParameters = cms.PSet(
		pythia8CommonSettingsBlock,
		pythia8CUEP8M1SettingsBlock,
		pythia8PowhegEmissionVetoSettingsBlock,
		processParameters = cms.vstring(
			'POWHEG:nFinal = 1',   ## Number of final state particles
			## (BEFORE THE DECAYS) in the LHE
			## other than emitted extra parton
			'25:m0 = 125.0',
			'25:onMode = off',
			'25:onIfMatch = 13 -13', ## H -> mumu
		),
        parameterSets = cms.vstring(
			'pythia8CommonSettings',
			'pythia8CUEP8M1Settings',
			'pythia8PowhegEmissionVetoSettings',
			'processParameters'
		)
	)
)

ProductionFilterSequence = cms.Sequence(generator)
