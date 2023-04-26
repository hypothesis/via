from pyramid.view import view_config
from via.services.youtube import YoutubeAPI
from via.services.secure_link import has_secure_url_token


@view_config(
    route_name="view_video",
    decorator=(has_secure_url_token,),
    renderer="via:templates/video_viewer.html.jinja2",
)
def proxy_video(context, request):

    youtube_svc = request.find_service(YoutubeAPI)

    video_id = youtube_svc.parse_file_url(context.url_from_query())
    if not video_id:
        raise ValueError("Not youtube url we can parse")

    transcript = youtube_svc.get_transcript(video_id)

    return {
        "transcript": transcript,
        "video_id": video_id,
        "start_times": [e["start"] for e in transcript],
        "iframe_src": f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&widgetid=1&start=0&name=me",
    }
