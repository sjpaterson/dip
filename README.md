#  Deep Imaging Pipeline


 The Deep Imaging Pipeline (DIP) is adapted from the GLEAM-X pipeline (https://github.com/tjgalvin/GLEAM-X-pipeline).
 DIP is designed and optimized to process a large quantity of observations with minimal user input and then mosaic them to generate a deep field image.
 
 Configuration: Please edit "nextflow.config" to update user directories. The observations directory can be edited directly in the config or passed to the nextflow script with the paramater --obsdir.
 
 If using Pawsey and storing observation data in the /astro/mwasci/asvo directory, the report can be automatically updated with "createReport.py".
 This will update the report with the observational data reported by ASVO as ready to be processed.
 This requires MWA_CLIENT to be installed and the MWA_ASVO_API_KEY system variable to be set with you ASVO key.
 Link to AVSO documentation here.

 If not using Pawsey or your observations are not stored in /astro/mwasci/asvo, you will need to create symbolic links to each observation in your main observations directory.
 The use of symbolic links allows for easy reuse of observational data which will not be modified.


Containers:
This pipeline currently utilises two containers.
The first being the DIP container. The build information is in the container directory, however it utilises the MWA_REDUCE code which is from a private repository. You will require access to this repository to build the container. Alternatively, you may ask Sean Paterson for a copy of the container.
The second is the GLEAM-X container, this is a temporary situation due to current issues with BANE and AEGEAN.

 
 Using DIP:
 
 Update nextflow.config to reflect your user directories, the directory that will contain the symlinks to your mesasurement sets and any additional options.

 If using Pawsey and AVSO observations stored in /astro/mwasci/asvo: "createReport.py" can been run, DIP will then automatically create the symlinks for each batch of observations. You can control the number of observations to process at a time by editing dip.sbatch. The default is 120 which is reflected in the line "manageReport.py create 120", the value 120 can be changed to the number of desired observations to be processed per run.

 If not run on Pawsey or not using ASVO: Create symlinks to the observations you wish to process in your observations directory. It will process all symlinks in the directory so it is recommended to do it in batches suitable for your system.

 Step One: Run download.sh
 This is step uses minimum resources so can be run on the login node. A number of observations to request from the AVSO can be specified as an input, default is 120.
 
 Step Two: Run dip.sbatch
 This will need the be rerun until all observations have been processed.
 On success, DIP will replace the symlink with a folder containing the processed observation.

 Once all observations have been completed, they can be mosaicked together with dip_mosaic available from [Future GitHub link].
 Step Two: Run mosaic.sbatch

 Complete! Your deep image should now be accessible in the deep image folder specified in your nextflow.config.


 Notes for Pawsey users:
 The majority of the data management is automated.
 DIP will automatically create the symlinks required basing the data from the report created by createReport.py and specified in the nextflow.config.
 If an observaiton fails for a reason other than bad visibility data, it will automatically recreate the symlink and retry the next run.
 It will attempt an observation for a maximum of 3 times.
