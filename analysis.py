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

ROOT.gROOT.SetBatch(True) # disable graph display

data_fastsim = pd.read_csv("data/fastsim.csv", skipinitialspace=True)
data_fullsim = pd.read_csv("data/fullsim.csv", skipinitialspace=True)
num_of_evts = data_fastsim.shape[0]
nbins = int(num_of_evts ** (1.0/3.0))
h = {}
for key in data_fastsim.columns.get_values():
	c = ROOT.TCanvas("canvas_" + key, "canvas_" + key)
	h_fast = ROOT.TH1D(key+"_fast", key+"_fast", nbins, min(data_fastsim[key]), max(data_fastsim[key]))
	h_full = ROOT.TH1D(key+"_full", key+"_full", nbins, min(data_fullsim[key]), max(data_fullsim[key]))
	for x in data_fastsim[key]:
		h_fast.Fill(x)
	for x in data_fullsim[key]:
		h_full.Fill(x)
	h_fast.SetLineColor(ROOT.kBlue);
	h_full.SetLineColor(ROOT.kRed);
	h_fast.Draw()
	h_full.Draw("same")
	c.SaveAs("hist/"+key+".pdf")
	h[key+"_fast"] = h_fast
	h[key+"_full"] = h_full

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











