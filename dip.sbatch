#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --account=accountname
#SBATCH --partition=work
#SBATCH --time=24:00:00
#SBATCH --mem-per-cpu=8GB


CONTAINER=/software/projects/mwasci/user/containers/dip.sif

RUNNAME=$(date +%Y-%m-%d_%H-%M)

# Java for the user based Nextflow installation, and singulairty to run the reporting scripts.
module load nextflow/23.10.0
module load singularity/3.11.4-slurm

# Optimize Nextflow for running in a slurm process.
export NXF_OPTS="-Xms500M -Xmx2G"
export NXF_ANSI_LOG=false

# Check to ensure the beam data for mwa_pb_lookup exists. If not download it.
# The beamdata is no longer located at this destination, please contact us if required until
# a new home is created.
# if [[ ! -d "beamdata" ]]
#     then
#         mkdir "beamdata"
#         wget -P "beamdata" http://cerberus.mwa128t.org/mwa_full_embedded_element_pattern.h5
#         wget -O pb_lookup.tar.gz https://cloudstor.aarnet.edu.au/plus/s/77FRhCpXFqiTq1H/download
#         tar -xzvf pb_lookup.tar.gz -C "beamdata"
# fi

# Verify the contents of the report and then create the next 120 symlinks to process.
singularity exec $CONTAINER python bin/manageReport.py verify
singularity exec $CONTAINER python bin/manageReport.py create 120

# Process the observations.
nextflow run dip.nf -with-report -with-tower -name DIP_$RUNNAME

# Vertify the report contents after the processing run.
singularity exec $CONTAINER python bin/manageReport.py verify
