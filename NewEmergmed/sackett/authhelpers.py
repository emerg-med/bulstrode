# TODO: check user authorisation properly - or better yet do it in the Zone.objects.get() manager method then
# can use get_object_or_404() in the view
# see: http://stackoverflow.com/questions/11891606/row-level-permissions-in-django


def is_user_authorised_for_zone(zone_id):
    return True
