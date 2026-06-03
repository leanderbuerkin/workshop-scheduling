# Workshop Scheduling

This repository provides a branch-and-bound depth-first-search approach
to assign multiple Workshops to time tables according to the preferences given.

## Input Data

The input is a csv-file with one columnn for each workshop and one row for each participant.
In the rows, each participant can distibute any (positive) amount of preference points.

## Logic

### Preprocessing

In the preprocessing, the rows are normalized (each cell divided by the sum of the whole row).
The columns are sorted by their sum.

### Generating Time Slots

First, pareto-optimal time slots are created,
that means that no time_slot that contains a subset of the workshops of this time slot has a higher score.

#### Time Slot Scores

Since the workshops in one time slot take place at the same time,
only preferences of those participants that want to participate in exactly one of those workshops are counted.

That's why there is also no maximum amount of workshops at the same time needed.

### Generating Time Tables

The time tables are generated in a tree-like fashion:
Each time table stores which other time slots it accepts,
accepted are those that only contain workshops not yet present in the time table.

Then the time tables are expanded sorted by the upper bound of their score:
The current score + the scores of the best accepted time slots missing to complete time table.

When there are the maximum amount of time tables with the target length,
all time tables with an upper score bellow the worst time table at target length are deleted.
