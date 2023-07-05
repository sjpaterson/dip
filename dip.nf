// Deep Image Pipeline
nextflow.enable.dsl=2

process checkBeamData{
  output:
    val 'completed'
  """
  #! /bin/bash -l

  if [[ ! -d "$projectDir/beamdata" ]]
    then
        mkdir "$projectDir/beamdata"
        wget -P "$projectDir/beamdata" http://cerberus.mwa128t.org/mwa_full_embedded_element_pattern.h5
        wget -O pb_lookup.tar.gz https://cloudstor.aarnet.edu.au/plus/s/77FRhCpXFqiTq1H/download
        tar -xzvf pb_lookup.tar.gz -C "$projectDir/beamdata"
  fi
  """
}

// A secondary check to ensure the directory is a synbolic link (observation has not been processed).
// If it isn't then it has been processed, therefore exit with error.
// Else continue and clear the report entry.
process startObsProcessing {
  input:
    path obsid
    // val ready
  output:
    path obsid

    """
    obsStartCheckReport.py "$params.reportCsv" ${obsid} "$params.obsdir"
    """
}

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

process image {
  // If you need the entire image output for debugging or assessing the observations, uncomment the below.
  publishDir params.obsdir, mode: 'copy', overwrite: true

  // Set SLURM job time limit to 150 minutes, increase it by 200 minutes each time it times out for a maximum of 3 retries.
  time { 360.minutes * task.attempt }
  errorStrategy 'retry'
  maxRetries 3
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

process postImage {
  label 'gleamx'
  publishDir params.obsdir, mode: 'copy', overwrite: true

  time 3.hour
  memory '176G'

  input:
    path obsid
    each subchan
  output:
    // Only output the final images. If the interim files are required, uncomment the publish option in the image process.
    path "${obsid}/*_deep-*-image-*_warp.fits"
    path "${obsid}/*_deep-*-image-*_comp.fits"
    path "${obsid}/*_deep-*-image-*_rms.fits"
    path "${obsid}/*_deep-*-image-*_bkg.fits"
    path "${obsid}/*weight*.fits"

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

  // To move to the sbatch instead to not need to wait to spawn a new job
  // Check to see if the beam data for mwa_pb_lookup exists. If not download it.
  // checkBeamData()
  
  // Process each observation in the specified observation directory.
  //startObsProcessing(obsDirCh, checkBeamData.out)
  startObsProcessing(obsDirCh)
  calibrate(startObsProcessing.out)
  image(calibrate.out)
  postImage(image.out, subChans)
}
