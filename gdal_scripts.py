from osgeo import gdal, ogr, osr
import rasterio as rio
import rasterio.mask
import fiona
import numpy as np
import subprocess
import glob

'''NOTES
Methods/attributes of a vector object:
'AbortSQL', 'CommitTransaction', 'CopyLayer', 'CreateLayer', 'DeleteLayer', 'Dereference', 'Destroy', 'ExecuteSQL', 
'FlushCache', 'GetDescription', 'GetDriver', 'GetLayer', 'GetLayerByIndex', 'GetLayerByName', 'GetLayerCount', 
'GetMetadata', 'GetMetadataDomainList', 'GetMetadataItem', 'GetMetadata_Dict', 'GetMetadata_List', 'GetName', 
'GetRefCount', 'GetStyleTable', 'GetSummaryRefCount', 'Reference', 'Release', 'ReleaseResultSet', 'RollbackTransaction', 
'SetDescription', 'SetMetadata', 'SetMetadataItem', 'SetStyleTable', 'StartTransaction', 'SyncToDisk', 'TestCapability', 
'__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', 
'__getitem__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__len__', '__lt__', 
'__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', 
'__subclasshook__', '__swig_destroy__', '__weakref__', 'name', 'this', 'thisown'

Methods/attributes of a layer of a vector object:
'AlterFieldDefn', 'AlterGeomFieldDefn', 'Clip', 'CommitTransaction', 'CreateFeature', 'CreateField', 'CreateFields', 
'CreateGeomField', 'DeleteFeature', 'DeleteField', 'Dereference', 'Erase', 'FindFieldIndex', 'GetArrowStream', 
'GetArrowStreamAsNumPy', 'GetArrowStreamAsPyArrow', 'GetDescription', 'GetExtent', 'GetFIDColumn', 'GetFeature', 
'GetFeatureCount', 'GetFeaturesRead', 'GetGeomType', 'GetGeometryColumn', 'GetGeometryTypes', 'GetLayerDefn', 
'GetMetadata', 'GetMetadataDomainList', 'GetMetadataItem', 'GetMetadata_Dict', 'GetMetadata_List', 'GetName', 
'GetNextFeature', 'GetRefCount', 'GetSpatialFilter', 'GetSpatialRef', 'GetStyleTable', 'GetSupportedSRSList', 
'Identity', 'Intersection', 'Reference', 'Rename', 'ReorderField', 'ReorderFields', 'ResetReading', 'RollbackTransaction', 
'SetActiveSRS', 'SetAttributeFilter', 'SetDescription', 'SetFeature', 'SetIgnoredFields', 'SetMetadata', 'SetMetadataItem', 
'SetNextByIndex', 'SetSpatialFilter', 'SetSpatialFilterRect', 'SetStyleTable', 'StartTransaction', 'SymDifference', 
'SyncToDisk', 'TestCapability', 'Union', 'Update', 'UpdateFeature', 'UpsertFeature', 
'__bool__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__enter__', '__eq__', '__exit__', '__format__', 
'__ge__', '__getattribute__', '__getitem__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', 
'__iter__', '__le__', '__len__', '__lt__', '__module__', '__ne__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', 
'__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'schema', 'this', 'thisown'

Methods/attributes of a feature of a vector object:
'Clone', 'Dereference', 'Destroy', 'DumpReadable', 'Equal', 'ExportToJson', 'FillUnsetWithDefault', 'GetDefnRef', 'GetFID', 
'GetField', 'GetFieldAsBinary', 'GetFieldAsDateTime', 'GetFieldAsDouble', 'GetFieldAsDoubleList', 'GetFieldAsISO8601DateTime', 
'GetFieldAsInteger', 'GetFieldAsInteger64', 'GetFieldAsInteger64List', 'GetFieldAsIntegerList', 'GetFieldAsString', 
'GetFieldAsStringList', 'GetFieldCount', 'GetFieldDefnRef', 'GetFieldIndex', 'GetFieldType', 'GetGeomFieldCount', 
'GetGeomFieldDefnRef', 'GetGeomFieldIndex', 'GetGeomFieldRef', 'GetGeometryRef', 'GetNativeData', 'GetNativeMediaType', 
'GetStyleString', 'IsFieldNull', 'IsFieldSet', 'IsFieldSetAndNotNull', 'Reference', 'SetFID', 'SetField', 
'SetFieldBinaryFromHexString', 'SetFieldDoubleList', 'SetFieldInteger64', 'SetFieldInteger64List', 'SetFieldIntegerList', 
'SetFieldNull', 'SetFieldString', 'SetFieldStringList', 'SetFrom', 'SetFromWithMap', 'SetGeomField', 'SetGeomFieldDirectly', 
'SetGeometry', 'SetGeometryDirectly', 'SetNativeData', 'SetNativeMediaType', 'SetStyleString', 'UnsetField', 'Validate', 
'_SetField2', '__class__', '__cmp__', '__copy__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', 
'__ge__', '__getattr__', '__getattribute__', '__getitem__', '__getstate__', '__gt__', '__hash__', '__init__', 
'__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', 
'__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', '__swig_destroy__', 
'__weakref__', '_getfieldindex', 'geometry', 'items', 'keys', 'this', 'thisown'

''' 

def addBuffer(inVectName, outVectName, bufferDist, driverName='ESRI Shapefile'):
    '''Borrowed heavily from GDAL/OGR Cookbook:
    http://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html?highlight=buffer#create-buffer
    '''
    driver = ogr.GetDriverByName(driverName)
    vect = driver.Open(inVectName)
    bufferedOut = driver.CreateDataSource(outVectName)
    bufferedLyr = bufferedOut.CreateLayer(outVectName)
    featureDefn = bufferedLyr.GetLayerDefn() ## Why is this necessary? Shouldn't I be copying lyr defn from the original vect?

    # Iterate over all layers, adding them to new layer one-by-one
    layersIterator = vect.GetLayer() ## returns all features in the original vector
    for layer in layersIterator:
        geom = layer.GetGeometryRef() ## Not clear here --- why not just layer.geometry()?
        buffered = geom.Buffer(bufferDist) # add buffer

        # Create the new feature, add it to the output layer
        outLayer = ogr.Feature(featureDefn)
        outLayer.SetGeometry(buffered)
        bufferedLyr.CreateFeature(outLayer)
        outLayer = None # reset --- why is this mecessary?

def maskRasterByVect(raster_path, vect_path, clipped_raster_path):
    '''Code from: https://rasterio.readthedocs.io/en/stable/topics/masking-by-shapefile.html
    '''
    with fiona.open(vect_path) as vect:
        vect_mask = [feature['geometry'] for feature in vect]

    with rio.open(raster_path) as src:
        band_names = src.descriptions
        out_image, out_transform = rasterio.mask.mask(src, vect_mask, crop=True)
        out_meta = src.meta
    
    out_meta.update({"height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})
    
    with rio.open(clipped_raster_path, "w", **out_meta) as dest:
        dest.write(out_image)
        dest.descriptions = band_names

def rgb2rgba(in_raster_path, out_raster_path, rbandNum=3, gbandNum=2, bbandNum=1):
    ## OPEN FILES, SET UP VARS
    driver = gdal.GetDriverByName("GTiff")
    raster = gdal.Open(in_raster_path)
    prj = raster.GetProjection()
    bands = [raster.GetRasterBand(n) for n in (rbandNum, gbandNum, bbandNum)]
    minMaxL = [[0,band.ReadAsArray().max(),0,255] for band in bands] # [min, max, destMin, destMax] by band

    # CREATE ALPHA BAND
    nodata = -9999
    alphaArray = np.logical_or.reduce([np.array(band.ReadAsArray())!=nodata for band in bands])
    
    # OUTPUT AS COMPRESSED TIF
    ## Learned to create a new raster using Francisco's rgb_quick.py script (shared via email June 30, 2023)
    outRaster = driver.Create(out_raster_path, alphaArray.shape[1], alphaArray.shape[0], 3, gdal.GDT_Byte)
    originX, pixelWidth, b, originY, d, pixelHeight = raster.GetGeoTransform()
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))

    for band_num, band in zip(range(1,4), bands):
        band = band.ReadAsArray().astype(float)
        outband = outRaster.GetRasterBand(band_num)
        band[band==nodata] = 0.0
        band *= 255 / band.max()
        outband.WriteArray(band.astype(int))
        outband.SetNoDataValue(0)
    
    # write alpha band
    outband = outRaster.GetRasterBand(4)
    outband.WriteArray(alphaArray)
    outband.SetNoDataValue(0)

    # settings srs from input tif file. ?? Is it necessary to do this after adding bands?
    outRasterSRS = osr.SpatialReference(wkt=prj)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


    # Old method: using gdal translate, but not ideal because requires editing original file
    # raster.GetRasterBand(4).WriteArray(alphaArray)
    # gdal.Translate(out_raster_path, in_raster_path, 
    #                bandList=[rbandNum, gbandNum, bbandNum], 
    #                maskBand=4, 
    #                outputType=gdal.GDT_Byte, 
    #                scaleParams=minMaxL, 
    #                options = ['PHOTOMETRIC=YCBCR', 'COMPRESS=JPEG'])
    


def mergeShpFiles(shpFilePathsL, outFile):
    ## UPDATE THIS TO NOT USE THE SUBPROCESS BY IMPORTING: from osgeo_utils import ogrmerge, then call ogrmerge()
    '''ogrmerge(src_datasets: Optional[Sequence[str]] = None, dst_filename: Union[str, os.PathLike, NoneType] = None, driver_name: Optional[str] = None, overwrite_ds: bool = False, overwrit
e_layer: bool = False, update: bool = False, append: bool = False, single_layer: bool = False, layer_name_template: Optional[str] = None, skip_failures: bool = False, src_geom_types: Opt
ional[Sequence[int]] = None, field_strategy: Optional[str] = None, src_layer_field_name: Optional[str] = None, src_layer_field_content: Optional[str] = None, a_srs: Optional[str] = None,
 s_srs: Optional[str] = None, t_srs: Optional[str] = None, dsco: Optional[Sequence[str]] = None, lco: Optional[Sequence[str]] = None, progress_callback: Optional = None, progress_arg: Op
tional = None)
    '''
    process = subprocess.run(' '.join(['ogrmerge.py -single -o', outFile, shpFilePathsL[0], shpFilePathsL[1], '-src_layer_field_name date']),
                             shell=True,
                             stdout=subprocess.PIPE,
                             universal_newlines=True)
    print(process.stdout)
    
    for shpF in shpFilePathsL[2:]:
        print('Currently appending:', shpF.split('/')[-1])
        process = subprocess.run(' '.join(['ogrmerge.py -single -o', outFile, outFile, shpF, '-overwrite_layer -src_layer_field_name date']),
                                shell=True,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
        print(process.stdout)

def convertVect(informat, infile, outformat, outfile):
    gdal.UseExceptions()
    gdal.VectorTranslate(outfile, srcDS=infile, format=outformat)


def printVect(format, infile):
    '''From chapter 3 of Geoprocessing with Python
    https://www.manning.com/books/geoprocessing-with-python
    '''
    pass



if __name__ == '__main__':
    ## testing
    # outBuffer = '/Users/cd/Downloads/drive-download-20230621T173107Z-001/teak_allSampleRoadsBuffered.shp'
    # clippedRaster = '/Users/cd/Downloads/drive-download-20230621T173107Z-001/teak_clipped.tif'
    # outRaster = '/Users/cd/Downloads/teak_RGBA.tif'
    # inRaster = '/Users/cd/Downloads/DP3.30006.001_TEAK__reflectance_mosaic.tif'
    # addBuffer('/Users/cd/Downloads/drive-download-20230621T173107Z-001/teak_allSampleRoads.shp', outBuffer, 200)
    # maskRasterByVect(inRaster, '/Users/cd/Downloads/drive-download-20230621T173107Z-001/teak_200m_sampleSites_fullJuneUpdate.shp', clippedRaster)
    # rgb2rgba(clippedRaster, outRaster)

    # shpFiles = glob.glob('/Users/cd/Documents/field_data/garmin/*.shp')
    # mergeShpFiles(shpFiles, '/Users/cd/Documents/field_data/garmin/garmin_merged.shp')
    convertVect('KML','/Users/cd/Desktop/NEON_2023_FieldWork/basemaps/fire/burned_creekfire.kmz', 'ESRI Shapefile', '/Users/cd/Desktop/NEON_2023_FieldWork/basemaps/fire/burned_creekfire.shp')
    convertVect('KML','/Users/cd/Desktop/NEON_2023_FieldWork/basemaps/fire/unburned_creekfire.kmz', 'ESRI Shapefile', '/Users/cd/Desktop/NEON_2023_FieldWork/basemaps/fire/unburned_creekfire.shp')


    '''ogrmerge.py -single -o merged.shp /Users/cd/Downloads/drive-download-20230726T181224Z-001/TEAK072023.shp /Users/cd/Downloads/drive-download-20230726T181224Z-001/TEAK0715231.shp -src_layer_field_name date'''
