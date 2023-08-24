import sys, shutil, os
sys.path.append('/Users/cd/Documents/GDAL_scripts')
import gdal_scripts
import glob
import numpy as np

MTBS_dir = sys.argv[1]
temp_dir = MTBS_dir + '/../temp_allshp/' # to store all the shapefiles from unzipped folders before merging shapefiles
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

if __name__ == '__main__':
    # Look through list of directories, unzippping all, leaving in same MTBS_dir
    zip_filesL = glob.glob(MTBS_dir + '/**/*.zip',
                           recursive=True)
    
    for f in zip_filesL:
        shutil.unpack_archive(f, f.strip('.zip'))
    
    # for all the shp files + associated metadata files that don't end in mask.shp, copy to temp_dir
    all_shp_filesL = glob.glob(MTBS_dir + '/**/*.shp', 
                               recursive=True)
    
    shp_filesL = np.array(
        [glob.glob(f.strip('shp')+'*') for f in all_shp_filesL
                           if '_mask' not in f]
                ).flatten()
    
    for f in shp_filesL:
        print(f, temp_dir + f.split('/')[-1])
        shutil.copy(f, temp_dir + f.split('/')[-1])

    # merge all shapefiles in tempdir using gdal_scripts.mergeShpFiles(shpFilePathsL, outFile)
    gdal_scripts.mergeShpFiles(glob.glob(temp_dir+'*.shp'), MTBS_dir+'/merged_mtbs.shp')

    # delete temp_dir
    shutil.rmtree(temp_dir)
    
    pass