from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>¡Hola Mundo! Rufingo funcionando 🎉</h1>")
