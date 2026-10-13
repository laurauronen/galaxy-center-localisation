from lenstronomy.LensModel.Solver.lens_equation_solver import LensEquationSolver

def lens_gw (ra, dec, lensmodel, kwargs_lens):
    """
    Given lens model and GW location, created lensed parameters for GW.

    Parameters:
    -----------
    ra: float
        Right ascension of the GW event
    dec: float
        Declination of the GW event
    lensmodel: class
        Lens model
    kwargs_lens: list
        Lens model parameters

    Returns:
    --------
    dictionary: dict
        Dictionary of lensed parameters
    """

    solver = LensEquationSolver(lensModel = lensmodel)
    theta_ra, theta_dec = solver.image_position_from_source(ra, dec, kwargs_lens)

    magnifications = lensmodel.magnification(theta_ra, theta_dec, kwargs_lens)
    arrival_times = lensmodel.arrival_time(theta_ra, theta_dec, kwargs_lens)

    image_types = []

    dictionary = {'muX': magnifications,
                  'delta_t': arrival_times, 
                  'delta_N': image_types,
                  'theta_ra': theta_ra, 
                  'theta_dec': theta_dec}

    return dictionary
