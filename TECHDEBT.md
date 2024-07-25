#

These are ordered by how they should be done.

## Concurrency
(Chromium's concurrency model is inferior to golangs.)

There are tiny race conditions in cornercases that will prompt chrome to terminate with a segfault or a dangling pointer warning,
they are unlikely and they occur only during destruction. To solve them, the code must be reorganized:

The job_line will be marked as non-interruptable during shutdown. To be fair, it will even CALL shutdown and provide an escape for all tasks if it does, effectively marking itself as dead.

Tabs can only be created on job_line, and it must sort it immeditately (ie same task, before calling others) into a queue so that if the next task is the shutdown process, job_line will see it in one of the queues and destroy it. That means a sort_both task to check both queues and see if a tab or job should be matched. Of course, if shut down is called, both the create_tab process and the sort_both will bail early if a previous job_line task marked the job_line tasks as EOL.

Active_jobs, (idle) tabs, and (idle) jobs queues and maps must be added to and removed from only by job_line.
However, active_jobs are effectively passed by job_line to browser_sequence which can then pass it back to job_line. Returned jobs are always destroyed, failed or not, and tabs are placed back into an idle queue (or resorted with new job immediately).
job_line can _inform_ browser_sequence that all active_jobs are to be cancelled. The next browser_sequence task that uses that job will cancel the tab for the browserline and can even destroy the job! If the empty pointer is left in active_jobs, it doesn't matter, no one will look, nobody complains if empty null-set pointers go down with the program.

In summary: job_line should tell itself not to partition any new tabs or new jobs, and to cancel early all requests as such. It should go trhough all idle tabs and ask the browser to destroy them. It can destroy all idle jobs. It should go through all the active jobs and ask the browser to destroy them.

Active_jobs can be read by the browser task group on browser_sequence that is started and finished by job_line (and the tab closed and job marked as dead. A request by job_line for browser_task might be out of order, and browser_tab should mark it dead and then allow its next in-order task to actually pass it back to job_line to be fully destroyed, and NOT call its next in-order task. Once it passes an active job back to the job_line, it should not access it again. The job_line will remove that job and tab from active_jobs and call any one of it's self-owned sort methods, unless it sees it was marked as dead in which case it will simply dispose of it.

If job_line is satisfied that all active tasks are eliminated and all idle_tabs are elimninate, it can call browser shutdown. That means on shutdown, it must count the number of active jobs, and then as they are passed back, kill it each one, and when the counter is reduced, shutdown.
## Scopes

Scopes in general is heavily overengineered (while the the tab driver is not). There is no need for having other consumers write js, py, and c++ to create a scope. A scope should simple by a folder named "myScope" with an index.html which functions as a "template" page for the visualization software, and then a "myScope.js" which receives arguments from python (through c++ or not in our new architecutre), and executes the myScope.js script on top fo the myScope/index.html template page. Can pass the desired download directory and no need to pass the raw data back to json as well.

Other users will NOT send us pull requests to add scopes to our base repo. They will import kaleido as a dependency, and they will initialize a class w/ a path to their myScope.js and template page. They will wrap it in a function for their library and our class will start the chromium process navigating to their index.html, and then their function will cause kaleido to execute the myScope.js script and pass whatever arguments it needs to it.

## Messaging consistency

There is currently an old mode, the original architecture had IPC via commandline options AND by json messages. No need, do all through JSON, only works if the above is achieved.

## Naming of variables

I have several id variables (job id, message id) and message id is just called id. Change it to message id.

## Class Organization (and .h/.cc file)

In general, the scopes or ANY c++ (whats not eliminated by techdebt earlier executed), needs to have its DECLARATIONS in .h files, its DEFINITIONS in .cc files, anything else makes the linker break. (inline in .h is ok).

## Exit

We shoudl catch Ctl+C signals and send ourselves the end stdin signal in return, but only one time! and that would allow users who ctl+c to try a graceful shutdown, but would termiante come hell or highwater if double Ctl+C is sent.
