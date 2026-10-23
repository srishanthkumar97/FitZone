from datetime import date, timedelta

from models import Attendance


def attendance_streaks(attendance_dates: list[date], today: date) -> tuple[int, int]:
    dates = sorted({day for day in attendance_dates if day <= today})
    if not dates:
        return 0, 0

    date_set = set(dates)
    anchor = today if today in date_set else today - timedelta(days=1)
    current = 0
    while anchor in date_set:
        current += 1
        anchor -= timedelta(days=1)

    longest = 1
    run = 1
    for previous, day in zip(dates, dates[1:]):
        if day == previous + timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    return current, longest


def serialize_attendance(attendance: Attendance) -> dict:
    return {
        "id": attendance.id,
        "user_id": attendance.user_id,
        "attendance_date": attendance.attendance_date.isoformat(),
        "check_in_time": attendance.check_in_time.isoformat(),
        "check_out_time": (
            attendance.check_out_time.isoformat()
            if attendance.check_out_time
            else None
        ),
        "status": attendance.status,
        "created_at": attendance.created_at.isoformat() if attendance.created_at else None,
    }
