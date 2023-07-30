#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=24:00:00
#SBATCH --mem-per-cpu=4GB

CONTAINER=/astro/mwasci/user/containers/dip.sif

module load nextflow
module load singularity

export NXF_OPTS="-Xms500M -Xmx2G"
export NXF_ANSI_LOG=false

singularity exec $CONTAINER python bin/manageReport.py verify

nextflow run getBeamSize.nf -with-report
nextflow run convolveBeam.nf -with-report
nextflow run mosaic.nf -with-report

