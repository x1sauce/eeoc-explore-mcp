# Data access

The tools read an immutable snapshot of published EEOC aggregate statistics. Inputs select a metric, geography and fiscal years. Source URLs are returned as citations. Tool handlers do not fetch caller-supplied URLs or connect to private databases. Blank and suppressed counts retain their distinct status.

The default transport is local stdio. Hosting the HTTP version involves separate environment-specific access and deployment decisions.
