from django.db import connection
from django.http import HttpResponse


def view1(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 'foo'")
        cursor.fetchone()
    return HttpResponse('view1')


def view2(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 'bar'")
        cursor.fetchone()
    return HttpResponse('view2')


def view3(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 'baz'")
        cursor.fetchone()
    return HttpResponse('view2')
