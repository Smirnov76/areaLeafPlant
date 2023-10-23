import cv2 as cv
import numpy as np
import os
from PIL import Image, ImageFilter

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

    def findContours(self, bin_image, min_area):
        contours_select = []
        contours, hierarchy = cv.findContours(bin_image, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv.contourArea(cnt)
            if (area > min_area):
                contours_select.append(cnt)
        return contours_select

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
            image_copy = image.copy()

            image = cv.GaussianBlur(image, (5, 5), 0)
            lab_img = cv.cvtColor(image, cv.COLOR_BGR2Lab)
            l, a, b = cv.split(lab_img)

            # pixel segmentation by inRange function
            bin_box = cv.inRange(a, 140, 255)
            bin_leafs = cv.inRange(a, 85, 120)

            # smoothing binary image
            bin_leafs_rgb = cv.cvtColor(bin_leafs, cv.COLOR_BGR2RGB)
            bin_leafs_pil = Image.fromarray(bin_leafs_rgb)
            bin_leafs_pil = bin_leafs_pil.filter(ImageFilter.ModeFilter(size=9))
            bin_leafs_sm = np.asarray(bin_leafs_pil)
            bin_leafs_sm = cv.cvtColor(bin_leafs_sm, cv.COLOR_RGB2GRAY)

            all_areas = []

            height, width, channels = image.shape
            segm_image = np.zeros((height, width, 3), np.uint8)
            segm_image[:] = self.colors[0]

            # find etalon box contour and his area
            box_contour = self.findContours(bin_box.copy(), 1500)
            box_mask = np.zeros((height, width, 1), np.uint8)
            cv.drawContours(box_mask, box_contour, 0, 255, thickness=cv.FILLED)
            # box_area = cv.countNonZero(box_mask)

            box_area = cv.contourArea(box_contour[0])
            area_pix_cm = (box_area, round(box_area/box_area, 2))
            all_areas.append(area_pix_cm)
            x, y, w, h = cv.boundingRect(box_contour[0])

            # draw all contours and save segmentation image
            cv.drawContours(segm_image, box_contour, -1, self.colors[2], thickness=-1)
            leafs_contours = self.findContours(bin_leafs_sm.copy(), 3000)
            cv.drawContours(segm_image, leafs_contours, -1, self.colors[1], thickness=-1)
            os.makedirs(self.output_dir, exist_ok=True)
            cv.imwrite(os.path.join(self.output_dir, f"{image_name}_SEGM.jpg"), segm_image)

            # put result areas of contours into result image
            cv.putText(segm_image, f"1: {round(box_area/box_area, 2)}cm2", (x, y), self.fontStyle["font"],
                       self.fontStyle["scale"], self.fontStyle["color"], self.fontStyle["thickness"], cv.LINE_AA)

            leaf_masks = []
            for i, contour in enumerate(leafs_contours):
                leaf_mask = np.zeros((height, width, 1), np.uint8)
                cv.drawContours(leaf_mask, leafs_contours, i, 255, thickness=cv.FILLED)
                leaf_masks.append(leaf_mask)
                # leaf_area = cv.countNonZero(leaf_mask)

                leaf_area = cv.contourArea(contour)
                area_pix_cm = (leaf_area, round(leaf_area/box_area, 2))
                all_areas.append(area_pix_cm)

                x, y, w, h = cv.boundingRect(leafs_contours[i])
                cv.putText(segm_image, f"{i+2}: {round(leaf_area/box_area, 2)}cm2", (x, y), self.fontStyle["font"],
                           self.fontStyle["scale"], self.fontStyle["color"], self.fontStyle["thickness"], cv.LINE_AA)

            # save result image
            result_image = cv.addWeighted(image_copy, 0.5, segm_image, 0.7, 0.0)
            cv.imwrite(os.path.join(self.output_dir, f"{image_name}_AREA.jpg"), result_image)
            print(f"{curImg} - complete")
            self.al_per_image[curImg] = all_areas
        return self.al_per_image