# widdler

## Introduction

Widdler is a command-line tool for executing WDL workflows on Cromwell servers.
Features include:

* Workflow execution: Execute a workflow on a specified Cromwell server.
* Workflow restart: Restart a previously executed workflow.
* Workflow queries: Query workflow(s) to get metadata information and more, and query by labels.
* Workflow result explanation: Get more detailed information on fails at the command line. 
* Workflow monitoring: Monitor a specific workflow or set of user-specific workflows to completion.
* Workflow labeling: Add one ore more labels to a given workflow that can then be queried.
* Workflow abortion: Abort a running workflow.
* JSON validation: Validate a JSON input file against the WDL file intended for use.

## Dependencies

Widdler requires Python 2.7 and Java-1.8 to be loaded in your environment in order for full functionality to work.
In addition, it uses the following Python libraries. See [requirements.txt](https://github.com/broadinstitute/widdler/blob/master/requirements.txt) for additional Python library requirements.

## Usage

Below is widdler's basic help text. Widdler expects one of three usage modes to
be indicated as it's first argument: run, query, or abort.

```
usage: widdler.py <run | monitor | query | abort | validate |restart | explain | label> [<args>]

Description: A tool for executing and monitoring WDLs to Cromwell instances.

positional arguments:
  {restart,explain,abort,monitor,query,run,validate,label}

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
  -l LABEL, --label LABEL
                        A key:value pair to assign. May be used multiple
                        times. (default: None)
  -m, --monitor         Monitor the workflow and receive an e-mail
                        notification when it terminates. (default: False)
  -i INTERVAL, --interval INTERVAL
                        If --monitor is selected, the amount of time in
                        seconds to elapse between status checks. (default: 30)
  -V, --verbose         If selected, widdler will write the current status to
                        STDOUT until completion while monitoring. (default:
                        False)
  -n, --no_notify       When selected, disable widdler e-mail notification of
                        workflow completion. (default: False)
  -d DEPENDENCIES, --dependencies DEPENDENCIES
                        A zip file containing one or more WDL files that the
                        main WDL imports. (default: None)
  -D, --disable_caching
                        Don't used cached data. (default: False)
  -S {ale,btl-cromwell,localhost,gscid-cromwell}, --server {ale,btl-cromwell,localhost,gscid-cromwell}
                        Choose a cromwell server from ['ale', 'btl-cromwell',
                        'localhost', 'gscid-cromwell'] (default: None)
```

For example:

```widdler.py run myworkflow.wdl myinput.json -S ale```

This will return a workflow ID and status if successfully submitted, for example:

```{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'status': 'Submitted'}```

This will execute a workflow that uses subworkflows:

```widdler.py run myworkflow.wdl myinput.json -S ale -d mydependencies.zip```

Users may also invoke widdler's monitoring and labeling capabilities when initiating a workflow. See below for an 
explanation of monitoring and labeling options.

### widdler.py restart

If a workflow has been previously executed to a Cromwell server, it is possible to restart the workflow after it has
completed and run it again with the same inputs simply by providing the workflow ID and server of the original run.
The usage for performing this action is as follows:

```
usage: widdler.py restart <workflow id>

Restart a submitted workflow.

positional arguments:
  workflow_id           workflow id of workflow to restart.

optional arguments:
  -h, --help            show this help message and exit
  -S {ale,btl-cromwell,localhost,gscid-cromwell}, --server {ale,btl-cromwell,localhost,gscid-cromwell}
                        Choose a cromwell server from ['ale', 'btl-cromwell',
                        'localhost', 'gscid-cromwell'] (default: None)
  -D, --disable_caching
                        Don't used cached data. (default: False)
```

For example:

```python widdler.py restart b931c639-e73d-4b59-9333-be5ede4ae2cb -S ale
```

Will restart workflow b931xxx and return the new workflow id like so:

```
Workflow restarted successfully; new workflow-id: 164678b8-2a52-40f3-976c-417c777c78ef
```


### widdler.py query

Below is widdler's query help text. Aside from the workflow ID it expects one or more optional
arguments to request basic status, metadata, and/or logs. 

```
usage: widdler.py query <workflow id> [<args>]

Query cromwell for information on the submitted workflow.

positional arguments:
  workflow_id           workflow id for workflow execution of interest.
                        (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -s, --status          Print status for workflow to stdout (default: False)
  -m, --metadata        Print metadata for workflow to stdout (default: False)
  -l, --logs            Print logs for workflow to stdout (default: False)
  -u USERNAME, --username USERNAME
                        Owner of workflows to monitor. (default: Osiris)
  -L LABEL, --label LABEL
                        Query status of all workflows with specific label(s).
                        (default: None)
  -d DAYS, --days DAYS  Last n days to query. (default: 7)
  -S {ale,btl-cromwell,localhost,gscid-cromwell}, --server {ale,btl-cromwell,localhost,gscid-cromwell}
                        Choose a cromwell server from ['ale', 'btl-cromwell',
                        'localhost', 'gscid-cromwell'] (default: None)
  -f {Running,Submitted,QueuedInCromwell,Failed,Aborted,Succeeded}, --filter {Running,Submitted,QueuedInCromwell,Failed,Aborted,Succeeded}
                        Filter by a workflow status from those listed above.
                        May be specified more than once. (default: None)

  -a, --all             Query for all users. (default: False)  
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

In addition, users can query for workflows by username:

```
python widdler.py query -S ale -u amr
```

returns (truncated to save space):
```Determining amr's workflows...
[{'end': '2017-09-18T12:16:15.420-04:00',
  'id': '4948665e-ab50-4524-a986-a3215df884f0',
  'metadata': 'http://ale:9000/api/workflows/v1/4948665e-ab50-4524-a986-a3215df884f0/metadata',
  'name': 'gatk',
  'start': '2017-09-18T12:15:58.652-04:00',
  'status': 'Aborted',
  'timing': 'http://ale:9000/api/workflows/v1/4948665e-ab50-4524-a986-a3215df884f0/timing'},
 {'end': '2017-09-18T12:20:48.307-04:00',
  'id': 'bc38de08-06be-4845-85c2-2322176d7844',
  'metadata': 'http://ale:9000/api/workflows/v1/bc38de08-06be-4845-85c2-2322176d7844/metadata',
  'name': 'gatk',
  'start': '2017-09-18T12:20:39.061-04:00',
  'status': 'Aborted',
  'timing': 'http://ale:9000/api/workflows/v1/bc38de08-06be-4845-85c2-2322176d7844/timing'},
```
However, we may only want the workflows from the last 4 days, so we can use the -d flag.

```
> python widdler.py query -S ale -u amr -d 4
```
returns
```
Determining amr's workflows...
[{'end': '2017-09-19T11:29:04.346-04:00',
  'id': 'bed73265-6eaf-4984-895d-5054aa7f577c',
  'metadata': 'http://ale:9000/api/workflows/v1/bed73265-6eaf-4984-895d-5054aa7f577c/metadata',
  'name': 'gatk',
  'start': '2017-09-19T10:02:47.247-04:00',
  'status': 'Succeeded',
  'timing': 'http://ale:9000/api/workflows/v1/bed73265-6eaf-4984-895d-5054aa7f577c/timing'}]
```

Users can also assign labels to workflows(see below) and then query based on those labels. Supposing I tagged some
workflows with a key of 'foo' and a value of 'bar', I can query the following:

```
python widdler.py query -S ale -L foo:bar
```

Which prints:
```
{
    "results": [
        {
            "status": "Aborted",
            "start": "2017-09-18T12:15:58.652-04:00",
            "end": "2017-09-18T12:16:15.420-04:00",
            "name": "gatk",
            "id": "4948665e-ab50-4524-a986-a3215df884f0"
        },
        {
            "status": "Aborted",
            "start": "2017-09-18T12:20:39.061-04:00",
            "end": "2017-09-18T12:20:48.307-04:00",
            "name": "gatk",
            "id": "bc38de08-06be-4845-85c2-2322176d7844"
        }
    ]
}
```

Suppose, however, I want to filter my list by multiple labels, so I only want the foo:bar workflows that also
are labeled moo:cow. I can query using multiple labels.

```
python widdler.py query -S ale -L foo:bar -L moo:cow
```

This returns a subset of the prior query:

```
{
    "results": [
        {
            "status": "Aborted",
            "start": "2017-09-18T12:20:39.061-04:00",
            "end": "2017-09-18T12:20:48.307-04:00",
            "name": "gatk",
            "id": "bc38de08-06be-4845-85c2-2322176d7844"
        }
    ]
}
```

Users can further filter queries by the current status, and may do this multiple times. For example, to see
all Succeeded workflows for user amr:

```python widdler.py query -S ale -u amr -f Succeeded
```

returns

```Determining amr's workflows...
   [{'end': '2017-09-19T11:29:04.346-04:00',
     'id': 'bed73265-6eaf-4984-895d-5054aa7f577c',
     'metadata': 'http://ale:9000/api/workflows/v1/bed73265-6eaf-4984-895d-5054aa7f577c/metadata',
     'name': 'gatk',
     'start': '2017-09-19T10:02:47.247-04:00',
     'status': 'Succeeded',
     'timing': 'http://ale:9000/api/workflows/v1/bed73265-6eaf-4984-895d-5054aa7f577c/timing'}]
```

Multiple status filters may also be combined:

```python widdler.py query -S ale -u amr -f Succeeded -f Aborted
```

returns:


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

### widdler.py explain

Running widdler.py explain will provide information at command line similar to the monitor e-mail, including workflow
status, root directory, stdout and stderr information, and useful links. Usage is as follows:

```
usage: widdler.py explain <workflowid>

Explain the status of a workflow.

positional arguments:
  workflow_id           workflow id of workflow to abort.

optional arguments:
  -h, --help            show this help message and exit
  -S {ale,btl-cromwell}, --server {ale,btl-cromwell}
                        Choose a cromwell server from ['ale', 'btl-cromwell']
                        (default: None)
```

This example:
```
python widdler.py explain b931c639-e73d-4b59-9333-be5ede4ae2cb -S ale
```

will return:
```-------------Workflow Status-------------
{'id': 'b931c639-e73d-4b59-9333-be5ede4ae2cb',
 'status': 'Failed',
 'workflowRoot': '/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb'}
-------------Failed Stdout-------------
/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb/call-ApplySnpRecalibration/execution/stdout:
[Errno 2] No such file or directory: u'/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb/call-ApplySnpRecalibration/execution/stdout'
-------------Failed Stderr-------------
/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb/call-ApplySnpRecalibration/execution/stderr:
[Errno 2] No such file or directory: u'/cil/shed/apps/internal/cromwell_gaag/cromwell-executions/gatk/b931c639-e73d-4b59-9333-be5ede4ae2cb/call-ApplySnpRecalibration/execution/stderr'
-------------Cromwell Links-------------
http://ale:9000/api/workflows/v1/b931c639-e73d-4b59-9333-be5ede4ae2cb/metadata
http://ale:9000/api/workflows/v1/b931c639-e73d-4b59-9333-be5ede4ae2cb/timing
```

Note that in this case, there were no stdout or stderr for the step that failed in the workflow. 

### widdler.py label

Widdler allows users to attach one or more key:value pairs to a workflow so as to label them. This allows
users to query workflows with custom labels that are meaningful to them. For example, if users have multiple
workflows related to a plasmodium genome, the user could apply a "organism:plasmodium" label to every workflow
using that genome and then query for it later. The following is the usage for widdler.py label.

```
usage: widdler.py label <workflow_id> [<args>]

Label a specific workflow with one or more key/value pairs.

positional arguments:
  workflow_id           workflow id for workflow to label. (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -S {ale,btl-cromwell,localhost,gscid-cromwell}, --server {ale,btl-cromwell,localhost,gscid-cromwell}
                        Choose a cromwell server from ['ale', 'btl-cromwell',
                        'localhost', 'gscid-cromwell'] (default: None)
  -l LABEL, --label LABEL
                        A key:value pair to assign. May be used multiple
                        times. (default: None)
```

For example:

```
python widdler.py label bc38de08-06be-4845-85c2-2322176d7844 -S ale -l organism:plasmodium
```

returns

```
Labels successfully applied:
{
  "id": "bc38de08-06be-4845-85c2-2322176d7844",
  "labels": {
    "organism": "plasmodium",
    "id": "bc38de08-06be-4845-85c2-2322176d7844"
  }
}
```

Multiple labels can also be applied at once:

```
python widdler.py label bc38de08-06be-4845-85c2-2322176d7844 -S ale -l organism:plasmodium -l: group:BTL
```

returns

```Labels successfully applied:
{
  "id": "bc38de08-06be-4845-85c2-2322176d7844",
  "labels": {
    "group": "btl",
    "organism": "plasmodium",
    "id": "bc38de08-06be-4845-85c2-2322176d7844"
  }
}
```

### widdler.py valdiate
(Requires Java-1.8, so make sure to 'use Java-1.8' before trying validation)

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
  -n, --no_notify       When selected, disable widdler e-mail notification of
                        workflow completion. (default: False)
  -S {ale,btl-cromwell}, --server {ale,btl-cromwell}
                        Choose a cromwell server from ['ale', 'btl-cromwell']
                        (default: None)
```

#### Single Workflow Monitoring

Aside from monitoring of a single workflow with widdler's run command, you can also execute a monitor as in the 
following example:
 
```
widdler.py monitor 7ff17cb3-12f1-4bf0-8754-e3a0d39178ea -S btl-cromwell
```

In this case, widdler will continue to silently monitor this workflow until it detects a terminal status. An 
 e-mail will be sent to <user>@broadinstitute.org when a terminal status is detected, which will include
the metadata of the workflow.

If --verbose were selected, the user would have seen a STDOUT message indicating the workflows status at intervals 
defined by the --interval parameter, which has a default of 30 seconds. 

If --no_notify were selected, an e-mail would not be sent.

#### User Workflow Monitoring

User's may also monitor all workflows for a given user name by omitting the workflow_id parameter and specifying the
--user parameter like so:

```
widdler.py monitor -u amr -n -S btl-cromwell
```

Here, the user 'amr' is monitoring any workflows currently executed by the user 'amr.' All othe parameters for 
 workflow monitoring, such as intervals and verbose mode, apply to user workflow monitoring as well.

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

## Known Issues

* Widdler will sometimes print 'null' to stdout. This does not impact proper operation of widdler.
