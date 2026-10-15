# A plain template copy, not a shared library

New apps are made from this GitHub template and renamed with `make init NAME=...`. They do not depend on a shared package with the camera, speaker and Alexa plumbing. One copy is simple to read and change, and needs no package releases. The cost: fixes made here or in an app (such as the cat app this came from) do not flow to the others; they are copied by hand.

## Considered Options

- **Shared library plus a thin template**: fixes reach every app, but two repos to release and keep in step.
- **Copier template**: can pull later template fixes, but the template itself is Jinja files that cannot run or be tested as they are.
