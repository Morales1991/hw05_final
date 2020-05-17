import datetime as dt


def year(request):
    year = dt.datetime.today().date().year
    return {"year":year}
