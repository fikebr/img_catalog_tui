# add search

add the capability to add search tools to the application.

## Pages (Search & Results)

### Search:

a front end for the search types that i want to perform.
- each search type gets it's own section
- opens the results in new tab

### Results:

this page displays the results of the search from the previous page in a tabular format.
- responsive.
- sorting by column
- filtering by column
- bulk actions on the current results (move, perform a review, export data)
- hide\unhide columns

## Search types

- prompt: imagesets where prompt contains X
- status, good_for, posted_to: status = X, good_for contains Y and posted_to does not contain Z
- folder: folder = X
- imageset_name: imageset_name contains X
- 'status', 'needs': 'status' = X and 'needs' contains Y or 'needs' is not null

## results columns

selection checkbox
folder_name
imagesetname
status
edit
good_for
needs
posted_to
thumbnail
action buttons

## action buttons

- open imageset
- open edit pop-up
- copy full imageset folder path


