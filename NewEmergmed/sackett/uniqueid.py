from .models import UniqueIdentifier


def generate_next():
    return __generate_next_core()       # TODO look up config to see if we want annual series or not


def __generate_next_core(series=''):
    # to ensure thread safety, the process is as follows:
    # - create a blank entry to reserve an id in the database
    # - load all entries from the specified series and then calculate the identifier based on those that were
    #   created before this one
    # - update the blank entry in the database with the calculated id
    # - delete any entries before this one since we only need the latest (to calculate the next) - ignoring those with
    #   a zero identifier since they are in the process of being updated
    # thus if two identifiers are created concurrently, the process can happen in any order and still
    # safely result in unique sequential ids
    blank_identifier = 0

    new_unique_identifier = UniqueIdentifier(series=series, identifier=blank_identifier)
    new_unique_identifier.save()

    all_in_series = UniqueIdentifier.objects.filter(series=series).order_by('-id')  # most recent first

    calculated_identifier = 0

    for u in all_in_series:
        if u.id >= new_unique_identifier.id:        # only interested in anything prior to this one
            continue

        if u.identifier == 0:
            calculated_identifier += 1              # include in-progress updates in our count
        else:
            calculated_identifier += u.identifier   # and stop counting if/when we get to a concrete value
            break

    calculated_identifier += 1

    new_unique_identifier.identifier = calculated_identifier
    new_unique_identifier.save()

    for u in UniqueIdentifier.objects.filter(series=series):
        if u.id < new_unique_identifier.id and u.identifier > blank_identifier:
            u.delete()

    return calculated_identifier
