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
        rm "$projectDir/pb_lookup.tar.gz"
  fi
  """
}


process generateCalibration {
  input:
    path obsid
    val ready
  output:
    path obsid

    """
    export MWA_PB_BEAM="$projectDir/beamdata/gleam_xx_yy.hdf5"
    export MWA_PB_JONEs="$projectDir/beamdata/gleam_jones.hdf5"
    cd $obsid
    generateCalibration.py $projectDir $obsid
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
    image.py $projectDir $obsid $params.briggs $params.tukey
    """
}

process postImage {
  publishDir params.obsdir, mode: 'copy', overwrite: true

  input:
    path obsid
    each subchan
  output:
    path "${obsid}/*deep*"
    path "${obsid}/*_xm*"

    """
    cd $obsid
    postImage.py $projectDir $obsid $subchan
    """
}



workflow {
  // Directory where the observations are stored.
  obsDirFull = params.obsdir + '/*'
  obsDirCh = Channel.fromPath(obsDirFull, type: 'dir')
  subChans = Channel.of('0000', '0001', '0002', '0003', 'MFS')

  // Check to see if the beam data for mwa_pb_lookup exists. If not download it.
  checkBeamData()
  
  // No observations requiring autoflag so have left it out, will revisit once the full list has been obtained.
  // Process each observation in the specified observation directory.
  generateCalibration(obsDirCh, checkBeamData.out)
  applyCalibration(generateCalibration.out)
  flagUV(applyCalibration.out)
  image(flagUV.out)
  postImage(image.out, subChans)
   
}
