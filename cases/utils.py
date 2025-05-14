from calendar import HTMLCalendar
from django.utils.translation import gettext_lazy as _
from activities.models import hearing,task
from .models import LitigationCases


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter cases by day
    def formatday(self, day, cases, hearings, tasks):
        cases_per_day = cases.filter(start_time__day=day)
        hearings_per_day = hearings.filter(hearing_date__day=day)
        tasks_per_day = hearings.filter(created_at__day=day)
        d = ''
        cases_list = ''
        hearings_list = ''
        tasks_list = ''
        cases_count = cases_per_day.count()
        hearings_count =hearings_per_day.count()
        tasks_count =tasks_per_day.count()
        for case in cases_per_day:
            # cases_list += f"<a href='{case.get_html_url}'>{case.name[:20]}</a><br>"
            cases_list += f'<li><div class="day-data day-data-primary" ><a href="{case.get_html_url}"><i class="bi bi-briefcase"></i> {case.name[:20]}</a></div></li>'
        for hearing in hearings_per_day:
            # hearings_list += f"<a href='{hearing.get_html_url}'>{hearing.name[:20]}</a><br>"
            hearings_list +=f'<li><div class="day-data day-data-warning" ><a href="{hearing.get_html_url}"><i class="fa fa-gavel" aria-hidden="true"></i> {hearing.name[:20]}</a></div></li>'
        for task in tasks_per_day:
            # tasks_list += f"<a href='{task.get_html_url}'>{task.name[:20]}</a><br>"
            tasks_list += f'<li><div class="day-data day-data-dark" ><a href="{task.get_html_url}"><i class="bi bi-list-task"></i> {task.name[:20]}</a></div></li>'


        if cases_count > 0:
            # d += f'<li><div data-bs-html="true" class="day-data day-data-primary d-flex justify-content-between align-items-start" data-bs-toggle="popover" title="{_("Cases")}" data-bs-content="{cases_list}"><i class="bi bi-briefcase"></i> <span class="text-right">{cases_count}</span></div></li>'
            d +=cases_list
        if hearings_count > 0:
            # d += f'<li><div data-bs-html="true" class="day-data day-data-warning d-flex justify-content-between align-items-start" data-bs-toggle="popover" title="{_("Hearings")}" data-bs-content="{hearings_list}"><i class="fa fa-gavel" aria-hidden="true"></i> <span class="text-right">{hearings_count}</span></div></li>'
            d += hearings_list
        if tasks_count > 0:
            # d += f'<li><div data-bs-html="true" class="day-data day-data-dark d-flex justify-content-between align-items-start" data-bs-toggle="popover" title="{_("Tasks")}" data-bs-content="{tasks_list}"><i class="bi bi-list-task"></i> <span class="text-right">{tasks_count}</span></div></li>'
            d +=tasks_list
        if day != 0:
            return f"<td><div class='calendar-day'><p class='date d-flex justify-content-between align-items-start px-2'>{day}</p><ul class='case px-2' >{d}</ul></div></td>"
        return '<td></td>'

    # formats a week as a tr
    def formatweek(self, theweek, cases, hearings,tasks):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, cases,hearings,tasks)
        return f'<tr> {week} </tr>'

    # formats a month as a table
    # filter cases by year and month
    def formatmonth(self, withyear=True):
        cases = LitigationCases.objects.filter(start_time__year=self.year, start_time__month=self.month)
        hearings = hearing.objects.filter(hearing_date__year=self.year, hearing_date__month=self.month,latest=True)
        tasks = task.objects.filter(created_at__year=self.year, created_at__month=self.month)
        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, cases,hearings,tasks)}\n'
        cal += '</tbody></table>'
        return cal