from django.shortcuts import render, redirect
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.contrib.auth.decorators import login_required

import ffmpeg
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import ffmpeg

def homepage(request):
    return render(request, 'uploader/homepage.html')

# Configure OAuth Client ID and Secret
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Disable HTTPS requirement for testing

def sign_in(request):
    flow = Flow.from_client_secrets_file(
        'client_secret_3834195627-e286mkbqbk59bks5dgdn489cc0sq8btt.apps.googleusercontent.com.json',
        scopes=['https://www.googleapis.com/auth/youtube.upload'],
        redirect_uri='http://127.0.0.1:8000/oauth2callback'
    )

    # Generate the authorization URL
    authorization_url, state = flow.authorization_url(prompt='consent')

    # Store the state in the session for later verification
    request.session['state'] = state

    # Redirect the user to the authorization URL
    return redirect(authorization_url)

from googleapiclient.discovery import build

def oauth2callback(request):
    state = request.session.get('state')

    flow = Flow.from_client_secrets_file(
        'client_secret_3834195627-e286mkbqbk59bks5dgdn489cc0sq8btt.apps.googleusercontent.com.json',
        scopes=['https://www.googleapis.com/auth/youtube.upload'],
        redirect_uri='http://127.0.0.1:8000/oauth2callback',
        state=state
    )

    flow.fetch_token(authorization_response=request.build_absolute_uri())

    credentials = flow.credentials
    # Store the credentials securely in the session or database
    request.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }

    if request.user.is_authenticated:
        request.user.link_google_credentials(credentials_to_dict(credentials))
        messages.success(request, "Google account successfully linked!")

    return redirect('upload_page')


def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }


# Assuming the client_secret and API credentials are stored securely
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm

def login_page(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('homepage')
    else:
        form = AuthenticationForm()

    return render(request, 'uploader/login.html', {'form': form})

def logout_page(request):
    logout(request)
    return redirect('homepage')


import os
import subprocess
from datetime import datetime
from django.http import FileResponse, HttpResponse
from django.shortcuts import render
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TEMP_VIDEO_PATH = "/tmp/generated_video.mp4"

def save_temp_file(file):
    path = f'/tmp/{file.name}'
    with open(path, 'wb') as f:
        f.write(file.read())
    return path

from moviepy.editor import AudioFileClip, concatenate_audioclips, ImageClip, CompositeVideoClip, concatenate_videoclips
import os
import logging
import time
import shutil
from django.conf import settings

logging.basicConfig(level=logging.INFO)

TEMP_VIDEO_PATH = "/tmp/generated_video.mp4"

from moviepy.editor import *
from moviepy.video.fx.resize import resize
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.video.fx.margin import margin
import os
import shutil
import logging
import time

import random
from moviepy.video.fx.all import fadein, fadeout
from moviepy.video.fx.margin import margin
from moviepy.video.compositing.transitions import crossfadein

def apply_random_transition(clip, duration=1.0):
    """Apply a random transition effect to a clip."""
    transitions = [
        lambda c: fadein(c, duration),
        lambda c: c.crossfadein(duration),
    ]
    transition = random.choice(transitions)
    return transition(clip)

def apply_random_exit_transition(clip, duration=1.0):
    """Apply a random exit transition effect to a clip."""
    transitions = [
        lambda c: fadeout(c, duration),
        lambda c: c.crossfadeout(duration),
    ]
    transition = random.choice(transitions)
    return transition(clip)

def generate_slideshow(audio_paths, image_paths, audio_lengths):
    """
    Generate a slideshow video with audio and transitions.
    
    Args:
        audio_paths (list): List of paths to audio files
        image_paths (list): List of paths to image files
        audio_lengths (list): List of audio clip lengths
    
    Returns:
        str: URL path to the generated video
    """
    start_time = time.time()
    logging.info("Starting slideshow generation...")
    
    for audio_path in audio_paths:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
    for image_path in image_paths:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
    
    try:
        logging.info("Processing audio files...")
        audio_clips = [AudioFileClip(audio) for audio in audio_paths]
        concatenated_audio = concatenate_audioclips(audio_clips)
        audio_length = concatenated_audio.duration
        
        transition_duration = 1.0 
        effective_duration = audio_length - (transition_duration * (len(image_paths) - 1))
        time_per_image = effective_duration / len(image_paths)
        
        logging.info("Processing image files...")
        image_clips = []
        target_size = (1920, 1080)  # Full HD resolution
        
        for i, img_path in enumerate(image_paths):
            try:
                img_clip = ImageClip(img_path)
                
                current_size = img_clip.size
                width_scale = target_size[0] / current_size[0]
                height_scale = target_size[1] / current_size[1]
                scale_factor = min(width_scale, height_scale)
                
                new_size = (
                    int(current_size[0] * scale_factor),
                    int(current_size[1] * scale_factor)
                )
                
                img_clip = (img_clip
                           .resize(newsize=new_size)
                           .set_position('center')
                           .set_duration(time_per_image + transition_duration))
                
                if i == 0:
                    img_clip = fadein(img_clip, transition_duration)
                elif i == len(image_paths) - 1:
                    img_clip = fadeout(img_clip, transition_duration)
                else:
                    img_clip = fadein(img_clip, transition_duration)
                    img_clip = fadeout(img_clip, transition_duration)

                img_clip = img_clip.margin(20, color=(255, 255, 255))
                
                image_clips.append(img_clip)
                
            except Exception as e:
                logging.error(f"Error processing image {img_path}: {str(e)}")
                raise
        
        logging.info("Creating final video with transitions...")
        slideshow = concatenate_videoclips(
            image_clips,
            method="compose",
            padding=-transition_duration
        )
        
        slideshow = slideshow.set_audio(concatenated_audio)
        
        if abs(slideshow.duration - audio_length) > 0.1:
            slideshow = slideshow.set_duration(audio_length)
        
        logging.info("Writing video file...")
        slideshow.write_videofile(
            TEMP_VIDEO_PATH,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='5000k',
            threads=2,
            logger=None
        )
        
        logging.info(f"Video processing finished in {time.time() - start_time} seconds")
        
        if os.path.exists(TEMP_VIDEO_PATH):
            media_video_path = os.path.join(settings.MEDIA_ROOT, "generated_video.mp4")
            shutil.move(TEMP_VIDEO_PATH, media_video_path)
            logging.info(f"Video moved to {media_video_path}")
            
            if not os.path.exists(media_video_path):
                raise FileNotFoundError(f"Failed to save video at {media_video_path}")
        else:
            raise FileNotFoundError(f"Temporary video file not found at {TEMP_VIDEO_PATH}")
        
        concatenated_audio.close()
        for clip in image_clips:
            clip.close()
        slideshow.close()
        
        video_url = os.path.join(settings.MEDIA_URL, "generated_video.mp4")
        return video_url
        
    except Exception as e:
        logging.error(f"Error generating slideshow: {str(e)}")
        if os.path.exists(TEMP_VIDEO_PATH):
            os.remove(TEMP_VIDEO_PATH)
        raise

def get_audio_length(audio_path):
    return float(ffmpeg.probe(audio_path)['format']['duration'])

@login_required
def upload_page(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        audios = request.FILES.getlist('audio')
        images = request.FILES.getlist('images')
        thumbnail = request.FILES['thumbnail']
        schedule_time = request.POST.get('schedule_time')

        audio_paths = [save_temp_file(audio) for audio in audios]
        image_paths = [save_temp_file(img) for img in images]
        thumbnail_path = save_temp_file(thumbnail)

        audio_lengths = [get_audio_length(path) for path in audio_paths]

        slideshow_video = generate_slideshow(audio_paths, image_paths, audio_lengths)

        preview_video_path = slideshow_video 

        return render(request, 'uploader/video_preview2.html', {
            'preview_video': preview_video_path,
            'title': title,
            'description': description,
            'thumbnail': thumbnail_path,
            'schedule_time': schedule_time,
        })

    return render(request, 'uploader/upload_page.html')

from django.http import HttpResponseBadRequest
import shutil


from datetime import datetime, timedelta
from django.utils.timezone import now, make_aware
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def save_video(request):
    """Handles saving the video to the user's local machine."""
    # video_path = TEMP_VIDEO_PATH
    video_filename = "generated_video.mp4"
    video_path = os.path.join(settings.MEDIA_ROOT, video_filename)
    if os.path.exists(video_path):
        response = FileResponse(open(video_path, 'rb'))
        response['Content-Disposition'] = 'attachment; filename="generated_video.mp4"'
        return response
    return HttpResponse("Video not found", status=404)

# @login_required
# @csrf_exempt
# def publish_to_youtube(request):
#     """Publishes the video to YouTube."""
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         title = data.get('title')
#         description = data.get('description')
#         # video_path = TEMP_VIDEO_PATH
#         video_filename = "generated_video.mp4"
#         video_path = os.path.join(settings.MEDIA_ROOT, video_filename)
#         thumbnail_path = data.get('thumbnail')
#         schedule_time = request.POST.get('schedule_time')

#         if schedule_time:
#             schedule_time = datetime.fromisoformat(schedule_time)
#             if schedule_time.tzinfo is None:
#                 schedule_time = make_aware(schedule_time)

#             if schedule_time < now():
#                 schedule_time = now() + timedelta(minutes=5)

#         credentials = Credentials(**request.session.get('credentials'))
#         youtube = build('youtube', 'v3', credentials=credentials)

#         request_body = {
#             'snippet': {
#                 'title': title,
#                 'description': description,
#                 'tags': ['generated', 'slideshow'],
#                 'categoryId': '22',
#             },
#             'status': {
#                 'privacyStatus': 'private' if schedule_time else 'public',
#                 'publishAt': schedule_time if schedule_time else None
#             },
#         }

#         media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

#         video_upload = youtube.videos().insert(
#             part='snippet,status',
#             body=request_body,
#             media_body=media
#         )
#         response = video_upload.execute()

#         if thumbnail_path:
#             youtube.thumbnails().set(
#                 videoId=response['id'],
#                 media_body=MediaFileUpload(thumbnail_path)
#             ).execute()

#         return JsonResponse({'status': 'Video Published!', 'videoId': response['id']})
#     return JsonResponse({'error': 'Invalid Request'}, status=400)




import datetime
from django.utils.dateparse import parse_datetime

@login_required
@csrf_exempt
def publish_to_youtube(request):
    """Publishes the video to YouTube, optionally scheduling it."""
    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description')
        # video_path = TEMP_VIDEO_PATH
        video_filename = "generated_video.mp4"
        video_path = os.path.join(settings.MEDIA_ROOT, video_filename)
        thumbnail_path = data.get('thumbnail')
        schedule_time = data.get('schedule_time')  # New addition

        # Parse and format schedule_time if provided
        scheduled_start_time = None
        if schedule_time:
            scheduled_start_time = parse_datetime(schedule_time).isoformat() + "Z"

        credentials = request.user.get_google_credentials()

        youtube = build('youtube', 'v3', credentials=credentials)

        request_body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['generated', 'slideshow'],
                'categoryId': '22',
            },
            'status': {
                'privacyStatus': 'private' if scheduled_start_time else 'public',
                'publishAt': scheduled_start_time if scheduled_start_time else None
            },
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        video_upload = youtube.videos().insert(
            part='snippet,status',
            body=request_body,
            media_body=media
        )
        response = video_upload.execute()

        if thumbnail_path:
            youtube.thumbnails().set(
                videoId=response['id'],
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()

        return JsonResponse({'status': 'Video Published!', 'videoId': response['id']})
    return JsonResponse({'error': 'Invalid Request'}, status=400)
