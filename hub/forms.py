from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Contribution, Event

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ["event", "department", "date", "hours", "description"]

    def __init__(self, *args, user=None, initial_event=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Event.objects.filter(status="SCHEDULED")
        if user and not user.profile.is_coordinator:
            qs = qs.filter(signups__user=user, signups__status="CONFIRMED")
        self.fields["event"].queryset = qs.order_by("date")
        if initial_event:
            self.fields["event"].initial = initial_event
        for name, f in self.fields.items():
            f.widget.attrs['class'] = 'form-select' if name in ('event', 'department') else 'form-control'
        self.fields["date"].widget = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        self.fields["hours"].widget.attrs.update({'step': '0.5', 'min': '0'})

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "date", "location", "capacity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')
        self.fields["date"].widget = forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
        self.fields["capacity"].widget.attrs['min'] = '0'
