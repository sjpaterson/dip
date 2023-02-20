// Convolve to Common Beam - Deep Image Pipeline
nextflow.enable.dsl=2

// Convolve each observation.
process convolve {
  publishDir "$params.mosaicdir/observations", mode: 'copy', overwrite: true

  label 'racstools'

  input:
    tuple val(obsid), path(obspath), val(bmaj), val(bmin), val(bpa)
  output:
    path '*'

    """
    beamcon_2D --bmaj $bmaj --bmin $bmin --bpa $bpa --conv_mode astropy -v $obspath
    """
}


workflow {
  Channel.fromPath("$params.mosaicdir/data/beaminfo.csv") \
        | splitCsv(header:true) \
        | map { row-> tuple(row.obsid, file(row.obspath), row.bmaj, row.bmin, row.bpa) } \
        | convolve

}
