#!/bin/bash -l

CONTAINER=/software/projects/$PAWSEY_PROJECT/$USER/containers/mantaray.sif

module load singularity/4.1.0-slurm

# Start downloading specified number of obs, default is 120.
singularity exec $CONTAINER python bin/manageReport.py download $1
