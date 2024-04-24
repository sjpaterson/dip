// Deep Image Pipeline
nextflow.enable.dsl=2


// Update the report to ensure the entry for the obsid is clear.
// Perform a secondary check to ensure the directory is a synbolic link (observation has not been processed).
// If it isn't, then it has been processed and therefore exit with error.
process startObsProcessing {
  input:
    path obsid
  output:
    path obsid

    """
    obsStartCheckReport.py "$params.reportCsv" ${obsid} "$params.obsdir"
    """
}

// Calibrate the obsid flagging bad tiles.
process calibrate {
  input:
    path obsid
  output:
    path obsid

    """
    export MWA_PB_BEAM="$projectDir/beamdata/gleam_xx_yy.hdf5"
    export MWA_PB_JONEs="$projectDir/beamdata/gleam_jones.hdf5"
    cd $obsid
    calibrate.py $projectDir $obsid $params.reportCsv
    """
}

// Perform the image processing with wsclean.
process image {
  publishDir params.obsdir, mode: 'copy', overwrite: true

  // Set SLURM job time limit to 360 minutes, increase it each time it times out for a maximum of 2 retries.
  time { 360.minutes * task.attempt }
  errorStrategy 'retry'
  maxRetries 2
  memory '110G'

  input:
    path obsid
  output:
    path obsid

    """
    cd $obsid
    image.py $projectDir $obsid $params.briggs $params.tukey $params.reportCsv
    """
}

// Join the linear polarisations and scale them to match GLEAM.
process postImage {
  publishDir params.obsdir, mode: 'copy', overwrite: true

  time 3.hour
  memory '176G'

  input:
    path obsid
    each subchan
  output:
    // Only output the new images and diagnostics created for the subchan processed.
    path "${obsid}/*_deep-*-image-*_warp.fits"
    path "${obsid}/*_deep-*-image-*_comp.fits"
    path "${obsid}/*_deep-*-image-*_rms.fits"
    path "${obsid}/*_deep-*-image-*_bkg.fits"
    path "${obsid}/*_deep-*-image-*_cf.fits"
    path "${obsid}/*_deep-*-image-*_scaled.fits"
    path "${obsid}/*-beam.fits"
    path "${obsid}/*_xm.fits"
    path "${obsid}/*weight*.fits"
    path "${obsid}/matched_*.csv"
    path "${obsid}/acalc_*.txt"
    path "${obsid}/*.png"

    """
    cd $obsid
    postImage.py $projectDir $obsid $subchan $params.reportCsv $params.ra $params.dec
    """
}



workflow {
  // Directory where the observations are stored.
  // Only process the symbolic links.
  obsDirFull = params.obsdir + '/*'
  obsDirCh = Channel.fromPath(obsDirFull, type: 'dir').filter{java.nio.file.Files.isSymbolicLink(it)}
  subChans = Channel.of('0000', '0001', '0002', '0003', 'MFS')

  
  // Process each observation (symlink) in the specified observation directory.
  startObsProcessing(obsDirCh)
  calibrate(startObsProcessing.out)
  image(calibrate.out)
  postImage(image.out, subChans)
}
