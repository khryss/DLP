from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index_view),
    url(r'(?P<quiz_id>.+)/$', views.quiz_view, name='quiz'),
]
