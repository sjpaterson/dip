// Mosaic - Deep Image Pipeline
nextflow.enable.dsl=2

process generateLists {
  output:
    path "imagelist"
    path "weightlist"

    """
    genMosaicLists.py "$params.reportCsv" "$params.mosaicdir/observations" swarp $params.mosaicSample
    """
}

process mosaic {
  // publishDir params.mosaicdir, mode: 'copy', overwrite: true

  // Request a larger amount of storage on /nvmetmp.
  clusterOptions = '--tmp=500g'

  // Set SLURM job time limit to 24hr.
  time 24.hour

  input:
    path imagelist
    path weightlist
  
  output:
    path imagelist
    path weightlist
    path "deep.fits"
    path "deep.weight.fits"
    path "swarp.xml"

    """
    swarp -c "$projectDir/swarp.config" @"$imagelist"
    """
}

process measureRMS {
  input:
    path imagelist
    path weightlist
    path deep
    path deepweight
    path swarpxml
  output:
    path imagelist
    path weightlist
    path deep
    path deepweight
    path swarpxml
    path "*"

    """
    BANE --cores 48 --compress --noclobber $deep
    """
}

process generateCatalogue {
  publishDir params.mosaicdir, mode: 'copy', overwrite: true

  input:
    path imagelist
    path weightlist
    path deep
    path deepweight
    path swarpxml
    path rms
  output:
    path imagelist
    path weightlist
    path deep
    path deepweight
    path swarpxml
    path rms
    path "*"

    """
    aegean --cores 1 --autoload --table="$deep" "$deep"
    """
}

workflow {
  // Generate the image and weight lists and then mosaic them using SWARP.
  generateLists()
  mosaic(generateLists.out)
  measureRMS(mosaic.out)
  generateCatalogue(measureRMS.out)
}
