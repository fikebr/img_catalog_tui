
from . import views_api
from . import views_html


def register_routes(app):

    # routes to serve html
    app.add_url_rule('/', endpoint='index', view_func=views_html.index)
    app.add_url_rule('/folders', endpoint='folders', view_func=views_html.folders)
    app.add_url_rule('/folder/<string:foldername>/review/<string:review_type>', endpoint='reviews', view_func=views_html.reviews)

    # utility routes
    app.add_url_rule('/health', endpoint='health', view_func=views_html.health)
    app.add_url_rule('/favicon.ico', endpoint='favicon', view_func=views_api.favicon)
    
    # Image file serving from folder locations
    app.add_url_rule('/images/<string:foldername>/<string:imageset_name>/<path:filename>', endpoint='serve_image', view_func=views_html.serve_image)



    ## API endpoints

    app.add_url_rule('/api/folders', endpoint='api_folders', view_func=views_api.folders)
    app.add_url_rule('/api/folders/add/<path:folder_path>', endpoint='api_folders_add', view_func=views_api.folders_add, methods=['POST'])
    app.add_url_rule('/api/folders/<string:foldername>', endpoint='api_folders_delete', view_func=views_api.folders_delete, methods=['DELETE'])
    
    
    app.add_url_rule('/api/folder/<string:foldername>', endpoint='api_folder', view_func=views_api.folder)
    app.add_url_rule('/api/imageset/<string:foldername>/<string:imageset>', endpoint='api_imageset', view_func=views_api.imageset)
    
    app.add_url_rule('/api/folder/<string:foldername>/review/new', endpoint='api_review_new', view_func=views_api.review_new)

    # TODO: api routes for changing status, edits, needs
    # TODO: api routes for performing an interview
    # TODO: api routes for reviews: new->working, 