from . import authentication_route, user_route, demo_route, other_routes, map_route


def initialize(app, db):
    """Initialize all route.

    :param app: Flask application
    :param db: Database object
    """
    authentication_route.init(app)
    user_route.init(app)
    other_routes.init(app)
    map_route.init(app)
