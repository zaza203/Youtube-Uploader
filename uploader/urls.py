from django.urls import path
from uploader import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('signin/', views.sign_in, name='sign_in'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('upload_page/', views.upload_page, name='upload_page'),
    path('preview/', views.upload_page, name='preview_page'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    # path('save_video/', views.video_preview, name='save_video'),
    # path('publish_video/', views.video_preview, name='publish_video'),
    # path('save_and_publish_video/', views.video_preview, name='save_and_publish_video'),
    path('save_video/', views.save_video, name='save_video'),
    path('publish_to_youtube/', views.publish_to_youtube, name='publish_to_youtube'),
]
