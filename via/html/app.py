from pywb.apps.cli import WaybackCli

from via.html.config import Configuration
from via.html.hooks import Hooks
from via.html.patch import apply_hooks


class ViaCli(WaybackCli):
    def __init__(self):
        args, config = Configuration.parse()
        print("Starting with args:", args)
        print("Config:", config)

        self.hooks = Hooks(config)

        super().__init__(
            args=args,
            desc="Via HTML Rewriter",
            default_port=Configuration.DEFAULT_PORT,
        )

    def load(self):
        app = super().load()

        apply_hooks(app.rewriterapp, self.hooks)

        return app


if __name__ == "__main__":
    ViaCli().run()
