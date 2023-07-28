'''Created in SHIFT office hours by Phil Brodrick
'''

from osgeo import gdal
import argparse
import utm





def main(rawargs=None) -> None:
    parser = argparse.ArgumentParser(description='Convert from UTM to LL')
    parser.add_argument('input_file', type=str)
    parser.add_argument('output_file', type=str)
    parser.add_argument('utm_zone', type=str)
    args = parser.parse_args(rawargs)


    input_ds = gdal.Open(args.input_file)
    input_dat = input_ds.ReadAsArray() # b,y,x, np compatible array
    output_dat = np.zeros(input_dat.shape)

    #nodata_mask = input_dat == input_ds.GetRasterBand(1).GetNoDataValue()
    nodata_mask = input_dat[0,...] == -9999

    converted_dat = utm.to_latlon(input_dat[0,nodata_mask], input_dat[1,nodata_mask])
    output_dat[0,nodata_mask] = converted_dat[0]
    output_dat[1,nodata_mask] = converted_dat[1]
    output_dat[2,nodata_mask] = input_dat[2, nodata_mask]


    # create blank output file
    driver = gdal.GetDriverByName('ENVI')
    driver.Register()

    outDataset = driver.Create(args.output_file,
                               input_dat.shape[2], # x
                               input_dat.shape[1], # y
                               3, # bands
                               gdal.GDT_Float32, # data type
                               options=['INTERLEAVE=BIL'] # extras, optional
                               )
    outDataset.SetProjection(input_ds.GetProjection())
    outDataset.SetGeoTransform(input_ds.GetGeoTransform())

    # gt = input_ds.GetGeoTransform()
    # [x_ul_px, x_px_size, x_px_rotation, y_ul_px, y_px_rotation, y_px_size]
    # pixel 120, 200 would be:
    # c_x = x_ul_px + 120 * gt[1] # assuming no rotation
    # c_y = y_ul_px + 120 * gt[4] # assuming no rotation
    # say you are at c_x, c_y, you can get to px_ x/y through:
    # px_x = (c_x - gt[0]) / gt[1]
    # px_y = (c_y - gt[3]) / gt[4]



    for _b in range(output_dat.shape[0]):
        outDataset.GetRasterBand(_b+1).WriteArray(output_dat[_b,...])
        outDataset.GetRasterBand(_b+1).SetNoDataValue(-9999)
    del outDataset

    





if __name__ == '__main__':
    main()
