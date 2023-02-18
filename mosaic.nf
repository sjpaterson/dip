// Mosaic - Deep Image Pipeline
nextflow.enable.dsl=2


process generateLists {
  output:
    path "imagelist"
    path "weightlist"

    """
    genMosaicLists.py "$params.reportCsv" m
    """
}


process mosaic {
  publishDir params.mosaicdir, mode: 'copy', overwrite: true

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
    path "*"

    """
    swarp -c "$projectDir/swarp.config" @"$imagelist"
    """
}


workflow {
  // Generate the image and weight lists and then mosaic them using SWARP.
  generateLists()
  mosaic(generateLists.out)

}
