from .users import users_bp
from .posts import posts_bp
from .comments import comments_bp
from .bans import bans_bp


blueprints = [users_bp, posts_bp, comments_bp, bans_bp]
