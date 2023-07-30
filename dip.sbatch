#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=24:00:00
#SBATCH --mem-per-cpu=8GB

CONTAINER=/astro/mwasci/user/containers/dip.sif

module load nextflow
module load singularity

export NXF_OPTS="-Xms500M -Xmx2G"
export NXF_ANSI_LOG=false

singularity exec $CONTAINER python bin/manageReport.py verify
singularity exec $CONTAINER python bin/manageReport.py create 120

nextflow run dip.nf -with-report

singularity exec $CONTAINER python bin/manageReport.py verify
