import numpy as np
import random
import pandas as pd

# GLOBAL PROBLEM SETUP

# SECOND YEAR: SEMESTER 1

Staff = \
    {
        "COMP2399": ["Amy", "Paulie", "Mark", "Sam", "Noleen"],  # the first teacher in the list represents the lecturer
        "COMP2244": ["Owen", "John", "Tom", "Haiko", "Alan", "Rob"],
        "COMP2579": ["Natasha", "Sarah", "Max", "Dibayan"],
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

# Separate loads for each teacher based on the session, to limit the amount of groups a teacher can have
lecture_load = {t: 0 for t in all_teachers}
tutorial_load = {t: 0 for t in all_teachers}

Modules = {}

for module_code, teachers in Staff.items():
    Modules[module_code] = \
        {
            "Lecture": create_groups(teachers, all_teachers, LECTURE_GROUPS, lecture_load, 1),
            # "Lab session": create_groups(teachers, 3),
            "tutorials": create_groups(teachers, all_teachers, TUTORIAL_GROUPS, tutorial_load, 2),
            # "Personal Tutorials": create_groups(all_teachers, 27),
        }

# print(Modules)

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
#
#         lab_events.append({
#             "type": "lab",
#             "module": module_name,
#             "lab_group": lab_group,
#             "teacher": info["teacher"]
#         })
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
all_events = (
        lecture_events
        # + lab_events
        + tutorial_events
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

        # # RULE 1: Labs cannot be parallel
        # if type_i == "lab" and type_j == "lab":
        #     C[i][j] = HARD_PENALTY

        # RULE 2: Tutorial clashes
        if type_i == "tutorial" and type_j == "tutorial":

            tut_i = event_i["tutorial_group"]
            tut_j = event_j["tutorial_group"]

            # Same tutorial group cannot overlap
            if tut_i == tut_j:
                C[i][j] = HARD_PENALTY
            else:
                C[i][j] = 0

        # RULE 3: Same teacher cannot teach two events at the same time
        if teacher_i == teacher_j:
            C[i][j] = HARD_PENALTY

        # RULE 4: Lectures clash with everything
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

    # Students prefer lectures/tutorial before 17:00
    if hour >= 17:
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

# FITNESS FUNCTION

# for sequential constraints

SEQUENTIAL_RULES = {
    ("lecture", "tutorial"): HARD_PENALTY
}

events_by_module_type = {}

for idx, event in enumerate(all_events):

    module = event["module"]
    e_type = event["type"]

    if module not in events_by_module_type:
        events_by_module_type[module] = {}

    events_by_module_type[module].setdefault(e_type, []).append(idx)

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
        #
        # elif e_type == "lab":
        #     lab_soft += total_soft
        #
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
                        hard_penalty += penalty

    # Bookmark: add breaks between each same tutorial
    # introduce breaks constraints

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

# # SELECTION (TOURNAMENT)
#
# def select(population):
#     a = random.choice(population)
#     b = random.choice(population)
#     return a if fitness(a) < fitness(b) else b
#
#
# # CROSSOVER
#
# def crossover(p1, p2):
#     point = random.randint(1, len(p1) - 1)
#     return p1[:point] + p2[point:]
#
#
# # MUTATION
#
# def mutate(timetable, rate=0.1):
#     for i in range(len(timetable)):
#         if random.random() < rate:
#             event_type = all_events[i]["type"]
#             timetable[i] = random.choice(valid_start_slots[event_type])
#     return timetable
#
#
# def genetic_algorithm(generations=1001, population_size=50, elite_size=2, mutation_rate=0.1):
#     # Initial population
#     population = [random_timetable() for _ in range(population_size)]
#
#     for gen in range(generations):
#         # Sort population in ascending order by fitness (lexicographic: hard, tutorial, lecture, lab, personal)
#         population.sort(key=fitness)
#
#         # Best individual this generation
#         best = population[0]
#         best_fit = fitness(best)
#
#         # Print best timetable
#         print(f"\nGeneration {gen:3d} | Fitness: {best_fit}")
#         for idx, slot_index in enumerate(best):
#             event = all_events[idx]
#             event_name = f"{event['module']} | {event['type']} | {event['group']} | {event['teacher']}"
#             print(f"{event_name:40s} -> {decode_slot(slot_index, event)}")
#
#         # Early stopping if no hard clashes
#         if best_fit[0] == 0:
#             print("\nNo hard clashes! Acceptable timetable found.")
#             return best
#
#         # Elitism: keep top individuals
#         new_population = population[:elite_size]
#
#         # Generate rest of new population
#         while len(new_population) < population_size:
#             parent1 = select(population)
#             parent2 = select(population)
#             child = crossover(parent1, parent2)
#             child = mutate(child, rate=mutation_rate)
#             new_population.append(child)
#
#         # Replace old population
#         population = new_population
#
#
# # # Format timetable neatly
# #
# # # Show all columns
# # pd.set_option("display.max_columns", None)
# #
# # # Show all rows
# # pd.set_option("display.max_rows", None)
# #
# # # # widen display width so it fits
# # # pd.set_option("display.width", 200)
# #
# # def print_timetable(best, all_events, decode_slot):
# #     rows = []
# #
# #     # Build row data
# #     for idx, slot_index in enumerate(best):
# #         event = all_events[idx]
# #         slot = decode_slot(slot_index)  # e.g. "MON 11:00-12:00"
# #         day, time = slot.split()
# #
# #         session_text = f"{event['module']} {event['group']}\n{event['teacher']}"
# #
# #         rows.append({
# #             "Day": day,
# #             "Time": time,
# #             "Session": session_text
# #         })
# #
# #     df = pd.DataFrame(rows)
# #
# #     # Combine sessions that share same Day + Time
# #     df = (
# #         df.groupby(["Day", "Time"])["Session"]
# #         .apply(lambda x: "\n\n".join(x))
# #         .reset_index()
# #     )
# #
# #     # Create pivot table
# #     timetable = df.pivot(index="Day", columns="Time", values="Session")
# #
# #     # Sort days properly
# #     day_order = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
# #     timetable = timetable.reindex(
# #         sorted(timetable.index, key=lambda d: day_order.index(d))
# #     )
# #
# #     # Sort times chronologically
# #     timetable = timetable.reindex(
# #         sorted(timetable.columns, key=lambda t: int(t.split(":")[0])),
# #         axis=1
# #     )
# #
# #     # Replace NaN with empty cell
# #     timetable = timetable.fillna("-")
# #
# #     print("\nTimetable:\n")
# #     print(timetable)
#
#
# # Run GA
# best_solution = genetic_algorithm()
# # print_timetable(best_solution, all_events, decode_slot)
# # Print final timetable once (temporary)
# print("\nFinal timetable:\n")
# for idx, slot_index in enumerate(best_solution):
#     event = all_events[idx]
#     print(event, "->", decode_slot(slot_index))
#
# # ====================== TESTING ======================
#
# # from test_timetable import *
# #
# # test_teacher_clash(all_events, best_solution, decode_slot)
# # test_group_clash(all_events, best_solution, decode_slot)
# # test_teacher_group_limit(all_events)
# # test_two_sessions_per_group(all_events) # Only for tutorials
# #
# # print("All timetable tests passed.")

# Bookmark:
# add git.ignore
# create a testing code to analyse the timetable like it follows all scheduling constraints (lectures, labs, PT)
# now assign lectures, lab sessions, personal tutorials
# better the clash preferences that already exist so that it thinks abt all sessions
# modify sequential constraints to make one tutorial session happen after one lecture session
# once implemented for all sessions upload on a different branch so that you can later compare your this model (lexicographic) with future models you make better
# add breaks between sessions too