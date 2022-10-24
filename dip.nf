// Deep Image Pipeline
nextflow.enable.dsl=2

process checkBeamData{
  output:
    stdout
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
  output:
    path obsid

    """
    export MWA_PB_BEAM="$projectDir/beamdata/gleam_xx_yy.hdf5"
    export MWA_PB_JONEs="$projectDir/beamdata/gleam_jones.hdf5"
    generateCalibration.py $projectDir $params.obsdir $obsid
    """
}

process applyCalibration {
  input:
    file obsid
  output:
    file obsid

    """
    #! /bin/bash -l
    
    measurementSet="$params.obsdir/${obsid}/${obsid}.ms"
    calibrationFile="$params.obsdir/${obsid}/${obsid}_local_gleam_model_solutions_initial_ref.bin"

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
    file obsid
  output:
    file obsid

    """
    ${projectDir}/bin/gleamx/ms_flag_by_uvdist.py "$params.obsdir/${obsid}/${obsid}.ms" DATA -a
    """
}

process image {
  input:
    file obsid
  output:
    file obsid

    """
    image.py $projectDir $params.obsdir $obsid
    """
}

process postImage {
  input:
    file obsid
  output:
    file obsid

    """
    postImage.py $projectDir $params.obsdir $obsid
    """
}


workflow {
  // Directory where the observations are stored.
  obsDirFull = params.obsdir + '/*'
  obsDirCh = Channel.fromPath(obsDirFull, type: 'dir')

  // Check to see if the beam data for mwa_pb_lookup exists.
  // If not download it.
  checkBeamData()

  // TO FIX: Ensure beam data is downloaded before continueing with the processing.
  
  // No observations requiring autoflag so have left it out, will revisit once the full list has been obtained.
  // Process each observation in the directory.

  generateCalibration(obsDirCh) | applyCalibration | flagUV | image | postImage
  
}
