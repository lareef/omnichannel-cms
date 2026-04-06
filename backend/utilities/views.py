from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from .models import BusinessCalendar, BusinessHourRule, Holiday
from .forms import BusinessCalendarForm, BusinessHourRuleForm, HolidayForm
from django.contrib import messages

class AdminRequiredMixin(UserPassesTestMixin):
    """Allow access only to users with admin role or superuser."""
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        # return user.role and user.role.code == 'admin'
        return user.role.code in ['supervisor', 'admin', 'manager']


# ----- Calendar Management -----

class CalendarListView(AdminRequiredMixin, ListView):
    model = BusinessCalendar
    template_name = 'utilities/calendar/calendar_list.html'
    context_object_name = 'calendars'
    paginate_by = 20
    ordering = ['name']


class CalendarDetailView(AdminRequiredMixin, DetailView):
    model = BusinessCalendar
    template_name = 'utilities/calendar/calendar_detail.html'
    context_object_name = 'calendar'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.object
        context['hour_rules'] = calendar.hour_rules.all().order_by('day_of_week', 'start_time')
        context['holidays'] = calendar.holidays.all().order_by('date')
        return context


class CalendarCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = BusinessCalendar
    form_class = BusinessCalendarForm
    template_name = 'utilities/calendar/calendar_form.html'
    success_url = reverse_lazy('utilities:calendar_list')
    success_message = "Calendar '%(name)s' created successfully."


class CalendarUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = BusinessCalendar
    form_class = BusinessCalendarForm
    template_name = 'utilities/calendar/calendar_form.html'
    success_url = reverse_lazy('utilities:calendar_list')
    success_message = "Calendar '%(name)s' updated successfully."


class CalendarDeleteView(AdminRequiredMixin, DeleteView):
    model = BusinessCalendar
    template_name = 'utilities/calendar/calendar_confirm_delete.html'
    success_url = reverse_lazy('utilities:calendar_list')
    success_message = "Calendar deleted."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


# ----- Business Hour Rules -----

class BusinessHourRuleCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = BusinessHourRule
    form_class = BusinessHourRuleForm
    template_name = 'utilities/calendar/businesshour_form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['calendar'] = self.kwargs['calendar_pk']
        return initial

    def get_success_url(self):
        return reverse_lazy('utilities:calendar_detail', kwargs={'pk': self.object.calendar.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['calendar'] = BusinessCalendar.objects.get(pk=self.kwargs['calendar_pk'])
        return kwargs

    def form_valid(self, form):
        form.instance.calendar_id = self.kwargs['calendar_pk']
        return super().form_valid(form)


class BusinessHourRuleUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = BusinessHourRule
    form_class = BusinessHourRuleForm
    template_name = 'utilities/calendar/businesshour_form.html'

    def get_success_url(self):
        return reverse_lazy('utilities:calendar_detail', kwargs={'pk': self.object.calendar.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['calendar'] = self.object.calendar
        return kwargs


class BusinessHourRuleDeleteView(AdminRequiredMixin, DeleteView):
    model = BusinessHourRule
    template_name = 'utilities/calendar/businesshour_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('utilities:calendar_detail', kwargs={'pk': self.object.calendar.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Business hour rule deleted.")
        return super().delete(request, *args, **kwargs)


# ----- Holidays -----

class HolidayCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Holiday
    form_class = HolidayForm
    template_name = 'utilities/calendar/holiday_form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['calendar'] = self.kwargs['calendar_pk']
        return initial

    def get_success_url(self):
        return reverse_lazy('utilities:calendar_detail', kwargs={'pk': self.object.calendar.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['calendar'] = BusinessCalendar.objects.get(pk=self.kwargs['calendar_pk'])
        return kwargs

    def form_valid(self, form):
        form.instance.calendar_id = self.kwargs['calendar_pk']
        return super().form_valid(form)


class HolidayUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Holiday
    form_class = HolidayForm
    template_name = 'utilities/calendar/holiday_form.html'

    def get_success_url(self):
        return reverse_lazy('utilities:calendar_detail', kwargs={'pk': self.object.calendar.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['calendar'] = self.object.calendar
        return kwargs


class HolidayDeleteView(AdminRequiredMixin, DeleteView):
    model = Holiday
    template_name = 'utilities/calendar/holiday_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('utilities:calendar_detail', kwargs={'pk': self.object.calendar.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Holiday deleted.")
        return super().delete(request, *args, **kwargs)