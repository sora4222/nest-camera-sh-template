# Glossary

Words used in code, docs and commits. A new app adds its own words here (for example what its Subject is).

## Watching

**Subject**:
The thing the camera watches for: a pet, a person, a ball, what is on a screen.
_Avoid_: target, object

**Frame**:
One picture from the camera.
_Avoid_: image, snapshot

**Subject Action**:
What the Subject is doing, such as "at the desk" or "on Instagram".
_Avoid_: activity, behaviour

**Model**:
Anything that reads a Frame and gives values back, such as an ONNX network. An app can have as many as it wants; docs call them Model X, Model Y.
_Avoid_: detector, classifier (a Model may fill these roles, but the developer decides)

**Model Output**:
Everything the Models gave back for one Frame. A later Model can read what earlier ones gave.
_Avoid_: scene, findings, results

**State**:
The condition the app is in now. It decides which logic and Models run next.
_Avoid_: mode, status

**Event**:
Something worth logging and maybe announcing.

## Telling people

**Listener**:
A person who may hear Announcements.

**Speaker**:
A Google Home or Alexa device that can say a message out loud.

**Announcement**:
A message a Speaker says about an Event.

**Urgency**:
How important an Announcement is: Info, Normal or Urgent. Never spoken aloud.

**Quiet Hours**:
A repeating time when Announcements are held back. There can be many.

**Do Not Disturb**:
A one-off quiet time, switched on now until a set end time.
