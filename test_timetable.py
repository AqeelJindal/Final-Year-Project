# =========================================================
# TIMETABLE TEST SUITE
# =========================================================
# This file contains validation tests for the generated timetable.
# The tests check that the final timetable satisfies the main hard constraints
# used in the genetic algorithm model, including teacher clashes, group clashes,
# session counts, working hours and the teaching group hierarchy.


# =========================================================
# TEACHER CLASH TEST
# =========================================================

def test_teacher_clash(all_events, timetable, decode_slot):
    """
    Checks that no teacher is assigned to two events at the same time.

    This is a hard constraint because a staff member cannot physically teach
    more than one session in the same time slot.
    """

    n_events = len(all_events)

    # Compare every unique pair of events.
    for i in range(n_events):
        for j in range(i + 1, n_events):

            # Only events placed in the same slot can clash.
            if timetable[i] != timetable[j]:
                continue

            e1 = all_events[i]
            e2 = all_events[j]

            # If both events have the same teacher and the same start slot,
            # the timetable violates the teacher clash constraint.
            assert e1["teacher"] != e2["teacher"], (
                f"Teacher clash at {decode_slot(timetable[i], e1)}: "
                f"{e1} <-> {e2}"
            )


# =========================================================
# GROUP CLASH TEST
# =========================================================

def test_group_clash(all_events, timetable, decode_slot):
    """
    Checks that repeated sessions for the same teaching group do not occur
    at the same time.

    This test covers:
    - tutorial groups,
    - lecture groups,
    - lab groups.
    """

    n_events = len(all_events)

    for i in range(n_events):
        for j in range(i + 1, n_events):

            # Only events with the same assigned slot need to be checked.
            if timetable[i] != timetable[j]:
                continue

            e1 = all_events[i]
            e2 = all_events[j]

            # Tutorial sessions for the same tutorial group cannot overlap.
            if e1["type"] == "tutorial" and e2["type"] == "tutorial":
                same_group = e1["tutorial_group"] == e2["tutorial_group"]

                assert not same_group, (
                    f"Tutorial group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # Lecture sessions for the same module cannot overlap.
            # Lectures use the module as the group identifier because each
            # module has one implicit lecture group for the whole cohort.
            elif e1["type"] == "lecture" and e2["type"] == "lecture":
                same_group = e1["module"] == e2["module"]

                assert not same_group, (
                    f"Lecture group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # Lab sessions for the same lab group cannot overlap.
            elif e1["type"] == "lab" and e2["type"] == "lab":
                same_group = e1["lab_group"] == e2["lab_group"]

                assert not same_group, (
                    f"Lab group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )


# =========================================================
# TEACHER GROUP LOAD TEST
# =========================================================

def test_teacher_group_limit(
    all_events,
    max_lecture_groups=1,
    max_lab_groups=1,
    max_tutorial_groups=2,
    max_personal_tutorial_groups=1,
    max_groups_overall=2,
):
    """
    Checks that each teacher stays within the group assignment limits used
    when the timetable problem is created.

    The test checks both:
    - limits for each session type, and
    - the overall number of unique groups assigned to each teacher.
    """

    # Stores all unique groups taught by each teacher across all session types.
    teacher_groups = {}

    # Stores unique groups taught by each teacher, separated by event type.
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
                "personal tutorial": set(),
            }

        # Create a unique group identifier depending on the session type.
        # This prevents repeated sessions of the same group being counted twice.
        if event_type == "lecture":
            group_key = ("lecture", module)

        elif event_type == "lab":
            group_key = ("lab", module, event["lab_group"])

        elif event_type == "tutorial":
            group_key = ("tutorial", module, event["tutorial_group"])

        elif event_type == "personal tutorial":
            group_key = (
                "personal tutorial",
                module,
                event["personal_tutorial_group"],
            )

        else:
            raise ValueError(f"Unknown event type: {event_type}")

        # Add the group to the teacher's overall and type-specific sets.
        teacher_groups[teacher].add(group_key)
        teacher_type_groups[teacher][event_type].add(group_key)

    # Check each teacher's group counts against the defined limits.
    for teacher, groups in teacher_groups.items():
        lecture_count = len(teacher_type_groups[teacher]["lecture"])
        lab_count = len(teacher_type_groups[teacher]["lab"])
        tutorial_count = len(teacher_type_groups[teacher]["tutorial"])
        personal_tutorial_count = len(
            teacher_type_groups[teacher]["personal tutorial"]
        )
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


# =========================================================
# SESSION COUNT TEST
# =========================================================

def test_two_sessions_per_group(all_events):
    """
    Checks that each group has the expected number of weekly sessions.

    Expected session counts:
    - lectures: 2 sessions per module,
    - tutorials: 2 sessions per tutorial group,
    - labs: 2 sessions per lab group,
    - personal tutorials: 1 session per personal tutorial group.
    """

    group_sessions = {}

    for event in all_events:
        module = event["module"]
        e_type = event["type"]

        # Identify the relevant group number for each event type.
        if e_type == "tutorial":
            group = event["tutorial_group"]

        elif e_type == "lecture":
            group = 1  # lectures have one implicit cohort-level group

        elif e_type == "lab":
            group = event["lab_group"]

        elif e_type == "personal tutorial":
            group = event["personal_tutorial_group"]

        else:
            continue

        # Count sessions by module, event type and group.
        key = (module, e_type, group)

        if key not in group_sessions:
            group_sessions[key] = 0

        group_sessions[key] += 1

    # Compare the observed number of sessions against the expected number.
    for (module, e_type, group), count in group_sessions.items():
        expected_count = 1 if e_type == "personal tutorial" else 2

        assert count == expected_count, (
            f"{module} {e_type} group {group} has {count} sessions "
            f"instead of {expected_count}"
        )


# =========================================================
# WORKING HOURS TEST
# =========================================================

def test_sessions_within_working_hours(all_events, timetable, event_duration, HOURS):
    """
    Checks that all sessions stay within the working day.

    Sessions must:
    - start at or after 09:00, and
    - finish by 18:00.
    """

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


# =========================================================
# SESSION HIERARCHY CLASH TEST
# =========================================================

def test_session_clash(all_events, timetable, decode_slot):
    """
    Checks clash rules between different types of teaching sessions.

    The test covers four main rules:
    1. Lectures cannot clash with any other session.
    2. Tutorials cannot clash with labs from the same lab group.
    3. Personal tutorials cannot clash with tutorials from the same tutorial group.
    4. Personal tutorials cannot clash with labs from the same lab group.
    """

    n_events = len(all_events)

    for i in range(n_events):
        for j in range(i + 1, n_events):

            # Only events scheduled in the same slot can clash.
            if timetable[i] != timetable[j]:
                continue

            e1 = all_events[i]
            e2 = all_events[j]

            # -------------------------------------------------
            # Rule 1: lectures cannot clash with any session
            # -------------------------------------------------
            # Lectures are treated as whole-cohort events, so they must not
            # overlap with lectures, tutorials, labs or personal tutorials.
            if e1["type"] == "lecture" or e2["type"] == "lecture":
                assert False, (
                    f"Lecture clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # -------------------------------------------------
            # Rule 2: lab vs tutorial clash
            # -------------------------------------------------
            # A tutorial cannot overlap with a lab if both belong to the same
            # lab group.
            if (e1["type"] == "lab" and e2["type"] == "tutorial") or (
                e1["type"] == "tutorial" and e2["type"] == "lab"
            ):
                if e1["type"] == "lab":
                    lab_event = e1
                    tut_event = e2
                else:
                    lab_event = e2
                    tut_event = e1

                same_group = lab_event["lab_group"] == tut_event["lab_group"]

                assert not same_group, (
                    f"Lab and tutorial group clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )

            # -------------------------------------------------
            # Rule 3: personal tutorial vs tutorial clash
            # -------------------------------------------------
            # A personal tutorial cannot overlap with a tutorial if both belong
            # to the same tutorial group.
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

            # -------------------------------------------------
            # Rule 4: personal tutorial vs lab clash
            # -------------------------------------------------
            # A personal tutorial cannot overlap with a lab if both belong to
            # the same lab group.
            if (e1["type"] == "personal tutorial" and e2["type"] == "lab") or (
                e1["type"] == "lab" and e2["type"] == "personal tutorial"
            ):
                if e1["type"] == "personal tutorial":
                    pt_event = e1
                    lab_event = e2
                else:
                    pt_event = e2
                    lab_event = e1

                same_group = pt_event["lab_group"] == lab_event["lab_group"]

                assert not same_group, (
                    f"Personal tutorial and lab clash at {decode_slot(timetable[i], e1)}: "
                    f"{e1} <-> {e2}"
                )
