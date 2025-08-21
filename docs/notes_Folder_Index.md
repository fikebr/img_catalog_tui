# Folder Index

when the user uses the Folder -> Scan menu.
ask fr the folder, scan the folder & build an index.json and index.html
overwrite the existing (if there is one)



## pseudo code

def folder_scan(folder_name):

    index = {}

    open folder_name

    for item in folder_name

        if item is_folder and not item starts with "_":
            imageset = item
            index[imageset] = {}

            open folder_name\imageset

            for subitem in imageset_folder

                if subitem if_file and subitem is the orig image
                    index[imageset]["orig"] = subitem

    convert index to a json string
    save json string to index.json
    load templates\index.html as jinja template
    process the jinja template and same the html to index.html

## index.html

is a static html file with inline css and inline vanilla javascript logic
there is a header that lists the folder name and a timestamp for when it was created.
each imageset will have it's own card
    the card header will list the imageset name
    the card body will display the orig image
    clicking on the image will open the image up in a new tab
    the card will have a "copy imageset" button that sends just the imageset to the clipboard
    the card will have a "copy folder" button that sends the full path of the imageset folder to the clipboard
    the card will have a "open" button that will open a imageset report html (if it exists) in a new tab

there will be javascript logic that will hide the card if the asscociated image file is not found.