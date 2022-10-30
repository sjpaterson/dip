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
  input:
    path obsid
  output:
    path obsid

    """
    cd $obsid
    image.py $projectDir $obsid
    """
}

process postImage_0000 {
  input:
    path obsid
  output:
    path obsid

    """
    cd $obsid
    postImage.py $projectDir $obsid 0000
    """
}

process postImage_0001 {
  input:
    path obsid
  output:
    path obsid

    """
    cd $obsid
    postImage.py $projectDir $obsid 0001
    """
}

process postImage_0002 {
  input:
    path obsid
  output:
    path obsid

    """
    cd $obsid
    postImage.py $projectDir $obsid 0002
    """
}

process postImage_0003 {
  input:
    path obsid
  output:
    path obsid

    """
    cd $obsid
    postImage.py $projectDir $obsid 0003
    """
}

process postImage_MFS {
  publishDir params.obsdir, mode: 'move', overwrite: true

  input:
    path obsid
  output:
    path obsid

    """
    cd $obsid
    postImage.py $projectDir $obsid MFS
    """
}



workflow {
  // Directory where the observations are stored.
  obsDirFull = params.obsdir + '/*'
  obsDirCh = Channel.fromPath(obsDirFull, type: 'dir')
  //subChans = Channel.of('0000', '0001', '0002', '0003', 'MFS')

  // Check to see if the beam data for mwa_pb_lookup exists. If not download it.
  checkBeamData()
  
  // No observations requiring autoflag so have left it out, will revisit once the full list has been obtained.
  // Process each observation in the specified observation directory.

  generateCalibration(obsDirCh, checkBeamData.out)
  applyCalibration(generateCalibration.out)
  flagUV(applyCalibration.out)
  image(flagUV.out)

  // Likely a better method to achieve the below, will investigate later.
  postImage_0000(image.out)
  postImage_0001(postImage_0000.out)
  postImage_0002(postImage_0001.out)
  postImage_0003(postImage_0002.out)
  postImage_MFS(postImage_0003.out)
   
}
