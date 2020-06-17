#######################
# importing libraries #
#######################

# import ROOT in batch mode
import sys,os
import math
import numpy as np
import pandas as pd
oldargv = sys.argv[:]
#sys.argv = [ '-b-' ]
import ROOT
#ROOT.gROOT.SetBatch(True)
sys.argv = oldargv

# load FWLite C++ libraries
ROOT.gSystem.Load("libFWCoreFWLite.so");
ROOT.gSystem.Load("libDataFormatsFWLite.so");
ROOT.FWLiteEnabler.enable()

# load FWlite python libraries
from DataFormats.FWLite import Handle, Events

## das query. do voms_proxy_init -voms cms
from subprocess import check_output
import re

####################
# global variables #
####################

# setup eos redirector for fetching ROOT files
eos_redirector = "root://eoscms.cern.ch/"

# pdg mc particle id
muon_id = 13
higgs_id = 25

# particle masses in [GeV]
muon_mass = 0.105
higgs_mass = 125
''' get a list of files under a certain directory '''
num_files = 15
sim_mode = "fastsim"
cut = "min_dR_l02"
dir_fast = "/store/user/amarini/GluGlu_HToMuMu_M125_13TeV_powheg_pythia8/FastSim_94X-MINIAODSIM"
dir_full = "/store/user/amarini/GluGlu_HToMuMu_M125_13TeV_powheg_pythia8/FullSim_94X-MINIAODSIM"
if sim_mode == "fullsim":
	LFN = dir_full
	onMiniAOD = True
elif sim_mode == "fastsim":
	LFN = dir_fast
	onMiniAOD = False
list_of_files = check_output("eos " + eos_redirector + " find -f " + LFN, shell=True)
blacklist=[]
files = [x for x in list_of_files.split('\n')[0:num_files] if '/store' in x and x not in blacklist] 
#files = list_of_files.split('\n')[0:1] # cutting down num of files, for testing

''' set up a few parameters '''
#onlyEvent=12345
onlyEvent=None
verbose=True

#######################
# Function Definition #
#######################

# convert the four momentum of a particle 
# from (m, pt, eta, phi) to (E, px, py, pz)
# requires (m, pt, eta, phi) 
# returns (E, px, py, pz) in a 1D numpy array
def to_Epxpypz(m, pt, eta, phi):
	p_mag = pt * math.cosh(eta)
	E = math.sqrt(p_mag ** 2 + m ** 2)
	pz = pt * math.sinh(eta)
	px = pt * math.cos(phi)
	py = pt * math.sin(phi)
	return np.array([E, px, py, pz])

# calculate the invariant mass of a two-particle system
# requires four-momenta of the two particles in np array in [E, px, py, pz]
# return the invariant mass as a double
def binary_inv_m(p1, p2):
	return math.sqrt(np.add(p1[0], p2[0]) ** 2 - \
				np.linalg.norm(np.add(p1[1:], p2[1:])) ** 2)

# calculate the delta_R geometric info of 2 particles
# requires the phi and eta info of the 2 particles
# returns delta_R
def get_delta_R(eta1, phi1, eta2, phi2):
	return math.sqrt((phi1 - phi2) ** 2 + (eta1 - eta2) ** 2)

#############################
# initializing data holders #
#############################
# note, "dimuon" here means 2 muons separately, not the two muons as
# a whole system, unless otherwise noted
data = {}
#data['dimuon_pt_1'] = []
#data['dimuon_eta_1'] = []
#data['dimuon_phi_1'] = []
#data['dimuon_pt_2'] = []
#data['dimuon_eta_2'] = []
#data['dimuon_phi_2'] = []
#data['dimuon_p'] = []
data['m_mu_mu'] = []
#data['dimuon_sys_pt'] = []
#data['higgs_pt'] = []
#data['higgs_eta'] = []
#data['higgs_phi'] = []
data['delta_R'] = []

h = {}
h["all"] = ROOT.TH1D("all","mt",10,0.5,10.5)

######################################
# Main loop over events in each file #
######################################
# allow termination by ctrl+c
try:

	for f in files:

		# tries to fetch the file from eos, pass if fetching is unsuccessful for one file
		try:
			# open file (you can use 'edmFileUtil -d /store/whatever.root' to get the physical file name)
			print "->Opening file",f.split()[0]
			if 'file:' in f.split()[0] :
				events = Events(f.split()[0])
			else:
				events = Events(eos_redirector + f.split()[0])
				#events = Events("root://xrootd-cms.infn.it//"+f.split()[0]) #AAA
			
			lhe,lheLabel = Handle("LHEEventProduct"),"externalLHEProducer"
			handlePruned  = Handle ("std::vector<reco::GenParticle>")
			handleJets  = Handle ("std::vector<reco::GenJet>")

			if onMiniAOD:
				labelPruned = ("prunedGenParticles")
				labelJets = ("slimmedGenJets")
				labelMuon = ("slimmedMuons")
				handleMuon = Handle ("vector<pat::Muon>")
			else:
				labelPruned = ("genParticles")
				labelJets = ("ak4GenJets")
				labelMuon = ("muons")
				handleMuon = Handle ("vector<reco::Muon>")
			
			if events==None: 
				print "Events is none.Try to continue"
				continue        
			
			evt_counter = 0 # for testing purpose, so one can terminate the loop after a handful of evts
			for iev,event in enumerate(events):
				
				# cutting down num. of evts, comment out for production 
				#if evt_counter > 29:
				#	break
				#evt_counter += 1
				

				if onlyEvent != None and event.eventAuxiliary().event() != onlyEvent: continue

				#if verbose:
				print "\n-> Event %d: run %6d, lumi %4d, event %12d" \
						% (iev,event.eventAuxiliary().run(), 
						event.eventAuxiliary().luminosityBlock(),event.eventAuxiliary().event())

				# tries to extract genParticles from each event
				try:
					event.getByLabel(lheLabel, lhe)
					hepeup = lhe.product().hepeup()
					#if verbose:
					#  for i in range(0,hepeup.IDUP.size() ):
					#    x=ROOT.TLorentzVector()
					#    x.SetPxPyPzE( hepeup.PUP[i][0],hepeup.PUP[i][1],hepeup.PUP[i][2],hepeup.PUP[i][3]) 
					#    if hepeup.ISTUP[i] != 1: continue;
					#    print " *) pdgid=",hepeup.IDUP[i],"pt=",x.Pt(),"eta=",x.Eta(),"phi=",x.Phi()

					w=lhe.product().weights()[0].wgt

					# GEN PARTICLES
					if verbose:
						print " ------------ "
					event.getByLabel (labelPruned, handlePruned)
					pruned = handlePruned.product()
					
					event.getByLabel(labelMuon, handleMuon)
					recomuons = handleMuon.product()
				except RuntimeError:
					print "-> RuntimeERROR trying to continue"
					continue
				
				'''variables to store physical parameters within each events'''
				# muon four-momentum vector (E, px, py, pz)
				# 2D, first index for muon enumerator, second for 4-vec components
				# note, "dimuon" here means 2 muons separately, not the two muons as
				# a whole system, unless otherwise noted
				dimuon_p4 = []
				dimuon_pt = []
				dimuon_eta = []
				dimuon_phi = []
				higgs_pt = 0
				higgs_phi = 0
				higgs_eta = 0
				muon_counter = 0
				delta_R_gen = 0
				delta_R_reco = 0
				print_once_higgs = True
				print_once_muons = True
				m_mu_mu_candidates = []
				delta_R_reco_candidates = []
				ddelta_R_candidates = []
				dm_mu_mu_candidates = []
				higgs_res_generous = 15

				''' loop over each object in genParticles '''
				for p in pruned:
					if not p.mother(0): continue
					if p.mother(0).pdgId() == higgs_id and abs(p.pdgId()) == muon_id:
						muon_counter += 1
						dimuon_p4.append([p.mass(), p.pt(), p.eta(), p.phi()])
						#print "Muon E is {}, px is {}, py is {}, pz is {}"\
						#	.format(*to_Epxpypz(p.mass(), p.pt(), p.eta(), p.phi()))

				# check to make sure that we selected the muons from higgs decay
				if muon_counter == 2:
					dimuon_p4 = np.array(dimuon_p4)
					#print binary_inv_m(dimuon_p4[0], dimuon_p4[1])
					delta_R_gen = get_delta_R(dimuon_p4[0][2], dimuon_p4[0][3], dimuon_p4[1][2], dimuon_p4[1][3])
					# calculate pt of the dimuon as a whole system
					#dimuon_sys_pt = math.sqrt((dimuon_p[0][1] + dimuon_p[1][1]) ** 2 + 
					#						  (dimuon_p[0][2] + dimuon_p[1][2]) ** 2)  
					# store particle info from each evt to arries
					#data['dimuon_pt_1'].append(np.amax(np.array(dimuon_pt)))
					#data['dimuon_pt_2'].append(np.amin(np.array(dimuon_pt)))
					#data['dimuon_eta_1'].append(np.amax(np.array(dimuon_eta)))
					#data['dimuon_eta_2'].append(np.amin(np.array(dimuon_eta)))
					#data['dimuon_phi_1'].append(np.amax(np.array(dimuon_phi)))
					#data['dimuon_phi_2'].append(np.amin(np.array(dimuon_phi)))
					#data['dimuon_p'].append(dimuon_p)
					#data['dimuon_sys_pt'].append(dimuon_sys_pt)
					#data['dimuon_inv_m'].append(dimuon_inv_m)
					#data['higgs_pt'].append(higgs_pt)
					#data['higgs_eta'].append(higgs_eta)
					#data['higgs_phi'].append(higgs_phi)
				else:
					continue
					#print 'wrong config in HMM decay'

				'''loop over reco muons'''
				for ind, mu in enumerate(recomuons[:-1]):
					for second_mu in recomuons[ind+1:]:
						if mu.charge()*second_mu.charge() == -1:
							p1 = to_Epxpypz(mu.mass(), mu.pt(), mu.eta(), mu.phi())
							p2 = to_Epxpypz(second_mu.mass(), second_mu.pt(), second_mu.eta(), second_mu.phi())
							delta_R_reco = get_delta_R(mu.eta(), mu.phi(), second_mu.eta(), second_mu.phi())
							ddelta_R = abs(delta_R_reco - delta_R_gen)
							if ddelta_R < 0.2 and delta_R_gen:
								m_mu_mu = binary_inv_m(p1, p2)
								m_mu_mu_candidates.append(m_mu_mu)
								dm_mu_mu_candidates.append(abs(m_mu_mu - higgs_mass))
								delta_R_reco_candidates.append(delta_R_reco)
								ddelta_R_candidates.append(ddelta_R)
						else:
							continue
						
				print 'delta_R in reco:', delta_R_reco_candidates


				if len(m_mu_mu_candidates):
					m_mu_mu_candidates = np.array(m_mu_mu_candidates)
					delta_R_reco_candidates = np.array(delta_R_reco_candidates)
					#i_dR_min = np.where(ddelta_R_candidates == np.amin(ddelta_R_candidates))[0]
					i_m_min = np.where(dm_mu_mu_candidates == np.amin(dm_mu_mu_candidates))[0]
					#if i_dR_min == i_m_min:
					data['m_mu_mu'].append(float(m_mu_mu_candidates[i_m_min]))
					data['delta_R'].append(float(delta_R_reco_candidates[i_m_min]))
					#else:
					#	for x in delta_R_reco_candidates:
					#		if abs(delta_R_reco_candidates[i_min]

				else:
					print 'No match between reco and gen muons based on delta_R'
					
					#print np.amin(off_center)
						#print "Muon E is {}, px is {}, py is {}, pz is {}"\
						#.format(*to_Epxpypz(mu.mass(), mu.pt(), mu.eta(), mu.phi()))

				'''
				for p in pruned:

					# getting particle decay info
					mother = p.mother(0)
					mpdg = 0
					if mother: mpdg = mother.pdgId()
					#if verbose:
					print " *) PdgId : %s   pt : %s  eta : %s   phi : %s mother : %s" \
								%(p.pdgId(),p.pt(),p.eta(),p.phi(),mpdg) 

					# getting dimuon and higgs parameters
					if abs(p.pdgId()) == muon_id and mpdg == higgs_id:
						muon_counter += 1
						
						# calculate muon four momentum (E, px, py, pz)
						p_mag = p.pt() * math.cosh(p.eta())
						energy = math.sqrt(p_mag ** 2 + muon_mass ** 2)
						pz = p.pt() * math.sinh(p.eta())
						px = p.pt() * math.cos(p.phi())
						py = p.pt() * math.sin(p.phi())

						dimuon_p.append([energy,px,py,pz])
						dimuon_pt.append(p.pt())
						dimuon_eta.append(p.eta())
						dimuon_phi.append(p.phi())
						if higgs_pt == 0: higgs_pt = mother.pt()
						if higgs_eta == 0: higgs_eta = mother.eta()
						if higgs_phi == 0: higgs_phi = mother.phi()
					'''
				'''
						# print HMM infos
						if print_once_muons:
								print "HMM process in this event:"
								print_once_muons = False
						print "Final State Particle ID: %d; Mother Particle ID and pt: %d %f; Grandma ID: %d" %\
								(p.pdgId(), mpdg, mother.pt(), mother.mother(0).pdgId())

					# print mother of the higgs
					if abs(p.pdgId()) == higgs_id:
						if print_once_higgs:
							print "All Higgs particles in this event: "
							print_once_higgs = False
						print "Particle ID is: %d; Mother ID is: %d; Particle pt is: %f" % \
								(p.pdgId(), p.mother(0).pdgId(), p.pt())
					'''

				'''
				event.getByLabel(labelJets, handleJets)
				njets=0
				taujet=None
				leadjetpt=0
				for j in handleJets.product():
					if verbose:
						print " *) GenJet :   pt : %s  eta : %s   phi : %s " %(j.pt(),j.eta(),j.phi()) 
					if j.pt()<30: continue
					if abs(j.eta())>4.7: continue
					jet=ROOT.TLorentzVector()
					jet.SetPtEtaPhiM(j.pt(),j.eta(),j.phi(),j.mass())
					if lep != None and lep.DeltaR(jet)<0.1: continue ## exclude lep-jets
					if jet.DeltaR(tau) <0.1 :
						taujet=jet
						continue
					njets+=1
					leadjetpt=max(leadjetpt,j.pt())
                
				#njets
				hp=tau+nu ## true

				h["mass"].Fill(hp.M())

				#return TMath::Sqrt( 2.* fabs(pt1) * fabs(pt2) * fabs( 1.-TMath::Cos(ChargedHiggs::deltaPhi(phi1,phi2)) ) );
				if taujet : h["mt-had"] . Fill(math.sqrt(2*taujet.Pt()*met.Pt()*(1.-math.cos(met.DeltaPhi(taujet)))),w)
				if lep    : h["mt-lep"] . Fill(math.sqrt(2*lep.Pt()*met.Pt()*(1.-math.cos(met.DeltaPhi(lep)))),w)
				h["njets"] . Fill(njets,w)
				h["taupt"] . Fill(tau.Pt(),w)
				if taujet : h["tauhpt"] . Fill(taujet.Pt(),w)
				if lep    : h["leppt"] . Fill(lep.Pt(),w)
				h["met"] . Fill(met.Pt(),w)
				if lep: h["lep-met-dphi"] . Fill(abs(lep.DeltaPhi(met)),w)
				h["leadjetpt"] . Fill(leadjetpt,w)
				'''
		except TypeError:
			# eos sucks
			print "Unable to fetch file"
			pass

except KeyboardInterrupt:
    pass

# store data into csv files
#for keys in data:
#	print keys, len(data[keys])

data = pd.DataFrame.from_dict(data)
data.to_csv('data/m_mu_mu_' + sim_mode + '_' + cut + '.csv', index = False)
#print data['dimuon_inv_m']

print "DONE"


