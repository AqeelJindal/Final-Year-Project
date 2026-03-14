def test_teacher_clash(all_events, timetable, decode_slot):
    """Two teachers cannot teach two events at the same time."""

    n_events = len(all_events)

    for i in range(n_events):
        for j in range(i + 1, n_events):

            if timetable[i] != timetable[j]:
                continue

            e1 = all_events[i]
            e2 = all_events[j]

            assert e1["teacher"] != e2["teacher"], (
                f"Teacher clash at {decode_slot(timetable[i], e1)}: "
                f"{e1} <-> {e2}"
            )


# Extend this test case to lectures and labs later on
def test_group_clash(all_events, timetable, decode_slot):
    """
    Two sessions of the same tutorial group cannot happen at the same time.
    Two sessions of the same lecture cannot happen at the same time.
    """
    n_events = len(all_events)

    for i in range(n_events):
        for j in range(i + 1, n_events):

            if timetable[i] != timetable[j]:
                continue

            e1 = all_events[i]
            e2 = all_events[j]

            if e1["type"] == "tutorial" and e2["type"] == "tutorial":
                same_group = e1["tutorial_group"] == e2["tutorial_group"]

                assert not (same_group), (
                    f"Tutorial group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            if e1["type"] == "lecture" and e2["type"] == "lecture":
                same_group = e1["module"] == e2["module"]

                assert not (same_group), (
                    f"Lecture group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )


# Extend this test case to labs and personal tutorials later on
def test_teacher_group_limit(all_events):
    """Each teacher must teach at most 2 tutorial groups."""

    teacher_groups = {}

    for event in all_events:

        if event["type"] != "tutorial":
            continue

        teacher = event["teacher"]
        group = event["tutorial_group"]

        if teacher not in teacher_groups:
            teacher_groups[teacher] = set()

        teacher_groups[teacher].add(group)

    for teacher, groups in teacher_groups.items():
        assert len(groups) <= 2, (
            f"Teacher {teacher} assigned to {len(groups)} tutorial groups: {groups}"
        )

# later extend to labs and personal tutorials
def test_two_sessions_per_group(all_events):
    """
    Each tutorial group must have exactly 2 sessions per week.
    Each module must also have exactly 2 lecture sessions per week.
    """

    group_sessions = {}

    for event in all_events:

        module = event["module"]
        e_type = event["type"]

        if e_type == "tutorial":
            group = event["tutorial_group"]

        elif e_type == "lecture":
            group = 1  # lectures have a single implicit group

        else:
            continue

        key = (module, e_type, group)

        if key not in group_sessions:
            group_sessions[key] = 0

        group_sessions[key] += 1

    for (module, e_type, group), count in group_sessions.items():
        assert count == 2, (
            f"{module} {e_type} group {group} has {count} sessions instead of 2"
        )


def test_sessions_within_working_hours(all_events, timetable, event_duration, HOURS):
    """All sessions must start at or after 9:00 and end by 18:00."""

    for i, event in enumerate(all_events):
        slot = timetable[i]
        duration = event_duration[event["type"]]

        hour_index = slot % len(HOURS)
        start_hour = HOURS[hour_index]
        end_hour = start_hour + duration

        assert start_hour >= 9, (
            f"Session starts before 9:00: {event} starts at {start_hour}"
        )

        assert end_hour <= 18, (
            f"Session ends after 18:00: {event} ends at {end_hour}"
        )

# New test cases:
# check tutorial are after lectures
# check there are breaks between tutorials
# session clashes
