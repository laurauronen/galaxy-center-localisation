# galaxy-center-localisation
Associating lensed GWs with galactic centres 

Structure 
The project is run over several regimes 
- Small lens 
- Average lens
- Large lens
- Increased modelling uncertainties (3%, 5%, 10%) 
- Recast $r_{10}$ measurement (relative, not absolute) + Gaussian prior 

The repository is structured as follows 
- true$_$bbh : to run 'main' script for lens reconstruction + true BBH localisation 
- bkgs : to run background localisation 
- submit : generic condor submission scripts 
- log$_$funcs : log likelihoods (for each specified regime), GW lensing function, random position generator for bkg
- misc$_$scripts : plotting and dag-writing scripts
- results : summary result files (json dict with true 90th percentile, bkg 90th percentile, and FAP) 

