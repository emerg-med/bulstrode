from uuid import uuid4
from .constants import *
from .enumerations import LockRefreshResult, LockStates
from .models import RecordLock
from .utils import utc_now


def release_lock(lock_type, lock_uuid):
    current_locks = RecordLock.objects.filter(type=lock_type).filter(uuid=lock_uuid)
    current_locks.delete()


def try_acquire_lock(record_id, lock_type, force):
    lock_rows = list(RecordLock.objects.filter(type=lock_type).filter(record_id=record_id))
    now = utc_now()

    if len(lock_rows) > 0:
        if (now - lock_rows[-1].last_refresh_date_time).seconds <= RECORD_LOCKING_MAX_LIVE_LOCK_TIME_SECONDS:
            if force:
                for lock_row in lock_rows:
                    lock_row.delete()
            else:
                return None
        else:
            for lock_row in lock_rows:
                lock_row.delete()
    new_lock = RecordLock(type=lock_type, record_id=record_id, state=LockStates.Pending.value,
                          uuid=uuid4(), acquired_date_time=now, last_refresh_date_time=now)
    new_lock.save()

    other_locks = list(RecordLock.objects.filter(id__lt=new_lock.id)
                       .filter(type=lock_type)
                       .filter(record_id=record_id))

    if len(other_locks) == 0:
        new_lock.state = LockStates.Acquired.value
        new_lock.save()
    else:
        new_lock.delete()
        return None

    return str(new_lock.uuid)


def try_refresh_lock(lock_type, lock_uuid):
    current_locks = list(RecordLock.objects.filter(type=lock_type).filter(uuid=lock_uuid))

    if len(current_locks) == 1:
        current_locks[0].last_refresh_date_time = utc_now()
        current_locks[0].save()
        return LockRefreshResult.Success.value
    elif len(current_locks) == 0:
        return LockRefreshResult.Failure.value
    else:
        # TODO log error
        return LockRefreshResult.Error.value
