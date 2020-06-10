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

''' get a list of files under a certain directory '''
sim_mode = "fullsim"
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
#files = [x for x in list_of_files.split('\n') if '/store' in x and x not in blacklist] 
files = list_of_files.split('\n')[0:1] # cutting down num of files, for testing

''' set up a few parameters '''
#onlyEvent=12345
onlyEvent=None
verbose=True

#############################
# initializing data holders #
#############################
# note, "dimuon" here means 2 muons separately, not the two muons as
# a whole system, unless otherwise noted
data = {}
data['dimuon_pt_1'] = []
data['dimuon_eta_1'] = []
data['dimuon_phi_1'] = []
data['dimuon_pt_2'] = []
data['dimuon_eta_2'] = []
data['dimuon_phi_2'] = []
#data['dimuon_p'] = []
data['dimuon_inv_m'] = []
data['dimuon_sys_pt'] = []
data['higgs_pt'] = []
data['higgs_eta'] = []
data['higgs_phi'] = []

h = {}
h["all"] = ROOT.TH1D("all","mt",10,0.5,10.5)

## counters events
try:

	for f in files:
		# tries to fetch the file from eos
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
			else:
				labelPruned = ("genParticles")
				labelJets = ("ak4GenJets")

			if events==None: 
				print "Events is none.Try to continue"
				continue        
			evt_counter = 0 # for testing purpose, so one can terminate the loop after a handful of evts
			for iev,event in enumerate(events):
				
				# cutting down num. of evts, comment out for production 
				if evt_counter > 0:
					break
				evt_counter += 1
				

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
					
					labelMuon = ("recoMuon")
					handleMuon = Handle ("std::vector<reco::Muon>")
					event.getByLabel(labelMuon, handleMuon)
					recomuons = handleMuon.product()
				except RuntimeError:
					print "-> RuntimeERROR trying to continue"
					continue
				print "past try block"
				h["all"].Fill(1,w)
				h["all"].Fill(2,w*w)
				h["all"].Fill(3,1)

				#mu=ROOT.TLorentzVector()
				#nu=ROOT.TLorentzVector()
				#met=ROOT.TLorentzVector()
				#lep=ROOT.TLorentzVector()
				#lep=None
				
				'''variables to store physical parameters within each events'''
				'''info from all events are attached to the xx_arr variables at the end'''
				# muon four-momentum vector (E, px, py, pz)
				# 2D, first index for muon enumerator, second for 4-vec components
				# note, "dimuon" here means 2 muons separately, not the two muons as
				# a whole system, unless otherwise noted
				dimuon_p = []
				dimuon_pt = []
				dimuon_eta = []
				dimuon_phi = []
				higgs_pt = 0
				higgs_phi = 0
				higgs_eta = 0
				muon_counter = 0
				print_once_higgs = True
				print_once_muons = True
				''' loop over each object in genParticles '''
				for mu in recomuons:
					print "mu loop"
					print mu.pdgId(), mu.pt(), mu.eta()
				for p in pruned:

					# getting particle decay info
					mother = p.mother(0)
					mpdg = 0
					if mother: mpdg = mother.pdgId()
					#if verbose:
					print "genParticle loop"
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
					if p.status() ==1 and abs(p.eta())<5 and abs(p.pdgId()) == 13:
						
					if p.status() ==1 and abs(p.eta())<4.7 and abs(p.pdgId()) not in [12,14,16]:
						tmp=ROOT.TLorentzVector()
						tmp.SetPtEtaPhiM( p.pt(),p.eta(),p.phi(),0.105)
						mu-=tmp

					if p.status() ==1 and (abs(p.pdgId())==11 or abs(p.pdgId())==13 ) and abs(mpdg)==15:
						lep=ROOT.TLorentzVector()
						lep.SetPtEtaPhiM(p.pt(),p.eta(),p.phi(),0.0 if abs(p.pdgId())==11 else 0.105)

					if abs(p.pdgId()) == 15 and abs(mpdg)==37:
						tau.SetPtEtaPhiM(p.pt(),p.eta(),p.phi(),1.7)

					if abs(p.pdgId()) == 16 and abs(mpdg)==37:
						nu.SetPtEtaPhiM(p.pt(),p.eta(),p.phi(),0.0)
				'''
				# check to make sure that we selected the muons from higgs decay
				if muon_counter == 2:
					dimuon_p = np.array(dimuon_p)
					dimuon_inv_m = math.sqrt(np.add(dimuon_p[0][0], dimuon_p[1][0]) ** 2 - \
							   np.linalg.norm(np.add(dimuon_p[0][1:], dimuon_p[1][1:])) ** 2)
					# calculate pt of the dimuon as a whole system
					dimuon_sys_pt = math.sqrt((dimuon_p[0][1] + dimuon_p[1][1]) ** 2 + 
											  (dimuon_p[0][2] + dimuon_p[1][2]) ** 2)  
					# store particle info from each evt to arries
					data['dimuon_pt_1'].append(np.amax(np.array(dimuon_pt)))
					data['dimuon_pt_2'].append(np.amin(np.array(dimuon_pt)))
					data['dimuon_eta_1'].append(np.amax(np.array(dimuon_eta)))
					data['dimuon_eta_2'].append(np.amin(np.array(dimuon_eta)))
					data['dimuon_phi_1'].append(np.amax(np.array(dimuon_phi)))
					data['dimuon_phi_2'].append(np.amin(np.array(dimuon_phi)))
					#data['dimuon_p'].append(dimuon_p)
					data['dimuon_sys_pt'].append(dimuon_sys_pt)
					data['dimuon_inv_m'].append(dimuon_inv_m)
					data['higgs_pt'].append(higgs_pt)
					data['higgs_eta'].append(higgs_eta)
					data['higgs_phi'].append(higgs_phi)
				else:
					print 'wrong config in HMM decay'


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
			pass

except KeyboardInterrupt:
    pass

# store data into csv files
#for keys in data:
#	print keys, len(data[keys])
data = pd.DataFrame.from_dict(data)
data.to_csv('data/' + sim_mode + '.csv', index = False)




#nbin = 1.0/3.0
#for key in data:
#	data[key] = np.array(data[key])
#	h[key] = 
#	for evt_entry in data[key]:
#		branch.Fill(evt_entry)
#tree.Fill()


''' more fitting for anothe script
c = ROOT.TCanvas("c", "c", 1800, 1200)

## fit the hist to a gaussian to get mass resolution
h['dimuon_inv_m'].Fit("gaus")

## get the fit function
f = h['dimuon_inv_m'].GetFunction("gaus")
ndf = f.GetNDF()
chi2 = f.GetChisquare()

## draw legend and add chi2/ndf
#legend = ROOT.TLegend(0.6, 0.8, 0.99, 0.99)
#legend.SetBorderSize(0)  # no border
#legend.SetFillStyle(0)  # make transparent
#legend.Draw()
#legend.AddEntry(None, '#chi^{2}' + ' / ndf = {:.3f} / {}'.format(chi2, ndf), '')
#legend.AddEntry(None, '= {:.3f}'.format(chi2/ndf), '')
#legend.Draw()

## draw the hist on canvas
h['dimuon_inv_m'].Draw()
c.SaveAs("inv_m.png")

##file output
fOut=ROOT.TFile("./data/" + sim_mode + ".root","RECREATE")
fOut.cd()
#for branch in tree:
tree.Write()
'''

print "DONE"


