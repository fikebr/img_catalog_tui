
from . import views_api
from . import views_html


def register_routes(app):

    # routes to serve html
    app.add_url_rule('/', endpoint='index', view_func=views_html.index)

    # Folder
    app.add_url_rule('/folders', endpoint='folders', view_func=views_html.folders)
    app.add_url_rule('/folder/<string:foldername>', endpoint='folder', view_func=views_html.folder) 
    app.add_url_rule('/folder/<string:foldername>/batch_update', endpoint='batch_update_form', view_func=views_html.batch_update_form)

    # Imageset
    app.add_url_rule('/imageset/<string:foldername>/<string:imageset_name>', endpoint='imageset', view_func=views_html.imageset)
    app.add_url_rule('/imageset/<string:foldername>/<string:imageset_name>/edit', endpoint='imageset_edit', view_func=views_html.imageset_edit)
    app.add_url_rule('/imageset/<string:foldername>/<string:imageset_name>/interview', endpoint='interview', view_func=views_html.interview)
    # app.add_url_rule('/imageset/<string:foldername>/<string:imageset_name/toml>', endpoint='imageset_toml', view_func=views_html.imageset_toml)
    
    # ImageFile
    app.add_url_rule('/imagefile/<string:foldername>/<string:imageset_name>/<path:filename>', endpoint='imagefile', view_func=views_html.imagefile)

    # utility routes
    app.add_url_rule('/health', endpoint='health', view_func=views_html.health)
    app.add_url_rule('/favicon.ico', endpoint='favicon', view_func=views_api.favicon)
    
    # Image file serving from folder locations
    app.add_url_rule('/images/<string:foldername>/<string:imageset_name>/<path:filename>', endpoint='serve_image', view_func=views_html.serve_image)

    # Reviews
    app.add_url_rule('/review/<string:foldername>/list', endpoint='reviews_list', view_func=views_html.reviews_list)
    app.add_url_rule('/review/<string:foldername>/<string:review_name>', endpoint='review', view_func=views_html.reviews)
    



    ## API endpoints

    app.add_url_rule('/api/folders', endpoint='api_folders', view_func=views_api.folders)
    app.add_url_rule('/api/folders/add/<path:folder_path>', endpoint='api_folders_add', view_func=views_api.folders_add, methods=['POST'])
    app.add_url_rule('/api/folders/<string:foldername>', endpoint='api_folders_delete', view_func=views_api.folders_delete, methods=['DELETE'])
    
    
    app.add_url_rule('/api/folder/<string:foldername>', endpoint='api_folder', view_func=views_api.folder)
    app.add_url_rule('/api/folder/<string:foldername>/batch_update', endpoint='api_batch_update', view_func=views_api.batch_update, methods=['POST'])
    
    
    app.add_url_rule('/api/imageset/<string:foldername>/<string:imageset>', endpoint='api_imageset', view_func=views_api.imageset, methods=['GET'])
    app.add_url_rule('/api/imageset/<string:foldername>/<string:imageset>/update', endpoint='api_imageset_update', view_func=views_api.imageset_update, methods=['POST'])
    
    app.add_url_rule('/api/folder/<string:foldername>/review/new', endpoint='api_review_new', view_func=views_api.review_new)

    app.add_url_rule('/api/interview', endpoint='api_interview', view_func=views_api.interview, methods=['POST'])
    
    app.add_url_rule('/api/imagefile/<string:foldername>/<string:imageset_name>/<path:filename>/thumbnail', endpoint='api_create_thumbnail', view_func=views_api.create_thumbnail, methods=['POST'])
    app.add_url_rule('/api/imagefile/<string:foldername>/<string:imageset_name>/<path:filename>/watermark', endpoint='api_create_watermark', view_func=views_api.create_watermark, methods=['POST'])
    

    # TODO: api routes for reviews: new->working, 