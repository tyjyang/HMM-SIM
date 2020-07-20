#######################
# importing libraries #
#######################

# import ROOT in batch mode
import sys,os
import math
import numpy as np
import pandas as pd
from scipy import stats
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

ROOT.gROOT.SetBatch(True) # disable graph display
data_fastsim = pd.read_csv("data/m_mu_mu_fastsim_min_dR_l04.csv", skipinitialspace = True, dtype = float)
data_fullsim = pd.read_csv("data/m_mu_mu_fullsim_min_dR_l04.csv", skipinitialspace=True, dtype = float)
#data_fastsim = pd.read_csv("data/m_mu_mu_fastsim_min_inv_m_dR_l04.csv", skipinitialspace = True, dtype = float)
#data_fullsim = pd.read_csv("data/m_mu_mu_fullsim_min_inv_m_dR_l04.csv", skipinitialspace=True, dtype = float)
#data_fastsim['Hmm_met'] = data_fastsim["higgs_pt"] - data_fastsim["dimuon_sys_pt"]
#data_fullsim['Hmm_met'] = data_fullsim["higgs_pt"] - data_fullsim["dimuon_sys_pt"]
#data_fastsim['dimuon_delta_eta'] = abs(data_fastsim["dimuon_eta_1"] - data_fastsim["dimuon_eta_2"])
#data_fullsim['dimuon_delta_eta'] = abs(data_fullsim["dimuon_eta_1"] - data_fullsim["dimuon_eta_2"])

#data_fastsim = pd.concat([data_fastsim, met_fast, delta_eta_fast], axis = 1)
#print data_fastsim.columns.get_values()

#data_fullsim['dimuon_inv_m'] = data_fullsim.loc[data_fullsim['dimuon_inv_m'] < 125]
num_evts_fast = data_fastsim.shape[0]
num_evts_full = data_fullsim.shape[0]
num_evts = min([num_evts_fast, num_evts_full])
h = {}

for key in data_fastsim.columns.get_values():
	c = ROOT.TCanvas("canvas_" + key, "canvas_" + key)
	data_fastsim[key] = np.array(data_fastsim[key])
	data_fullsim[key] = np.array(data_fullsim[key])
	# upper and lower bounds
	lb = (np.amin(data_fastsim[key]) + np.amin(data_fullsim[key])) / 2
	ub = (np.amax(data_fastsim[key]) + np.amax(data_fullsim[key])) / 2
	if key == 'm_mu_mu':
		lb, ub = 115, 135
	#iqr = stats.iqr(data_fastsim[key])
	#nbins = int(2 * (num_evts ** (1.0/3.0)))
	nbins = int((ub - lb) * 2)
	# declare hists and fill in data points
	h_fast = ROOT.TH1D(key+"_fast", key+"_fast", nbins, lb, ub)
	h_full = ROOT.TH1D(key+"_full", key+"_full", nbins, lb, ub)
	for x in data_fastsim[key][:num_evts]:
		if x >= lb and x <= ub: h_fast.Fill(x)
	for x in data_fullsim[key][:num_evts]:
		if x >= lb and x <= ub: h_full.Fill(x)
	'''set graph properties'''
	h_fast.SetLineColor(ROOT.kBlue);
	h_full.SetLineColor(ROOT.kRed);
	h_fast.SetMinimum(0)
	h_full.SetMinimum(0)
	h_full.SetFillColor(ROOT.kRed)
	h_full.SetFillStyle(3004)
	h_fast.Draw()
	#scale = h_fast.Integral() / h_full.Integral()
	#scale = 1
	#h_full.Scale(scale)
	# superpose 2 hists
	h_full.Draw("SAMES")
	ROOT.gPad.Update()
	# draw 2nd axis on right
	#rightmax = 1.1 * h_full.GetMaximum()
	#axis = ROOT.TGaxis(ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymin(),
	#		           ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymax(),0,rightmax,510,"+L")
	#axis.SetLineColor(ROOT.kRed)
	#axis.SetLabelColor(ROOT.kRed)
	#axis.Draw()
	ROOT.gPad.BuildLegend(0, 1, 0.2, 0.9)
	ROOT.gPad.Update() # MANDOTARY for accessing stat boxes below
	
	# set new title for the overlaid hists, so there is no fast or full in it
	title = ROOT.gPad.FindObject("title")
	title_new = ROOT.TPaveText(title.GetX1(),title.GetY1(),title.GetX2(),title.GetY2(),"")
	title_new.AddText(key)
	title_new.Draw()
	# separate stat boxes for overlaid hists
	st_fast = ROOT.TPaveStats()
	st_fast = h_fast.FindObject("stats")
	st_fast.SetX1NDC(0.8)
	st_fast.SetY1NDC(0.85)
	st_fast.SetX2NDC(1)
	st_fast.SetY1NDC(0.77)
	st_full = ROOT.TPaveStats()
	st_full = h_full.FindObject("stats")
	st_full.SetX1NDC(0.8)
	st_full.SetY1NDC(0.7)
	st_full.SetX2NDC(1)
	st_full.SetY2NDC(0.55)
	c.SaveAs("hist/"+key+".pdf")
	h[key+"_fast"] = h_fast
	h[key+"_full"] = h_full
	if key == 'dimuon_inv_m':
		h[key+"_fast"].Fit("gaus")
		h[key+"_full"].Fit("gaus")

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











