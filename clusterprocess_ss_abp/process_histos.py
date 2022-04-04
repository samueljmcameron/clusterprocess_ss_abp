import numpy as np
import pickle
import sys

from lammpstools import HistogramLoader, CondensedArray_oTwo, CondensedArray_oThree


def process_histos(basename,eof,pos_bins,cutoff,runslist,nskip=None,
                   theta_bins=None,dtype='rdf',varname='c_myhistos',
                   histdict=None,runstarts=None,t_start=-1):

    """
    
    Process multiple runs of a single binned 'histo' type
    of data, and put into a final dictionary with averages of the
    runs and other information.

    Parameters
    ----------
    basename : string
        First part of the file name (prior to the run
        number).
    eof : string
        Second part of the file name (after the run number).
    pos_bins : int
        Number of position bins expected in the files.
    cutoff : float
        Distance that binning is cut off at as expected in the
        files.
    runslist : 1D array like of ints
        List of runs to scan over.
    nskip : int (optional)
        Number of position bins to be skipped as expected in
        the files. Default is None. Only used for certain
        values of the 'dtype' argument (see below).
    theta_bins : int (optional)
        Number of theta bins expected in the files. Default
        is None. Only used for certain values of the 'dtype'
        argument (see below).
    dtype : string (optional)
        Type of data to be expected. Acceptable arguments are
        'rdf', '3bod', or '3bodfull.' Default is 'rdf'.
    varname : string (optional)
        prefix name of header in # row output of data. Default
        is 'c_myhistos'.
    histdict : dict (optional)
        Dictionary labeling columns in the rdf input files and assigning
        them a number in the output files. Default is None, which then
        chooses an appropriate histdict dependent on data type.
    runstarts : 1D list of strings (optional)
        Strings to insert in basename for each different run.
        Length of list should be same as runslist length above.
        Default is None.
    t_start : integer (optional)
        A single start time for all the different runs. Necessary if
        the runs all start at different times to average correctly
        (assuming same end time and time spacing). Default is -1.

    Returns
    -------
    finaldict : dictionary
        Contains average values for the different binned quantities,
        as well as other useful information that is shared by all
        runs scanned over.
    missed_runs : list of ints
        Every time a data file from a specific run is missing, the
        run number is appended to this list.
    

    """

    if dtype == 'rdf':
        if histdict == None:
            histdict = {'g' : 2, 'U_1' : 3, 'C_1' : 4, 'U_2' : 5,
                        'C_2' : 6, 'UC' : 7, 'D_2' : 8, 'ncoord' : 9}
    elif dtype == '3bod':
        if nskip == None:
            raise ValueError("need nskip argument for dtype='3bod'.")
        if histdict == None:
            histdict={'g3' : 3 , 'g3cos' : 4}
    elif dtype == '3bodfull':
        if nskip == None:
            raise ValueError("need nskip argument for dtype='3bodfull'.")
        if theta_bins == None:
            raise ValueError("need theta_bins argument for dtype='3bodfull' dtype.")
        if histdict == None:
            histdict={'g3' : 4 }

    missed_runs = []
    # store the times of measurement (same for each of the nrun runs)
    times = []

    # store all of the measurement data
    histlist = []

    print(histdict)

    count = 0

    nruns = len(runslist)
    tmpname = basename
    for run_index,run in enumerate(runslist):

        if runstarts != None:
            basename = tmpname.replace('HERE',runstarts[run_index])

        fname = basename + f'{run}'+eof
        print(fname)
        try:
            hl = HistogramLoader(fname)
        except FileNotFoundError:
            missed_runs.append(run)
            print(f'missed run {run} of {fname}')

            continue

        try:
            dat = hl.data[0]


        except IndexError:
            missed_runs.append(run)
            print(f'missed run {run} of {fname}')
            continue




        if dtype == 'rdf':
            tmpbinnum = pos_bins
        elif dtype == '3bod':
            tmpbinnum = int((pos_bins-2*nskip)*(pos_bins-2*nskip+1))//2
        elif dtype == '3bodfull':
            tmpbinnum = int((pos_bins-2*nskip)*(pos_bins-2*nskip+1)
                            *theta_bins)//2
            
        nbins = dat['nbins']
        
        if tmpbinnum != nbins:
            raise ValueError('bin args do not match data length.')

        num_neglected_timesteps = 0
        # iterate over each measurement of the run
        for timestep,data_t in enumerate(hl.data):

            if int(hl.data[timestep]['timestep']) < t_start:
                num_neglected_timesteps += 1
                continue

            if count == 0:


                # save all times that histograms were measured (same for each run)
                times.append(hl.data[timestep]['timestep'])



                # at each timestep, create arrays of shape 
                #    (nruns,nbins) for each histogram

                histlist.append({})

                for key,value in histdict.items():
                    histlist[timestep-num_neglected_timesteps][key] = np.empty([nruns,nbins],float)

            for key,value in histdict.items():
                histlist[timestep-num_neglected_timesteps][key][count,:] = data_t[f'{varname}[{value}]']

        count += 1

    if dtype == '3bod':
        eo = CondensedArray_oTwo(pos_bins,nskip)
        reshape = eo.reshape

    elif dtype == '3bodfull':
        eo = CondensedArray_oThree(pos_bins,theta_bins,nskip)
        reshape = eo.reshape
    elif dtype == 'rdf':

        def reshape(x):
            return x

    # list with items containing dicts of averages and std devs
    #    at each timestep

    estimators = []


    print(f"count={count}")
    for timestep in range(len(hl.data)):
        estimators.append({})

        for key,value in histlist[timestep].items():
            estimators[timestep][key] = reshape(np.mean(value[:count,:],axis=0))
            estimators[timestep][key+'_std'] = reshape(np.std(value[:count,:],axis=0))



    rs = (np.linspace(0,float(cutoff),num=pos_bins,endpoint=False)
          +0.5*float(cutoff)/pos_bins)


    # store final values of 




    if dtype == '3bod':
        finaldict = {'estimators' : estimators, 'nskip' : nskip, 'r3s' : rs,
                     'timesteps' : times, 'nruns' : count }

    elif dtype == '3bodfull':
        thetas = (np.linspace(0,np.pi,num=theta_bins,endpoint=False)
                  +0.5*np.pi/theta_bins)
        finaldict = {'estimators' : estimators, 'nskip' : nskip, 'r3s' : rs,
                     'thetas' : thetas, 'timesteps' : times, 'nruns' : count }

    elif dtype == 'rdf':
        finaldict = {'estimators' : estimators, 'r' : rs,
                     'timesteps' : times , 'nruns' : count }

    return finaldict,missed_runs



if __name__ == "__main__":


    basename = f'histosbins{bins}cutoff{cutoff}'
    basename += f'_{rho}_{fp}_{epsilon}_{Pi}'

    finaldict,missed_runs = process_histos(basename,'.rdf',pos_bins,cutoff,nruns)
