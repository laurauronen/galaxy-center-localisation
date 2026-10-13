from lensgw import lens_gw
from lenstronomy.LensModel.lens_model import LensModel
import numpy as np

lens_model_list = ['EPL', 'SHEAR']
z_source = 1.5
z_lens = 0.7
lensModel = LensModel(lens_model_list=lens_model_list, z_source=z_source, z_lens=z_lens)

def log_likelihood (time_delays,magnifications,samples_mcmc, y_rel, theta): 

    random_index = np.random.randint(0, len(samples_mcmc))
    sample = samples_mcmc[random_index]

    kwargs_lens = [{'theta_E' : sample[0],
                    'e1' : sample[2], 
                    'e2' : sample[3], 
                    'center_x' : sample[4], 
                    'center_y' : sample[5],
                    'gamma' : sample[1]},
                    {'gamma1' : sample[6],
                     'gamma2' : sample[7]}]

    x_source, y_source = sample[13], sample[14]
    x_gw = theta[0]
    y_gw = theta[1]

    rel_dist = np.sqrt((x_source - x_gw)**2 + (y_source - y_gw)**2)
    #rel_dist = np.sqrt(theta[0]**2 + theta[1]**2) 

    model = lens_gw(x_gw, y_gw, lensModel, kwargs_lens)
    if len(model['delta_t']) > 1:
        y_rel.append(rel_dist)
        model_dt = (model['delta_t'] - model['delta_t'][0]) * 24 * 3600
        model_dmu = model['muX'] / model['muX'][0]

        model_dt = model_dt[1:]
        model_dmu = model_dmu[1:]

        time_delays = time_delays[1:]
        magnifications = magnifications[1:]

        # compute the log likelihood
        log_l = 0

        if len(model_dt) == len(time_delays):
            for i in range(len(time_delays)):
                sigma_t = time_delays[i] * 0.01
                log_l += -0.5*(time_delays[i] - model_dt[i])**2/sigma_t**2

            for i in range(len(magnifications)):
                sigma_mu = magnifications[i] * 0.2
                log_l += -0.5*(magnifications[i] - model_dmu[i])**2/sigma_mu**2

        else:
            log_l = -np.inf

    else: 
        log_l = -np.inf

    return log_l

def log_prior (theta):

    x,y = theta

    if -0.5 < x < 0.5 and -0.5 < y < 0.5:
        return 0.0
    return -np.inf

def log_probability (theta, time_delays, magnifications, samples_mcmc, y_rel):

    lp = log_prior(theta)

    if not np.isfinite(lp):
        return -np.inf

    ll = log_likelihood(time_delays, magnifications, samples_mcmc, y_rel, theta)
    if not np.isfinite(ll):
        return -np.inf

    return lp + ll