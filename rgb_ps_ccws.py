import cv2 as cv
import numpy as np
import os

class areaLeaf:
    def __init__(self, images, input_folder, output_folder):
        self.images = images
        self.input_dir = input_folder
        self.output_dir = output_folder
        self.colors = self.readConfig("config.txt")
        self.al_per_image = {}

        self.fontStyle = {
            "font": cv.FONT_HERSHEY_SIMPLEX,
            "scale": 1.2,
            "color": (20, 20, 20),
            "thickness": 2
        }

    def pixelColor(self, bgr, color_list):
        dists = []
        aa = np.array((int(bgr[0]), int(bgr[1]), int(bgr[2])))
        for color in color_list:
            bb = np.array(color)
            dists.append(np.linalg.norm(aa - bb))

        index_min_dist = dists.index(min(dists))
        return color_list[index_min_dist]

    def readConfig(self, config_file):
        allColors = []
        with open(config_file, "r") as file:
            config = file.readlines()

        for i in range(len(config) - 1):
            ar = config[i].split(" ")
            allColors.append((int(ar[0]), int(ar[1]), int(ar[2])))

        return allColors

    def run(self):

        for cont, curImg in enumerate(self.images):
            print(f"[{cont + 1}/{len(self.images)}] {curImg}")
            image_name = f"{curImg.split('.')[0]}"

            filenameCurr = os.path.join(self.input_dir, curImg)
            image = cv.imread(filenameCurr, cv.IMREAD_UNCHANGED)

            blr = cv.GaussianBlur(image, (15, 15), 0)
            segmented_image = blr.copy()

            # pixels painting
            height, width, depth = image.shape
            for i in range(0, height):
                for j in range(0, width):
                    bgr = (segmented_image[i, j])
                    segmented_image[i, j] = self.pixelColor(bgr, self.colors)

            # save segmentation image
            os.makedirs(self.output_dir, exist_ok=True)
            cv.imwrite(os.path.join(self.output_dir, f"{image_name}_SEGM.jpg"), segmented_image)

            # analysis image for find leafs
            gray_img = cv.cvtColor(segmented_image, cv.COLOR_BGR2GRAY)
            blurred = cv.GaussianBlur(gray_img, (7, 7), 0)
            threshold = cv.threshold(blurred, 0, 255, cv.THRESH_BINARY_INV | cv.THRESH_OTSU)[1]
            analysis = cv.connectedComponentsWithStats(threshold, 10, cv.CV_32S)
            (totalLabels, label_ids, values, centroid) = analysis

            # find etalon square area
            etalonSize = 0
            for i in range(1, totalLabels):
                area = values[i, cv.CC_STAT_AREA]
                center = (int(centroid[i][1]), int(centroid[i][0]))
                b, g, r = image[center[0], center[1]]
                if (int(r) > int(g) + int(b)):
                    etalonSize = area
                    break

            # put value of areas into image
            leaf_areas = []
            for i in range(1, totalLabels):
                area = values[i, cv.CC_STAT_AREA]
                org = (values[i][0], values[i][1])
                cv.putText(image, f"{i}: {round(area/etalonSize, 2)}cm2", org, self.fontStyle["font"],
                            self.fontStyle["scale"], self.fontStyle["color"], self.fontStyle["thickness"], cv.LINE_AA)
                area_pix_cm = (area, round(area/etalonSize, 2))
                leaf_areas.append(area_pix_cm)

            # save result image
            added_image = cv.addWeighted(image, 0.5, segmented_image, 0.7, 0)
            cv.imwrite(os.path.join(self.output_dir, f"{image_name}_AREA.jpg"), added_image)
            print(f"{curImg} - complete")
            self.al_per_image[curImg] = leaf_areas
        return self.al_per_image