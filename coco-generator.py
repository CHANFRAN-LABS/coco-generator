import cv2
import json
import os
import argparse

parser = argparse.ArgumentParser(description="Generate COCO json dataset from grayscale object labels")
parser.add_argument("-i", "--images", default="", type=str, metavar="PATH", help="path to images folder")
parser.add_argument("-a", "--annotations", default="", type=str, metavar="PATH", help="path to annotations json file")
parser.add_argument("-o", "--output", default="coco-dataset", type=str, metavar="PATH", help="output coco json filename | defaults to coco-dataset")
parser.add_argument("-c", "--category_id", default=1, type=int, metavar="PATH", help="default category id for objects in your dataset. If you have more than one category, you need to enter the rest manually in the output json | defaults to 1")
parser.add_argument("-l", "--license_id", default=4, type=int, metavar="PATH", help="default license id for your images. If you have more than one license, you need to enter the rest manually in the output json  | defaults to 4")

class CocoGenerator:
	def __init__(self, arguments):
		self.images_folder = arguments.images
		self.labels_folder = arguments.annotations
		self.image_paths = os.listdir(self.images_folder)
		self.image_list = []
		self.annotation_list = []
		self.image_id = 1
		self.annotation_id = 1
		self.default_category = arguments.category_id
		self.default_license = arguments.license_id
		self.default_iscrowd = 0
		self.output_path = arguments.output + ".json"
		self.resolution = 0.05		#bilateral filter diameter of 5% of image size. This is neccessary to prevent over-segmenting objects in the label
		self.threshold = 70			#this value is arbitrary as THRESH_OTSU calculates the optimal threshold based on the image

	def generate_mask(self, image_path):
		label = cv2.imread(self.labels_folder + image_path, cv2.IMREAD_GRAYSCALE)
		_, mask = cv2.threshold(label, self.threshold, 255, cv2.THRESH_OTSU)

		return mask

	def mask_to_polygons(self, mask):
		height, width = mask.shape
		blur_diameter = int((height + width) * 0.5 * self.resolution)
		blurred_mask = cv2.bilateralFilter(mask, blur_diameter, 75, 75)
		contours, _ = cv2.findContours(blurred_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
		polygons = []
		bboxes = []
		for object in contours:
			coordinates = []
			for coord in object:
				coordinates.append(int(coord[0][0]))
				coordinates.append(int(coord[0][1]))
			polygons.append(coordinates)
			bbox = cv2.boundingRect(object)
			bboxes.append(bbox)

		return polygons, bboxes

	def generate_coco_image(self, image_path):
		image = cv2.imread(self.images_folder + image_path)
		height, width, _ = image.shape
		coco_image = {
			"id": self.image_id,
			"license": self.default_license,
			"coco_url": "N/A",
			"flickr_url": "N/A",
			"width": width,
			"height": height,
			"file_name": image_path,
			"date_captured": "N/A"
		}

		self.image_list.append(coco_image)

	def create_annotation(self, object_polygon, object_bbox):
		object_area = object_bbox[2] * object_bbox[3]
		annotation = {
			"segmentation": [object_polygon],
			"area": [object_area],
			"iscrowd": self.default_iscrowd,
			"image_id": self.image_id,
			"bbox": object_bbox,
			"category_id": self.default_category,
			"id": self.annotation_id
		}
		
		self.annotation_list.append(annotation)
		self.annotation_id += 1

	def generate_coco_annotations(self, image_path):
		mask = self.generate_mask(image_path)
		object_polygons, object_bboxes = self.mask_to_polygons(mask)
		for i in range(len(object_polygons)):
			polygon = object_polygons[i]
			bbox = object_bboxes[i]
			self.create_annotation(polygon, bbox)

		self.image_id += 1

	def generate_coco_json(self):
		with open('coco-template.json') as file:
			coco_json = json.load(file)
		coco_json["images"] = self.image_list
		coco_json["annotations"] = self.annotation_list

		self.output_json = coco_json

		with open(self.output_path, 'w') as file:
			json.dump(self.output_json, file)

def main():
	args = parser.parse_args()
	coco_generator = CocoGenerator(args)
	for image_path in coco_generator.image_paths:
		coco_generator.generate_coco_image(image_path)
		coco_generator.generate_coco_annotations(image_path)

	coco_generator.generate_coco_json()

if __name__ == "__main__":
    main()