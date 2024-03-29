from django import forms
from allauth.account.forms import SignupForm
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3
from . import models
from courseshare import settings
from django_select2 import forms as s2forms

class CourseShareSignupForm(SignupForm):
    captcha = ReCaptchaField(widget=ReCaptchaV3, label='')
    first_name = forms.CharField(max_length=30, label='First Name', widget=forms.TextInput(attrs={"type": "text", "placeholder": "First Name", "autocomplete": "given-name"}))
    last_name = forms.CharField(max_length=30, label='Last Name', widget=forms.TextInput(attrs={"type": "text", "placeholder": "Last Name", "autocomplete": "family-name"}))
    school = forms.ModelChoiceField(queryset=models.School.objects.all())
    field_order = ['email', 'username', 'first_name', 'last_name', 'school', 'password1', 'password2', 'captcha']

    def save(self, request):
        user = super(CourseShareSignupForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        print(self.cleaned_data['school'])
        user.school = self.cleaned_data['school']
        user.save()
        return user


class AddTimetableSelectTermForm(forms.Form):
    term = forms.ModelChoiceField(queryset=models.Term.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(AddTimetableSelectTermForm, self).__init__(*args, **kwargs)
        self.fields['term'].queryset = models.Term.objects.filter(school=user.school).exclude(timetables__owner=user)

class SelectCoursesWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "code__icontains",
    ]

class TimetableSelectCoursesForm(forms.ModelForm):
    class Meta:
        model = models.Timetable
        fields = ['courses']
        widgets = {
            'courses': SelectCoursesWidget(attrs={'data-minimum-input-length': 0, 'data-placeholder': 'Start typing course code...'})
        }

    def __init__(self, *args, **kwargs):
        if kwargs['instance'] is not None:
            self.term = kwargs['instance'].term
        else:
            self.term = kwargs.pop('term')
        super(TimetableSelectCoursesForm, self).__init__(*args, **kwargs)
        self.fields['courses'].queryset = models.Course.objects.filter(term=self.term).order_by('code')

    def clean(self):
        courses = self.cleaned_data['courses']
        if courses.count() > settings.TIMETABLE_FORMATS[self.term.timetable_format]['courses']:
            raise forms.ValidationError(f'There are only {settings.TIMETABLE_FORMATS[self.term.timetable_format]["courses"]} courses in this term.')
        position_set = set()
        for i in courses:
            if i.position in position_set:
                raise forms.ValidationError(f'There are two or more conflicting courses.')
            else:
                position_set.add(i.position)

class AddCourseForm(forms.ModelForm):
    position = forms.ChoiceField(widget=forms.RadioSelect())

    class Meta:
        model = models.Course
        fields = ['code', 'position']

    def __init__(self, *args, **kwargs):
        self.term = kwargs.pop('term')
        super(AddCourseForm, self).__init__(*args, **kwargs)

        self.fields['position'].label = settings.TIMETABLE_FORMATS[self.term.timetable_format]['question']['prompt']
        self.fields['position'].choices = settings.TIMETABLE_FORMATS[self.term.timetable_format]['question']['choices']

        term_courses = self.term.courses.order_by('?')
        if term_courses:
            self.fields['code'].widget.attrs['placeholder'] = f'Ex. {term_courses[0].code}'

        self.position_set = list(settings.TIMETABLE_FORMATS[self.term.timetable_format]['positions'])
        self.position_set.sort()

    def clean_code(self):
        code = self.cleaned_data['code']
        courses = self.term.courses.filter(code=code)
        if courses:
            raise forms.ValidationError('A course with the same code exists for the selected term.')
        return code

    def clean_position(self):
        position = int(self.cleaned_data['position'])
        if position not in self.position_set:
            raise forms.ValidationError('Must be one of ' + ', '.join([str(i) for i in self.position_set]) + '.')
        return position

class TermAdminForm(forms.ModelForm):
    timetable_format = forms.ChoiceField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super(TermAdminForm, self).__init__(*args, **kwargs)
        self.fields['timetable_format'].choices = [(timetable_format, timetable_format) for timetable_format in settings.TIMETABLE_FORMATS]

class EventAdminForm(forms.ModelForm):
    schedule_format = forms.ChoiceField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super(EventAdminForm, self).__init__(*args, **kwargs)
        timetable_configs = settings.TIMETABLE_FORMATS

        self.fields['schedule_format'].initial = 'default'

        if 'instance' in kwargs and kwargs['instance'] is not None:
            instance = kwargs['instance']
            self.fields['schedule_format'].choices = [(timetable_format, timetable_format) for timetable_format in timetable_configs[instance.term.timetable_format]['schedules']]
        else:
            schedule_format_set = set()
            for timetable_config in timetable_configs.values():
                schedule_format_set.update(set(timetable_config['schedules'].keys()))
            self.fields['schedule_format'].choices = [(schedule_format, schedule_format) for schedule_format in schedule_format_set]

    def clean(self):
        cleaned_data = super().clean()
        term = cleaned_data.get('term')
        schedule_format = cleaned_data.get('schedule_format')

        timetable_configs = settings.TIMETABLE_FORMATS
        if schedule_format not in timetable_configs[term.timetable_format]['schedules']:
            raise forms.ValidationError(f'Schedule format "{schedule_format}" is not a valid day schedule in Term {term.name}.')
