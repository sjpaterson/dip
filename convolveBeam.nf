// Convolve to Common Beam - Deep Image Pipeline
nextflow.enable.dsl=2

// Convolve each observation.
process convolve {
  input:
    tuple val(obsid), val(obspath), val(bmaj), val(bmin), val(bpa)

    """
    echo $obspath $bmaj $bmin $bpa > $params.mosaicdir/${obsid}.txt
    """
}


workflow {
  Channel.fromPath("$params.mosaicdir/beaminfo.csv") \
        | splitCsv(header:true) \
        | map { row-> tuple(row.obsid, row.obspath, row.bmaj, row.bmin, row.bpa) } \
        | convolve

}
