from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
    <html>
        <head>
            <title>Minibanco</title>
            <meta http-equiv="refresh" content="0; url=/banco/">
        </head>
        <body>
            <p>Redirigiendo a <a href="/banco/">Minibanco</a>...</p>
        </body>
    </html>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('banco/', include('banco.urls')),
]