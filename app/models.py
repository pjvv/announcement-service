from pynamodb.attributes import BooleanAttribute, UnicodeAttribute
from pynamodb.models import Model
from settings import get_settings

settings = get_settings()


class AnnouncementModel(Model):
    class Meta:
        table_name = "AnnouncementsTable"
        region = settings.aws_region

    employer_id = UnicodeAttribute(hash_key=True)
    message = UnicodeAttribute()
    send_immediately = BooleanAttribute(default=False)
    send_at = UnicodeAttribute(null=True)
