#  Deep Imaging Pipeline - GLEAM-X

 This branch is the version of the pipeline closest to the GLEAM-X pipeline. The outputs from this will closely match what will be obtained from GLEAM-X.

 This pipeline is a conversion of the GLEAM-X pipeline (https://github.com/tjgalvin/GLEAM-X-pipeline) into a Nextflow script with some minor modifications to suit deep imaging requirements.

 The pipeline is still a work in progress, there are many sections which need updating and areas requiring a large amount of improvement. The current implementation is an intiial test to get everything working. Further enhancements are planned to improve the flow.
 
 Configuration: Please edit nextflow.config to update user directories. The observations directory can be edited directly in the config or passed to the nextflow script with the paramater --obsdir.
 Additionally, the dip.sbatch will need to be edited to point to the directory dip is stored.

 Execution: sbatch dip.sbatch



 Pipeline:

 Generate Calibration - Tested

 Apply Calibration - Tested

 Flag UV - Tested

 Image - Tested

 Post Image - Tested


