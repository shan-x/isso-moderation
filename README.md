# isso-moderation

Provide a minimalist web interface for Isso.
Uses Python3 + Flask.

## Configuration
In `app.py`, indicate the path to the database and the credentials for the access.

## Security
No security at all. Beware of SQL ijections -- even if normally, only the one with the credentials can send parameters.

## Functionnalities
### v O.1
  - basic auth with HTTP
  - search comments by author, email, IP or  thread title
  - delete selectionned comments
