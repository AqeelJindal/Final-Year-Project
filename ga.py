import numpy as np
import random

# =========================================================
# GLOBAL PROBLEM SETUP
# =========================================================
# This section defines the timetable scenario used in the project.
# The model represents a simplified Year 2 Semester 1 Computer Science
# timetable, using modules, staff members, teaching groups and event types.

# Staff assigned to each module.
# The first staff member in each list is treated as the module lecturer.
Staff = {
    "COMP2399": ["Amy", "Paulie", "Mark", "Oana", "Noleen", "Norah", "Aryan", "Alice", "Ojas", "Meheraab"],
    "COMP2244": ["Massimiliano", "Adri", "Tom", "Haiko", "Alan", "Rob", "Naila"],
    "COMP2579": ["Natasha", "Sarah", "Max", "Andrei", "Gori", "Arshad", "Xeung", "Xi"],
}

# =========================================================
# GROUP HIERARCHY
# =========================================================
# The timetable uses a hierarchy of teaching groups:
# Lecture group -> Lab groups -> Tutorial groups -> Personal tutorial groups.
# This allows smaller teaching sessions to be linked back to the larger
# student groups they belong to, so clashes can be checked consistently.

LECTURE_GROUPS = 1
LAB_GROUPS = 2
TUTORIAL_GROUPS = 5
PERSONAL_TUTORIAL_GROUPS = 14

# Personal tutorials are modelled as belonging to COMP2399 because they are
# part of the wider Year 2 structure rather than a separate taught module.
PERSONAL_TUTORIAL_MODULE = "COMP2399"

# COMP2579 does not have lab sessions in this simplified model.
NOT_LAB_MODULE = "COMP2579"


def validate_group_hierarchy():
    """
    Checks that the group hierarchy is valid before the timetable is created.
    Each lower-level group type must have at least as many groups as the level
    above it. This prevents impossible mappings between lectures, labs,
    tutorials and personal tutorials.
    """

    if LECTURE_GROUPS < 1:
        raise ValueError("LECTURE_GROUPS must be at least 1.")

    if LAB_GROUPS < LECTURE_GROUPS:
        raise ValueError(
            "Invalid hierarchy: LAB_GROUPS must be greater than LECTURE_GROUPS."
        )

    if TUTORIAL_GROUPS < LAB_GROUPS:
        raise ValueError(
            "Invalid hierarchy: TUTORIAL_GROUPS must be greater than LAB_GROUPS."
        )

    if PERSONAL_TUTORIAL_GROUPS < TUTORIAL_GROUPS:
        raise ValueError(
            "Invalid hierarchy: PERSONAL_TUTORIAL_GROUPS must be greater than TUTORIAL_GROUPS."
        )


# Validate the group structure before any events are generated.
validate_group_hierarchy()


# =========================================================
# STAFF GROUP ASSIGNMENT
# =========================================================
# The function below assigns teachers to the required teaching groups while
# respecting both type-specific load limits and an overall teaching load limit.


def create_groups(
    module_teachers,
    all_teachers,
    n_groups,
    type_teacher_load,
    max_groups_per_type,
    overall_teacher_load,
    max_groups_overall,
    forced_teacher=None,
):
    """
    Creates a dictionary of teaching groups and assigns a teacher to each group.

    Parameters:
    - module_teachers: staff normally associated with the module.
    - all_teachers: all available teachers across the timetable.
    - n_groups: number of groups required for this session type.
    - type_teacher_load: load counter for this specific session type.
    - max_groups_per_type: maximum groups a teacher can teach for this type.
    - overall_teacher_load: total load counter across all session types.
    - max_groups_overall: overall maximum groups per teacher.
    - forced_teacher: optional teacher who must be assigned to Group 1.

    Returns:
    - A dictionary where each group is linked to its assigned teacher.
    """

    groups = {}
    group_id = 1

    def can_assign(teacher):
        """Returns True if a teacher still has capacity for this assignment."""
        return (
            type_teacher_load[teacher] < max_groups_per_type
            and overall_teacher_load[teacher] < max_groups_overall
        )

    def assign_teacher(teacher, group_id):
        """Assigns a teacher to a group and updates load counters."""
        groups[f"Group{group_id}"] = {"teacher": teacher}
        type_teacher_load[teacher] += 1
        overall_teacher_load[teacher] += 1

    # If a specific teacher is required, assign them to Group 1 first.
    # This is used for lectures so the named lecturer teaches the lecture group.
    if forced_teacher is not None:
        if not can_assign(forced_teacher):
            raise ValueError(
                f"Forced teacher {forced_teacher} has no remaining capacity."
            )

        assign_teacher(forced_teacher, group_id)
        group_id += 1

    # Assign module staff first, because they are the most appropriate teachers
    # for the module-specific teaching groups.
    for teacher in module_teachers:
        while can_assign(teacher) and group_id <= n_groups:
            assign_teacher(teacher, group_id)
            group_id += 1

    # If more groups are still needed, allow other available staff to teach them.
    if group_id <= n_groups:
        other_teachers = [t for t in all_teachers if t not in module_teachers]

        for teacher in other_teachers:
            while can_assign(teacher) and group_id <= n_groups:
                assign_teacher(teacher, group_id)
                group_id += 1

    # If the required number of groups still cannot be covered, the scenario is
    # infeasible with the current staff capacity settings.
    if group_id <= n_groups:
        raise ValueError("Not enough teacher capacity to cover all groups.")

    return groups


# Create a single list of all teachers across all modules.
all_teachers = []

for teacher_list in Staff.values():
    all_teachers.extend(teacher_list)

# Remove duplicate teacher names while preserving the original order.
all_teachers = list(dict.fromkeys(all_teachers))

# Track how many groups each teacher has been assigned for each session type.
lecture_teacher_load = {t: 0 for t in all_teachers}
lab_teacher_load = {t: 0 for t in all_teachers}
tutorial_teacher_load = {t: 0 for t in all_teachers}
personal_tutorial_teacher_load = {t: 0 for t in all_teachers}

# Track each teacher's total load across all session types.
overall_teacher_load = {t: 0 for t in all_teachers}

# Maximum number of groups a teacher can be assigned to overall.
MAX_GROUPS_OVERALL = 2

# =========================================================
# MODULE STRUCTURE
# =========================================================
# Each module is given lecture groups, tutorial groups, lab groups where
# applicable, and personal tutorials where applicable.

Modules = {}

for module_code, teachers in Staff.items():
    lecturer = teachers[0]

    Modules[module_code] = {}

    # Create the lecture group. The first staff member is forced to teach it.
    Modules[module_code]["Lecture"] = create_groups(
        teachers,
        all_teachers,
        LECTURE_GROUPS,
        lecture_teacher_load,
        1,
        overall_teacher_load,
        MAX_GROUPS_OVERALL,
        forced_teacher=lecturer,
    )

    # Create lab groups unless the module has been defined as not requiring labs.
    if module_code == NOT_LAB_MODULE:
        Modules[module_code]["Lab session"] = {}
    else:
        Modules[module_code]["Lab session"] = create_groups(
            teachers,
            all_teachers,
            LAB_GROUPS,
            lab_teacher_load,
            1,
            overall_teacher_load,
            MAX_GROUPS_OVERALL,
        )

    # Create tutorial groups for each module.
    Modules[module_code]["tutorials"] = create_groups(
        teachers,
        all_teachers,
        TUTORIAL_GROUPS,
        tutorial_teacher_load,
        2,
        overall_teacher_load,
        MAX_GROUPS_OVERALL,
    )

    # Create personal tutorial groups only for the dummy personal tutorial module.
    if module_code == PERSONAL_TUTORIAL_MODULE:
        Modules[module_code]["Personal Tutorials"] = create_groups(
            teachers,
            all_teachers,
            PERSONAL_TUTORIAL_GROUPS,
            personal_tutorial_teacher_load,
            1,
            overall_teacher_load,
            MAX_GROUPS_OVERALL,
        )
    else:
        Modules[module_code]["Personal Tutorials"] = {}


# Debugging checks can be enabled if needed.
# print(Modules)
# print(lecture_teacher_load)
# print(lab_teacher_load)
# print(tutorial_teacher_load)
# print(personal_tutorial_teacher_load)
# print(overall_teacher_load)


# =========================================================
# PENALTY SETTINGS
# =========================================================
# Hard penalties are deliberately much larger than soft penalties. This supports
# a feasibility-first approach: the genetic algorithm should prioritise avoiding
# invalid timetables before improving preferences.

HARD_PENALTY = 10 ** 6
SOFT_SMALL = 10
SOFT_MEDIUM = 50
SOFT_LARGE = 200


# =========================================================
# EVENT GENERATION
# =========================================================
# Events are the individual timetable items that the genetic algorithm assigns
# to time slots. Each event stores its type, module, teacher and group identity.

# -------------------------
# Lecture events
# -------------------------
lecture_events = []

for module_name, module_data in Modules.items():
    for group_name, info in module_data["Lecture"].items():
        for session in range(2):  # each module has two lecture sessions per week
            lecture_events.append({
                "type": "lecture",
                "module": module_name,
                "teacher": info["teacher"],
            })

nL_lec = len(lecture_events)

# print(lecture_events)


# -------------------------
# Lab events
# -------------------------
lab_events = []

for module_name, module_data in Modules.items():
    for group_name, info in module_data["Lab session"].items():
        lab_group = int(group_name.replace("Group", ""))

        for session in range(2):  # each lab group has two lab sessions per week
            lab_events.append({
                "type": "lab",
                "module": module_name,
                "lab_group": lab_group,
                "teacher": info["teacher"],
            })

nL_lab = len(lab_events)

# print(lab_events)


# -------------------------
# Tutorial events
# -------------------------
tutorial_events = []

for module_name, module_data in Modules.items():
    for group_name, info in module_data["tutorials"].items():
        tutorial_group = int(group_name.replace("Group", ""))

        # Map each tutorial group to the lab group it belongs to.
        # This is used later to prevent clashes between related labs and tutorials.
        lab_group = ((tutorial_group - 1) * LAB_GROUPS) // TUTORIAL_GROUPS + 1

        for session in range(2):  # each tutorial group has two sessions per week
            tutorial_events.append({
                "type": "tutorial",
                "module": module_name,
                "lab_group": lab_group,
                "tutorial_group": tutorial_group,
                "teacher": info["teacher"],
            })

nL_tut = len(tutorial_events)

# print(tutorial_events)
# print(nL_tut)


# -------------------------
# Personal tutorial events
# -------------------------
per_tut_events = []

for module_name, module_data in Modules.items():
    for group_name, info in module_data["Personal Tutorials"].items():
        personal_tutorial_group = int(group_name.replace("Group", ""))

        # Map each personal tutorial group to its related tutorial group.
        tutorial_group = ((personal_tutorial_group - 1) * TUTORIAL_GROUPS) // PERSONAL_TUTORIAL_GROUPS + 1

        # Map the tutorial group to its related lab group.
        lab_group = ((tutorial_group - 1) * LAB_GROUPS) // TUTORIAL_GROUPS + 1

        for session in range(1):  # personal tutorials occur once per week
            per_tut_events.append({
                "type": "personal tutorial",
                "module": module_name,
                "lab_group": lab_group,
                "tutorial_group": tutorial_group,
                "personal_tutorial_group": personal_tutorial_group,
                "teacher": info["teacher"],
            })

nL_per_tut = len(per_tut_events)

# print(per_tut_events)
# print(nL_per_tut)


# Combine all generated events into one list.
# The genetic algorithm assigns one start time to each event in this list.
all_events = (
    lecture_events
    + tutorial_events
    + lab_events
    + per_tut_events
)

n_events = len(all_events)

# print(all_events)


# =========================================================
# TIMESLOT MODEL
# =========================================================
# The timetable is represented as a weekly grid from Monday to Friday,
# with hourly start slots from 09:00 to 17:00.

# Duration of each event type in hours.
event_duration = {
    "lecture": 2,
    "tutorial": 1,
    "lab": 1,
    "personal tutorial": 1,
}

DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
HOURS = list(range(9, 18))  # available hourly slots: 09:00 to 17:00

# Total number of grid slots in the timetable.
nG = len(DAYS) * len(HOURS)


def decode_slot(slot_index, event):
    """
    Converts a numerical slot index into a readable day and time range.
    This is mainly used when displaying or testing timetable results.
    """

    duration = event_duration[event["type"]]

    day_index = slot_index // len(HOURS)
    hour_index = slot_index % len(HOURS)

    day = DAYS[day_index]
    start = HOURS[hour_index]

    return f"{day} {start}:00-{start + duration}:00"


def valid_slots(duration):
    """
    Returns all valid start slots for an event with the given duration.
    This prevents multi-hour events, such as lectures, from starting so late
    that they run beyond the end of the working day.
    """

    slots = []

    for slot in range(nG):
        hour_index = slot % len(HOURS)

        if hour_index <= len(HOURS) - duration:
            slots.append(slot)

    return slots


# Precompute valid start slots for each event type.
valid_start_slots = {}

for e_type, duration in event_duration.items():
    valid_start_slots[e_type] = valid_slots(duration)


# =========================================================
# GLOBAL CLASH MATRIX
# =========================================================
# C stores pairwise clash penalties between events. If two events overlap in
# time and their matrix entry contains HARD_PENALTY, the timetable is invalid.
# This separates the definition of clashes from the fitness calculation.

C = np.zeros((n_events, n_events), dtype=np.int64)

for i in range(n_events):
    for j in range(n_events):
        if i == j:
            continue

        event_i = all_events[i]
        event_j = all_events[j]

        teacher_i = event_i["teacher"]
        teacher_j = event_j["teacher"]

        type_i = event_i["type"]
        type_j = event_j["type"]

        # RULE 1: Lab sessions for the same lab group must not overlap.
        if type_i == "lab" and type_j == "lab":
            lab_i = event_i["lab_group"]
            lab_j = event_j["lab_group"]

            if lab_i == lab_j:
                C[i][j] = HARD_PENALTY

        # RULE 2: Tutorial sessions for the same tutorial group must not overlap.
        if type_i == "tutorial" and type_j == "tutorial":
            tut_i = event_i["tutorial_group"]
            tut_j = event_j["tutorial_group"]

            if tut_i == tut_j:
                C[i][j] = HARD_PENALTY

        # RULE 3: Tutorials must not overlap with labs for the same lab group.
        if (type_i == "tutorial" and type_j == "lab") or (type_i == "lab" and type_j == "tutorial"):
            if type_i == "tutorial":
                tut_event = event_i
                lab_event = event_j
            else:
                tut_event = event_j
                lab_event = event_i

            tut_lab_group = tut_event["lab_group"]
            lab_group = lab_event["lab_group"]

            if tut_lab_group == lab_group:
                C[i][j] = HARD_PENALTY

        # RULE 4: Personal tutorials must not overlap with labs for the same lab group.
        if (type_i == "personal tutorial" and type_j == "lab") or (type_i == "lab" and type_j == "personal tutorial"):
            if type_i == "personal tutorial":
                per_tut_event = event_i
                lab_event = event_j
            else:
                per_tut_event = event_j
                lab_event = event_i

            per_tut_lab_group = per_tut_event["lab_group"]
            lab_group = lab_event["lab_group"]

            if per_tut_lab_group == lab_group:
                C[i][j] = HARD_PENALTY

        # RULE 5: Personal tutorials must not overlap with tutorials for the same tutorial group.
        if (type_i == "personal tutorial" and type_j == "tutorial") or (type_i == "tutorial" and type_j == "personal tutorial"):
            if type_i == "personal tutorial":
                per_tut_event = event_i
                tut_event = event_j
            else:
                per_tut_event = event_j
                tut_event = event_i

            per_tut_tut_group = per_tut_event["tutorial_group"]
            tut_group = tut_event["tutorial_group"]

            if per_tut_tut_group == tut_group:
                C[i][j] = HARD_PENALTY

        # RULE 6: A teacher cannot teach two events at the same time.
        if teacher_i == teacher_j:
            C[i][j] = HARD_PENALTY

        # RULE 7: Lectures clash with all other teaching events.
        # This reflects the assumption that the whole cohort attends lectures.
        if type_i == "lecture" or type_j == "lecture":
            C[i][j] = HARD_PENALTY

# print(C)


# =========================================================
# TEACHER TIME PREFERENCES
# =========================================================
# Teacher preferences are modelled as soft penalties. A penalty is applied when
# an event is scheduled in a slot that does not match the teacher's preference.

teacher_time_preferences = {}

event_types = ["lecture", "lab", "tutorial", "personal tutorial"]

# Initialise all teacher preference penalties to zero.
for teacher in all_teachers:
    teacher_time_preferences[teacher] = {}

    for e_type in event_types:
        teacher_time_preferences[teacher][e_type] = [0] * nG

# Define selected teacher preferences.
for slot in range(nG):
    day_index = slot // len(HOURS)
    hour_index = slot % len(HOURS)

    day = DAYS[day_index]
    hour = HOURS[hour_index]

    # Amy prefers lectures before 12:00.
    if hour >= 12:
        teacher_time_preferences["Amy"]["lecture"][slot] = SOFT_SMALL

    # Amy prefers tutorials after 12:00.
    if hour < 12:
        teacher_time_preferences["Amy"]["tutorial"][slot] = SOFT_SMALL

    # Natasha prefers morning lectures.
    if hour >= 11:
        teacher_time_preferences["Natasha"]["lecture"][slot] = SOFT_SMALL

    # Sarah prefers not to teach tutorials on Thursday.
    if day == "THU":
        teacher_time_preferences["Sarah"]["tutorial"][slot] = SOFT_SMALL

# print(teacher_time_preferences)


# =========================================================
# STUDENT TIME PREFERENCES
# =========================================================
# Student preferences are also modelled as soft penalties. In this simplified
# model, all students are treated as one combined student body.

student_time_preferences = {}
student_time_preferences["ALL_STUDENTS"] = {}

# Initialise all student preference penalties to zero.
for e_type in event_types:
    student_time_preferences["ALL_STUDENTS"][e_type] = [0] * nG

for slot in range(nG):
    day_index = slot // len(HOURS)
    hour_index = slot % len(HOURS)

    day = DAYS[day_index]
    hour = HOURS[hour_index]

    # Students prefer lectures and tutorials before 16:00.
    if hour >= 16:
        student_time_preferences["ALL_STUDENTS"]["lecture"][slot] = SOFT_MEDIUM
        student_time_preferences["ALL_STUDENTS"]["tutorial"][slot] = SOFT_MEDIUM

    # Students prefer not to have tutorials on Friday.
    if day == "FRI":
        student_time_preferences["ALL_STUDENTS"]["tutorial"][slot] = SOFT_MEDIUM

    # Students prefer lectures in the afternoon.
    if hour > 15 or hour < 12:
        student_time_preferences["ALL_STUDENTS"]["lecture"][slot] = SOFT_MEDIUM

# print(student_time_preferences)


# =========================================================
# GENETIC ALGORITHM REPRESENTATION
# =========================================================
# A chromosome is a list of time-slot indices. Each gene corresponds to one
# event in all_events, and the value of that gene is the assigned start slot.


def random_timetable():
    """
    Creates a random timetable chromosome by assigning each event to one of its
    valid start slots.
    """

    timetable = []

    for event in all_events:
        e_type = event["type"]
        timetable.append(random.choice(valid_start_slots[e_type]))

    return timetable


# print(n_events)
# print(len(random_timetable()))
# print(random_timetable())


# =========================================================
# FITNESS FUNCTION SETUP
# =========================================================
# The fitness function returns a tuple rather than a single number. Python
# compares tuples lexicographically, so hard penalties are minimised first,
# followed by soft penalties. This supports a feasibility-first objective.

# Soft sequencing rule: lectures should occur before tutorials for the same module.
SEQUENTIAL_RULES = {
    ("lecture", "tutorial"): SOFT_LARGE,
}

# Group events by module and event type to make sequencing checks easier.
events_by_module_type = {}

for idx, event in enumerate(all_events):
    module = event["module"]
    e_type = event["type"]

    if module not in events_by_module_type:
        events_by_module_type[module] = {}

    events_by_module_type[module].setdefault(e_type, []).append(idx)


# Hard gap rules between repeated sessions of the same type.
# The first value is the minimum number of days required between sessions.
SESSION_GAP_RULES = {
    "lecture": (1, HARD_PENALTY),    # at least 1 day between lecture sessions
    "tutorial": (2, HARD_PENALTY),   # at least 2 days between tutorial sessions
    "lab": (1, HARD_PENALTY),        # at least 1 day between lab sessions
}

# Group repeated sessions so that gap constraints are checked within the
# correct module and group combination.
sessions_by_key = {}

for idx, event in enumerate(all_events):
    e_type = event["type"]
    module = event["module"]

    if e_type not in SESSION_GAP_RULES:
        continue

    if e_type == "lecture":
        key = (module, e_type)

    elif e_type == "tutorial":
        key = (module, e_type, event["tutorial_group"])

    elif e_type == "lab":
        key = (module, e_type, event["lab_group"])

    sessions_by_key.setdefault(key, []).append(idx)


def fitness(timetable):
    """
    Evaluates a timetable and returns a lexicographic fitness tuple:

    (hard_penalty, lecture_soft, tutorial_soft, lab_soft, personal_soft)

    A timetable is feasible only if hard_penalty is zero. Soft penalties are
    separated by event type so the final result can show where the timetable
    performs better or worse against preferences.
    """

    hard_penalty = 0
    tutorial_soft = 0
    lecture_soft = 0
    lab_soft = 0
    personal_soft = 0

    # -----------------------------------------------------
    # 1. Clash penalties
    # -----------------------------------------------------
    # For each pair of events, check whether their occupied time ranges overlap.
    # If they overlap and the clash matrix says they cannot overlap, add a hard
    # penalty.
    for i in range(n_events):
        for j in range(i + 1, n_events):
            slot_i = timetable[i]
            slot_j = timetable[j]

            dur_i = event_duration[all_events[i]["type"]]
            dur_j = event_duration[all_events[j]["type"]]

            slots_i = set(range(slot_i, slot_i + dur_i))
            slots_j = set(range(slot_j, slot_j + dur_j))

            if slots_i & slots_j:
                hard_penalty += C[i][j]

    # -----------------------------------------------------
    # 2. Teacher and student time preference penalties
    # -----------------------------------------------------
    # Soft penalties are added when an event is placed in a time slot that
    # conflicts with staff or student preferences.
    for i, event in enumerate(all_events):
        teacher = event["teacher"]
        e_type = event["type"]
        slot = timetable[i]

        teacher_pen = teacher_time_preferences[teacher][e_type][slot]
        student_pen = student_time_preferences["ALL_STUDENTS"][e_type][slot]

        total_soft = teacher_pen + student_pen

        if e_type == "tutorial":
            tutorial_soft += total_soft

        elif e_type == "lecture":
            lecture_soft += total_soft

        elif e_type == "lab":
            lab_soft += total_soft

        elif e_type == "personal tutorial":
            personal_soft += total_soft

    # -----------------------------------------------------
    # 3. Sequencing penalties
    # -----------------------------------------------------
    # Penalise cases where tutorials are scheduled before lectures for the
    # same module.
    for (earlier_type, later_type), penalty in SEQUENTIAL_RULES.items():
        for module, types in events_by_module_type.items():
            earlier_events = types.get(earlier_type, [])
            later_events = types.get(later_type, [])

            for i in earlier_events:
                for j in later_events:
                    start_i = timetable[i]
                    start_j = timetable[j]

                    if start_i >= start_j:
                        lecture_soft += penalty
                        tutorial_soft += penalty

    # -----------------------------------------------------
    # 4. Gap constraints between repeated sessions
    # -----------------------------------------------------
    # Ensure repeated sessions for the same module/group are spread across
    # the week rather than being placed too close together.
    for key, event_indices in sessions_by_key.items():
        e_type = key[1]
        min_gap, penalty = SESSION_GAP_RULES[e_type]

        for i in range(len(event_indices)):
            for j in range(i + 1, len(event_indices)):
                idx_i = event_indices[i]
                idx_j = event_indices[j]

                slot_i = timetable[idx_i]
                slot_j = timetable[idx_j]

                day_i = slot_i // len(HOURS)
                day_j = slot_j // len(HOURS)

                gap = abs(day_i - day_j)

                if gap < min_gap:
                    hard_penalty += penalty

    return (
        hard_penalty,
        lecture_soft,
        tutorial_soft,
        lab_soft,
        personal_soft,
    )


# print(fitness(random_timetable()))


# =========================================================
# GENETIC OPERATORS
# =========================================================
# These functions define how the genetic algorithm selects parents, combines
# them, and introduces random changes into new candidate timetables.


def select(population):
    """
    Tournament selection. Two candidate timetables are chosen at random and the
    better one, based on the lexicographic fitness tuple, is selected.
    """

    a = random.choice(population)
    b = random.choice(population)
    return a if fitness(a) < fitness(b) else b


def crossover(p1, p2):
    """
    Single-point crossover. A cut point is selected and the child receives the
    first part of parent 1 and the second part of parent 2.
    """

    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:]


def mutate(timetable, rate=0.1):
    """
    Mutation randomly changes event start slots. When a gene mutates, it is
    reassigned to a valid start slot for that event type.
    """

    for i in range(len(timetable)):
        if random.random() < rate:
            event_type = all_events[i]["type"]
            timetable[i] = random.choice(valid_start_slots[event_type])

    return timetable


# =========================================================
# GENETIC ALGORITHM
# =========================================================
# The algorithm is split into two phases:
# Phase 1 finds any feasible timetable with zero hard penalties.
# Phase 2 starts from that feasible timetable and improves soft preferences
# while retaining feasibility.


def genetic_algorithm(
    generations=1001,
    population_size=50,
    elite_size=3,
    mutation_rate=0.1,
    stagnation_limit=100,
):
    """
    Runs the two-phase genetic algorithm and returns the best feasible solution.
    """

    # =============================
    # PHASE 1: FIND FEASIBLE SOLUTION
    # =============================

    print("\n--- Phase 1: Searching for feasible timetable ---")

    population = [random_timetable() for _ in range(population_size)]
    feasible_solution = None

    for gen in range(generations):
        population.sort(key=fitness)
        best = population[0]
        best_fit = fitness(best)

        print(f"Phase1 Gen {gen:3d} | Hard penalty: {best_fit[0]}")

        # A timetable is feasible once all hard constraints are satisfied.
        if best_fit[0] == 0:
            feasible_solution = best
            print("\nFeasible timetable found!")
            break

        # Elitism keeps the best candidates unchanged for the next generation.
        new_population = population[:elite_size]

        # Fill the rest of the new population using selection, crossover and mutation.
        while len(new_population) < population_size:
            parent1 = select(population)
            parent2 = select(population)

            child = crossover(parent1, parent2)
            child = mutate(child, rate=mutation_rate)

            new_population.append(child)

        population = new_population

    if feasible_solution is None:
        print("\nNo feasible timetable found.")
        return None

    # =============================
    # PHASE 2: OPTIMISE SOFT PENALTIES
    # =============================

    print("\n--- Phase 2: Optimising soft penalties ---")

    # Create a new population around the feasible timetable.
    # This gives the algorithm feasible material to improve from.
    population = [feasible_solution]

    while len(population) < population_size:
        new_individual = mutate(feasible_solution.copy(), rate=0.1)
        population.append(new_individual)

    best_solution = feasible_solution
    stagnant_generations = 0

    for gen in range(generations):
        population.sort(key=fitness)

        best = population[0]
        best_fit = fitness(best)

        print(f"Phase2 Gen {gen:3d} | Fitness: {best_fit}")

        # Update the best solution if the new timetable improves the full
        # lexicographic fitness tuple.
        if best_fit < fitness(best_solution):
            best_solution = best
            stagnant_generations = 0
        else:
            stagnant_generations += 1

        # Stop early if no improvement has been made for a fixed number of generations.
        if stagnant_generations >= stagnation_limit:
            print(f"\nNo improvement for {stagnation_limit} generations. Stopping early.")
            break

        new_population = population[:elite_size]

        while len(new_population) < population_size:
            parent1 = select(population)
            parent2 = select(population)

            child = crossover(parent1, parent2)
            child = mutate(child, rate=mutation_rate)

            # In Phase 2, only feasible children are kept so soft optimisation
            # does not reintroduce hard-constraint violations.
            if fitness(child)[0] == 0:
                new_population.append(child)

        population = new_population

    return best_solution


# =========================================================
# TIMETABLE VISUALISATION
# =========================================================
# This section converts the best genetic algorithm solution into a visual weekly
# timetable. Events are colour-coded by module and labelled by session type,
# group and teacher.

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import textwrap


def plot_timetable(best_solution, all_events, DAYS, HOURS):
    """
    Plots the final timetable as a weekly grid.

    Each cell represents a day-hour slot. If multiple events occur in the same
    slot, they are stacked within the same cell. Module colours are used instead
    of repeating module codes inside every event label.
    """

    fig, ax = plt.subplots(figsize=(22, 10))

    n_days = len(DAYS)
    n_hours = len(HOURS)

    # -----------------------------------------------------
    # Store events by timetable cell
    # -----------------------------------------------------
    # This dictionary groups events by exact day and hour so they can be drawn
    # in the correct grid position.
    timetable = {day: {hour: [] for hour in HOURS} for day in DAYS}

    for idx, slot in enumerate(best_solution):
        event = all_events[idx]
        duration = event_duration[event["type"]]

        day_index = slot // len(HOURS)
        hour_index = slot % len(HOURS)

        day = DAYS[day_index]
        module = event["module"]
        teacher = event["teacher"]
        e_type = event["type"]

        # Create compact labels for each event type.
        if e_type == "lecture":
            label = f"Lecture\n{teacher}"
        elif e_type == "tutorial":
            label = f"Tut {event['tutorial_group']}\n{teacher}"
        elif e_type == "lab":
            label = f"Lab {event['lab_group']}\n{teacher}"
        elif e_type == "personal tutorial":
            label = f"PT {event['personal_tutorial_group']}\n{teacher}"

        # Add the event to every hour it occupies.
        for h in range(duration):
            timetable[day][HOURS[hour_index + h]].append({
                "module": module,
                "label": label,
            })

    # -----------------------------------------------------
    # Module colours
    # -----------------------------------------------------
    module_colors = {
        "COMP2399": "#8dd3c7",
        "COMP2244": "#bebada",
        "COMP2579": "#fb8072",
    }

    # -----------------------------------------------------
    # Draw timetable grid
    # -----------------------------------------------------
    ax.set_xlim(0, n_hours)
    ax.set_ylim(0, n_days)
    ax.invert_yaxis()

    for x in range(n_hours + 1):
        ax.axvline(x, color="black", linewidth=1)

    for y in range(n_days + 1):
        ax.axhline(y, color="black", linewidth=1)

    # -----------------------------------------------------
    # Draw event boxes and labels
    # -----------------------------------------------------
    margin_x = 0.04
    margin_y = 0.04
    internal_gap = 0.03

    for d, day in enumerate(DAYS):
        for h, hour in enumerate(HOURS):
            events = timetable[day][hour]

            if not events:
                continue

            n_events_cell = len(events)
            usable_width = 1 - 2 * margin_x
            usable_height = 1 - 2 * margin_y

            total_gap = internal_gap * (n_events_cell - 1)
            box_height = (usable_height - total_gap) / n_events_cell

            # Reduce font size as more events are stacked into the same cell.
            if n_events_cell == 1:
                fontsize = 9
            elif n_events_cell == 2:
                fontsize = 8
            elif n_events_cell == 3:
                fontsize = 7
            else:
                fontsize = 6

            for i, ev in enumerate(events):
                x0 = h + margin_x
                y0 = d + margin_y + i * (box_height + internal_gap)

                color = module_colors.get(ev["module"], "lightgrey")

                rect = patches.Rectangle(
                    (x0, y0),
                    usable_width,
                    box_height,
                    facecolor=color,
                    edgecolor="black",
                    linewidth=1.0,
                )
                ax.add_patch(rect)

                # Wrap long teacher names so they fit inside event boxes.
                wrapped_label = "\n".join(
                    textwrap.fill(line, width=14)
                    for line in ev["label"].split("\n")
                )

                txt = ax.text(
                    x0 + usable_width / 2,
                    y0 + box_height / 2,
                    wrapped_label,
                    ha="center",
                    va="center",
                    fontsize=fontsize,
                    fontweight="bold",
                    color="black",
                    clip_on=True,
                    bbox=dict(
                        facecolor="white",
                        edgecolor="none",
                        alpha=0.7,
                        boxstyle="round,pad=0.2",
                    ),
                )

                # Clip text so it does not spill outside its event rectangle.
                txt.set_clip_path(rect)

    # -----------------------------------------------------
    # Axis labels and formatting
    # -----------------------------------------------------
    ax.set_xticks(np.arange(n_hours) + 0.5)
    ax.set_xticklabels([f"{h}:00-{h + 1}:00" for h in HOURS], fontsize=10)

    ax.set_yticks(np.arange(n_days) + 0.5)
    ax.set_yticklabels(DAYS, fontsize=11)

    ax.tick_params(length=0)
    ax.set_title("University Timetable", fontsize=16, pad=15)

    for spine in ax.spines.values():
        spine.set_visible(False)

    # -----------------------------------------------------
    # Legend
    # -----------------------------------------------------
    # The legend explains the colour coding used for each module.
    legend_handles = [
        patches.Patch(facecolor=colour, edgecolor="black", label=module)
        for module, colour in module_colors.items()
    ]

    ax.legend(
        handles=legend_handles,
        title="Modules",
        loc="upper right",
        bbox_to_anchor=(1.01, 1),
        frameon=True,
    )

    plt.tight_layout()
    plt.show()


# =========================================================
# RUN FINAL TIMETABLE MODEL
# =========================================================
# The genetic algorithm is repeated until a feasible solution is found.
# The final solution is then visualised as a weekly timetable.

best_solution = None

while best_solution is None:
    best_solution = genetic_algorithm()

plot_timetable(best_solution, all_events, DAYS, HOURS)


# =========================================================
# TESTING
# =========================================================
# These automated tests check that the generated timetable satisfies the main
# hard constraints and structural requirements of the model.

from test_timetable import *

test_teacher_clash(all_events, best_solution, decode_slot)
test_group_clash(all_events, best_solution, decode_slot)
test_teacher_group_limit(all_events)
test_two_sessions_per_group(all_events)
test_sessions_within_working_hours(all_events, best_solution, event_duration, HOURS)
test_session_clash(all_events, best_solution, decode_slot)

print("All timetable tests passed.")

# Development note:
# Check that this code runs correctly when pushed to GitHub.
