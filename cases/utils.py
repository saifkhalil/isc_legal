from calendar import HTMLCalendar

from .models import LitigationCases


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter cases by day
    def formatday(self, day, cases):
        cases_per_day = cases.filter(start_time__day=day)
        d = ''
        for case in cases_per_day:
            d += f'<li > {case.get_html_url} </li>'

        if day != 0:
            return f"<td><span class='date text-center'>{day}</span><ul class='case' > {d} </ul></td>"
        return '<td></td>'

    # formats a week as a tr
    def formatweek(self, theweek, cases):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, cases)
        return f'<tr> {week} </tr>'

    # formats a month as a table
    # filter cases by year and month
    def formatmonth(self, withyear=True):
        cases = LitigationCases.objects.filter(start_time__year=self.year, start_time__month=self.month)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, cases)}\n'
        return cal