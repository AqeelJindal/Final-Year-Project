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


def test_teacher_group_limit(
    all_events,
    max_lecture_groups=1,
    max_lab_groups=1,
    max_tutorial_groups=2,
    max_personal_tutorial_groups=1,
    max_groups_overall=2
):
    """
    Check that each teacher respects:

    - lecture group limit
    - lab group limit
    - tutorial group limit
    - personal tutorial group limit
    - overall unique group limit
    """

    teacher_groups = {}
    teacher_type_groups = {}

    for event in all_events:
        teacher = event["teacher"]
        event_type = event["type"]
        module = event["module"]

        if teacher not in teacher_groups:
            teacher_groups[teacher] = set()

        if teacher not in teacher_type_groups:
            teacher_type_groups[teacher] = {
                "lecture": set(),
                "lab": set(),
                "tutorial": set(),
                "personal tutorial": set()
            }

        if event_type == "lecture":
            group_key = ("lecture", module)

        elif event_type == "lab":
            group_key = ("lab", module, event["lab_group"])

        elif event_type == "tutorial":
            group_key = ("tutorial", module, event["tutorial_group"])

        elif event_type == "personal tutorial":
            group_key = ("personal tutorial", module, event["personal_tutorial_group"])

        else:
            raise ValueError(f"Unknown event type: {event_type}")

        # overall unique groups
        teacher_groups[teacher].add(group_key)

        # per-type unique groups
        teacher_type_groups[teacher][event_type].add(group_key)

    for teacher, groups in teacher_groups.items():
        lecture_count = len(teacher_type_groups[teacher]["lecture"])
        lab_count = len(teacher_type_groups[teacher]["lab"])
        tutorial_count = len(teacher_type_groups[teacher]["tutorial"])
        personal_tutorial_count = len(teacher_type_groups[teacher]["personal tutorial"])
        overall_count = len(groups)

        assert lecture_count <= max_lecture_groups, (
            f"Teacher {teacher} assigned to {lecture_count} lecture groups "
            f"instead of at most {max_lecture_groups}: "
            f"{teacher_type_groups[teacher]['lecture']}"
        )

        assert lab_count <= max_lab_groups, (
            f"Teacher {teacher} assigned to {lab_count} lab groups "
            f"instead of at most {max_lab_groups}: "
            f"{teacher_type_groups[teacher]['lab']}"
        )

        assert tutorial_count <= max_tutorial_groups, (
            f"Teacher {teacher} assigned to {tutorial_count} tutorial groups "
            f"instead of at most {max_tutorial_groups}: "
            f"{teacher_type_groups[teacher]['tutorial']}"
        )

        assert personal_tutorial_count <= max_personal_tutorial_groups, (
            f"Teacher {teacher} assigned to {personal_tutorial_count} personal tutorial groups "
            f"instead of at most {max_personal_tutorial_groups}: "
            f"{teacher_type_groups[teacher]['personal tutorial']}"
        )

        assert overall_count <= max_groups_overall, (
            f"Teacher {teacher} assigned to {overall_count} unique groups overall "
            f"instead of at most {max_groups_overall}: {groups}"
        )


def test_two_sessions_per_group(all_events):
    """
    Each tutorial group must have exactly 2 sessions per week.
    Each module must have exactly 2 lecture sessions per week.
    Each lab group must have exactly 2 sessions per week.
    Each personal tutorial group must have exactly 1 session per week.
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

        elif e_type == "personal tutorial":
            group = event["personal_tutorial_group"]

        else:
            continue

        key = (module, e_type, group)

        if key not in group_sessions:
            group_sessions[key] = 0

        group_sessions[key] += 1

    for (module, e_type, group), count in group_sessions.items():
        expected_count = 1 if e_type == "personal tutorial" else 2

        assert count == expected_count, (
            f"{module} {e_type} group {group} has {count} sessions instead of {expected_count}"
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


def test_session_clash(all_events, timetable, decode_slot):
    """
    Session clash rules:

    1. Lectures cannot clash with any other session.
    2. Tutorials under the same lab group cannot clash with labs and vice versa.
    3. Personal tutorials cannot clash with tutorials of the same tutorial group.
    4. Personal tutorials cannot clash with labs of the same lab group.
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

            # Rule 2: lab vs tutorial clash
            if (e1["type"] == "lab" and e2["type"] == "tutorial") or (
                e1["type"] == "tutorial" and e2["type"] == "lab"
            ):

                if e1["type"] == "lab":
                    lab_event = e1
                    tut_event = e2
                else:
                    lab_event = e2
                    tut_event = e1

                same_group = (
                    lab_event["lab_group"] == tut_event["lab_group"]
                )

                assert not same_group, (
                    f"Lab and tutorial group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # Rule 3: personal tutorial vs tutorial clash
            if (e1["type"] == "personal tutorial" and e2["type"] == "tutorial") or (
                e1["type"] == "tutorial" and e2["type"] == "personal tutorial"
            ):

                if e1["type"] == "personal tutorial":
                    pt_event = e1
                    tut_event = e2
                else:
                    pt_event = e2
                    tut_event = e1

                same_group = (
                    pt_event["tutorial_group"] == tut_event["tutorial_group"]
                )

                assert not same_group, (
                    f"Personal tutorial and tutorial clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # Rule 4: personal tutorial vs lab clash
            if (e1["type"] == "personal tutorial" and e2["type"] == "lab") or (
                e1["type"] == "lab" and e2["type"] == "personal tutorial"
            ):

                if e1["type"] == "personal tutorial":
                    pt_event = e1
                    lab_event = e2
                else:
                    pt_event = e2
                    lab_event = e1

                same_group = (
                    pt_event["lab_group"] == lab_event["lab_group"]
                )

                assert not same_group, (
                    f"Personal tutorial and lab clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

# New test cases:
# check tutorial are after lectures
# check there are breaks between tutorials
# build test cases for soft constraints too
