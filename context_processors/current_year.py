import datetime as dt


def year(request):
    return {'year': dt.datetime.today().date().year}
