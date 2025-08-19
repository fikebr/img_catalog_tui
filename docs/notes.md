# Image Catalog TUI

A TUI app that presents the user with a menu of actions and based on selection it will ask questions then act

## tech stack

- python: programming language
- uv: module management & run scripts
- modules: toml, pillow, rich, textual, argparse, 
- pyinstaller: convert python to exe

## notes

- do not make the user type out the whole menu option. give every option a one char key (a to z) do not use x, u or h
- keep the menu logic seperate from the business logic so that i can add other interfaces to the business logic in the future.



## Menus

x = exit app
u = go up a level
h = help


folder
	scan
	index
	
	
imageset
	exif_parse
	exif_clean


## command_line_params

input_folder: string, no default, required
config_file: string, default: .\config.toml
	
## configuration parameters 

file_tags = orig, thumb, v2, v3, v4, v5, up2, up3, up4, up6

## Sample EXIF data for a midjourney image

90s Retro Sublimation Clipart --ar 3:4 --stylize 750 --v 7 Job ID: 53d6686d-db8c-499e-9250-c2afb94cf34d

## Sample EXIF data for a fooocus image

"{\"adm_guidance\": \"(1.5, 0.8, 0.3)\", \"base_model\": \"hotart_5\", \"base_model_hash\": \"f341bff20f\", \"clip_skip\": 2, \"full_negative_prompt\": [\"\"], \"full_prompt\": [\"a girl meditating; with plants in the sunroom; an empty thought bubble foating overhead | in the style of Harumi Hironaka u95-y105\"], \"guidance_scale\": 4, \"loras\": [], \"metadata_scheme\": \"fooocus\", \"negative_prompt\": \"\", \"performance\": \"Speed\", \"prompt\": \"a girl meditating; with plants in the sunroom; an empty thought bubble foating overhead | in the style of Harumi Hironaka u95-y105\", \"prompt_expansion\": \"\", \"refiner_model\": \"None\", \"refiner_switch\": 0.5, \"resolution\": \"(896, 1152)\", \"sampler\": \"dpmpp_2m_sde_gpu\", \"scheduler\": \"karras\", \"seed\": \"7191714424689809151\", \"sharpness\": 5, \"steps\": 40, \"styles\": \"[]\", \"vae\": \"Default (model)\", \"version\": \"Fooocus v2.5.5\"}"

## Example TOML file..

imageset = "2024-06-10_00-08-45_4697"
source = "midjourney" #fooocus, freepik, other

[review]
needs = ""

[biz]
good_for = ""
posted_to = ""

[interview]
interview_date = "2025-08-18 15:46"
template_used = "inverview_template_2.tmpl"
title = ""
description = ""


[midjourney]
description = "a 35mm photography shot of a deserted beach at sunrise, with footprints leading to the water, soft waves washing ashore, and a few distant sailboats; the color temperature is warm with natural lighting, capturing the peaceful solitude of the early morning --ar 3:4 --v 7 Job ID: 758b8376-b799-4065-ac91-90d109ab15a8"
prompt = "a 35mm photography shot of a deserted beach at sunrise, with footprints leading to the water, soft waves washing ashore, and a few distant sailboats; the color temperature is warm with natural lighting, capturing the peaceful solitude of the early morning --ar 3:4 --v 7"
jobid = "758b8376-b799-4065-ac91-90d109ab15a8"

[fooocus]
Prompt = "a pen and ink children's story graphic novel page | in the style of Kelly Freas"
"Negative Prompt" = "ugly face, deformed hands, watermark, signature"
"Fooocus V2 Expansion" = ""
Styles = "[]"
Performance = "Quality"
Resolution = "(896, 1152)"
"Guidance Scale" = "6"
Sharpness = "6"
"ADM Guidance" = "(1.5, 0.8, 0.3)"
"Base Model" = "hotart_2.safetensors"
"Refiner Model" = "None"
"Refiner Switch" = "0.5"
"CLIP Skip" = "2"
Sampler = "dpmpp_3m_sde_gpu"
Scheduler = "karras"
VAE = "Default (model)"
Seed = "5034843562244127231"
"Metadata Scheme" = "False"
Version = "Fooocus v2.4.3"
"Full raw prompt" = "Positivea pen and ink children's story graphic novel page | in the style of Kelly Freas\nNegativeugly face, deformed hands, watermark, signature"

## Sample menu config menu.toml

[folder]

[folder.scan]
description = "scan a new folder of images"
command = "folder_scan"
questions = ["folder_name|What folder to scan?"]

[folder.index]
description = "index a folder that has already been scanned and create a index.json and a index.html"
command = "folder_index"
questions = ["folder_name|What folder to scan?"]

[imageset]

[imageset.html]
description = "Create an HTML report of the imageset"
command = "imageset_html"
questions = ["folder_name|What folder to scan?", "imageset|What imageset?"]

[imageset.interview]
description = "Perform an interview for the imageset."
command = "imageset_interview"
questions = ["folder_name|What folder to scan?", "imageset|What imageset?", "interview_template|What template to use for the interview?"]



## Pseudo Code


def main()

	config = get_config()
	logger = setup_logger()
	args = parse_args()
    menu_config = load_menu_config() # see "Sample menu config menu.toml" for an example of the menu config file that needs to be parsed.
	
	while True:
	
		command, c_args = start_menu()
		
		if command == "x":
			exit
			
		handle_command(command, c_args)
		
def handle_command(command, c_args):

	if command == "folder_scan":
		folder_scan(c_args)
		
	if command == "some_other_command":
		other_command(c_args)


def folder_scan(c_args)

	folder_name = c_args{"folder_name"}
	
	# get this imagesets in the folder
	imagesets = get_imagesets_in_folder(folder_name)
	
	# are any of the folders "abandoned" if yes then delete the folder.
	imagesets = delete_abandoned_folders(folder_name, imagesets)
	
	# make sure that each folder has an "orig" file.
	tag_orig_file(folder_name, imagesets)
	
	# parse the EXIF metadata from the orig file and load it into the toml file.
	extract_exif_data_from_orig_images(folder_name)
	
	
def extract_exif_data_from_orig_images(folder_name):
	
	with open folder_name:
		
		for subfolder in folder_name:
		
			if subfolder starts with "_":
			
				skip
				
			get the orig_image_file # the image file in the folder that has the *_orig tag.
			get the toml_file # the file in the folder with the *.toml extension
						
			if orig_image_file is not found
				skip
				
			toml_data = {}
			
			if toml_file exists:
				toml_data = parse the toml_file
			else
				toml_data["imageset"] = subfolder
				
			if toml_data -> midourney -> prompt exists and is not null
				skip

			if toml_data -> fooocus -> prompt exists and is not null
				skip
				
			use Pillow to open the orig_image file and parse the exif metadata.
			
			if image exif "PNG:Fooocus_scheme" == "fooocus": # then this is an image generated by the fooocus app
				data = image exif "PNG:Parameters"
				
				# see "Sample EXIF data for a fooocus image" for an example of what data should look like.
				
				data_parsed = json parse data
				
				toml_data{"source"} = "fooocus"
				toml_data{"fooocus"} = data_parsed
				

			if image exif "PNG:Author" == "aardvark_fike": # then this is an image generated by the midjourney app
				data = image exif "PNG:Description"
				# see "Sample EXIF data for a midjourney image" for an example of what data should look like.

				toml_data{"source"} = "midjourney"
				toml_data{"midjourney"}{"description"} = data
				
				prompt, jobid = parse_data_into_prompt_and_jobid(data)
				
				toml_data{"midjourney"}{"prompt"} = prompt
				toml_data{"midjourney"}{"jobid"} = jobid
				
			# convert toml_data to a toml string and then write it to the toml_file

			
	
def tag_orig_file(folder_name, imagesets):

	for imageset in imagesets:
		imageset_folder = f"{folder_name}\\{imageset}"
		
		with open imageset_folder:
			
			# if there already a "*_orig*" file in the folder?
			# - then skip
			
			# if no _orig file is found then
			# - get a list of all image files.

			# - if there is only one file then
			#   - tag that file as _orig

			# - if there are multiple image files
			#   - find the file that has no other tags and tag it as _orig
	
def delete_abandoned_folders(folder_name, imagesets):
	# an "abandoned" folder is a folder that has no image files.
	
	imagesets_to_delete = []
	
	for imageset in imagesets:
		imageset_folder = f"{folder_name}\\{imageset}"
	
		for files in imageset_folder:
			 
			 if no imagefiles found:
				imagesets_to_delete.append(imageset)
				
	if imagesets_to_delete:
		
		for im in imagesets_to_delete:
			folder_to_delete = f"{folder_name}\\{im}"
			delete(folder_to_delete)
			print(f"Deleted abandoned folder: {im}")
			
		imagesets = imagesets - imagesets_to_delete
	
	return imagesets


def get_imageset_from_filename(file):
	"get the imageset for a file based on the files name"

	file_base, file_ext = parse_file_parts(file)

	# remove tags from the filename
	tags = []
	for tag in config.file_tags
		if f"_{tag}" exists in file_base then
			tags.append(tag)
			remove f"_{tag}" from file_base
	
	return file_base, file_ext, tags




def get_imagesets_in_folder(folder_name):
	"returns a list of the imagesets in a parent folder"
	
	imagesets = []
	
	with open folder_name
		for file in folder
			# if file is a folder then that is the imageset
			if file is a folder and does not start with "_"
				imagesets.append(file)
			
			# if file is a file then get the imageset name,
			# create a folder and move all the associated files in
			elsif file is a file and does not start with "_" and exists
				imageset, ext, tags = get_imageset_from_filename(file)
				
				# create an imageset folder (if needed)
				create_folder(imageset)
	
				# move all files (f"*{imageset}*") into the new imageset_folder
				move_files(imageset, folder_name)
				
				imagesets.append(imageset)
				
				
	return imagesets			
				
				
if __name__ == "__main__":
	main()
	
	
## psuedo code for the logging module

import logging
from logging.handlers import RotatingFileHandler
import os

LOG_FORMAT = "%(asctime)s %(levelname)s %(lineno)d - %(message)s"  # %(filename)s
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = "logs/app.log"
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


# Usage:
# import logging
# from log import setup_logging
# setup_logging()
# logging.error("This is an error message")


def setup_logging():
    """
    Configure logging settings for the application.

    Logs are written to a rotating file with a maximum size of 10 MB.
    The log format includes the date, time, log level, line number, and message.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create the log directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating log directory: {e}")
            return

    # Set up the rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=LOG_FILE_MAX_SIZE, backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    # Also log to the console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
