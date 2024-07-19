

# Basic Architecture

We provide an API on stdin/stdout, expecting JSON, which can 

1. start tabs
2. start jobs on tabs

```
                                             all within one c++ executable
                                  -----------------------------------------------------
Plotly <-- JSON via STDIN/OUT --> [ kaleido <-- SimpleDevToolsClient --> Browser/Tabs ]
```

There are three parts:

1. `kaleido_main()`, which is responsible for inits boilerplate.
2. `Kaleido`, which sits between the user and Dispatch handling IO + some init.
3. `Dispatch`, which manages jobs and tabs.

# Concurency

*About Chromium's Model:*

Chromium uses callbacks and allows posting tasks to protothreads (`Sequence`s).
You can start your own sequences with various `TaskTraits`- pooled, parallel, ordered, etc.
Callbacks registered from `Sequence`s are perilous (point A), and limited tools are provided to
ensure they pass chromium's own race condition checks. `BindPostTask` doesn't always work.
Maybe try again but BindPostTask a non nestable task? Maybe never use chromium again.

Chromium highly discourages use of concurrency primitives (spinlocks, mutexes, etc).
It provides no safe messaging interface between tasks or sequences (like
Go's `chan<-`).

Without the above, memory must be handled from tasks posted to an `OrderedSequence`.
Callback's cannot be registered easily from an `OrderedSequence` (point A).
Combined **you cannot access stateful memory from callbacks.**

## How it is solved:

### Output to User

Requirement: Output to user cannot be mixed- messages must be whole. 

Therefore: All complete messages are tasks posted to a `SequencedTaskRunner` (`output_sequence`).

Rules: Such a task can be posted from anywhere.

### Input from User

The input listener is started in a parallel threadpool. Only one input listener runs,
and it must call itself to restart, ensuring order.

### SimpleDevToolsClient Tab Comms

DevTools Protocol uses message/session id labels, internally managed by `SimpleDevToolsClient`.
You register callbacks w/ your requests. Very NodeJS like, no async/await available.

## Tab Dispatch

`Dispatch` sends jobs to tabs as tabs free up, using queues to manage.
Most of `SimpleDevToolsClient` cannot be executed on a sequence (sequences 
registering callbacks makes Chromium angry).
So while most of `Dispatch`'s methods are a chain of callbacks, the last step in every
chain, which registers no callbacks, will post a task to a sequence (`job_line`),
who will make the actually memory modification in an atomic way relave to other
memory operations.

