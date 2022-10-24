#!/usr/bin/env python

"""Script to help identify which calibrate solution files are not appropriate to apply, and helps to 
identify ones close in time that are appropriate. 

TODO: Add a custom fromfile function. There was a bug in some of the original XY/YX correction and 
      refant code that would cause the XY/YX Jones terms to be turned from NaNs to finite numbers,
      and this messed up the statistics. This custome fromfile function should be made to ensure
      that this does not happen. A 2x2 Jones should be completely finite or completely NaN'd. 

TODO: Load in the metafits files and count the number of tiles that are known to be bad flagged 
      out and exclude them from the statistics. This is distinct from tiles that are completely
      flagged because they did not converge. 

"""

import os
import sys
import logging 

import numpy as np

from calplots.aocal import fromfile


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(module)s:%(levelname)s:%(lineno)d %(message)s")
logger.setLevel(logging.INFO)

#try:
#    from gleam_x.db import mysql_db as gxdb
#except:
    #print("Warning: unable to import the database connection")
gxdb = None

#THRESHOLD = (
#    0.25  # acceptable level of flagged solutions before the file is considered ratty
#)
MWABW = 30720 # Spectral coverage in kilohertz  

def obtain_cen_chan(obsids, disable_db_check=False):
    """Retrieve the cenchan for a set of specified pointings. This will be done through the 
    meta-database, but should be expanded in the future to dial home to the mwa meta-data service

    Args:
        obsids (iterable): collection of obsids to check

    Keyword Args:
        disable_db_check (bool): Normal behaviour will raise an error if the GX database can not be contaced. If True this check is ignored (default: False)
    
    Returns:
        cenchans (numpy.ndarray): the cenchan of each obsid
    """
    cen_chan = np.array([1 for i in obsids])

    if gxdb is None:
        if disable_db_check:
            return cen_chan
        else:
            raise ValueError("GX Database configuration is not configured. ")

    try:
        con = gxdb.connect()

        obsids = [int(o) for o in obsids]

        cursor = con.cursor()

        # Need to wrangle the formatting so we can use the WHERE a IN b syntax
        cursor.execute(
            f"SELECT cenchan FROM observation WHERE obs_id IN ({', '.join(['%s' for _ in obsids])}) ",
            (*obsids,),
        )

        return np.squeeze(np.array([o[0] for o in cursor.fetchall()]))

    except:
        if disable_db_check:
            print("WARNING: Database lookup failed. Setting all cenchans to 1")
            return cen_chan
        else:
            raise ValueError("GX Database is not contactable. ")

def derive_edge_channel_flagged(ao_results, edge_bw_flag, no_sub_bands):
    """Knowing how wide the MWA subbands are, this function will return the
    number of edge channels flagged of each sub-band. This is useful when 
    attempting to compute meaningful flagging statistics as these will always
    be flagged despite the state of the array and data. 

    Args:
        ao_results (AOCal): AOCal solutions file opened against a valid MWA calibration solutions files
        edge_bw_flag (float): The bandwidth either side of of each sub-band that should be flagged
        no_sub_bands (int): Number of sub-bands that make up the MWA frequency axis throughout the signal process chain

    Returns:
        int: number of channels that are deemed as edge channels
    """

    logger.debug(f"Number of channels {ao_results.n_chan}")
    logger.debug(f"Supplied number of subbands {no_sub_bands=}")

    freq_res = MWABW // ao_results.n_chan
    logger.debug(f"Channel frequency resolution {freq_res} KHz")

    no_chan_flag = edge_bw_flag // freq_res 
    logger.debug(f"Number of edge channels flagged {no_chan_flag=} either side of subband")

    # Flagging either side of a sub-band
    total_chans_flag = 2 * no_chan_flag * no_sub_bands
    logger.debug(f"{no_sub_bands=} {total_chans_flag=} Bandwidth flagged={total_chans_flag*freq_res} KHz")

    return total_chans_flag

def check_solutions(
    aofile, 
    * ,
    threshold=0.25, 
    segments=None, 
    segment_threshold=None,
    ignore_edge_channels=True, 
    edge_bw_flag=80,
    no_sub_bands=24,
    **kwargs):
    """Inspects the ao-calibrate solutions file to evaluate its reliability

    Args:
        aofile (str): aocal solutions file to inspect
    
    Keyword Args:
        threshold (float): The threshold, between 0 to 1, where too many solutions are flagged before the file becomes invalid (default: 0.25)
        segments (int): If not None, divide the frequency axis up into a set of segments, and ensure each segment has enough data (default: None)
        ignore_edge_channels (bool): Remove edge channels flagged from the threshold statistics (default: True)
        edge_bw_flag (float): The total bandwidth to flag (default: 80)
        no_sub_bands (int): The number of sub-bands that make up the MWA signal processing (default: 24)

    Returns:
        bool: a valid of invalid aosolutions file
    """
    threshold = threshold / 100 if threshold > 1 else threshold
    logger.debug(f"Threshold level set is {threshold=}")

    if not os.path.exists(aofile):
        logger.debug(f"{aofile} not found")
        return False

    logger.debug(f"Loading {aofile=}")
    ao_results = fromfile(aofile)

    no_chan = ao_results.n_chan
    no_ant = ao_results.n_ant

    if logger.level == logging.DEBUG:
        total_flag = 0

        for ant in range(ao_results.shape[1]):
            ant_data = ao_results[:,ant,:,:]
            flag_lvl = np.sum(np.isnan(ant_data)) / np.prod(ant_data.shape)
            
            logger.debug(f"{ant=} {ant_data.shape=} Flagged={flag_lvl*100:.2f}% {no_chan=}")

            if flag_lvl == 1.:
                total_flag += 1

        logger.debug(f"Total set of antennas completely flagged: {total_flag}")

    logger.debug(f"AOFile datashape {ao_results.shape=}")
    
    # For each antenna this number of edge channels are flagged
    no_edges = derive_edge_channel_flagged(
        ao_results, 
        edge_bw_flag,
        no_sub_bands
        ) if ignore_edge_channels else 0
    
    # now scale to the number of antenna
    no_edges *= no_ant
    
    # and because there are four nans per solution in the Jones
    no_edges *= 4

    logger.debug(f"Removing {no_edges=} from statistic")
    ao_flagged = (np.sum(np.isnan(ao_results)) - no_edges) / (np.prod(ao_results.shape) - no_edges)

    logger.debug(f"{ao_flagged:.4f} fraction flagged")
    if ao_flagged > threshold:
        return False

    if segments is not None: 
        segments = int(segments)

        assert ao_results.shape[0] == 1, "Segment checks not implemented across multiple time steps"
        
        # shape is timestep, antenna, channel, pol
        no_chan = ao_results.shape[2]
        
        assert no_chan % segments == 0, f"{no_chan} channels is not evenly divisible by {segments} segments"
        stride = no_chan // segments        
        logger.debug(f"{segments=} and {stride=}")
        
        segment_threshold = threshold if segment_threshold is None else segment_threshold
        segment_threshold = segment_threshold / 100 if segment_threshold > 1. else segment_threshold
        logger.debug(f"Using {segment_threshold=}")

        no_seg_edges = (no_edges / segments)
        if no_edges > 0:
            logger.debug(f"Assuming {no_seg_edges=} per segment")

        for i in range(segments):
            chan_slice = slice(i*stride, (i+1)*stride)
            seg_ao_data = ao_results[:,:,chan_slice,:]
            seg_ao_flagged = (np.sum(np.isnan(seg_ao_data)) - no_seg_edges) / (np.prod(seg_ao_data.shape) - no_seg_edges)

            logger.debug(f"segment={i} {chan_slice} {seg_ao_data.shape} {seg_ao_flagged=}")

            if seg_ao_flagged > segment_threshold:
                return False

    return True


def report(obsids, cobsids, file=None, only_calids=False):
    """Report when an obsid has been associated with a new copied obsid solution file

    Args:
        obsid (iterable): Subject obsid with a missing solutions file
        cobsid (iterable): Obsid to copy solutions from
    
    Keyword Args:
        file (_io.TextIOWrapper): An open file handler to write to
    """
    for o, c in zip(obsids, cobsids):
        if only_calids:
            print(c, file=file)
        else:
            print(o, c, file=file)


def find_valid_solutions(
    obsids,
    dry_run=False,
    base_path=".",
    same_cen_chan=True,
    suffix="_local_gleam_model_solutions_initial_ref.bin",
    disable_db_check=False,    
    *args,
    **kwargs,
):
    """Scans across a set of obsids to ensure a `calibrate` solutions file is found. If a obsids does not have this file, cidentify one close in time. 

    Directory structure is assumed to follow basic GLEAM-X pipeline:
        {obsid}/{obsid}{suffix}
    
    Minimal options are provide to configure this. 

    Args:
        obsids (numpy.ndarray): Array of obsids
    
    Keyword Args:
        dry_run (bool): Just present actions, do not carry them out (default: False)
        base_path (str): Prefix of path to search for ao-solutions (default: '.')
        same_cen_chan (bool): Force obsids to have the same central channel when considering candidate solutions (default: True)
        suffix (str): Suffix of the solution file, in GLEAM-X pipeline this is `{obsid}_{solution}` (default: '_local_gleam_model_solutions_initial_ref.bin')
        disable_db_check (bool): Normal behaviour will raise an error if the GX database can not be contaced. If True this check is ignored (default: False)

    Returns:
        calids (numpy.ndarray): Parrallel array with calibration solution obsid corresponding to the obsids specified in `obsids`
    """
    obsids = obsids.astype(np.int)
    calids = obsids.copy()

    logger.debug(f"{len(obsids)=} in presented set of obsids")

    sol_present = np.array(
        [
            check_solutions(f"{base_path}/{obsid}/{obsid}{suffix}", **kwargs)
            for obsid in obsids
        ]
    )

    if np.all(sol_present == False):
        logger.error("No potenial calibration scans. base_path needs to be set?")
        sys.exit(1)

    if same_cen_chan:
        cen_chan = obtain_cen_chan(obsids, disable_db_check=disable_db_check)
    else:
        cen_chan = np.array([1 for obsid in obsids])

    chan_lookup = {k: k == cen_chan for k in np.unique(cen_chan)}

    for pos in np.argwhere(~sol_present):
        obsid = obsids[pos]

        obs_chan = cen_chan[pos][0]
        present = sol_present & chan_lookup[obs_chan]

        cobsid = obsids[present][np.argmin(np.abs(obsids[present] - obsid))]
        calids[pos] = cobsid

    return calids



def run(mode, aofile=None, threshold=0.25, segments=None, segment_threshold=None, include_edge_channels=False, flag_edge_width=80, no_subbands=24, obsids=None, no_report=False, calids_out=None, only_calids=False, base_path='.', any_cen_chan=False, disable_db_check=False, suffix='_local_gleam_model_solutions_initial_ref.bin', verbose=False):

    if verbose:
        logger.setLevel(logging.DEBUG)

    if mode == "subbands":
        logger.debug(f"Loading solutions file {aofile}")
        ao_results = fromfile(aofile)
    
        derive_edge_channel_flagged(
            ao_results,
            flag_edge_width,
            no_subbands
        )

    elif mode == "check":
        print("Checking Mode")
        if segments is not None:
            print(f"Applying nan threshold checks to {segments} sub-bands")
        
        if check_solutions(
            aofile, 
            threshold=threshold, 
            segments=segments,
            segment_threshold=segment_threshold,
            ignore_edge_channels=not include_edge_channels,
            flag_edge_width=flag_edge_width,
            no_sub_bands=no_subbands

        ):
            print(f"{aofile} passed")
            return 'pass'
        else:
            print(f"{aofile} failed")
            return 'fail'

    elif mode == "assign":
        print("Assigning calibration")
        if segments is not None:
            print(f"Applying nan threshold checks to {segments} sub-bands")

        obsids = np.loadtxt(obsids, dtype=int)
        calids = find_valid_solutions(
            obsids,
            threshold=threshold,
            same_cen_chan=not any_cen_chan,
            base_path=base_path.rstrip("/"),
            disable_db_check=disable_db_check,
            suffix=suffix,
            segments=segments,
            segment_threshold=segment_threshold,
            ignore_edge_channels=not include_edge_channels,
            flag_edge_width=flag_edge_width,
            no_sub_bands=no_subbands
        )

        if not no_report:
            report(obsids, calids)
        if calids_out is not None:
            with open(calids_out, "w") as outfile:
                report(obsids, calids, file=outfile, only_calids=only_calids)
    else:
        print("Invalid directive supplied. ")
        exit(-1)

    return 'error'
