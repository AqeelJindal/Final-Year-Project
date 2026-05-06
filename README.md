GENETIC ALGORITHM UNIVERSITY TIMETABLING SYSTEM
-----------------------------------------------

Custom university timetabling system in Python using a genetic algorithm to generate
a feasible weekly timetable while also improving staff and student preferences.

This project implements a simplified Year 2 Semester 1 Computer Science timetable.
The system models lectures, labs, tutorials and personal tutorials as timetable events,
then assigns each event to a weekly time slot using a genetic algorithm. Hard constraints
are used to prevent invalid timetables, such as teacher clashes, group clashes and
sessions outside working hours. Soft constraints are used to improve timetable quality,
including staff time preferences, student preferences and sequencing between lectures
and tutorials.

The genetic algorithm uses a two-phase approach. The first phase searches for a feasible
timetable with no hard-constraint violations. Once feasibility is achieved, the second
phase optimises the timetable by reducing soft-constraint penalties while keeping the
solution feasible.

FEATURES
--------

- Genetic algorithm for automated university timetable generation
- Two-phase optimisation: feasibility first, then soft-preference improvement
- Lexicographic fitness function separating hard and soft penalties
- Support for lectures, labs, tutorials and personal tutorials
- Teaching group hierarchy linking lectures, lab groups, tutorial groups and personal tutorial groups
- Teacher load limits across different session types
- Hard constraints for teacher clashes, group clashes and session timing
- Soft constraints for staff preferences, student preferences and lecture-tutorial sequencing
- Visual timetable output using Matplotlib
- Automated test suite to validate the final timetable

TECHNOLOGIES
------------

- Python
- NumPy
- Matplotlib
- Randomised genetic algorithm operators
- Automated testing with assertion-based validation functions

PROJECT STRUCTURE
-----------------

ga.py
    Main timetable generation program. This file defines the timetable data,
    creates teaching events, builds the clash matrix, runs the genetic algorithm
    and plots the final timetable.

test_timetable.py
    Validation test file. This checks that the final timetable satisfies the main
    hard constraints, including teacher clashes, group clashes, session counts,
    working hours and hierarchy-based session clashes.

HOW IT WORKS
------------

1. The timetable problem is defined using modules, staff, teaching groups and session types.
2. Events are generated for lectures, labs, tutorials and personal tutorials.
3. A clash matrix is created to store hard-constraint relationships between events.
4. A chromosome represents a timetable as a list of time-slot assignments.
5. The genetic algorithm generates and evolves candidate timetables.
6. Phase 1 searches for a timetable with zero hard penalties.
7. Phase 2 improves the feasible timetable by reducing soft penalties.
8. The final timetable is displayed as a colour-coded weekly grid.
9. Automated tests are run to confirm that the timetable satisfies key constraints.

CONSTRAINTS
-----------

Hard constraints include:

- A teacher cannot teach two events at the same time
- Lectures cannot clash with any other teaching session
- Sessions for the same tutorial group cannot overlap
- Sessions for the same lab group cannot overlap
- Tutorials cannot clash with labs from the same lab group
- Personal tutorials cannot clash with related tutorials or labs
- Sessions must remain within working hours
- Repeated sessions must be spread across the week

Soft constraints include:

- Staff time preferences
- Student time preferences
- Avoiding tutorials on less preferred days
- Avoiding late lectures and tutorials
- Scheduling lectures before tutorials where possible

RUNNING THE PROJECT
-------------------

Install the required Python libraries:

    pip install numpy matplotlib

Run the main timetable program:

    python ga.py

The program will search for a feasible timetable, optimise the soft penalties,
display the final timetable visually, and then run the validation tests.

LEARNING OUTCOMES
-----------------

This project demonstrates practical understanding of:

- Genetic algorithms and evolutionary optimisation
- Constraint-based university timetabling
- Hard and soft constraint modelling
- Lexicographic multi-objective fitness evaluation
- Timetable representation using chromosomes
- Clash matrix construction
- Automated validation testing
- Visualisation of timetable outputs in Python
```
