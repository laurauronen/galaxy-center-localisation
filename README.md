# galaxy-center-localisation
[![DOI](https://zenodo.org/badge/1139670699.svg)](https://doi.org/10.5281/zenodo.22675771)

Associating lensed GWs with galactic centres 

Structure 
The project is run over several regimes 
- Small lens, Average lens, Large lens
- Uniform localisation prior
- Recast $r_{10}$ measurement (relative, not absolute) + Gaussian prior 
- Increased modelling uncertainties (3%, 5%, 10%)
- Two alternative backgrounds (Gaussian and Uniform in diamond caustic)
- Weighted mean statistic

The repository is structured as follows 
- true_bbh : to run 'main' script for lens reconstruction + true BBH localisation 
- bkgs : to run background localisation 
- submit : generic condor submission scripts 
- log_funcs : log likelihoods (for each specified regime), GW lensing function, random position generator for bkg
- misc_scripts : plotting and dag-writing scripts
- results : summary result files (json dict with true 90th percentile, bkg 90th percentile, and FAP) 

