// Convolve to Common Beam - Deep Image Pipeline
nextflow.enable.dsl=2

// Convolve each observation.
process convolve {
  // publishDir "$params.mosaicdir/observations", mode: 'copy', overwrite: true

  // label 'racstools'

  input:
    tuple val(obsid), val(obspath), val(bmaj), val(bmin), val(bpa)
  output:
    tuple val(obsid), val(obspath)
    path '*'

    """
    cp "${obspath}/${obsid}_deep-MFS-image-pb_warp.fits" ./
    beamcon_2D --bmaj $bmaj --bmin $bmin --bpa $bpa --conv_mode astropy -v ${obsid}_deep-MFS-image-pb_warp.fits
    """
}

process resample {
  publishDir "$params.mosaicdir/observations", mode: 'copy', overwrite: true

  label 'gleamx'

  input:
    tuple val(obsid), val(obspath)
    path files
  output:
    path '*'

    """
    swarp "${obsid}_deep-MFS-image-pb_warp.sm.fits" -c "/astro/mwasci/spaterson/dip/swarp_resample.config" -WEIGHT_IMAGE "${obspath}/${obsid}_deep-MFS-image-pb_warp_weight.fits"
    """
}


workflow {
  Channel.fromPath("$params.mosaicdir/data/beaminfo.csv") \
        | splitCsv(header:true) \
        | map { row-> tuple(row.obsid, row.obspath, row.bmaj, row.bmin, row.bpa) } \
        | convolve \
        | resample

}
