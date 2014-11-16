#
# Regular cron jobs for the j1708-drivers package
#
0 4	* * *	root	[ -x /usr/bin/j1708-drivers_maintenance ] && /usr/bin/j1708-drivers_maintenance
