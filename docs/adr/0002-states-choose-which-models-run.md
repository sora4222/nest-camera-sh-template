# The State chooses which Models run

The app is a state machine. The current State says which Models run (and how often, with `every_frame`); the Model Output then decides the next State and any Events. There is no fixed pipeline and no built-in Visit: ideas like the cat app's Visit and its Result model are built as States by the developer. This keeps slow Models from running when they are not needed, and keeps one app's ideas out of the template.

## Considered Options

- **Fixed pipeline with `only_when` rules per Model**: simpler for one Model, but the rules spread across config and get hard to follow with many Models.
- **Built-in Visit pattern**: fits the cat app, but most new apps (screens, desks, balls) do not have Visits.
