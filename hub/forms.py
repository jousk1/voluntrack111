from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Contribution, Department, Event

"""
Forms in this module:
    - UserRegistrationForm: User account creation
    - ContributionForm: Volunteer hours logging
    - EventForm: Event creation and editing
"""

class UserRegistrationForm(UserCreationForm):
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
        """Add Bootstrap styling to all form fields."""
        super().__init__(*args, **kwargs)
        
        # Apply Bootstrap form-control class to all fields
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ["event", "department", "date", "hours", "description"]

    def __init__(self, *args, user=None, initial_event=None, **kwargs):
        """
        Initialize form with user-specific field configuration.
        
        Args:
            user: Current user (for filtering events and pre-selecting department)
            initial_event: Event to pre-select (when coming from event detail page)
        """
        super().__init__(*args, **kwargs)

        # EVENT FIELD 
        # Filter events based on user role
        event_queryset = Event.objects.filter(status="SCHEDULED")
        
        if user and not user.profile.is_coordinator:
            # Non-coordinators can only log hours for events they're signed up for
            event_queryset = event_queryset.filter(
                signups__user=user, 
                signups__status="CONFIRMED"
            )
        
        self.fields["event"].queryset = event_queryset.order_by("date")
        self.fields["event"].required = False  # Event is optional
        
        # Pre-select event if provided
        if initial_event:
            self.fields["event"].initial = initial_event

        # DEPARTMENT FIELD
        dept_queryset = Department.objects.order_by("name")
        self.fields["department"].queryset = dept_queryset
        
        # Set appropriate empty label based on whether departments exist
        if dept_queryset.exists():
            self.fields["department"].empty_label = "Select a department..."
        else:
            self.fields["department"].empty_label = "No departments available"
            self.fields["department"].help_text = (
                "No departments exist. Please contact an administrator."
            )

        # Pre-select user's department if they have one
        if user and hasattr(user, 'profile') and user.profile.department:
            self.fields["department"].initial = user.profile.department

        # WIDGET STYLING
        # Apply Bootstrap classes to all fields
        for name, field in self.fields.items():
            if name in ('event', 'department'):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

        # Configure date input as HTML5 date picker
        self.fields["date"].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )

        # Configure hours input with step for half-hours
        self.fields["hours"].widget.attrs.update({
            'step': '0.5',
            'min': '0',
            'placeholder': 'e.g., 2.5'
        })

        # Configure description as textarea
        self.fields["description"].widget.attrs.update({
            'rows': '4',
            'placeholder': 'Describe the work you did...'
        })

class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ["title", "description", "department", "date", "location", "capacity"]

    def __init__(self, *args, user=None, **kwargs):
        """
        Initialize form with user-specific configuration.
        
        Args:
            user: Current coordinator (for pre-selecting department)
        """
        super().__init__(*args, **kwargs)

        # WIDGET STYLING
        # Apply Bootstrap classes to all fields
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

        # Configure date as datetime-local input
        self.fields["date"].widget = forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )

        # Configure capacity with minimum value
        self.fields["capacity"].widget.attrs.update({
            'min': '0',
            'placeholder': '0 for unlimited'
        })
        self.fields["capacity"].help_text = "Maximum signups allowed (0 = unlimited)"

        # DEPARTMENT FIELD
        self.fields["department"].widget.attrs['class'] = 'form-select'
        self.fields["department"].queryset = Department.objects.order_by("name")
        self.fields["department"].empty_label = "No department (optional)"
        self.fields["department"].required = False

        # Pre-select coordinator's department if they have one
        if user and user.profile.is_coordinator and user.profile.department:
            self.fields["department"].initial = user.profile.department

        #   FIELD HELP TEXT  
        self.fields["title"].help_text = "A clear, descriptive name for the event"
        self.fields["location"].help_text = "Where the event will take place"
        self.fields["description"].widget.attrs.update({
            'rows': '4',
            'placeholder': 'Describe the event, what volunteers will do, what to bring...'
        })
