import numpy as np
import pickle
import sys

from lammpstools import LogLoader

def autocorrelation(xs):

    xp = np.fft.ifftshift(xs)#(xs-np.average(xs))/np.sqrt(np.var(xs)))
    n, = xp.shape

    xp = np.r_[xp[:n//2],np.zeros_like(xp),xp[n//2:]]
    
    f = np.fft.fft(xp)

    iff = np.fft.ifft(np.abs(f)**2)

    return iff.real[:n]/(np.arange(n)[::-1]+1)#iff.real[:n//2]/(np.arange(n//2)[::-1]+n//2)

def process_logs(basename,eof,runslist,
                 outputs = ['c_pairpress','c_pfd'],runstarts=None,
                 t_start=-1,autoCorrs=[]):

    """
    
    Check multiple runs of a log type of data,
    and keep a record of those runs which were missed or
    incorrectly formatted due to being cancelled by the job
    scheduler.

    Parameters
    ----------
    basename : string
        First part of the file name (prior to the run
        number). If it includes the phrase 'HERE', then
        this bit will be replaced with phrases from runstarts
        keyword below.
    eof : string
        Second part of the file name (after the run number).
    runslist : 1D array like of ints
        List of runs to scan over.
    outputs : list of strings (optional)
        Names of the computes that are in the thermo output.
        Default is ['c_pairpress','c_pfd'].
    runstarts : 1D list of strings (optional)
        Strings to insert in basename for each different run.
        Length of list should be same as runslist length above.
        Default is None.
    t_start : integer (optional)
        A single start time for all the different runs. Necessary if
        the runs all start at different times to average correctly
        (assuming same end time and time spacing). Default is -1.
    autoCorrs : list of strings (optional) or None
        Names of the computes that are in the thermo output which
        should calculate autocorrelations. To avoid computing any
        autocorrelations, set this to None.
        Default is a copy of the outputs list.

    Returns
    -------
    finaldict : dictionary
        Contains average values for the different log quantities,
        as well as other useful information that is shared by all
        runs scanned over.
    missed_runs : list of ints
        Every time a data file from a specific run is missing, the
        run number is appended to this list.


    """

    # list of missed runs
    missed_runs = []

    if not autoCorrs:
        autoCorrs = outputs.copy()
    elif autoCorrs is None:
        autoCorrs = []

    # time periods of measurement (same for each of the nrun runs)
    #  i.e. if there is a pre-quench and a post-quench chunk of
    #  thermo data in the log, then this will be a list of length
    #  two, the first entry containing all pre-quench time points
    #  and the second entry containing all post-quench time points.
    timeperiods = []

    # store all of the measurement data at each time period
    histlist = []

    

    # necessary in case files are missing
    count = 0

    nruns = len(runslist)
    tmpname = basename
    for run_index,run in enumerate(runslist):

        if runstarts != None:
            basename = tmpname.replace('HERE',runstarts[run_index])

        fname = basename + f"{run}"+ eof
        print(fname)
        try:
            ll = LogLoader(fname)
        except FileNotFoundError:
            missed_runs.append(run)
            print(f'missed run {run} of {fname} as no file exists.')
            continue
        except IndexError:
            missed_runs.append(run)
            print(f'missed run {run} of {fname} as data block is incomplete.')
            continue

        try:
            # necessary to see if all data is present
            dat = ll.data[0]
        except IndexError:
            missed_runs.append(run)
            print(f'missed run {run} of {fname} as no data is present.')
            continue


        # loop over data chunks (sometimes pre-quench data 
        #   is nice to have).
        for timeperiod,data_t in enumerate(ll.data):

            mask = ll.data[timeperiod]['Step']
            
            mask = (mask >= t_start)
            if count == 0:

                # if first run, then get step data
                #   (for each time period)
                current_times = ll.data[timeperiod]['Step'][mask]
                ntime = len(current_times)
                timeperiods.append(current_times)

                # and add a dict to the output list
                histlist.append({})

                # and initialise the above dict with arrays to store
                #   thermo data at each run
                for key in outputs:
                    histlist[timeperiod][key] = np.empty([nruns,ntime],float)
                for key in autoCorrs:
                    histlist[timeperiod][key + "_autocorr"] = np.empty([nruns,ntime],float)

                
            # save data in current entry of histlist
            for key in outputs:
                histlist[timeperiod][key][count,:] = data_t[key][mask]
            for key in autoCorrs:
                histlist[timeperiod][key + "_autocorr"][count,:] = autocorrelation(data_t[key][mask])
        count += 1


    # list which will contain time-dependent averages over all runs
    #   for which the file existed, for each time period
    estimators = []

    print(f'count={count}')

    for timeperiod in range(len(ll.data)):

        # add a dict for current time period
        estimators.append({})

        # average over runs for each item
        for key,value in histlist[timeperiod].items():
            estimators[timeperiod][key] = np.mean(value[:count,:],axis=0)
            estimators[timeperiod][key+'_std'] = np.std(value[:count,:],axis=0)


    # store final values of 
    finaldict = {'estimators' : estimators,
                 'timeperiods' : timeperiods , 'nruns' : count }



    return finaldict,missed_runs


if __name__ == "__main_":

    basename = f'logpress_{rho}_{fp}_{epsilon}_{Pi}'
