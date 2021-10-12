import numpy as np
# import pyimagej

from scyjava import config, jimport

# headless
# config.add_option('-Xmx6g')
config.add_option('-Djava.awt.headless=true')
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

# Use these for visual debugging
# ImageJ = jimport('ij.ImageJ')
# imagej = ImageJ()


def save_rois_to_zip(rois, roi_filename):
    DataOutputStream = jimport('java.io.DataOutputStream')
    out = None
    names = ['point_%05d.roi' % x for x in range(len(rois))]
    ZipOutputStream = jimport('java.util.zip.ZipOutputStream')
    ZipEntry = jimport('java.util.zip.ZipEntry')
    BufferedOutputStream = jimport('java.io.BufferedOutputStream')
    FileOutputStream = jimport('java.io.FileOutputStream')
    zos = ZipOutputStream(BufferedOutputStream(FileOutputStream(roi_filename)))
    out = DataOutputStream(BufferedOutputStream(zos))
    RoiEncoder = jimport('ij.io.RoiEncoder')
    re = RoiEncoder(out)

    for k in range(len(rois)):
        label = names[k]
        roi = rois[k]
        if roi is not None:
            zos.putNextEntry(ZipEntry(label))
            re.write(roi)
            out.flush()
    out.close()


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
    # roi_manager = RoiManager(False)
    rois = []

    num_failed = 0

    MaximumFinder = jimport('ij.plugin.filter.MaximumFinder')
    ImageProcessor = jimport('ij.process.ImageProcessor')
    PointRoi = jimport('ij.gui.PointRoi')
    ResultsTable = jimport('ij.measure.ResultsTable')
    results_table = ResultsTable.getResultsTable()

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

        maximum_finder = MaximumFinder()
        maximum_finder.setup('', proj)

        ip = proj.getProcessor()
        tolerance = 10
        mode = 4  # 3 is "POINT_SELECTION" in imagej, 0 is "SINGLE_POINTS", 4 is LIST
        exclude_on_edges = True
        is_EDM = False
        _ = maximum_finder.findMaxima(ip, tolerance, False,
                                      ImageProcessor.NO_THRESHOLD, mode,
                                      exclude_on_edges, is_EDM)
        # keep looking at https://imagej.nih.gov/ij/developer/source/ij/plugin/filter/MaximumFinder.java.html
        # in analyzeAndMarkMaxima for how PointRoi are setup
        if results_table.size() > 0:
            x = results_table.getValue(0, 0)
            y = results_table.getValue(1, 0)
            pt_roi = PointRoi(x, y)
            results_table.reset()

            # TODO: pick up debugging here, inspect
            # import time
            # proj.show()
            # proj.setRoi(PointRoi(x, y))
            # time.sleep(30)

            if pt_roi is not None:
                z_coord = y
                new_points[k, 8] = z_coord

                # Set the hyperstack position
                pt_roi.setLocation(point[6], point[7])
                pt_roi.setImage(imp)
                pt_roi.setPosition(target_channel, int(z_coord), int(point[0]))

                # roi_manager.addRoi(pt_roi)
                rois += [pt_roi]
            else:
                num_failed += 1
                new_points[k, 8] = np.NAN
        else:
            num_failed += 1
            new_points[k, 8] = np.NAN

    print('Number of failed detections: %d' % num_failed)

    np.savetxt(output_filename,
               new_points.astype(int),
               delimiter=';',
               fmt='%i',
               header='time_point;number;Area;Mean;Min;Max;X;Y;Z')

    # save_rois_to_zip(rois, roi_filename)


if __name__ == '__main__':
    # csv_filename = sys.argv[1]
    # image_filename = sys.argv[2]

    csv_filename = '/mnt/data/Finotto_Lise/project/04_Processed_Data/01_Annotated_Macrophages/201013_LBT070_5dpi_Pos003.csv'
    image_filename = '/mnt/data/Finotto_Lise/project/02_Primary_Data/201013_LBT070_5dpi_Pos003.tif'
    output_filename = '/mnt/data/Finotto_Lise/project/04_Processed_Data/02_Annotated_Macrophages_3D/201013_LBT070_5dpi_Pos003.csv'
    roi_filename = '/mnt/data/Finotto_Lise/project/04_Processed_Data/02_Annotated_Macrophages_3D/201013_LBT070_5dpi_Pos003.zip'

    find_points(image_filename, csv_filename, output_filename, roi_filename)
