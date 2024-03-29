from django.views.generic.base import RedirectView
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django.urls import reverse
from django.urls import reverse_lazy
from . import mixins
from .. import models

class ProfileRedirect(RedirectView):
    permanent = False
    query_string = False
    pattern_name = "profile_detail"

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        return reverse(self.pattern_name, args=[user.username])

class Profile(DetailView, mixins.TitleMixin):
    model = models.User
    context_object_name = 'profile'
    template_name = 'timetable/profile/detail.html'

    def get_slug_field(self):
        return 'username'

    def get_title(self):
        return f'User {self.get_object().username}'
    
class ProfileUpdate(UpdateView, mixins.TitleMixin):
    model = models.User
    fields = ['description', 'timezone']
    template_name = 'timetable/profile/update.html'
    success_url = reverse_lazy('profile_redirect')
    title = 'Update Profile'

    def get_object(self):
        return self.request.user
