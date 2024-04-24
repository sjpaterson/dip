#!/bin/bash -l

CONTAINER=containers/dip.sif

module load singularity/3.11.4-slurm

# Start downloading specified number of obs, default is 120.
singularity exec $CONTAINER python bin/manageReport.py download $1
