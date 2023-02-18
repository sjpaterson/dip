// Convolve to Common Beam - Deep Image Pipeline
nextflow.enable.dsl=2

// Placed in a separate process as the RACS-TOOLS container does not contain Pandas.
process getObsList {
  output:
    path "obslist"

    """
    genMosaicLists.py "$params.reportCsv" c 10
    """
}

process getBeamSize {
  label 'beamconv'

  input:
    path obslist

  output:
    path "beamlog"
    path "convlog"

    """
    beamcon_2D -v --logfile convlog --log beamlog -d --conv_mode astropy `cat $obslist`
    """
}

process saveBeamInfo {
  publishDir params.mosaicdir, mode: 'copy', overwrite: true

  input:
    path beamlog
    path convlog

  output:
    path beamlog
    path convlog
    path '*'

    """
    readBeamInfo.py $beamlog
    """
}



workflow {
  // Convolve to common beam.
  getObsList()
  getBeamSize(getObsList.out)
  saveBeamInfo(getBeamSize.out)  
}
