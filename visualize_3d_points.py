import numpy as np
# import pyimagej

from scyjava import config, jimport

# headless
# config.add_option('-Xmx6g')
# config.add_option('-Djava.awt.headless=true')
config.add_repositories(
    {'scijava.public': 'https://maven.scijava.org/content/groups/public'})
config.add_endpoints('net.imagej:imagej:2.3.0')
config.add_endpoints('net.imagej:imagej-legacy:0.38.0')
HashMap = jimport("java.util.HashMap")

IJ = jimport('ij.IJ')
RoiManager = jimport('ij.plugin.frame.RoiManager')
Roi = jimport('ij.gui.Roi')
Duplicator = jimport('ij.plugin.Duplicator')
Slicer = jimport('ij.plugin.Slicer')
ZProjector = jimport('ij.plugin.ZProjector')
ImageProcessor = jimport('ij.process.ImageProcessor')
PointRoi = jimport('ij.gui.PointRoi')
ResultsTable = jimport('ij.measure.ResultsTable')

# Use these for visual debugging
ImageJ = jimport('ij.ImageJ')
imagej = ImageJ()

roimanager = RoiManager()


def visualize_points(image_filename, csv_filename):
    # img = tifffile.imread(image_filename)
    imp = IJ.openImage(image_filename)
    imp.show()
    points = np.genfromtxt(csv_filename, delimiter=';')

    # Remove header (time_point;number;Area;Mean;Min;Max;X;Y;Z)
    points = points[1:, :]
    print('Number of points: %d' % points.shape[0])

    N = points.shape[0]

    target_channel = 2

    # Loop over points and find their Z-values
    for k in range(N):
        point = points[k, :]

        frame = int(point[0])
        roi = PointRoi(float(point[6]), float(point[7]))

        print([
            k,
            int(point[6]),
            int(point[7]), frame, target_channel,
            int(point[8])
        ])

        # imp.setPosition(target_channel, int(point[8]), frame)
        roi.setPosition(target_channel, int(point[8]), frame)

        roimanager.addRoi(roi)


if __name__ == '__main__':
    # csv_filename = sys.argv[1]
    # image_filename = sys.argv[2]

    image_filename = '/mnt/data/Finotto_Lise/project/02_Primary_Data/201013_LBT070_5dpi_Pos003.tif'
    point_filename = '/mnt/data/Finotto_Lise/project/04_Processed_Data/02_Annotated_Macrophages_3D/201013_LBT070_5dpi_Pos003.csv'

    visualize_points(image_filename, point_filename)
