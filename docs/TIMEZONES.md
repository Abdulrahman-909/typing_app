# Days, goals and streaks
Store timestamps in UTC. On result insertion, compute local_date from the profile's IANA timezone; that date never changes later. The first result on a date snapshots that date's goal in goal_minutes; later results use the same threshold. Historical days use their saved threshold, so changing the current goal does not erase past streaks.

A streak is consecutive dates reaching the minutes threshold. An unfinished current day does not break yesterday's streak. DST changes clock duration but not the calendar-date rule. Changing timezone affects only future records. Returning to the same local date continues that date's existing record totals.

Desktop profiles currently default to Asia/Kabul, matching this project's intended classroom context; automatic system-zone detection and editable local-zone UI remain to be added. Current web profiles can choose any available IANA zone.
