from django.http import HttpResponse


def index(request):
    return HttpResponse("Welcome to the League of Ordinary Gentlemen.")