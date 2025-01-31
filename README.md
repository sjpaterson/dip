#  Deep Imaging Pipeline


 The Deep Imaging Pipeline (DIP) is adapted from the GLEAM-X pipeline (https://github.com/tjgalvin/GLEAM-X-pipeline).
 DIP is designed and optimized to process a large quantity of observations with minimal user input and then mosaic them to generate a deep field image.
 Default configuration is for DIP to be run on Pawsey Setonix and utilises AVSO to download oberservations.
 
 Configuration: Please edit "nextflow.config" to update user directories. The observations directory can be edited directly in the config or passed to the nextflow script with the paramater --obsdir.
 
 If using Pawsey and storing observation data in the /scratch/mwasci/asvo directory, the report can be automatically updated with "createReport.py".
 This will update the report with the observational data reported by ASVO as ready to be processed.
 This requires MWA_CLIENT (https://github.com/MWATelescope/manta-ray-client) to be installed and the MWA_ASVO_API_KEY system variable to be set with you ASVO key.
 https://mwatelescope.atlassian.net/wiki/spaces/MP/pages/24972779/MWA+ASVO+Command+Line+Clients

 If not using Pawsey or your observations are not stored in /scratch/mwasci/asvo, you will need to create symbolic links to each observation in your main observations directory.
 The use of symbolic links allows for easy reuse of observational data which will not be modified.


Containers:
The build information is in the container directory, however it utilises the MWA_REDUCE code which is from a private repository. You will require access to this repository to build the container. Alternatively, you may ask Sean Paterson for a copy of the container.

 
 Using DIP:
 
 Update nextflow.config to reflect your user directories, the directory that will contain the symlinks to your mesasurement sets and any additional options.
 Update dip.sbatch with your accountname and the location of the DIP singularity container (recommended storage location of the container is /software/projects/[project]/[username]/containers).
 Currently the beaminfo is not hosted online, please contact myself to obtain a copy of this to include in the beaminfo directory.

 For AVSO, you will need to set your MWA_ASVO_API_KEY environment variable.
 https://mwatelescope.atlassian.net/wiki/spaces/MP/pages/24972779/MWA+ASVO+Command+Line+Clients#Finding-your-API-key

 To monitor the Nextflow run, you will need to set your TOWER_ACCESS_TOKEN environment variable.
 https://metagenomics-pipelines.readthedocs.io/en/latest/nf_tower.html
 
 If not run on Pawsey or not using ASVO: Create symlinks to the observations you wish to process in your observations directory. It will process all symlinks in the directory so it is recommended to do it in batches suitable for your system.

 Step One: Run download.sh
 This step uses minimum resources so can be run on the login node. A number of observations to request from the AVSO can be specified as an input, default is 120.
 
 Step Two: Run dip.sbatch
 This will need the be rerun until all observations have been processed.
 On success, DIP will replace the symlink with a folder containing the processed observation.

 To check the download status and provide the number of observations successfully downloaded and available to process, status.sh can be run.

 Once all observations have been completed, they can be mosaicked together with dip_mosaic available from [Future GitHub link].
 
 Complete! Your deep image should now be accessible in the deep image folder specified in your nextflow.config.


 Notes for Pawsey users:
 The majority of the data management is automated.
 DIP will automatically create the symlinks required basing the data from the report created by createReport.py and specified in the nextflow.config.
 If an observaiton fails for a reason other than bad visibility data, it will automatically recreate the symlink and retry the next run.
 It will attempt an observation for a maximum of 3 times.
