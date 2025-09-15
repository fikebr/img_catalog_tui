
from . import views_api
from . import views_html


def register_routes(app):


    app.add_url_rule('/folder/<string:foldername>/review/<string:review_type>', endpoint='reviews', view_func=views_html.reviews)
    app.add_url_rule('/', endpoint='index', view_func=views_html.index)
    app.add_url_rule('/health', endpoint='health', view_func=views_html.health)
    app.add_url_rule('/favicon.ico', endpoint='favicon', view_func=views_api.favicon)
    
    # Image file serving from folder locations
    app.add_url_rule('/images/<string:foldername>/<string:imageset_name>/<path:filename>', endpoint='serve_image', view_func=views_html.serve_image)



    ## API endpoints

    app.add_url_rule('/api/folders', endpoint='folders', view_func=views_api.folders)
    app.add_url_rule('/api/folder/<string:foldername>', endpoint='folder', view_func=views_api.folder)
    app.add_url_rule('/api/imageset/<string:foldername>/<string:imageset>', endpoint='imageset', view_func=views_api.imageset)
    
    app.add_url_rule('/api/folder/<string:foldername>/review/new', endpoint='review_new_api', view_func=views_api.review_new)

    # TODO: api routes for changing status, edits, needs
    # TODO: api routes for performing an interview
    # TODO: api routes for reviews: new->working, 