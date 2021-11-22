from django.contrib import admin
from survey.api.models import *

admin.site.register(Survey)
admin.site.register(Submission)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Answer)
admin.site.register(SelectAnswer)
