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

// A secondart check to ensure the directory is a synbolic link (observation has not processed).
// If it isn't then it has been processed, then exit with error.
// Else ocntinue and clear the report entry.
process startObsProcessing {
  input:
    path obsid
    val ready
  output:
    path obsid

    """
    obsStartCheckReport.py "$params.reportCsv" ${obsid} "$params.obsdir"
    """
}

process generateCalibration {
  input:
    path obsid
  output:
    path obsid

    """
    export MWA_PB_BEAM="$projectDir/beamdata/gleam_xx_yy.hdf5"
    export MWA_PB_JONEs="$projectDir/beamdata/gleam_jones.hdf5"
    cd $obsid
    generateCalibration.py $projectDir $obsid $params.reportCsv
    """
}

process applyCalibration {
  input:
    path obsid
  output:
    path obsid

    """
    #! /bin/bash -l
    
    cd $obsid
    measurementSet="${obsid}.ms"
    calibrationFile="${obsid}_local_gleam_model_solutions_initial_ref.bin"

    if [[ ! -e "\${calibrationFile}" ]]
    then
      echo "Unable to load calibration file: \${calibrationFile}"
      exit -1
    fi

    applysolutions -nocopy "\${measurementSet}" "\${calibrationFile}"
    updateReport.py "$params.reportCsv" ${obsid} applyCalibration Success
    """
}

process flagUV {
  input:
    path obsid
  output:
    path obsid

    """
    cd $obsid
    ${projectDir}/bin/gleamx/ms_flag_by_uvdist.py "${obsid}.ms" DATA -a
    updateReport.py "$params.reportCsv" ${obsid} flagUV Success
    """
}

process uvSub {
  time 2.hour
  
  input:
    path obsid
  output:
    path obsid

    """
    export MWA_PB_BEAM="$projectDir/beamdata/gleam_xx_yy.hdf5"
    export MWA_PB_JONEs="$projectDir/beamdata/gleam_jones.hdf5"
    cd $obsid
    uvSub.py $projectDir $obsid $params.reportCsv
    """
}

process image {
  publishDir params.obsdir, mode: 'copy', overwrite: true

  // Set SLURM job time limit to 2hr, increase it by 2hr each time it times out for a maximum of 3 retries.
  time { 2.hour * task.attempt }
  errorStrategy 'retry'
  maxRetries 3

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
  publishDir params.obsdir, mode: 'copy', overwrite: true

  time 2.hour

  input:
    path obsid
    each subchan
  output:
    path "${obsid}/*deep*"
    path "${obsid}/*_xm*"

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

  // Check to see if the beam data for mwa_pb_lookup exists. If not download it.
  checkBeamData()
  
  // No observations requiring autoflag so have left it out, will revisit once the full list has been obtained.
  // Process each observation in the specified observation directory.
  startObsProcessing(obsDirCh, checkBeamData.out)
  generateCalibration(startObsProcessing.out)
  applyCalibration(generateCalibration.out)
  flagUV(applyCalibration.out)
  uvSub(flagUV.out)
  image(uvSub.out)
  postImage(image.out, subChans)
}
