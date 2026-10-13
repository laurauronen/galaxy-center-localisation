import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# lenstronomy module import
from lenstronomy.Util import image_util, data_util

from lenstronomy.LensModel.lens_model import LensModel
from lenstronomy.Plots import lens_plot
from lenstronomy.LightModel.light_model import LightModel
from lenstronomy.Plots import chain_plot
from lenstronomy.Plots.model_plot import ModelPlot
from lenstronomy.Data.pixel_grid import PixelGrid
from lenstronomy.Data.psf import PSF
from lenstronomy.ImSim.image_model import ImageModel
from lenstronomy.Data.imaging_data import ImageData
import emcee

from lenstronomy.LightModel.Profiles.gaussian import GaussianEllipse
gauss = GaussianEllipse()

from lensgw import lens_gw
from log_funcs import * 
import os
import json 
import pickle as pkl

import argparse 
parser = argparse.ArgumentParser()
parser.add_argument('--start', type=int, help='start index')
parser.add_argument('--cpus', type=int, help='number of cpus')
parser.add_argument('--total', type=int, help='total number of points')
parser.add_argument('--job', type=int, help='job number')
parser.add_argument('--outdir', type=str, help='output directory')
args = parser.parse_args()

mypoints = []
start = args.start
cpus = args.cpus
total = args.total
job = args.job
outputdir = args.outdir
step = total // cpus

for i in range(cpus):
    mypoints.append([start, start+step])
    start += step

print(mypoints)

outdir = 'average_system/Outdir_lens_reconstruction'

lens_model_list = ['EPL', 'SHEAR']
z_source = 1.5
z_lens = 0.7
lensModel = LensModel(lens_model_list=lens_model_list, z_source=z_source, z_lens=z_lens)

# Load the data
with open(outdir+'/samples.pkl', 'rb') as f:
    samples_mcmc = pkl.load(f)

with open(outdir+'/pixel_grid.pkl', 'rb') as f:
    pixel_grid = pkl.load(f)

with open(outdir+'/random_positions.json', 'r', encoding='utf-8') as f:
    ran_pos = json.load(f)

with open(outdir+'/kwargs_result.json', 'r', encoding='utf-8') as f:
    kwargs_result = json.load(f)

percentile90 = {}
os.environ["OMP_NUM_THREADS"] = "1"

def dictionary_manager (shared_dict, dict_entry):
    shared_dict[dict_entry['index']] = dict_entry['y_rel_90']

def myprocess (points):
    start = points[0]
    end = points[1]

    inner_points = []
    mean_points = []

    for i in range(start, end, 1):
        t = False 

        while t == False:
            pix_x, pix_y = ran_pos[str(i)]['ra'], ran_pos[str(i)]['dec']
            bbh_x, bbh_y = pixel_grid.map_pix2coord(pix_x, pix_y)

            lensgw_result = lens_gw(bbh_x, bbh_y, lensModel, kwargs_result['kwargs_lens'])

            if len(lensgw_result['delta_t']) == 4:
                t = True
            else:
                break
                
        delta_t_array = (lensgw_result['delta_t'] - lensgw_result['delta_t'][0]) * 24 * 3600
        delta_mu_array = lensgw_result['muX'] / lensgw_result['muX'][0]

        y_rel_i = []
        ndim = 2
        nwalkers = 50

        pos = [np.array([0., 0.]) + 0.05*np.random.randn(ndim) for i in range(nwalkers)]
        sampler = emcee.EnsembleSampler(nwalkers, ndim, log_probability, args=(delta_t_array, delta_mu_array, samples_mcmc, y_rel_i))
        sampler.run_mcmc(pos, 10000, progress=True)

        # get 90th percentile 
        #y_rel_i = np.array(y_rel_i).flatten()
        #y_rel_i = np.sort(y_rel_i)
        #y_rel_i = y_rel_i[int(0.1*len(y_rel_i))]

        with open(outdir+'/imagelens.pkl', 'rb') as f:
            imageLens = pkl.load(f)

        flat_samples = sampler.get_chain(discard=1, thin=1, flat=True)
        y_rel = []
        xra = []
        yra = []

        for theta in flat_samples:
            x_gw, y_gw = theta

            # replicate the SAME stochastic step
            random_index = np.random.randint(0, len(samples_mcmc))
            sample = samples_mcmc[random_index]

            x_source, y_source = sample[13], sample[14]
            rel_dist = np.sqrt((x_source - x_gw)**2 + (y_source - y_gw)**2)

            y_rel.append(rel_dist)
            xra.append(x_gw)
            yra.append(y_gw)

        x, y = pixel_grid.map_coord2pix(xra, yra)

        xdist, ydist, f, r = [], [], [], []

        for i, xi in enumerate(x):
            pix_x = int(xi)
            pix_y = int(y[i])
            rel_dist = y_rel[i]
            flux = imageLens[pix_y, pix_x]

            xdist.append(pix_x)
            ydist.append(pix_y)
            f.append(flux)
            r.append(rel_dist)

        # then we want to do sum(r*f) / sum(f)
        r = np.array(r)
        f = np.array(f)
        weighted_mean = np.nansum(r*f) / np.nansum(f)
        mean = np.nanmean(r)

        print('point {0} done'.format(i))
        inner_points.append((i, weighted_mean, mean))
    return inner_points


import multiprocess as mp

if __name__ == '__main__':
    with mp.Pool(cpus) as p:   
        entry1 = p.map(myprocess, mypoints)
        percentile90 = {}
        meanpoints = {}
        for e in entry1:
            for point in e:
                percentile90[point[0]] ={'weighted_mean': point[1], 'mean': point[2]}

with open(outputdir+'weight_means_'+str(job)+'.json', 'w', encoding='utf-8') as f:
    json.dump(percentile90, f, ensure_ascii=False, indent=4)