import numpy as np
import random
import pandas as pd

# GLOBAL PROBLEM SETUP

# SECOND YEAR: SEMESTER 1

Staff = \
    {
        "COMP2399": ["Amy", "Paulie", "Mark", "Oana", "Noleen", "Norah", "Aryan", "Alice", "Ojas", "Meheraab"],
        # the first teacher in the list represents the lecturer
        "COMP2244": ["Massimiliano", "Adri", "Tom", "Haiko", "Alan", "Rob", "Naila"],
        "COMP2579": ["Natasha", "Sarah", "Max", "Andrei", "Gori", "Arshad", "Xeung", "Xi"],
    }

# GLOBAL VARIABLES (Add other global variables here)
LECTURE_GROUPS = 1
LAB_GROUPS = 3
TUTORIAL_GROUPS = 9
PERSONAL_TUTORIAL_GROUPS = 27


def create_groups(module_teachers, all_teachers, n_groups, teacher_load, max_groups):
    groups = {}

    group_id = 1

    # Assign module teachers first
    for teacher in module_teachers:
        while teacher_load[teacher] < max_groups and group_id <= n_groups:
            groups[f"Group{group_id}"] = {"teacher": teacher}
            teacher_load[teacher] += 1
            group_id += 1

    # If groups remain, use other teachers
    if group_id <= n_groups:
        other_teachers = [t for t in all_teachers if t not in module_teachers]

        for teacher in other_teachers:
            while teacher_load[teacher] < max_groups and group_id <= n_groups:
                groups[f"Group{group_id}"] = {"teacher": teacher}
                teacher_load[teacher] += 1
                group_id += 1

    # Check if enough teachers were available
    if group_id <= n_groups:
        raise ValueError("Not enough teacher capacity to cover all groups.")

    return groups


all_teachers = []

for teacher_list in Staff.values():
    all_teachers.extend(teacher_list)

#  loads for each teacher, to limit the amount of groups a teacher can have
#  each teacher will have at most the highest number in max group parameter while creating modules
teacher_load = {t: 0 for t in all_teachers}

Modules = {}

for module_code, teachers in Staff.items():
    Modules[module_code] = \
        {
            "Lecture": create_groups(teachers, all_teachers, LECTURE_GROUPS, teacher_load, 1),
            # a teacher will not necessariliy have equal to the max groups limit amount of groups
            # "Lab session": create_groups(teachers, all_teachers, LAB_GROUPS, teacher_load, 1),
            "tutorials": create_groups(teachers, all_teachers, TUTORIAL_GROUPS, teacher_load, 2),
            # "Personal Tutorials": create_groups(all_teachers, 27),
        }

# print(Modules)
# print(teacher_load)

# GLOBAL CONSTRAINTS
HARD_PENALTY = 10 ** 6
SOFT_SMALL = 10
SOFT_MEDIUM = 50
SOFT_LARGE = 200

# LECTURES

lecture_events = []

for module_name, module_data in Modules.items():
    for group_name, info in module_data["Lecture"].items():
        for session in range(2):  # two sessions per week
            lecture_events.append({
                "type": "lecture",
                "module": module_name,
                "teacher": info["teacher"]
            })

nL_lec = len(lecture_events)

# print(lecture_events)

# # LAB SESSION
#
# lab_events = []
#
# for module_name, module_data in Modules.items():
#     for group_name, info in module_data["Lab session"].items():
#
#         lab_group = int(group_name.replace("Group", ""))
#         for session in range(2):  # two sessions per week
#             lab_events.append({
#                 "type": "lab",
#                 "module": module_name,
#                 "lab_group": lab_group,
#                 "teacher": info["teacher"]
#             })
#
# nL_lab = len(lab_events)
#
# # print(lab_events)


# TUTORIALS

tutorial_events = []
tutorials_per_lab = TUTORIAL_GROUPS // LAB_GROUPS

for module_name, module_data in Modules.items():

    for group_name, info in module_data["tutorials"].items():

        tutorial_group = int(group_name.replace("Group", ""))

        lab_group = (tutorial_group - 1) // tutorials_per_lab + 1

        for session in range(2):  # two sessions per week
            tutorial_events.append({
                "type": "tutorial",
                "module": module_name,
                "lab_group": lab_group,
                "tutorial_group": tutorial_group,
                "teacher": info["teacher"]
            })

nL_tut = len(tutorial_events)

# print(tutorial_events)
# print(nL_tut)

# # PERSONAL TUTORIALS
#
# per_tut_events = []
#
# personal_groups_per_tutorial = 3
#
# for module_name, module_data in Modules.items():
#
#     n_groups = len(module_data["tutorials"])
#     tutorials_per_lab = n_groups // n_lab_groups
#
#     for group_name, info in module_data["Personal Tutorials"].items():
#
#         tutorial_group = int(group_name.replace("Group", ""))
#
#         lab_group = (tutorial_group - 1) // tutorials_per_lab + 1
#
#         for p in range(1, personal_groups_per_tutorial + 1):
#
#             personal_group = (tutorial_group - 1) * personal_groups_per_tutorial + p
#
#             per_tut_events.append({
#                 "type": "personal tutorial",
#                 "module": module_name,
#                 "lab_group": lab_group,
#                 "tutorial_group": tutorial_group,
#                 "personal_tutorial_group": personal_group,
#                 "teacher": info["teacher"]
#             })
#
# nL_per_tut = len(per_tut_events)
# print(per_tut_events)
#
# UNIFIED EVENT LIST
all_events = \
    (
            lecture_events
            + tutorial_events
            # + lab_events
        # + per_tut_events
    )

n_events = len(all_events)

# print(all_events)

# TIMESLOTS

event_duration = {
    "lecture": 2,
    "tutorial": 1,
    # "lab": 1,
    # "personal tutorial": 1
}

DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
HOURS = list(range(9, 18))  # 9 to 17

nG = len(DAYS) * len(HOURS)


# to later compute (day, hour)
def decode_slot(slot_index, event):
    duration = event_duration[event["type"]]

    day_index = slot_index // len(HOURS)
    hour_index = slot_index % len(HOURS)

    day = DAYS[day_index]
    start = HOURS[hour_index]

    return f"{day} {start}:00-{start + duration}:00"


# so that sessions with more than 1 hr slot get assigned correctly
def valid_slots(duration):
    slots = []

    for slot in range(nG):
        hour_index = slot % len(HOURS)

        if hour_index <= len(HOURS) - duration:
            slots.append(slot)

    return slots


valid_start_slots = {}

for e_type, duration in event_duration.items():
    valid_start_slots[e_type] = valid_slots(duration)

# GLOBAL CLASH MATRIX

C = np.zeros((n_events, n_events), dtype=np.int64)

for i in range(n_events):
    for j in range(n_events):
        if i == j:
            continue

        event_i = all_events[i]
        event_j = all_events[j]

        module_i = event_i["module"]
        module_j = event_j["module"]

        teacher_i = event_i["teacher"]
        teacher_j = event_j["teacher"]

        type_i = event_i["type"]
        type_j = event_j["type"]

        # # RULE 1: Labs vs Labs clashes
        # if type_i == "lab" and type_j == "lab":
        #     lab_i = event_i["lab_group"]
        #     lab_j = event_j["lab_group"]
        #
        #     # Same lab group cannot overlap
        #     if lab_i == lab_j:
        #         C[i][j] = HARD_PENALTY

        # RULE 2: Tutorial vs Tutorial clashes
        if type_i == "tutorial" and type_j == "tutorial":

            tut_i = event_i["tutorial_group"]
            tut_j = event_j["tutorial_group"]

            # Same tutorial group cannot overlap
            if tut_i == tut_j:
                C[i][j] = HARD_PENALTY

        # # RULE 3: Tutorial vs Lab clashes
        # if (type_i == "tutorial" and type_j == "lab") or (type_i == "lab" and type_j == "tutorial"):
        #
        #     # Identify tutorial and lab event
        #     if type_i == "tutorial":
        #         tut_event = event_i
        #         lab_event = event_j
        #     else:
        #         tut_event = event_j
        #         lab_event = event_i
        #
        #     tut_lab_group = tut_event["lab_group"]
        #     lab_group = lab_event["lab_group"]
        #
        #     # Clash only if same lab group
        #     if tut_lab_group == lab_group:
        #         C[i][j] = HARD_PENALTY

        # RULE 4: Same teacher cannot teach two events at the same time
        if teacher_i == teacher_j:
            C[i][j] = HARD_PENALTY

        # RULE 5: Lectures clash with everything
        if type_i == "lecture" or type_j == "lecture":
            C[i][j] = HARD_PENALTY

# print(C)

# TEACHER TIME PREFERENCES

teacher_time_preferences = {}

event_types = ["lecture", "lab", "tutorial", "personal tutorial"]

for teacher in all_teachers:
    teacher_time_preferences[teacher] = {}

    for e_type in event_types:
        teacher_time_preferences[teacher][e_type] = [0] * nG

# print(teacher_time_preferences)

# Soft rules
for slot in range(nG):
    day_index = slot // len(HOURS)
    hour_index = slot % len(HOURS)

    day = DAYS[day_index]
    hour = HOURS[hour_index]

    # Amy prefers lecture before 12
    if hour >= 12:
        teacher_time_preferences["Amy"]["lecture"][slot] = SOFT_SMALL

    # Amy prefers tutorials after 12
    if hour < 12:
        teacher_time_preferences["Amy"]["tutorial"][slot] = SOFT_SMALL

    # Natasha prefers morning lectures
    if hour >= 11:
        teacher_time_preferences["Natasha"]["lecture"][slot] = SOFT_SMALL

    # Sarah prefers no tutorials on THU
    if day == "THU":
        teacher_time_preferences["Sarah"]["tutorial"][slot] = SOFT_SMALL

# print(teacher_time_preferences)

# STUDENT TIME PREFERENCES

student_time_preferences = {}

# Students as one entity
student_time_preferences["ALL_STUDENTS"] = {}

for e_type in event_types:
    student_time_preferences["ALL_STUDENTS"][e_type] = [0] * nG

# print(student_time_preferences)

for slot in range(nG):
    day_index = slot // len(HOURS)
    hour_index = slot % len(HOURS)

    day = DAYS[day_index]
    hour = HOURS[hour_index]

    # Students prefer lectures/tutorial before 16:00
    if hour >= 16:
        student_time_preferences["ALL_STUDENTS"]["lecture"][slot] = SOFT_MEDIUM
        student_time_preferences["ALL_STUDENTS"]["tutorial"][slot] = SOFT_MEDIUM

    # Students prefer no tutorials on Fri
    if day == "FRI":
        student_time_preferences["ALL_STUDENTS"]["tutorial"][slot] = SOFT_MEDIUM

    # Students prefer afternoon lectures
    if hour > 15 or hour < 12:
        student_time_preferences["ALL_STUDENTS"]["lecture"][slot] = SOFT_MEDIUM


# print(student_time_preferences)


# GENETIC ALGORITHM

# CHROMOSOME (LIST OF SLOT INDICES)
# A chromosome: list of timeslot assignments for all the events

def random_timetable():
    timetable = []

    for event in all_events:
        e_type = event["type"]
        timetable.append(random.choice(valid_start_slots[e_type]))

    return timetable


# print(n_events)
# print(len(random_timetable()))
# print(random_timetable())

# FITNESS FUNCTION

# for sequential constraints

SEQUENTIAL_RULES = {
    ("lecture", "tutorial"): SOFT_LARGE
}

events_by_module_type = {}

for idx, event in enumerate(all_events):

    module = event["module"]
    e_type = event["type"]

    if module not in events_by_module_type:
        events_by_module_type[module] = {}

    events_by_module_type[module].setdefault(e_type, []).append(idx)

# for breaks constraints

SESSION_GAP_RULES = {
    "lecture": (1, SOFT_LARGE),  # 2 day gap between lecture sessions
    "tutorial": (3, SOFT_LARGE),  # 3 day gap between tutorial sessions
    # "lab": (1, SOFT_LARGE),
}

sessions_by_key = {}

for idx, event in enumerate(all_events):

    e_type = event["type"]
    module = event["module"]

    if e_type not in SESSION_GAP_RULES:
        continue

    # Define grouping key depending on session type
    if e_type == "lecture":
        key = (module, e_type)

    elif e_type == "tutorial":
        key = (module, e_type, event["tutorial_group"])

    # elif e_type == "lab":
    #     key = (module, e_type, event["lab_group"])

    # elif e_type == "personal tutorial":
    #     key = (module, e_type, event["personal_tutorial_group"])

    sessions_by_key.setdefault(key, []).append(idx)


def fitness(timetable):
    # Penalties separated by type

    hard_penalty = 0
    tutorial_soft = 0
    lecture_soft = 0
    # lab_soft = 0
    # personal_soft = 0

    # Clash
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

    # Time preferences
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

        # elif e_type == "lab":
        #     lab_soft += total_soft

        # elif e_type == "personal tutorial":
        #     personal_soft += total_soft

    # Sequential Constraints-modify it later
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

    # Break constraints between sessions of the same group and same module

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

                    if e_type == "lecture":
                        lecture_soft += penalty

                    elif e_type == "tutorial":
                        tutorial_soft += penalty

                    # elif e_type == "lab":
                    #     lab_soft += penalty

    return \
        (
            hard_penalty,
            lecture_soft,
            tutorial_soft,
            # lab_soft,
            # personal_soft
        )


# print(fitness(random_timetable()))


# GENETIC OPERATORS

# SELECTION (TOURNAMENT)

def select(population):
    a = random.choice(population)
    b = random.choice(population)
    return a if fitness(a) < fitness(b) else b


# CROSSOVER (modify it according to duration)

def crossover(p1, p2):
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:]


# MUTATION

def mutate(timetable, rate=0.1):
    for i in range(len(timetable)):
        if random.random() < rate:
            event_type = all_events[i]["type"]
            timetable[i] = random.choice(valid_start_slots[event_type])
    return timetable


def genetic_algorithm(generations=1001, population_size=50, elite_size=3, mutation_rate=0.1, stagnation_limit=50):

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

        if best_fit[0] == 0:
            feasible_solution = best
            print("\nFeasible timetable found!")
            break

        new_population = population[:elite_size]

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

    # Create population around feasible timetable
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

        if best_fit < fitness(best_solution):
            best_solution = best
            stagnant_generations = 0
        else:
            stagnant_generations += 1

        # Early stop if stagnated
        if stagnant_generations >= stagnation_limit:
            print(f"\nNo improvement for {stagnation_limit} generations. Stopping early.")
            break

        new_population = population[:elite_size]

        while len(new_population) < population_size:
            parent1 = select(population)
            parent2 = select(population)

            child = crossover(parent1, parent2)
            child = mutate(child, rate=mutation_rate)

            # keep only feasible children
            if fitness(child)[0] == 0:
                new_population.append(child)

        population = new_population

    return best_solution


# Format timetable neatly

def format_university_timetable(best_solution, all_events):

    DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
    HOURS = list(range(9, 18))

    # Create timetable grid
    timetable = {day: {hour: [] for hour in HOURS} for day in DAYS}

    for idx, slot in enumerate(best_solution):

        event = all_events[idx]
        duration = event_duration[event["type"]]

        day_index = slot // len(HOURS)
        hour_index = slot % len(HOURS)

        day = DAYS[day_index]
        start_hour = HOURS[hour_index]

        module = event["module"]
        teacher = event["teacher"]
        e_type = event["type"]

        if e_type == "lecture":
            group = "Lecture"
        else:
            group = f"Tut{event['tutorial_group']}"

        label = f"{module} {group} ({teacher})"

        # Fill each hour the event occupies
        for h in range(duration):
            timetable[day][start_hour + h].append(label)

    # Print table header
    header = ["Day"] + [f"{h}-{h+1}" for h in HOURS]
    print("\nUniversity Timetable:\n")
    print("{:<5}".format(header[0]), end=" ")

    for col in header[1:]:
        print("{:^25}".format(col), end=" ")
    print()

    # Print rows
    for day in DAYS:

        print("{:<5}".format(day), end=" ")

        for hour in HOURS:

            cell = "\n".join(timetable[day][hour]) if timetable[day][hour] else "-"

            print("{:^25}".format(cell), end=" ")

        print("\n")


# Run GA

best_solution = None

while best_solution is None:
    best_solution = genetic_algorithm()

format_university_timetable(best_solution, all_events)

# ====================== TESTING ======================

from test_timetable import *

test_teacher_clash(all_events, best_solution, decode_slot)
test_group_clash(all_events, best_solution, decode_slot)
test_teacher_group_limit(all_events)
test_two_sessions_per_group(all_events)
test_sessions_within_working_hours(all_events, best_solution, event_duration, HOURS)
test_session_clash(all_events, best_solution, decode_slot)

print("All timetable tests passed.")

# Bookmark:
# modify ga-analyse tt, format tt nicely-use the function created
# analyse the timetable
# add git.ignore
# create a testing code to analyse the timetable like it follows all scheduling constraints
# now assign  lab sessions, personal tutorials
# better the clash preferences that already exist so that it thinks abt all sessions
# modify sequential constraints to make one tutorial session happen after one lecture session
# once implemented for all sessions upload on a different branch so that you can later compare your this model (lexicographic) with future models you make better
# add breaks between sessions too in hours/days
