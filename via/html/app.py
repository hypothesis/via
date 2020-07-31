from pywb.apps.cli import ReplayCli

from via.html.config import Configuration
from via.html.hooks import Hooks
from via.html.patch import PatchedFrontEndApp, apply_post_app_hooks, apply_pre_app_hooks


class ViaCli(ReplayCli):
    @classmethod
    def create_app(cls):
        args, config = Configuration.parse()
        print("Starting with args:", args)
        print("Config:", config)

        hooks = Hooks(config)
        apply_pre_app_hooks(hooks)

        return cls(args, hooks)

    def __init__(self, args, hooks):
        self.hooks = hooks

        super().__init__(
            args=args,
            desc="Via HTML Rewriter",
            default_port=Configuration.DEFAULT_PORT,
        )

    def load(self):
        super().load()

        # Copied from WaybackCLI
        app = PatchedFrontEndApp(custom_config=self.extra_config)

        apply_post_app_hooks(app.rewriterapp, self.hooks)

        return app


if __name__ == "__main__":
    ViaCli.create_app().run()
