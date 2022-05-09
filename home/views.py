from django.shortcuts import render

from django.conf import settings
from django.shortcuts import redirect

import requests
import os

from isodate import parse_duration
from pytube import YouTube
from pytube.cli import on_progress


# Create your views here.


def home_view(request):
    search_URL = "https://www.googleapis.com/youtube/v3/search"
    video_URL = "https://www.googleapis.com/youtube/v3/videos"
    videos = []

    if request.method == "POST":
        data = request.POST["query"]

        search_params = {
            "part": "snippet",
            "q": data,
            "maxResults": 15,
            "type": "video",
            "key": settings.YOUTUBE_KEY,
        }

        videoId = []
        r = requests.get(search_URL, params=search_params)
        data = r.json()["items"]
        for i in data:
            if i["snippet"]["liveBroadcastContent"] != "live":
                videoId.append(i["id"]["videoId"])

        video_params = {
            "part": "snippet, contentDetails",
            "id": ",".join(videoId),
            "maxResults": 10,
            "key": settings.YOUTUBE_KEY,
        }

        v = requests.get(video_URL, params=video_params)
        video = v.json()["items"]

        for j in video:
            video_data = {
                "title": j["snippet"]["title"],
                "thumbnail": j["snippet"]["thumbnails"]["high"]["url"],
                "id": j["id"],
                "url": f"https://www.youtube.com/watch?v={j['id']}",
                "duration": parse_duration(j["contentDetails"]["duration"]),
            }

            videos.append(video_data)

    return render(request, "home/home_page.html", {"videos": videos})


def bytes_convert(a):
    b = a / (1000 * 1000)
    b = round(b)
    c = "MB"
    if b > 1000:
        b = a / (1000 * 1000 * 1000)
        b = round(b, 2)
        c = "GB"

    return f"{b} {c}"


def search_view(request, id):
    page = f"https://www.youtube.com/watch?v={id}"
    video = YouTube(page, on_progress_callback=on_progress)

    stream = video.streams.filter(progressive=True).order_by("resolution")
    stream2 = video.streams.filter(only_audio=True).order_by("abr")

    if request.method == "POST":
        App = request.POST["App"]
        if App[-1] == "s":
            files = stream2.filter(abr=App).first()
            downloaded_file = files.download()
            base, ext = os.path.splitext(downloaded_file)
            new_file = base + ".mp3"
            os.rename(downloaded_file, new_file)

        elif App[-1] == "p":
            files = stream.filter(res=App).first()
            files.download()

        return redirect("/")

    video = []
    v_size = []
    v2 = {}

    [video.append(i.resolution) for i in stream if i.resolution not in video]
    for a in video:
        v_size.append(bytes_convert(stream.filter(res=a).first().filesize))

    for i in range(len(video)):
        v2[video[i]] = v_size[i]

    audio = []
    a_size = []
    a2 = {}

    [audio.append(i.abr) for i in stream2]
    for a in audio:
        a_size.append(bytes_convert(stream2.filter(abr=a).first().filesize))

    for i in range(len(audio)):
        a2[audio[i]] = a_size[i]

    return render(request, "home/search_page.html", {"v2": v2, "a2": a2})
