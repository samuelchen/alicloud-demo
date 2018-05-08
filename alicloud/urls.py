"""alicloud URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from .views.index import IndexView
from .views.ecs import ECSView
from .views.oss import OSSView
from .views.backup import BackupView

def t(name):
    return 'alicloud/' + name


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', IndexView.as_view(template_name=t('index.html')), name='index'),
    url(r'^ecs/$', ECSView.as_view(template_name=t('ecs.html')), name='ecs'),
    url(r'^oss/$', OSSView.as_view(template_name=t('oss.html')), name='oss'),


    url(r'^backup/', BackupView.as_view(template_name=t('backup.html')), name='backup'),

]
