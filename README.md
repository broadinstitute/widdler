# widdler

## Introduction

Widdler is a command-line tool for executing WDL workflows on Cromwell servers.
Features include:

* Workflow execution: Execute a workflow on a specified Cromwell server.
* Workflow queries: Get the status, metadata, or logs for a specific workflow.
* Workflow monitoring: Monitor a specific workflow or set of user-specific workflows to completion.
* Workflow abortion: Abort a running workflow.
* JSON validation: Validate a JSON input file against the WDL file intended for use.

## Usage

Below is widdler's basic help text. Widdler expects one of three usage modes to
be indicated as it's first argument: run, query, or abort.

```
usage: widdler.py <run | query | abort> [<args>]

Description: A tool for executing and monitoring WDLs to Cromwell instances.

positional arguments:
  {abort,monitor,query,run,validate}

optional arguments:
  -h, --help            show this help message and exit

```

### widdler.py run

Below is widdler's run help text. It expects the user to provide a wdl file,
json file, and to indicate one of the available servers for execution. The validate option
validates both the WDL and the JSON file submitted and is on by default. 

```
usage: widdler.py run <wdl file> <json file> [<args>]

Submit a WDL & JSON for execution on a Cromwell VM.

positional arguments:
  wdl                   Path to the WDL to be executed.
  json                  Path the json inputs file.

optional arguments:
  -h, --help            show this help message and exit
  -v, --validate        Validate WDL inputs in json file. (default: False)
  -m, --monitor         Monitor the workflow and receive an e-mail
                        notification when it terminates. (default: False)
  -i INTERVAL, --interval INTERVAL
                        If --monitor is selected, the amount of time in
                        seconds to elapse between status checks. (default: 30)
  -V, --verbose         If selected, widdler will write the current status to
                        STDOUT until completion while monitoring. (default:
                        False)
  -n, --notify          If selected, enable widdler monitoring e-mail
                        notification of workflow completion. (default: True)
  -d DEPENDENCIES, --dependencies DEPENDENCIES
                        A zip file containing one or more WDL files that the
                        main WDL imports. (default: None)
  -S {ale,btl-cromwell}, --server {ale,btl-cromwell}
                        Choose a cromwell server from ['ale', 'btl-cromwell']
                        (default: None)
```

For example:

```widdler.py run myworkflow.wdl myinput.json -S ale```

This will return a workflow ID and status if successfully submitted, for example:

```{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'status': 'Submitted'}```

This will execute a workflow that uses subworkflows:

```widdler.py run myworkflow.wdl myinput.json -S ale -d mydependencies.zip```

Users may also invoke Widdler's monitoring capabilities when initiating a workflow. See below for an 
explanation of monitoring options.

### widdler.py query

Below is widdler's query help text. Aside from the workflow ID it expects one or more optional
arguments to request basic status, metadata, and/or logs. 

```usage: widdler.py query <workflow id> [<args>]
   
   Query cromwell for information on the submitted workflow.
   
   positional arguments:
     workflow_id           workflow id for workflow execution of interest.
   
   optional arguments:
     -h, --help            show this help message and exit
     -s, --status          Print status for workflow to stdout (default: False)
     -m, --metadata        Print metadata for workflow to stdout (default: False)
     -l, --logs            Print logs for workflow to stdout (default: False)
     -S {ale,btl-cromwell}, --server {ale,btl-cromwell}
                           Choose a cromwell server from ['ale', 'btl-cromwell']
                           (default: None)
   
```

For example:
```widdler.py 2f8bb5c6-8254-4d38-b010-620913dd325e query -s -S ale```

will return something like this:

```[{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'status': 'Running'}]```

and:

```widdler.py query 2f8bb5c6-8254-4d38-b010-620913dd325e -m -s ale```

will return a ton of information like so (truncated for viewability):
```
{'status': 'Running', 'submittedFiles': {'workflow': '# GATK WDL\r\n# import "hc_scatter.wdl" as sub\r\n\r\ntask VersionCheck {\r\n    String gatk\r\n    command {\r\n        source
/broad/software/scripts/useuse\r\n        use Java-1.8\r\n        use Python-2.7\r\n... 'ref': '/cil/shed/sandboxes/amr/dev/gatk_pipeline/output/pfal_5/Plasmodium_falciparum_3D7.fasta'}}]}, 'submi
ssion': '2017-07-14T11:26:05.931-04:00', 'workflowName': 'gatk', 'outputs': {}, 'id': '2f8bb5c6-8254-4d38-b010-620913dd325e'}]
```

and:

```widdler.py query 2f8bb5c6-8254-4d38-b010-620913dd325e -l -s ale```

```
[{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'calls': {'gatk.MakeSampleDir': [{'shardIndex': 0, 'attempt': 1, 'stderr': '/cil/shed/apps/internal/cromwell_new/cromwell-executions/ga
   tk/2f8bb5c6-8254-4d38-b010-620913dd325e/call-MakeSampleDir/shard-0/execution/stderr', 'stdout': '/cil/shed/apps/internal/cromwell_new/cromwell-executions/gatk/2f8bb5c6-8254-4d38-b010-
   620913dd325e/call-MakeSampleDir/shard-0/execution/stdout'}
```
### widdler.py abort

Below is widdler's abort usage. Simply provide the 

```usage: widdler.py abort <workflow id> <server>
   
   Abort a submitted workflow.
   
   positional arguments:
     workflow_id           workflow id of workflow to abort.
   
   optional arguments:
     -h, --help            show this help message and exit
     -S {ale,btl-cromwell}, --server {ale,btl-cromwell}
                           Choose a cromwell server from ['ale', 'btl-cromwell']
                           (default: None)
```

This example:
```widdler.py abort 2f8bb5c6-8254-4d38-b010-620913dd325e -S ale```

will return:
```
{'status': 'Aborted', 'id': '2f8bb5c6-8254-4d38-b010-620913dd325e'}
```
## Validation

Widdler validation attempts to validate the inputs in the user's supplied json file against the WDL
arguments in the supplied WDL file. Validation is OFF by default and so users must specify it using
the -v flag if using widdler.py run. Validaton can also be performed using widdler.py validate if you
wish to validate inputs without executing the workflow.

It will validate the following:
* That the value of a parameter in the json matches the same type of value the WDL expects. For example
if the WDL expects an integer and the parameter supplies a float, this will be flagged as an error.
* That if the parameter is of type File, that the file exists on the file system.
* If a parameter specified in the json is not expected by the WDL.
* If a parameter contains the string 'samples_file' it's value will be interpreted as an input TSV file in which
the last column of every row indicates a sample file. In this case, an existence check will be made on each
sample file.

It will NOT validate the following:
* The contents of arrays. It can't tell the difference between an array of strings and an array of integers, but
it can tell they are arrays, and if a parameter expects an array but is provided something else this will
be logged as an error.

A note on validating WDL files with dependencies: due to the limitations of the current implementation
of depedency validation, WDL file dependencies must be present in the same directory as the main WDL file
and must be unzipped. Otherwise validation may not work.

Validation may also be run as a stand-alone operation using widdler.py validate. Usage is as follows:

```
usage: widdler.py validate <wdl_file> <json_file>

Validate (but do not run) a json for a specific WDL file.

positional arguments:
  wdl         Path to the WDL associated with the json file.
  json        Path the json inputs file to validate.

optional arguments:
  -h, --help  show this help message and exit
```

For example:

```widdler.py mywdl.wdl myjson.json```

If the json file has errors, a list of errors will be reported in the same way that the runtime validation reports.
For example:
```
bad.json input file contains the following errors:
gatk.ts_filter_snp: 99 is not a valid Float.
gatk.tcir: False is not a valid Boolean. Note that JSON boolean values must not be quoted.
gatk.ploidy: 2.0 is not a valid Int.
Required parameter gatk.snp_annotation is missing from input json.
Required parameter gatk.ref_file is missing from input json.
```


### widdler.py monitor

Widdler allows the monitoring of workflow(s). Unlike the query options, monitoring persists until a workflow reaches
a terminal state (any state besides 'Running' or 'Submitted'). While monitoring, it can optionally print the status of
a workflow to the screen, and when a terminal state is reached, it can optionally e-mail the user (users are assumed
to be of the broadinstitute.org domain) when the workflow is finished.

Monitoring usage is as follows:

```
usage: widdler.py monitor <workflow_id> [<args>]

Monitor a particular workflow and notify user via e-mail upon completion. If
aworkflow ID is not provided, user-level monitoring is assumed.

positional arguments:
  workflow_id           workflow id for workflow to monitor. Do not specify if
                        user-level monitoring is desired. (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Owner of workflows to monitor. (default: <your user name>)
  -i INTERVAL, --interval INTERVAL
                        Amount of time in seconds to elapse between status
                        checks. (default: 30)
  -V, --verbose         When selected, widdler will write the current status
                        to STDOUT until completion. (default: False)
  -n, --notify          When selected, enable widdler e-mail notification of
                        workflow completion. (default: False)
  -S {ale,btl-cromwell}, --server {ale,btl-cromwell}
                        Choose a cromwell server from ['ale', 'btl-cromwell']
                        (default: None)
```

#### Single Workflow Monitoring

Aside from monitoring of a single workflow with widdler's run command, you can also execute a monitor as in the 
following example:
 
```
widdler.py monitor 7ff17cb3-12f1-4bf0-8754-e3a0d39178ea -n -S btl-cromwell
```

In this case, widdler will continue to silently monitor this workflow until it detects a terminal status. Since the user 
selected -n, an e-mail will be sent to <user>@broadinstitute.org when a terminal status is detected, which will include
the metadata of the workflow.

If --verbose were selected, the user would have seen a STDOUT message indicating the workflows status at intervals 
defined by the --interval parameter, which has a default of 30 seconds. 

#### User Workflow Monitoring
(Note this feature is still under active development and is currently quite primitive)

User's may also monitor all workflows for a given user name by omitting the workflow_id parameter and specifying the
--user parameter like so:

```
widdler.py monitor -u amr -n -S btl-cromwell
```

Here, the user 'amr' is monitoring all workflows ever executed by him using widdler. Any workflows not executed by 
widdler will not be monitored. Workflows in a terminal state prior to execution will have an e-mail sent immediately
regarding their status, and any running workflows will result in an e-mail once they terminate. Using the --verbose
option here would result in STDOUT output for each workflow that is monitored at intervals specified by --interval.

## Logging

Widdler logs information in the application's logs directory in a file called widdler.log.
This can be useful to find information on widdler executions including workflow id and query
results and can help users locate workflow IDs if they've been lost. Each execution in the log
is presented like so, with the user's username indicated in the start/stop separators for 
convenient identification.

```-------------New Widdler Execution by amr-------------
   2017-07-14 12:10:44,746 - widdler - INFO - Parameters chosen: {'logs': False, 'func': <function call_query at 0x00000000040B8378>, 'status': True, 'workflow_id': '7ff17cb3-12f1-4bf0-8754-e3a0d39178ea', 'server': 'btl-cromwell', 'metadata': False}
   2017-07-14 12:10:44,746 - widdler.cromwell.Cromwell - INFO - URL:http://btl-cromwell:9000/api/workflows/v1
   2017-07-14 12:10:44,746 - widdler.cromwell.Cromwell - INFO - Querying status for workflow 7ff17cb3-12f1-4bf0-8754-e3a0d39178ea
   2017-07-14 12:10:44,747 - widdler.cromwell.Cromwell - INFO - GET REQUEST:http://btl-cromwell:9000/api/workflows/v1/7ff17cb3-12f1-4bf0-8754-e3a0d39178ea/status
   2017-07-14 12:10:44,812 - widdler - INFO - Result: [{'id': '7ff17cb3-12f1-4bf0-8754-e3a0d39178ea', 'status': 'Running'}]
   2017-07-14 12:10:44,813 - widdler - INFO - 
   -------------End Widdler Execution by amr-------------
   ```