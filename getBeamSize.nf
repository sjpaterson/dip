// Convolve to Common Beam - Deep Image Pipeline
nextflow.enable.dsl=2

// Placed in a separate process as the RACS-TOOLS container does not contain Pandas.
// Create the imagelists used by RACS-TOOLS and SWARP.
process getObsList {
  output:
    path "obslist"
    path "imagelist"
    path "weightlist"
    path "beaminfo.csv"

    """
    mkdir $params.mosaicdir/data
    mkdir $params.mosaicdir/observations
    genMosaicLists.py "$params.reportCsv" "$params.mosaicdir/observations" 3
    """
}

// Calculate the common beam size with RACS-TOOLS.
process getBeamSize {
  label 'racstools'

  input:
    path obslist
    path imagelist
    path weightlist
    path beaminfocsv

  output:
    path imagelist
    path weightlist
    path beaminfocsv
    path "beamlog"
    path "convlog"

    """
    beamcon_2D -v --logfile convlog --log beamlog -d --conv_mode astropy `cat $obslist`
    """
}

// Save to common beam size in beaminfo.csv.
process saveBeamInfo {
  publishDir "$params.mosaicdir/data", mode: 'copy', overwrite: true

  input:
    path imagelist
    path weightlist
    path beaminfocsv
    path beamlog
    path convlog

  output:
    path imagelist
    path weightlist
    path beaminfocsv
    path beamlog
    path convlog

    """
    readBeamInfo.py $beamlog $beaminfocsv
    """
}

workflow {
  // Convolve to common beam.
  getObsList()
  getBeamSize(getObsList.out)
  saveBeamInfo(getBeamSize.out)
}
