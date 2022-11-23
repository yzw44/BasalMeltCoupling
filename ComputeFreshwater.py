import Freshwater as FW

### 1. Flatten file (Maybe I don't even need this step)
### 2. Pull 2 most recent files, if 2 files don't exist then end the process
### 3. Compute integrated mean over all the variables, and create a df
### 4. Compute the volume difference
### 5. Compute discharge, U
### 6. Compute BMB
### 7. Pass values to dataframe, as input to EC-Earth

# Define parameters
path = "/nobackup/users/donnelly/BasalMeltCoupling/"

# Define paths
mask_path = "/nobackup/users/donnelly/levermann-masks"
nc_out = path

# Load leverman masks (Maybe in future should just be replaces with coordinates)
driver = '/perm/nlcd/bisicles/BISICLES/code/filetools/nctoamr2d.Linux.64.mpiCC.gfortran.DEBUG.MPI.ex' # nc to amr hdf5 tool 

#files = open_files(path)
#flattenAMR(path,files,flatten)

filetoolsPath = r'/usr/people/donnelly/bisicles/BISICLES/code/filetools/'
filetoolFlatten = 'flatten2d.Linux.64.g++.gfortran.DEBUG.ex'
flatten = filetoolsPath + filetoolFlatten
file_path1 = "/nobackup/users/donnelly/Antarctica/ssp585/shelfbasedepth/plot.ssp585_shelfbase.004980.2d.hdf5"
file_path2 = "/nobackup/users/donnelly/Antarctica/ssp585/shelfbasedepth/plot.ssp585_shelfbase.005040.2d.hdf5"

file1 = FW.BISICLES(file_path1)
file2 = FW.BISICLES(file_path2)
df1 = file1.flattenStats(flatten)
df2 = file2.flattenStats(flatten)
print(df1)
print(df2)
