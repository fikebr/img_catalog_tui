
from . import views


def register_routes(app):

    app.add_url_rule('/', endpoint='hello', view_func=views.hello)
    app.add_url_rule('/health', endpoint='health', view_func=views.health)
    app.add_url_rule('/favicon.ico', endpoint='favicon', view_func=views.favicon)


    app.add_url_rule('/api/folders', endpoint='folders', view_func=views.folders)
    app.add_url_rule('/api/folder/<string:foldername>', endpoint='folder', view_func=views.folder)
    app.add_url_rule('/api/imageset/<string:foldername>/<string:imageset>', endpoint='imageset', view_func=views.imageset)

    # TODO: api routes for changing status, edits, needs
    # TODO: api routes for performing an interview
    # TODO: api routes for reviews: new->working, 