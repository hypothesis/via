import os
from gevent.monkey import patch_all;patch_all()
from pywb.apps.frontendapp import FrontEndApp

from via.rewriter.config import Configuration
from via.rewriter.hooks import Hooks
from via.rewriter.patch import apply_pre_app_hooks, apply_post_app_hooks


# The pywb CLI does this when enabling debug mode for dev. Should we do
# something similar?

# logging.basicConfig(
#   format='%(asctime)s: [%(levelname)s]: %(message)s',
#   level=logging.DEBUG if self.r.debug else logging.INFO
#   )

def create_app():
    config = Configuration.parse()

    # Change the directory so that the relative template paths work
    os.chdir(config['base_dir'])

    hooks = Hooks(config)
    apply_pre_app_hooks(hooks)

    application = FrontEndApp()

    apply_post_app_hooks(application.rewriterapp, hooks)

    return application


# Our job here is to leave this `application` attribute laying around as it's
# what uWSGI expects to find.
application = create_app()