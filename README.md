#  Deep Imaging Pipeline


 The Deep Imaging Pipeline is adapted from the GLEAM-X pipeline (https://github.com/tjgalvin/GLEAM-X-pipeline).
 DIP is designed to process a large quantity of observations with minimal user input and then mosaic them to generate a deep field image.
 
 Configuration: Please edit nextflow.config to update user directories. The observations directory can be edited directly in the config or passed to the nextflow script with the paramater --obsdir.
 
 If using Pawsey and storing observation data in the /astro/wmasci/asvo, the reports can be automatically updated createReport.py.
 This will update the reports with the observational data reported by ASVO as ready to be processed.
 This requires MWA_CLIENT to be installed and the MWA_ASVO_API_KEY system variable to be set with you ASVO key.
 Link to AVSO documentation here.

 If not using Pawsey or your observations are not store on /astro/mwasci/asvo, you will need to create symbolic links to your observations in your observation directory.
 The use of symbolic links allows for easy reuse of observational data which will not be modified.


Containers:
This pipeline utilises two containers.
The first being the DIP container, this can be built from the dip.def in the container subfolder.
The second is the GLEAM-X container which contains the binaries required for calibration, these are not publicly available.

 
 Using DIP:
 
 Update nextflow.config to reflect your user directories, the directory that will hold the symlinks to your mesasurement sets and any additional options.

 If using Pawsey and AVSO observations stored on /astro/mwasci/asvo: createReport.py can been run, DIP will then automatically create the symlinks for each batch of observations. You can control the number of observations to process at a time by editing dip.sbatch. The default is 120 which is reflected in the line "manageReport.py create 120", the value 120 can be changed to the number of desired observations per run.

 If not run on Pawsey or using ASVO: Create symlinks to the observations you wish to process in your observations directory. It will process all symlinks in the directory so it is recommended to do it in batches suitable for your system.

 
 First run dip.sbatch
 This will need the be rerun until all observations have been processed.
 On success, DIP will replace the symlink with a folder containing the processed observation.

 Then run mosaic.sbatch

 Completed! Your deep image should now be accessible in the deep image folder specified in your nextflow.config.


 Notes for Pawsey users:
 The majority of the data management is automated.
 DIP will automatically create the symlinks required basing the data from the report created by createReport.py and specified in the nextflow.config.
 If an observaiton fails for a reason other than bad visibility data, it will automatically recreate the symlink and retry the next run.
 It will attempt an observation for a maximum of 3 times.
