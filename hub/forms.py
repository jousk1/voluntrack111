"""Forms for VolunTrack."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Contribution, Department, Event


class UserRegistrationForm(UserCreationForm):
    # Form for new user registration
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address."
    )
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        help_text="Optional."
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        help_text="Optional."
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class ContributionForm(forms.ModelForm):
    # Form for logging volunteer hours
    
    class Meta:
        model = Contribution
        fields = ["event", "department", "date", "hours", "description"]

    def __init__(self, *args, user=None, initial_event=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Event field
        event_queryset = Event.objects.filter(status="SCHEDULED")
        
        if user and not user.profile.is_coordinator:
            event_queryset = event_queryset.filter(
                signups__user=user, 
                signups__status="CONFIRMED"
            )
        
        self.fields["event"].queryset = event_queryset.order_by("date")
        self.fields["event"].required = False
        
        if initial_event:
            self.fields["event"].initial = initial_event

        # Department field
        dept_queryset = Department.objects.order_by("name")
        self.fields["department"].queryset = dept_queryset
        
        if dept_queryset.exists():
            self.fields["department"].empty_label = "Select a department..."
        else:
            self.fields["department"].empty_label = "No departments available"
            self.fields["department"].help_text = (
                "No departments exist. Please contact an administrator."
            )

        if user and hasattr(user, 'profile') and user.profile.department:
            self.fields["department"].initial = user.profile.department

        # Widget styling
        for name, field in self.fields.items():
            if name in ('event', 'department'):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

        self.fields["date"].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )

        self.fields["hours"].widget.attrs.update({
            'step': '0.5',
            'min': '0',
            'placeholder': 'e.g., 2.5'
        })

        self.fields["description"].widget.attrs.update({
            'rows': '4',
            'placeholder': 'Describe the work you did...'
        })


class EventForm(forms.ModelForm):
    # Form for creating and editing events

    class Meta:
        model = Event
        fields = ["title", "description", "department", "date", "location", "capacity"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Widget styling
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

        self.fields["date"].widget = forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )

        self.fields["capacity"].widget.attrs.update({
            'min': '0',
            'placeholder': '0 for unlimited'
        })
        self.fields["capacity"].help_text = "Maximum signups allowed (0 = unlimited)"

        # Department field
        self.fields["department"].widget.attrs['class'] = 'form-select'
        self.fields["department"].queryset = Department.objects.order_by("name")
        self.fields["department"].empty_label = "No department (optional)"
        self.fields["department"].required = False

        if user and user.profile.is_coordinator and user.profile.department:
            self.fields["department"].initial = user.profile.department

        # Help text
        self.fields["title"].help_text = "A clear, descriptive name for the event"
        self.fields["location"].help_text = "Where the event will take place"
        self.fields["description"].widget.attrs.update({
            'rows': '4',
            'placeholder': 'Describe the event, what volunteers will do, what to bring...'
        })
