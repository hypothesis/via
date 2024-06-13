from glob import glob

bind = "0.0.0.0:9082"
reload = True
reload_extra_files = glob("via/templates/**/*", recursive=True)
timeout = 0
