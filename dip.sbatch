#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=24:00:00
#SBATCH --mem-per-cpu=8GB

module load nextflow

export NXF_OPTS="-Xms500M -Xmx2G"
export NXF_ANSI_LOG=false

nextflow run /astro/mwasci/user/dip/dip.nf -with-report
