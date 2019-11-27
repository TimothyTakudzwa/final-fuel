import time
import datetime

from django.forms import widgets


class TimeSelectorWidget(widgets.MultiWidget):
    def __init__(self, attrs=None):
        # create choices for hour, minutes, meridian
        # example below, the rest snipped for brevity.
        hours = [(hour, hour) for hour in range(1, 13)]
        minutes = [(minute, minute) for minute in range(00, 60)]
        periods = [('am', 'AM'), ('pm', 'PM')]
        _widgets = (
            widgets.Select(attrs=attrs, choices=hours),
            widgets.Select(attrs=attrs, choices=minutes),
            widgets.Select(attrs=attrs, choices=periods),
        )
        super(TimeSelectorWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            try:
                p = time.strptime(value, "%H:%M:%S")
                if p.tm_hour >= 12:
                    period = 'pm'
                else:
                    period = 'am'

                if p.tm_hour > 12:
                    hour = p.tm_hour - 12
                else:
                    hour = p.tm_hour
                return [hour, p.tm_min, period]
            except:
                return [None, None, None]
        return [None, None, None]

    def value_from_datadict(self, data, files, name):
        datelist = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)]
        try:
            if datelist[2] == 'pm':
                hour = int(datelist[0]) + 12
                if hour >= 24:
                    hour = 0
            else:
                hour = int(datelist[0])
            minute = int(datelist[1])
            D = datetime.time(hour, minute)
        except ValueError:
            return ''
        else:
            return str(D)
