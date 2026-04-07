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

# extend this to personal tutorials later on
def test_group_clash(all_events, timetable, decode_slot):
    """
    Two sessions of the same tutorial group cannot happen at the same time.
    Two sessions of the same lecture cannot happen at the same time.
    Two sessions of the same lab group cannot happen at the same time.
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

            elif e1["type"] == "lecture" and e2["type"] == "lecture":
                same_group = e1["module"] == e2["module"]

                assert not (same_group), (
                    f"Lecture group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            elif e1["type"] == "lab" and e2["type"] == "lab":
                same_group = e1["lab_group"] == e2["lab_group"]

                assert not (same_group), (
                    f"Lab group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )


# Extend this test case to personal tutorials later on
def test_teacher_group_limit(all_events):
    """
    Each teacher must teach at most:
    - 2 tutorial groups per module
    - 1 lab groups per module
    - lectures for at most 1 module
    """

    tutorial_groups = {}
    lab_groups = {}
    lecture_modules = {}

    for event in all_events:

        teacher = event["teacher"]
        event_type = event["type"]
        module = event["module"]

        # ---- Tutorials ----
        if event_type == "tutorial":
            group = event["tutorial_group"]

            if teacher not in tutorial_groups:
                tutorial_groups[teacher] = set()

            tutorial_groups[teacher].add((module, group))

        # ---- Labs ----
        elif event_type == "lab":
            group = event["lab_group"]

            if teacher not in lab_groups:
                lab_groups[teacher] = set()

            lab_groups[teacher].add((module, group))

        # ---- Lectures ----
        elif event_type == "lecture":

            if teacher not in lecture_modules:
                lecture_modules[teacher] = set()

            lecture_modules[teacher].add(module)

    for teacher, groups in tutorial_groups.items():
        assert len(groups) <= 2, (
            f"Teacher {teacher} assigned to {len(groups)} tutorial groups: {groups}"
        )

    for teacher, groups in lab_groups.items():
        assert len(groups) <= 1, (
            f"Teacher {teacher} assigned to {len(groups)} lab groups: {groups}"
        )

    for teacher, modules in lecture_modules.items():
        assert len(modules) <= 1, (
            f"Teacher {teacher} assigned to lectures for multiple modules: {modules}"
        )

# later extend to personal tutorials
def test_two_sessions_per_group(all_events):
    """
    Each tutorial group must have exactly 2 sessions per week.
    Each module must also have exactly 2 lecture sessions per week.
    Each lab group must have exactly 2 sessions per week.
    """

    group_sessions = {}

    for event in all_events:

        module = event["module"]
        e_type = event["type"]

        if e_type == "tutorial":
            group = event["tutorial_group"]

        elif e_type == "lecture":
            group = 1  # lectures have a single implicit group

        elif e_type == "lab":
            group = event["lab_group"]

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


# extend later for personal tutorials
def test_session_clash(all_events, timetable, decode_slot):
    """
    Session clash rules:

    1. Lectures cannot clash with any other session.
    2. Tutorials of the same group cannot clash.
    3. Labs of the same group cannot clash.
    4. Tutorials under the same lab group cannot clash with Lab and vice versa
    """

    n_events = len(all_events)

    for i in range(n_events):
        for j in range(i + 1, n_events):

            if timetable[i] != timetable[j]:
                continue

            e1 = all_events[i]
            e2 = all_events[j]

            # Rule 1: lectures cannot clash with anything
            if e1["type"] == "lecture" or e2["type"] == "lecture":
                assert False, (
                    f"Lecture clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # Rule 2: tutorial group clash
            if e1["type"] == "tutorial" and e2["type"] == "tutorial":
                same_group = e1["tutorial_group"] == e2["tutorial_group"]

                assert not (same_group), (
                    f"Tutorial group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # Rule 3: lab group clash
            if e1["type"] == "lab" and e2["type"] == "lab":
                same_group = e1["lab_group"] == e2["lab_group"]

                assert not (same_group), (
                    f"Lab group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # Rule 4: lab vs tutorial clash
            if (e1["type"] == "lab" and e2["type"] == "tutorial") or (e1["type"] == "tutorial" and e2["type"] == "lab"):

                if e1["type"] == "lab":
                    tut_event = e2
                    lab_event = e1
                else:
                    tut_event = e1
                    lab_event = e2

                tut_lab_group = tut_event["lab_group"]
                lab_group = lab_event["lab_group"]

                same_group = tut_lab_group == lab_group

                assert not (same_group), (
                    f"Lab and Tut group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

# New test cases:
# check tutorial are after lectures
# check there are breaks between tutorials
# build test cases for soft constraints too
