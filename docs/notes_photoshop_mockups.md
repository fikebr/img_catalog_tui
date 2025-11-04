# notes on integrating with photoshop to create mockup files.

this functionality in conjuntion with photoshop and a *.jsx script to create a set of mockup files for the given image file.

## Componenets

ImageMockup Class
Route: API: mockup_create
Route: HTML: imagefile_mockup: Get & Post
View: API & HTML: all logic needs to be in the view. no logic in the template unless absolutely necessary
HTML Template: if there are already mockups then just show thumbnails of those mockups and a "rebuild mockups" button. else show the form used to create new mockups

-----

# ImageMockup Class

a class to encapsulate all of the logic surrounding creating mockup images for a given ImageFile
"core\imagefile_mockups.py"

class ImageMockup

    config # the config object from the app
    base_folder #path to the mockup_base_folder. in config.
    mockup_type: poster, tshirt #the type of mockups to create for this image
    layer_name: 
    orientation: horizontal, vertical #the orienation of the imagefile
    image_file_path #the full path of the imagefile
    tags #the file tags from the file name
    version # is there is a version tag.
    output_folder # the full path to the folder where the files will be saved.
    mockups_folder # the full path to the folder that has all of the *.psd mockup files
    mockup_script # the *.jsx file to pass to photoshop
    mockup_script_json # the *.json file that the *.jsx script reads with the params that the script needs to run
    mockups: list[str] : a list of the existing mockup files (full path)

    def __init__: config, image_file_path, mockup_type, orientation
        then perform all of the _gets & _validates


    def _validate_base_folder
        get base_folder from config.
        if that folder no exist on the os then error

    def _validate_image_file
        if the imagefile from __init__ DNE then error

    def _get_file_tags
        use the get_tags_from_filename function to get the file tags for this image.

    def _get_version
        default to 1. if the image file has a version tag (ex. _v2, _v3, _v4, etc) then use that version instead

    def _get_layer_name
        layer name can come from __init__. if no then get it from config

    def to_dict @parameter
        convert the parameters of this object to a dict of strings and return

    def to_json @parameter
        takes the output of to_dict and create a json for it.

    def _validate_output_folder
        get the mockup_folder...
            does the imagefile have and version tags?... v2, v3, v4, etc.
            imagefile_folder = get the folder that the imagefile is in
            mockup_folder = <imagefile_folder>\_mockups_<version>
        create the mockup_folder

    def _get_mockups_folder
        mockups_folder = <base_folder>\<mockup_type>\<orientation>
        validate folder. error if not found

    def _get_mockup_script
        get script_name from config
        mockup_script = <base_folder>\<script_name>
        also set mockup_script_json = <base_folder>\params.json

    def _get_existing_mockup_images
        if output_folder is not set then _validate_output_folder
        if there are any image files in this folder then load them into the self.mockups list

    def _build_params_json
        validate that mockups_folder, image_file, layer_name, output_folder & mockup_script_json have been set.
        build a dict for mockups_folder, image_file, layer_name, output_folder and then convert to json
        write json to mockup_script_json. (overwrite if needed)

    def build_mockups
        get photoshop exe from config.
        validate the exe. if no then error.
        execute the exe passing the *.jsx script as a parameter.
        then run _get_existing_mockup_images



    
-----

## Views

### API: mockup_create

Inputs: image_file_path, mockup_type, orientation
Output: passed\failed

loads the object and executes the build_mockups method

### HTML: mockup (GET)

load the object and present the mockup template. that will either be a form to start a new mockup build or it will be a list of thumbnails for the existing mockups

### HTML: mockup (POST)

if the form above is being posted then load the object and execute the build_mockups prompt. then resent the above template.

-----

# JSX photoshop script

this script is outside of this project. these notes are only for informational purposes

the mockup *.jsx script will read a params.json file that has all the config info in it.
- mockups_folder
- image_file
- layer_name
- output_folder

scan mockups_folder for *.psd files.
for each *.psd file
    create an output file
