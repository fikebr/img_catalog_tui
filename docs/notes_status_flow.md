# State Flow


## selection options
status = ["new", "keep", "edit", "working", "posted", "archive"]
edits = ["creative", "photoshop", "rmbg"]
needs = ["upscale", "vector", "orig", "thumbnail", "interview"]
good_for = ["stock", "rb", "poster"]
posted_to = ["stock", "rb", "tp", "faa", "etsy"]

## Status Flow

new -> keep | archive
keep -> edit | working
edit -> working
working -> posted

## Edits

during edits review 