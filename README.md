# widdler

## Introduction

Widdler is a command-line tool for executing WDL workflows on Cromwell servers.
Features include:

* Workflow execution
* Workflow queries: status, metadata, logs
* Workflow abortion
* WDL and JSON validation (in progress).

## Usage

Below is widdler's basic help text. Widdler expects one of three usage modes to
be indicated as it's first argument: run, query, or abort.

```
usage: widdler.py <run | query | abort> [<args>]

Description: A tool for executing and monitoring WDLs to Cromwell instances.

positional arguments:
  {run,query,abort}

optional arguments:
  -h, --help         show this help message and exit
```

### widdler.py run

Below is widdler's run help text. It expects the user to provide a wdl file,
json file, and to indicate one of the available servers for execution. The validate option
validates both the WDL and the JSON file submitted and is on by default. 

```usage: widdler.py run <wdl file> <json file> [<args>]
   
   Submit a WDL & JSON for execution on a Cromwell VM.
   
   positional arguments:
     wdl                   Path to the WDL to be executed.
     json                  Path the json inputs file.
   
   optional arguments:
     -h, --help            show this help message and exit
     -v, --validate        Validate WDL and JSON files before execution. On by
                           default. (default: True)
     -S {ale,btl-cromwell}, --server {ale,btl-cromwell}
                           Choose a cromwell server from ['ale', 'btl-cromwell']
                           (default: None)
```

For example:

```widdler.py run myworkflow.wdl myinput.json -S ale```

This will return a workflow ID and status if successful, for example:

```{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'status': 'Submitted'}```

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
```widdler.py query -s -s ale```

will return something like this:

```[{'id': '2f8bb5c6-8254-4d38-b010-620913dd325e', 'status': 'Running'}]```

and:

```widdler.py query -m -s ale```

will return a ton of information like so (truncated for viewability):
```
{'status': 'Running', 'submittedFiles': {'workflow': '# GATK WDL\r\n# import "hc_scatter.wdl" as sub\r\n\r\ntask VersionCheck {\r\n    String gatk\r\n    command {\r\n        source
/broad/software/scripts/useuse\r\n        use Java-1.8\r\n        use Python-2.7\r\n... 'ref': '/cil/shed/sandboxes/amr/dev/gatk_pipeline/output/pfal_5/Plasmodium_falciparum_3D7.fasta'}}]}, 'submi
ssion': '2017-07-14T11:26:05.931-04:00', 'workflowName': 'gatk', 'outputs': {}, 'id': '2f8bb5c6-8254-4d38-b010-620913dd325e'}]
```

and:

```widdler.py query -l -s ale```

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

TBD