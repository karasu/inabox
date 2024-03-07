""" About inabox view """

from django.views import generic

class AboutView(generic.base.TemplateView):
    """ View to show about page """
    template_name = "app/about.html"
