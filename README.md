# galaxy-center-localisation
[![DOI](https://zenodo.org/badge/1139670699.svg)](https://doi.org/10.5281/zenodo.22675771)

Associating lensed GWs with galactic centres 

Structure 
The project is run over several regimes 
- Small lens, Average lens, Large lens
- Uniform localisation prior
- Recast $r_{10}$ measurement (relative, not absolute) + Gaussian prior 
- Increased modelling uncertainties (5%, 10%)
- One alternative backgrounds under two competing priors (uniform in caustic, with uniform and Gaussian localisation priors)
- Weighted mean statistic

The detailed instructions to run the script for the basic lens simulation
(theta_E = 1.0", uncertainties = 1%, uniform prior) are as follows:
1. Create a python 3.10 conda environment.
2. The following packages are required: numpy, lenstronomy, seaborn,
   matplotlib, emcee, corner, pandas, astropy, tqdm.
3. Go to the `scripts/` directory.
4. Run `python galaxy_centre.py` to create the simulation, run the
   true BBH localisation, and simulate the BBH background (typical runtime ~5
   hours).
4. Without condor, to run the first 100 BBHs in the background with 4 CPUs, run 
   `python galaxy_centre_background.py --start 0 --cpus N --total X --job 1
   -- outdir OUTDIR`, with `start` the starting index, `cpus` the number of
   CPUs to use, `total` the number of background BBHs to run, `job` the label for
   the batch of points, and `outdir` the desired output directory. Runtime
   depends on CPUs available and number of points run.
5. OPTIONAL If running on condor, you can generate the dag files for the background
   by running the cells in `dagfilewriting.ipynb` (amend paths as needed).
   Typical full background runtime on cluster ~1 week.

This will generate the `average_system/` directory with the simulation,
reconstruction, localisation, and background in `Outdir_lens_reconstruction/`,
and the background localisation results in `OUTDIR/`.

To run the other case studies: 
- `galaxy_centre_unc.py` = Increased uncertainties
- `galaxy_centre_rrel.py` = Recast r with Gaussian prior
- `galaxy_centre_small.py` = Small theta_E lens
- `galaxy_centre_best.py` = Large theta_E lens 
- `galaxy_centre_weighted.py` = Weighted r_mean statistic
- `galaxy_centre_uniprio.py` = Background with caustic-uniform prior

The corresponding backgrounds can be run with the
`galaxy_centre_background_*.py` script with the same name.
