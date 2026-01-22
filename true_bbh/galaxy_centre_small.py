import os

from lensgw import lens_gw
from log_funcs_small import log_probability
from random_position_generator import random_position_generator as random_position
import json
import pickle 

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import emcee
import corner
import seaborn as sns
import pandas as pd 

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
from lenstronomy.LightModel.Profiles.gaussian import GaussianEllipse
from lenstronomy.Workflow.fitting_sequence import FittingSequence
gauss = GaussianEllipse()

plt.rcParams.update({'font.family': 'serif'})

outdir = 'small_system/Outdir_lens_reconstruction'
# create the output directory if it does not exist
if not os.path.exists(outdir):
    os.makedirs(outdir)

#########################
# SET UP THE LENS MODEL #
#########################
# lens characteristics
center_x, center_y = 0, 0
# source (EM) characteristics
source_x, source_y = -0.02, 0.01

z_source = 2.0
z_lens = 1.5
lens_model_list = ['EPL', 'SHEAR']
kwargs_epl = {'theta_E': 0.5, 'center_x': center_x, 'center_y': center_y, 'e1': 0., 'e2': 0.1, 'gamma': 2.0}
kwargs_shear = {'gamma1': -0.05, 'gamma2': 0.1}
kwargs_lens = [kwargs_epl, kwargs_shear]
lensModel = LensModel(lens_model_list=lens_model_list, z_source=z_source, z_lens=z_lens)

# lens light
kwargs_lens_light_mag = [{'magnitude': 22, 
                          'R_sersic': .1, 
                          'n_sersic': 4, 
                          'e1': 0, 
                          'e2': 0.1, 
                          'center_x': center_x, 
                          'center_y': center_y}]
# source light
kwargs_source_mag = [{'magnitude': 25, 
                      'R_sersic': 0.01, 
                      'n_sersic': 1, 
                      'e1': -0.1, 
                      'e2': 0., 
                      'center_x': source_x, 
                      'center_y': source_y}]

lens_light_model_list = ['SERSIC_ELLIPSE'] 
source_light_model_list = ['SERSIC_ELLIPSE']
lensLightModel = LightModel(light_model_list=lens_light_model_list)
sourceLightModel = LightModel(light_model_list=source_light_model_list)

kwargs_source_light = data_util.magnitude2amplitude(light_model_class= sourceLightModel, 
                                                    kwargs_light_mag = kwargs_source_mag, 
                                                    magnitude_zero_point = 25.75)
kwargs_lens_light = data_util.magnitude2amplitude(light_model_class= lensLightModel, 
                                                  kwargs_light_mag = kwargs_lens_light_mag, 
                                                  magnitude_zero_point = 25.75)

kwargs_model = {'lens_model_list': ['EPL', 'SHEAR'],
                'lens_light_model_list': ['SERSIC_ELLIPSE'],
                'source_light_model_list': ['SERSIC_ELLIPSE']}

#####################
# GENERATE THE DATA #
#####################
numPix = 40
deltaPix = 0.067 

shift = numPix * deltaPix / 2

ra_start, dec_start = center_x - shift, center_y - shift
transform_pix2angle = np.array([[1, 0], [0, 1]]) * deltaPix
kwargs_pixel = {'nx': numPix, 'ny': numPix, 'ra_at_xy_0': ra_start, 'dec_at_xy_0': dec_start, 'transform_pix2angle': transform_pix2angle}
pixel_grid = PixelGrid(**kwargs_pixel)

fwhm = 0.067 #HST/JWST: 0.067, TMT/ELT: 0.01 in IR
kwargs_psf = {'psf_type': 'GAUSSIAN', 'fwhm': fwhm, 'pixel_size': deltaPix}
psf = PSF(**kwargs_psf)
kwargs_numerics = {'supersampling_factor': 1, 'supersampling_convolution': False}

imageModel = ImageModel(data_class=pixel_grid, 
                        psf_class=psf, 
                        lens_model_class=lensModel, 
                        source_model_class=sourceLightModel, 
                        lens_light_model_class=lensLightModel, 
                        point_source_class=None, 
                        kwargs_numerics=kwargs_numerics)

imageLens = imageModel.image(kwargs_lens=kwargs_lens,
                              kwargs_source=kwargs_source_light,
                                kwargs_lens_light=kwargs_lens_light,
                                kwargs_ps=None)

f, ax = plt.subplots(1, 2, figsize=(10, 10), sharex=False, sharey=False)

lens_plot.lens_model_plot(ax[0], lensModel=lensModel, kwargs_lens=kwargs_lens, sourcePos_x=source_x, sourcePos_y=source_y, point_source=True, with_caustics=True, fast_caustic=True)
ax[0].set_xlim(-0.5, 0.5)
ax[0].set_ylim(-0.5, 0.5)

ax[1].imshow(np.log10(imageLens), origin='lower', cmap='magma', vmax=10, vmin=-10)
plt.savefig(outdir+'/lens.png')

#####################
# OBSERVE THE DATA  #
#####################
background_rms = np.sqrt(np.mean((imageLens[0:10,0:10])**2))
exposure_time = 2500

kwargs_data = {'image_data': imageLens, 'background_rms': background_rms, 'exposure_time': exposure_time, 'ra_at_xy_0': ra_start, 'dec_at_xy_0': dec_start, 'transform_pix2angle': transform_pix2angle}

data_class = ImageData(**kwargs_data)

image_model = imageModel.image(kwargs_lens=kwargs_lens, kwargs_source=kwargs_source_light, kwargs_lens_light=kwargs_lens_light)

poisson = image_util.add_poisson(image_model, exp_time=exposure_time)
bkg = image_util.add_background(image_model, sigma_bkd=background_rms)
image_real = image_model + poisson + bkg

data_class.update_data(image_real)
kwargs_data['image_data'] = image_real

f, axes = plt.subplots(1, 1, figsize=(5, 5), sharex=False, sharey=False)

ax = axes

# set background to black 
ax.set_facecolor('black')
im = ax.matshow(np.log10(image_real), origin='lower', cmap='magma', vmin=-6, vmax=0)
plt.colorbar(im, ax=ax, label='log$_{10}$ flux', fraction=0.046, pad=0.04)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
ax.autoscale(False)
plt.savefig(outdir+'/observed.png')

##############################
# SET UP LENS RECONSTRUCTION #
##############################
# lens models
fixed_lens = []
kwargs_lens_init = []
kwargs_lens_sigma = []
kwargs_lower_lens = []
kwargs_upper_lens = []


fixed_lens.append({})  # for this example, we fix the power-law index of the lens model to be isothermal
kwargs_lens_init.append({'theta_E': 0.5, 'e1': 0., 'e2': 0.,
                         'center_x': 0., 'center_y': 0., 
                         'gamma': 2.0})
kwargs_lens_sigma.append({'theta_E': .2, 'e1': 0.1, 'e2': 0.1,
                         'center_x': 0.1, 'center_y': 0.1, 
                         'gamma': 0.5})
kwargs_lower_lens.append({'theta_E': 0.3, 'e1': -0.2, 'e2': -0.2, 
                          'center_x': -0.1, 'center_y': -0.1, 
                          'gamma': 1.8})
kwargs_upper_lens.append({'theta_E': 0.7, 'e1': 0.2, 'e2': 0.2, 
                          'center_x': 0.1, 'center_y': 0.1, 
                          'gamma': 2.2})

fixed_lens.append({'ra_0': 0, 'dec_0': 0})
kwargs_lens_init.append({'gamma1': 0., 'gamma2': 0.})
kwargs_lens_sigma.append({'gamma1': 0.05, 'gamma2': 0.05})
kwargs_lower_lens.append({'gamma1': -0.2, 'gamma2': -0.2})
kwargs_upper_lens.append({'gamma1': 0.2, 'gamma2': 0.2})

lens_params = [kwargs_lens_init, kwargs_lens_sigma, fixed_lens, 
               kwargs_lower_lens, kwargs_upper_lens]

fixed_source = []
kwargs_source_init = []
kwargs_source_sigma = []
kwargs_lower_source = []
kwargs_upper_source = []

fixed_source.append({})
kwargs_source_init.append({'R_sersic': 0.01, 'n_sersic': 1, 
                           'e1': 0, 'e2': 0, 'center_x': 0., 
                           'center_y': 0.0, 'amp': 500})
kwargs_source_sigma.append({'n_sersic': 0.5, 'R_sersic': 0.04, 
                            'e1': 0.5, 'e2': 0.5, 'center_x': 0.2, 
                            'center_y': 0.2, 'amp': 200})
kwargs_lower_source.append({'e1': -0.2, 'e2': -0.2, 
                            'R_sersic': 0.005, 'n_sersic': .5, 
                            'center_x': -0.3, 'center_y': -0.3, 
                            'amp': 0.1})
kwargs_upper_source.append({'e1': 0.2, 'e2': 0.2, 
                            'R_sersic': 0.03, 'n_sersic': 5., 
                            'center_x': 0.3, 'center_y': 0.3, 
                            'amp': 1000})

source_params = [kwargs_source_init, kwargs_source_sigma, 
                 fixed_source, kwargs_lower_source, kwargs_upper_source]

fixed_lens_light = []
kwargs_lens_light_init = []
kwargs_lens_light_sigma = []
kwargs_lower_lens_light = []
kwargs_upper_lens_light = []

fixed_lens_light.append({})
kwargs_lens_light_init.append({'R_sersic': 0.1, 'n_sersic': 4, 
                               'e1': 0.0, 'e2': 0.0, 
                               'center_x': 0., 'center_y': 0, 
                               'amp': 200})
kwargs_lens_light_sigma.append({'n_sersic': 1, 'R_sersic': 0.05, 
                                'e1': 0.5, 'e2': 0.5, 
                                'center_x': 0.1, 'center_y': 0.1, 
                                'amp': 100})
kwargs_lower_lens_light.append({'e1': -0.2, 'e2': -0.2, 
                                'R_sersic': 0.05, 'n_sersic': .5, 
                                'center_x': -0.1, 'center_y': -0.1, 
                                'amp': 0.1})
kwargs_upper_lens_light.append({'e1': 0.2, 'e2': 0.2, 
                                'R_sersic': 0.2, 'n_sersic': 5., 
                                'center_x': 0.1, 'center_y': 0.1, 
                                'amp': 500})

lens_light_params = [kwargs_lens_light_init, kwargs_lens_light_sigma, 
                     fixed_lens_light, kwargs_lower_lens_light, 
                     kwargs_upper_lens_light]

kwargs_params = {'lens_model': lens_params,
                'source_model': source_params,
                'lens_light_model': lens_light_params,
                }

kwargs_likelihood = {'source_marg': False}

multi_band_list = [[kwargs_data, kwargs_psf, kwargs_numerics]]

kwargs_data_joint = {'multi_band_list': multi_band_list,
                     'multi_band_type': 'single-band'
                    }
kwargs_constraints = {'linear_solver': False}

fitting_seq = FittingSequence(kwargs_data_joint, kwargs_model,
                              kwargs_constraints, kwargs_likelihood,
                              kwargs_params)

fitting_kwargs_list = [['PSO', {'sigma_scale': 1., 'n_particles': 10,
                                'n_iterations': 5000}],
                       ['MCMC', {'n_burn': 2000, 'n_run': 100000,
                                 'n_walkers': 50, 'sigma_scale': .1}]
                       ]

chain_list = fitting_seq.fit_sequence(fitting_kwargs_list)
kwargs_result = fitting_seq.best_fit()

modelPlot = ModelPlot(multi_band_list, kwargs_model,
                      kwargs_result, arrow_size=0.02,
                      cmap_string="magma",
                     linear_solver=kwargs_constraints.get('linear_solver', True))

f, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=False, sharey=False)

modelPlot.data_plot(ax=axes[0,0])
modelPlot.model_plot(ax=axes[0,1])
modelPlot.normalized_residual_plot(ax=axes[0,2])
modelPlot.source_plot(ax=axes[1, 0], deltaPix_source=0.01, numPix=100, v_min=-5, v_max=0)
modelPlot.convergence_plot(ax=axes[1, 1], v_max=1)
modelPlot.magnification_plot(ax=axes[1, 2])
f.tight_layout()
f.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0., hspace=0.05)
plt.savefig(outdir+'/fit.png')

f, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=False, sharey=False)

modelPlot.decomposition_plot(ax=axes[0,0], text='Lens light', lens_light_add=True, unconvolved=True)
modelPlot.decomposition_plot(ax=axes[1,0], text='Lens light convolved', lens_light_add=True)
modelPlot.decomposition_plot(ax=axes[0,1], text='Source light', source_add=True, unconvolved=True)
modelPlot.decomposition_plot(ax=axes[1,1], text='Source light convolved', source_add=True)
modelPlot.decomposition_plot(ax=axes[0,2], text='All components', source_add=True, lens_light_add=True, unconvolved=True)
modelPlot.decomposition_plot(ax=axes[1,2], text='All components convolved', source_add=True, lens_light_add=True, point_source_add=True)
f.tight_layout()
f.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0., hspace=0.05)
print(kwargs_result)
plt.savefig(outdir+'/decomposition.png')

sampler_type, samples_mcmc, param_mcmc, dist_mcmc  = chain_list[1]
param_class = fitting_seq.param_class
for i in range(len(chain_list)):
    chain_plot.plot_chain_list(chain_list, i)
plt.savefig(outdir+'/chains.png')

print("number of non-linear parameters in the MCMC process: ", len(param_mcmc))
print("parameters in order: ", param_mcmc)
print("number of evaluations in the MCMC process: ", np.shape(samples_mcmc)[0])
n_sample = len(samples_mcmc)
print(n_sample)
samples_mcmc_cut = samples_mcmc[int(n_sample*1/2.):]

#########################
# GENERATE REAL GW DATA #
#########################
bbh_x, bbh_y = source_x, source_y

theta_source = [bbh_x, bbh_y]
lensgw_result = lens_gw(bbh_x, bbh_y, lensModel, kwargs_result['kwargs_lens'])

delta_t_array = (lensgw_result['delta_t'] - lensgw_result['delta_t'][0]) * 24 * 3600
delta_mu_array = lensgw_result['muX'] / lensgw_result['muX'][0]

ndim = 2
nwalkers = 50
y_rel = []

pos = [np.array([0, 0]) + 0.05*np.random.randn(ndim) for i in range(nwalkers)]

sampler = emcee.EnsembleSampler(nwalkers,
                                ndim, log_probability,
                                args=(delta_t_array,
                                      delta_mu_array,
                                      samples_mcmc,
                                      y_rel))
sampler.run_mcmc(pos, 10000, progress=True)

samples = sampler.get_chain()
flat_samples = sampler.get_chain(discard=1, thin=1, flat=True)

plt.figure()
fig = corner.corner(flat_samples, labels=["$ra$", "$dec$"], truths=[0, 0], range=[(-1.0,1.0),(-1.0,1.0)])
plt.savefig(outdir+'/bbh_corner.png')

plt.figure()
plt.hist(y_rel, bins=100, histtype='step', color='k', linewidth=2, cumulative=True, density=True) 
plt.xlabel(r'$r_{rel}$')
plt.ylabel('CDF')
plt.axhline(0.1 , color='mediumvioletred', linestyle='--', label='$r_{10}$')
plt.legend()
plt.savefig(outdir+'/bbh_distance.png')

# get 90th percentile 
y_rel = np.array(y_rel)
y_rel_90 = np.nanpercentile(y_rel, 10)

#########################
# GENERATE RANDOM DATA  #
#########################

imageModel = ImageModel(data_class=pixel_grid,
                        psf_class=psf,
                        lens_model_class=None,
                        source_model_class=sourceLightModel,
                        lens_light_model_class=None,
                        point_source_class=None,
                        kwargs_numerics=kwargs_numerics)

imageLens = imageModel.image(kwargs_lens=None,
                                kwargs_source=kwargs_source_light,
                                    kwargs_lens_light=None,
                                    kwargs_ps=None)

ran_pos = random_position(imageLens, 10000).T

flat_ra = flat_samples[:,0]
flat_dec = flat_samples[:,1]
flat_to_pix_ra = pixel_grid.map_coord2pix(flat_ra, flat_dec)

true_pix_ra = pixel_grid.map_coord2pix(source_x, source_y)

plt.figure()
plt.axvline(x=20, color='k', label='Posterior')
plt.imshow(imageLens, origin='lower', cmap='magma', norm=LogNorm(vmin=0.000001, vmax=0.1))
# make 2d kde plot 
x = flat_to_pix_ra[0]
y = flat_to_pix_ra[1]
df = pd.DataFrame({'x': x, 'y': y})
plt.rcParams['font.family'] = 'serif'
sns.kdeplot(x=df.x, y=df.y, color='k', levels=[1-0.95], zorder=1)
plt.scatter(true_pix_ra[0], true_pix_ra[1], marker='x', c='crimson', zorder=2, s=100, label='True position')
plt.xlim(true_pix_ra[0]-10, true_pix_ra[0]+10)
plt.ylim(true_pix_ra[1]-10, true_pix_ra[1]+10)
plt.legend()
plt.savefig(outdir+'/kde.png')

plt.figure()
plt.imshow(imageLens, origin='lower', cmap='magma', norm=LogNorm(vmin=0.000001, vmax=0.1))
plt.scatter(ran_pos[1][:5000], ran_pos[0][:5000], color='white', s=5, marker='d', label='GW', zorder=5, alpha=0.1)
plt.xlim(10,30)
plt.ylim(10,30)
plt.savefig(outdir+'/ran_pos.png')

#####################
# SAVE THE RESULTS  #
#####################
# convert ran_pos to dictionary
pos_dict = {}

for i in range(len(ran_pos[0])):
    pos_dict[i] = {'ra': ran_pos[0][i], 'dec': ran_pos[1][i]}

with open(outdir+'/random_positions.json', 'w', encoding='utf-8') as f:
    json.dump(pos_dict, f)

# save the true position to a file
true_pos = {'ra': source_x, 'dec': source_y, '90th_percentile': y_rel_90}
with open(outdir+'/true_position.json', 'w', encoding='utf-8') as f:
    json.dump(true_pos, f)

with open(outdir+'/samples.pkl', 'wb') as f:
    pickle.dump(samples_mcmc, f)

# save pixel_grid2
with open(outdir+'/pixel_grid.pkl', 'wb') as f:
    pickle.dump(pixel_grid, f)

# save the lens model
with open(outdir+'/kwargs_result.json', 'w', encoding='utf-8') as f:
    json.dump(kwargs_result, f)

with open(outdir+'/position_mcmc.pkl', 'wb') as f:
    pickle.dump(flat_samples, f)

with open(outdir+'/modelplot.pkl', 'wb') as f:
    pickle.dump(modelPlot, f)

with open(outdir+'/relative_distance.pkl', 'wb') as f:
    pickle.dump(y_rel, f)