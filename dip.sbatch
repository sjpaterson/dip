#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=24:00:00
#SBATCH --mem-per-cpu=8GB

module load nextflow
module load singularity

export NXF_OPTS="-Xms500M -Xmx2G"
export NXF_ANSI_LOG=false

singularity exec /pawsey/mwa/singularity/python/python_latest.sif python bin/manageReport.py create

nextflow run dip.nf -with-report

singularity exec /pawsey/mwa/singularity/python/python_latest.sif python bin/manageReport.py verify

