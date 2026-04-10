import numpy as np
import random

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
# Lecture->Labs->Tut->PT
# Talk about the hierarchy
LECTURE_GROUPS = 1
LAB_GROUPS = 2
TUTORIAL_GROUPS = 5
PERSONAL_TUTORIAL_GROUPS = 14

PERSONAL_TUTORIAL_MODULE = "COMP2399"  # a dummy module, to create one set of PT's
NOT_LAB_MODULE = "COMP2579"

def validate_group_hierarchy():
    if LECTURE_GROUPS < 1:
        raise ValueError("LECTURE_GROUPS must be at least 1.")

    if LAB_GROUPS < LECTURE_GROUPS:
        raise ValueError(
            "Invalid hierarchy: LAB_GROUPS must be greater than LECTURE_GROUPS.")

    if TUTORIAL_GROUPS < LAB_GROUPS:
        raise ValueError(
            "Invalid hierarchy: TUTORIAL_GROUPS must be greater than LAB_GROUPS.")

    if PERSONAL_TUTORIAL_GROUPS < TUTORIAL_GROUPS:
        raise ValueError(
            "Invalid hierarchy: PERSONAL_TUTORIAL_GROUPS must be greater than TUTORIAL_GROUPS."
        )


validate_group_hierarchy()


def create_groups(module_teachers, all_teachers, n_groups, type_teacher_load, max_groups_per_type, overall_teacher_load,
                  max_groups_overall, forced_teacher=None):
    groups = {}
    group_id = 1

    def can_assign(teacher):
        return (
                type_teacher_load[teacher] < max_groups_per_type
                and overall_teacher_load[teacher] < max_groups_overall
        )

    def assign_teacher(teacher, group_id):
        groups[f"Group{group_id}"] = {"teacher": teacher}
        type_teacher_load[teacher] += 1
        overall_teacher_load[teacher] += 1

    # force specific teacher into Group1 first
    if forced_teacher is not None:
        if not can_assign(forced_teacher):
            raise ValueError(
                f"Forced teacher {forced_teacher} has no remaining capacity."
            )

        assign_teacher(forced_teacher, group_id)
        group_id += 1

    # assign module teachers first
    for teacher in module_teachers:
        while can_assign(teacher) and group_id <= n_groups:
            assign_teacher(teacher, group_id)
            group_id += 1

    # if groups remain, use other teachers
    if group_id <= n_groups:
        other_teachers = [t for t in all_teachers if t not in module_teachers]

        for teacher in other_teachers:
            while can_assign(teacher) and group_id <= n_groups:
                assign_teacher(teacher, group_id)
                group_id += 1

    if group_id <= n_groups:
        raise ValueError("Not enough teacher capacity to cover all groups.")

    return groups


all_teachers = []

for teacher_list in Staff.values():
    all_teachers.extend(teacher_list)

all_teachers = list(dict.fromkeys(all_teachers))  # remove duplicates safely

#  loads for each teacher, to limit the amount of groups a teacher can have
lecture_teacher_load = {t: 0 for t in all_teachers}
lab_teacher_load = {t: 0 for t in all_teachers}
tutorial_teacher_load = {t: 0 for t in all_teachers}
personal_tutorial_teacher_load = {t: 0 for t in all_teachers}

# overall load across all group assignments
overall_teacher_load = {t: 0 for t in all_teachers}

MAX_GROUPS_OVERALL = 2  # overall teacher limit

Modules = {}

for module_code, teachers in Staff.items():
    lecturer = teachers[0]

    Modules[module_code] = {}

    Modules[module_code]["Lecture"] = create_groups(
            teachers,
            all_teachers,
            LECTURE_GROUPS,
            lecture_teacher_load,
            1,
            overall_teacher_load,
            MAX_GROUPS_OVERALL,
            forced_teacher=lecturer
        )

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
            MAX_GROUPS_OVERALL
        )

    Modules[module_code]["tutorials"] = create_groups(
            teachers,
            all_teachers,
            TUTORIAL_GROUPS,
            tutorial_teacher_load,
            2,
            overall_teacher_load,
            MAX_GROUPS_OVERALL
        )

    if module_code == PERSONAL_TUTORIAL_MODULE:
        Modules[module_code]["Personal Tutorials"] = create_groups(
            teachers,
            all_teachers,
            PERSONAL_TUTORIAL_GROUPS,
            personal_tutorial_teacher_load,
            1,
            overall_teacher_load,
            MAX_GROUPS_OVERALL
        )
    else:
        Modules[module_code]["Personal Tutorials"] = {}

# print(Modules)
# print(lecture_teacher_load)
# print(lab_teacher_load)
# print(tutorial_teacher_load)
# print(personal_tutorial_teacher_load)
# print(overall_teacher_load)

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

# LAB SESSION

lab_events = []

for module_name, module_data in Modules.items():
    for group_name, info in module_data["Lab session"].items():

        lab_group = int(group_name.replace("Group", ""))
        for session in range(2):  # two sessions per week
            lab_events.append({
                "type": "lab",
                "module": module_name,
                "lab_group": lab_group,
                "teacher": info["teacher"]
            })

nL_lab = len(lab_events)

# print(lab_events)


# TUTORIALS

tutorial_events = []

for module_name, module_data in Modules.items():

    for group_name, info in module_data["tutorials"].items():

        tutorial_group = int(group_name.replace("Group", ""))

        lab_group = ((tutorial_group - 1) * LAB_GROUPS) // TUTORIAL_GROUPS + 1

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

# PERSONAL TUTORIALS

per_tut_events = []

for module_name, module_data in Modules.items():

    for group_name, info in module_data["Personal Tutorials"].items():

        personal_tutorial_group = int(group_name.replace("Group", ""))

        tutorial_group = ((personal_tutorial_group - 1) * TUTORIAL_GROUPS) // PERSONAL_TUTORIAL_GROUPS + 1

        lab_group = ((tutorial_group - 1) * LAB_GROUPS) // TUTORIAL_GROUPS + 1

        for session in range(1):  # once per week
            per_tut_events.append({
                "type": "personal tutorial",
                "module": module_name,  # dummy module
                "lab_group": lab_group,
                "tutorial_group": tutorial_group,
                "personal_tutorial_group": personal_tutorial_group,
                "teacher": info["teacher"]
            })

nL_per_tut = len(per_tut_events)

# print(per_tut_events)
# print(nL_per_tut)

# UNIFIED EVENT LIST
all_events = \
    (
            lecture_events
            + tutorial_events
            + lab_events
            + per_tut_events
    )

n_events = len(all_events)

# print(all_events)

# TIMESLOTS

event_duration = {
    "lecture": 2,
    "tutorial": 1,
    "lab": 1,
    "personal tutorial": 1
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

        # RULE 1: Labs vs Labs clashes
        if type_i == "lab" and type_j == "lab":
            lab_i = event_i["lab_group"]
            lab_j = event_j["lab_group"]

            # Same lab group cannot overlap
            if lab_i == lab_j:
                C[i][j] = HARD_PENALTY

        # RULE 2: Tutorial vs Tutorial clashes
        if type_i == "tutorial" and type_j == "tutorial":

            tut_i = event_i["tutorial_group"]
            tut_j = event_j["tutorial_group"]

            # Same tutorial group cannot overlap
            if tut_i == tut_j:
                C[i][j] = HARD_PENALTY

        # RULE 3: Tutorial vs Lab clashes
        if (type_i == "tutorial" and type_j == "lab") or (type_i == "lab" and type_j == "tutorial"):

            # Identify tutorial and lab event
            if type_i == "tutorial":
                tut_event = event_i
                lab_event = event_j
            else:
                tut_event = event_j
                lab_event = event_i

            tut_lab_group = tut_event["lab_group"]
            lab_group = lab_event["lab_group"]

            # Clash only if same lab group
            if tut_lab_group == lab_group:
                C[i][j] = HARD_PENALTY

        # RULE 4: Personal Tutorial vs Lab clashes
        if (type_i == "personal tutorial" and type_j == "lab") or (type_i == "lab" and type_j == "personal tutorial"):

            # Identify personal tutorial and lab event
            if type_i == "personal tutorial":
                per_tut_event = event_i
                lab_event = event_j
            else:
                per_tut_event = event_j
                lab_event = event_i

            per_tut_lab_group = per_tut_event["lab_group"]
            lab_group = lab_event["lab_group"]

            # Clash only if same lab group
            if per_tut_lab_group == lab_group:
                C[i][j] = HARD_PENALTY

        # RULE 5: Personal Tutorial vs Tutorial clashes
        if (type_i == "personal tutorial" and type_j == "tutorial") or (
                type_i == "tutorial" and type_j == "personal tutorial"):

            # Identify personal tutorial and tutorial event
            if type_i == "personal tutorial":
                per_tut_event = event_i
                tut_event = event_j
            else:
                per_tut_event = event_j
                tut_event = event_i

            per_tut_tut_group = per_tut_event["tutorial_group"]
            tut_group = tut_event["tutorial_group"]

            # Clash only if same tutorial group
            if per_tut_tut_group == tut_group:
                C[i][j] = HARD_PENALTY

        # RULE 6: Same teacher cannot teach two events at the same time
        if teacher_i == teacher_j:
            C[i][j] = HARD_PENALTY

        # RULE 7: Lectures clash with everything
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
    "lecture": (1, HARD_PENALTY),  # 1 day gap between lecture sessions
    "tutorial": (2, HARD_PENALTY),  # 2 day gap between tutorial sessions
    "lab": (1, HARD_PENALTY),
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

    elif e_type == "lab":
        key = (module, e_type, event["lab_group"])

    sessions_by_key.setdefault(key, []).append(idx)


def fitness(timetable):
    # Penalties separated by type

    hard_penalty = 0
    tutorial_soft = 0
    lecture_soft = 0
    lab_soft = 0
    personal_soft = 0

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

        elif e_type == "lab":
            lab_soft += total_soft

        elif e_type == "personal tutorial":
            personal_soft += total_soft

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
                    hard_penalty += penalty

    return \
        (
            hard_penalty,
            lecture_soft,
            tutorial_soft,
            lab_soft,
            personal_soft
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


def genetic_algorithm(generations=1001, population_size=50, elite_size=3, mutation_rate=0.1, stagnation_limit=100):
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

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


def plot_timetable(best_solution, all_events, DAYS, HOURS):
    fig, ax = plt.subplots(figsize=(22, 10))

    n_days = len(DAYS)
    n_hours = len(HOURS)

    # =========================================================
    # STORE EVENTS BY EXACT CELL
    # =========================================================
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

        if e_type == "lecture":
            label = f"{module}\nLecture\n{teacher}"
        elif e_type == "tutorial":
            label = f"{module}\nTutorial {event['tutorial_group']}\nLab Group {event['lab_group']}\n{teacher}"
        elif e_type == "lab":
            label = f"{module}\nLab {event['lab_group']}\n{teacher}"
        elif e_type == "personal tutorial":
            label = f"Personal Tutorial {event['personal_tutorial_group']}\nTutorial Group {event['tutorial_group']}\nLab Group {event['lab_group']}\n{teacher}"

        for h in range(duration):
            timetable[day][HOURS[hour_index + h]].append({
                "module": module,
                "label": label
            })

    # =========================================================
    # COLOURS
    # =========================================================
    module_colors = {
        "COMP2399": "#8dd3c7",
        "COMP2244": "#bebada",
        "COMP2579": "#fb8072"
    }

    # =========================================================
    # DRAW GRID
    # =========================================================
    ax.set_xlim(0, n_hours)
    ax.set_ylim(0, n_days)
    ax.invert_yaxis()

    for x in range(n_hours + 1):
        ax.axvline(x, color="black", linewidth=1)

    for y in range(n_days + 1):
        ax.axhline(y, color="black", linewidth=1)

    # =========================================================
    # DRAW EVENT BOXES ONLY
    # =========================================================
    margin_x = 0.04
    margin_y = 0.04
    internal_gap = 0.03

    # Store rectangles and their labels for hover
    rect_info = []

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
                    linewidth=0.8
                )
                ax.add_patch(rect)

                rect_info.append({
                    "rect": rect,
                    "label": ev["label"]
                })

    # =========================================================
    # HOVER ANNOTATION
    # =========================================================
    annot = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(15, 15),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="black", lw=1),
        arrowprops=dict(arrowstyle="->"),
        fontsize=10
    )
    annot.set_visible(False)

    def update_annot(rect, label, event):
        annot.xy = (event.xdata, event.ydata)
        annot.set_text(label)
        annot.set_visible(True)

    def hover(event):
        if event.inaxes != ax:
            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return

        for info in rect_info:
            rect = info["rect"]
            contains, _ = rect.contains(event)

            if contains:
                update_annot(rect, info["label"], event)
                fig.canvas.draw_idle()
                return

        if annot.get_visible():
            annot.set_visible(False)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)

    # =========================================================
    # AXIS LABELS
    # =========================================================
    ax.set_xticks(np.arange(n_hours) + 0.5)
    ax.set_xticklabels([f"{h}:00-{h + 1}:00" for h in HOURS], fontsize=10)

    ax.set_yticks(np.arange(n_days) + 0.5)
    ax.set_yticklabels(DAYS, fontsize=11)

    ax.tick_params(length=0)
    ax.set_title("University Timetable", fontsize=16, pad=15)

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    plt.show()


# Run GA

best_solution = None

while best_solution is None:
    best_solution = genetic_algorithm()

plot_timetable(best_solution, all_events, DAYS, HOURS)

for idx, slot_index in enumerate(best_solution):
    event = all_events[idx]
    module = event["module"]
    e_type = event["type"]
    teacher = event["teacher"]

    # Build group label depending on event type
    group_info = ""
    if e_type == "tutorial":
        group_info = f"Tut{event['tutorial_group']}"

    elif e_type == "lecture":
        group_info = "Lecture"

    elif e_type == "lab":
        group_info = f"Lab{event['lab_group']}"

    elif e_type == "personal tutorial":
        group_info = f"PT{event['personal_tutorial_group']}"

    event_name = f"{module} | {e_type} | {group_info} | {teacher}"
    print(f"{event_name:60s} -> {decode_slot(slot_index, event)}")

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
# modify ga-commit using some other name than hall of fame, to hide
# format tt nicely-with legends and different colours for each session type
# add git.ignore
# create a testing code to analyse the timetable like it follows all scheduling constraints
# better the clash preferences that already exist so that it thinks abt all sessions
# modify sequential constraints to make one tutorial session happen after one lecture session
# once implemented for all sessions upload on a different branch so that you can later compare your this model (lexicographic) with future models you make better
# add breaks between sessions too in hours/days
# remove extra info like lab groups or tutorial groups for other session from the popup
