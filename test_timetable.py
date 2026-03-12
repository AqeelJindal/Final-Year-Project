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
                f"Teacher clash at {decode_slot(timetable[i])}: "
                f"{e1} <-> {e2}"
            )


def test_group_clash(all_events, timetable, decode_slot):
    """Two sessions of the same group cannot happen at the same time."""

    n_events = len(all_events)

    for i in range(n_events):
        for j in range(i + 1, n_events):

            if timetable[i] != timetable[j]:
                continue

            e1 = all_events[i]
            e2 = all_events[j]

            assert e1["group"] != e2["group"], (
                f"Group clash at {decode_slot(timetable[i])}: "
                f"{e1} <-> {e2}"
            )


def test_teacher_group_limit(all_events):
    """Each teacher must teach at most 2 groups."""

    teacher_groups = {}

    for event in all_events:

        teacher = event["teacher"]
        group = event["group"]

        if teacher not in teacher_groups:
            teacher_groups[teacher] = set()

        teacher_groups[teacher].add(group)

    for teacher, groups in teacher_groups.items():

        assert len(groups) <= 2, (
            f"Teacher {teacher} assigned to {len(groups)} groups: {groups}"
        )

def test_two_sessions_per_group(all_events):
    """Each (module, group) pair must have exactly 2 tutorial sessions per week."""

    group_sessions = {}

    for event in all_events:

        module = event["module"]
        group = event["group"]

        key = (module, group)

        if key not in group_sessions:
            group_sessions[key] = 0

        group_sessions[key] += 1

    for (module, group), count in group_sessions.items():

        assert count == 2, (
            f"{module} {group} has {count} tutorial sessions instead of 2"
        )

# New test cases:
# sessions should start from 9 and end at 18