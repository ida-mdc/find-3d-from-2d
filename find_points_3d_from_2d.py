import numpy as np
# import pyimagej

from scyjava import config, jimport

config.add_repositories(
    {'scijava.public': 'https://maven.scijava.org/content/groups/public'})
config.add_endpoints('net.imagej:imagej:2.2.0')
config.add_endpoints('net.imagej:ij:1.53j')
HashMap = jimport("java.util.HashMap")

IJ = jimport('ij.IJ')
RoiManager = jimport('ij.plugin.frame.RoiManager')
Roi = jimport('ij.gui.Roi')
Duplicator = jimport('ij.plugin.Duplicator')
Slicer = jimport('ij.plugin.Slicer')
ZProjector = jimport('ij.plugin.ZProjector')

# Use these for visual debugging
# ImageJ = jimport('ij.ImageJ')
# imagej = ImageJ()


def find_points(image_filename, csv_filename, output_filename, roi_filename):
    # img = tifffile.imread(image_filename)
    imp = IJ.openImage(image_filename)
    points = np.genfromtxt(csv_filename, delimiter=';')

    # Remove header (time_point;number;Area;Mean;Min;Max;X;Y)
    points = points[1:, :]
    print('Number of points: %d' % points.shape[0])

    N = points.shape[0]
    new_points = np.c_[points.copy(), -1.0 * np.ones(N)]

    target_channel = 2

    duplicator = Duplicator()
    slicer = Slicer()
    half_region_size = [25.0, 25.0]
    roi_manager = RoiManager(False)

    num_failed = 0

    # Loop over points and find their Z-values
    for k in range(N):
        point = points[k, :]

        roi = Roi(point[6] - half_region_size[0],
                  point[7] - half_region_size[1], half_region_size[0] * 2.0,
                  half_region_size[1] * 2.0)

        imp.setPosition(target_channel, 1, int(point[0]))
        roi.setPosition(target_channel, 1, int(point[0]))
        imp.setRoi(roi)

        dup = duplicator.run(imp, target_channel, target_channel, 1,
                             imp.getNSlices(), int(point[0]), int(point[0]))
        resliced = slicer.reslice(dup)
        proj = ZProjector.run(resliced, 'avg')
        IJ.run(proj, "Find Maxima...",
               "prominence=10 output=[Point Selection]")
        pt_roi = proj.getRoi()
        if pt_roi is not None:
            z_coord = pt_roi.getYBase()
            new_points[k, 8] = z_coord

            # Set the hyperstack position
            pt_roi.setLocation(point[6], point[7])
            pt_roi.setImage(imp)
            pt_roi.setPosition(target_channel, int(z_coord), int(point[0]))

            roi_manager.addRoi(pt_roi)
        else:
            num_failed += 1
            new_points[k, 8] = np.NAN

    print('Number of failed detections: %d' % num_failed)

    np.savetxt(output_filename,
               new_points.astype(int),
               delimiter=';',
               fmt='%i',
               header='time_point;number;Area;Mean;Min;Max;X;Y;Z')

    roi_manager.runCommand('Save', roi_filename)


if __name__ == '__main__':
    # csv_filename = sys.argv[1]
    # image_filename = sys.argv[2]

    csv_filename = '/mnt/data/Finotto_Lise/project/04_Processed_Data/01_Annotated_Macrophages/201013_LBT070_5dpi_Pos003.csv'
    image_filename = '/mnt/data/Finotto_Lise/project/02_Primary_Data/201013_LBT070_5dpi_Pos003.tif'
    output_filename = '/mnt/data/Finotto_Lise/project/04_Processed_Data/02_Annotated_Macrophages_3D/201013_LBT070_5dpi_Pos003.csv'
    roi_filename = '/mnt/data/Finotto_Lise/project/04_Processed_Data/02_Annotated_Macrophages_3D/201013_LBT070_5dpi_Pos003.zip'

    find_points(image_filename, csv_filename, output_filename, roi_filename)
