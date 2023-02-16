// Mosaic - Deep Image Pipeline
nextflow.enable.dsl=2


process generateLists {
  output:
    path "imagelist"
    path "weightlist"

    """
    genMosaicLists.py "$params.reportCsv" 3
    """
}


process mosaic {
  publishDir params.mosaicdir, mode: 'copy', overwrite: true

  // Set SLURM job time limit to 24hr.
  // time 24.hour

  input:
    path imagelist
    path weightlist
  
  output:
    path imagelist
    path weightlist
    path "*"

    """
    swarp -c "$projectDir/swarp.config" @"$imagelist" > swarpcmd
    """
}


workflow {
  // Generate the image and weight lists and then mosaic them using SWARP.
  generateLists()
  mosaic(generateLists.out)

}
