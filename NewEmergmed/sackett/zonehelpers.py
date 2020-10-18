from .authhelpers import is_user_authorised_for_zone
from .constants import *
from .models import Bed, Episode, Zone


def get_zones_list():
    return sorted([z for z in Zone.objects.filter(deleted=False)
                   if is_user_authorised_for_zone(z.id)], key=lambda x: x.label)


def move_episode(zone_id, source, destination):     # TODO: null checks!
    episode = Episode.objects.get(id=source)    # int(source[2:]))

    if destination == ZONE_WAITING_LIST_DRAG_DATA_ID:
        destination_bed = Bed.objects.filter(zone_id=zone_id)\
                                     .filter(template_index=ZONE_WAITING_LIST_BED_INDEX)\
                                     .first()
    else:
        destination_bed = Bed.objects.filter(zone_id=zone_id)\
                                     .filter(template_index=int(destination))\
                                     .first()

    episode.bed = destination_bed
    episode.save()
