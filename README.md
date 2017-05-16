# log_parser
The class will process a log file, identify its records, perform a few validations to confirm they are ok, and extract specific fields from them for further study.

A usage case could be the following:

One of our logs is composed of records like this one:
```
EndTime=Sun Jul 31 23:09:12 2016
StartTime=1470020952.03
Time=94 msecs
Hostname=NU.US.amazon.com
Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
Info=REST.PUT.OBJECT
REMOTE_ADDR=10.51.71.65
Program=NVWRLDCBNFR1
History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
HostGroup=US
Marketplace=NMRN
Merchant=external
Operation=REST.PUT.OBJECT
Status=200
actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
next-server-endpoint=10.93.93.180:4545
index=f3a430000000000333b52000f084
objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
host=fubar.comcast.com
cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
requestId=F08C5EE16DF7DBD3'
requesterID=AWS:Q5JCJLQJT2EF05UO6VP14
objectkey=fubar
userAgent=NoAgentHere
```
We want to keep an eye on the time that the PUT operations take by customer and host in order to provide a consistent service across customers and hosts. We need to extract from the log information on customers, hosts, and times for PUT operations only. We know that some of the records could be corrupted (mostly with missing fields).

The parameters to be provided to the log_parser are the following:
- scheme: a list containing dictionaries that will help locate the records and the fields that need to be extracted from them
- num_record_lines: the expected number of lines per record
- record_filter: a function that selects which records to keep and which ones to discard

Each dictionary in the scheme list represents a field in a log record. They should have at least two keys:
- 'name': the name of the field
- 'regex': the regex that identifies the field in the log file

The first and last items in the scheme are used to identify the beginning and the end of a record (and are therefore mandatory); the rest, if provided, will be used to validate the record is in the right order and is complete.

If fields are to be extracted, they need to contain two additional keys:
- 'validator': a function that confirms whether the field is valid
- 'adjustator': a function that transforms the raw contents of the field into something more useful

This would be an example of an entry in the scheme that identifies 'Time' entries:
```
{'name':'Time',
 'regex':'Time=([0-9]+) msecs'}
```
This would identify 'Time' entries, extract them without validation, and turn them into an integer:
```
{'name':'Time',
 'regex':'Time=([0-9]+) msecs',
 'validator':lambda _: True,
 'adjustator':lambda x: int(x)}
```
If num_record_lines is ommited, the log_parser assumes the scheme is exhaustive (i.e., the scheme contains one entry for each of the fields in the records).

The record_filter function is applied once a record has been extracted to determine whether the data is relevant for the study at hand.

Once the log_parser has been defined, it can be used to parse log files by calling log_parser.parse_file(file_name). The parse_file function returns a list of the data extracted from the log file and another list with the corrupt recods and an error message foe each of them explaining what failed.

Running the file directly from the command line will create a sample log_parser and parse the file sample_log.log. This file contains 10 records, among which 5 are the PUT operations focus of our study and one is corrupt (with most of its fields missing). The expected output is the following:
```
Requested fields from the filtered and valid records found:
[94, 'NU.US.amazon.com', 'REST.PUT.OBJECT', 'AWS:Q5JCJLQJT2EF05UO6VP14']
[54, 'ALPHA.US.amazon.com', 'REST.PUT.OBJECT', 'AWS:M4QWXUQMTRB59SPH5LMLP']
[93, 'PHI.IE.amazon.com', 'REST.PUT.OBJECT', 'AWS:HNPD8TNTPZM0NOCCCWG0T']
[30, 'OMICRON.US.amazon.com', 'REST.PUT.OBJECT', 'AWS:84AFKQV0WN7ASW2UEU90I']
[51, 'BETA.CA.amazon.com', 'REST.PUT.OBJECT', 'AWS:BEUB332P7QMQVV4MCF066']
Invalid records found:
['Wrong number of lines', ['EndTime=Sun Jul 31 23:09:12 2016', 'StartTime=1470020952.03', 'Time=17 msecs', 'Hostname=ZETA.IE.amazon.com', 'index=f3a430000000000333b52000f084', 'objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1', 'host=fubar.comcast.com', 'cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8', "requestId=F08C5EE16DF7DBD3'", 'requesterID=AWS:I16UVHQTF365AW8VRXJP9', 'objectkey=fubar', 'userAgent=NoAgentHere']]
```
Happy parsing, and let me know if this helped you in any way!
