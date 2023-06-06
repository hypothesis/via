from h_vialib import Configuration
from pyramid.view import view_config


@view_config(renderer="via:templates/view_video.html.jinja2", route_name="view_video")
def view_video(request):
    _, client_config = Configuration.extract_from_params(request.params)

    video_id = request.matchdict["id"]
    transcript = {
        "segments": [
            {
                "time": 0,
                "text": "First segment of transcript",
            },
            {
                "time": 30,
                "text": "Second segment of transcript",
            },
        ],
    }

    return {
        "client_embed_url": request.registry.settings["client_embed_url"],
        "client_config": client_config,
        "transcript": transcript,
        "video_id": video_id,
    }
