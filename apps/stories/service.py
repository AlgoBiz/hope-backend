from django.db.models import F
from apps.stories.models import Hashtag, Story, MessageThread


def get_or_create_hashtags(names: list[str]) -> list[Hashtag]:
    """Normalize and bulk get-or-create hashtags from a list of strings."""
    hashtags = []
    for name in names:
        name = name.strip().lower()
        if name:
            obj, _ = Hashtag.objects.get_or_create(name=name)
            hashtags.append(obj)
    return hashtags


def increment_view_count(story: Story) -> None:
    """Atomically increment view_count to avoid race conditions."""
    Story.objects.filter(pk=story.pk).update(view_count=F('view_count') + 1)


def get_or_create_thread(story: Story, user, admin) -> tuple[MessageThread, bool]:
    return MessageThread.objects.get_or_create(
        story=story,
        user=user,
        defaults={'admin': admin},
    )
