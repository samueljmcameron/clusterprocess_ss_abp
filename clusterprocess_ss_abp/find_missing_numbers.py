import numpy as np
import pickle
from lammpstools import HistogramLoader

def find_missing_numbers(basename,eof,runslist):

    """
    
    Check multiple runs of a single binned 'histo' type
    of data, and keep a record of those runs which were missed or
    incorrectly formatted due to being cancelled by the job
    scheduler.

    Parameters
    ----------
    basename : string
        First part of the file name (prior to the run
        number).
    eof : string
        Second part of the file name (after the run number).
    runslist : 1D array like of ints
        List of runs to scan over.

    Returns
    -------
    missed_runs : list of ints
        Every time a data file from a specific run is missing, the
        run number is appended to this list.


    """

    missed_runs = []


    count = 0

    nruns = len(runslist)
    for run in runslist:

        fname = basename + f'{run}' + eof

        try:
            hl = HistogramLoader(fname)
        except FileNotFoundError:
            missed_runs.append(run)
            print(f'missed run {run} of {fname}.')
            continue

        try:
            dat = hl.data[0]
        except IndexError:
            missed_runs.append(run)
            print(f'missed run {run} of {fname}.')

            continue

        count += 1
    print(count)

    return missed_runs
