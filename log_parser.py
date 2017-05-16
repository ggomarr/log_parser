import re

class log_parser():
    def __init__(self,scheme,
                 num_record_lines=None,
                 record_filter=lambda _: True):
        self.scheme=self.compile_scheme(scheme)
        if num_record_lines:
            self.num_record_lines=num_record_lines
        else:
            self.num_record_lines=len(scheme)
        num_fields=0
        for rule in scheme:
            if 'validator' in rule:
                num_fields=num_fields+1
        self.num_fields=num_fields
        self.start_line_regexp=self.scheme[0]['regex']
        self.end_line_regexp=self.scheme[-1]['regex']
        self.record_filter=record_filter
    def compile_scheme(self,scheme):
        compiled_scheme=[]
        for rule in scheme:
            rule['regex']=re.compile(rule['regex'])
            compiled_scheme.append(rule)
        return compiled_scheme
    def read_record(self,f):
        record=[]
        done=False
        while not done:
            pos=f.tell()
            line=f.readline()
            if line:
                line=line.strip()
                if line:
                    if self.start_line_regexp.match(line) and len(record)>0:
                        f.seek(pos)
                        done=True
                    else:
                        record.append(line)
                        if self.end_line_regexp.match(line):
                            done=True
            else:
                done=True
        return record
    def process_record(self,record):
        if len(record)!=self.num_record_lines:
            return False,['Wrong number of lines',record]
        field_pos=0
        record_data=[]
        for line in record:
            field=self.scheme[field_pos]['regex'].match(line)
            if field:
                if 'validator' in self.scheme[field_pos]:
                    field=field.group(1)
                    valid_field=self.scheme[field_pos]['validator'](field)
                    if valid_field:
                        record_data.append(self.scheme[field_pos]['adjustator'](field))
                    else:
                        record_data.append('NA')
                        return False,['Invalid fields',record]
                field_pos=field_pos+1
        if self.num_fields!=len(record_data):
            return False,['Wrong number of fields',record]
        return True,record_data
    def parse_file(self,file_name):
        good_records=[]
        bad_records=[]
        f=open(file_name,'r')
        record=self.read_record(f)
        while record:
            fine_record,record_data=self.process_record(record)
            if fine_record==True:
                if self.record_filter(record_data):
                    good_records.append(record_data)
            else:
                bad_records.append(record_data)
            record=self.read_record(f)
        return good_records,bad_records

if __name__ == '__main__':
    hostnames=['ALPHA','BETA','GAMMA','DELTA','EPSILON','ZETA','ETA','THETA',
               'IOTA','KAPPA','LAMBDA','MU','NU','XI','OMICRON','PI','RHO',
               'SIGMA','TAU','UPSILON','PHI','CHI','PSI','OMEGA']
    hostgroups=['US','CA','SG','IE']
    operations=['REST.GET.OBJECT','REST.PUT.OBJECT','REST.DEL.OBJECT']
    scheme=[
            {'name':'EndTime',
             'regex':'EndTime='},
            {'name':'Time',
             'regex':'Time=([0-9]+) msecs',
             'validator':lambda _: True,
             'adjustator':lambda x: int(x)},
            {'name':'Host',
             'regex':'Hostname=(({})\.({})\.amazon.com)'.format('|'.join(hostnames),'|'.join(hostgroups)),
             'validator':lambda _: True,
             'adjustator':lambda x: x},
            {'name':'Operation',
             'regex':'Operation=({})'.format('|'.join(operations)),
             'validator':lambda _: True,
             'adjustator':lambda x: x},
            {'name':'Customer',
             'regex':'requesterID=(AWS:\w{21})',
             'validator':lambda _: True,
             'adjustator':lambda x: x},
            {'name':'userAgent',
             'regex':'userAgent='},
           ]
    target_ops=['REST.PUT.OBJECT']
    record_filter=lambda x: x[2] in target_ops
    my_parser=log_parser(scheme=scheme,num_record_lines=25,record_filter=record_filter)
    good,bad=my_parser.parse_file('sample_log.log')
    print('Requested fields from the filtered and valid records found:')
    for record in good:
        print(record)
    print('Invalid records found:')
    for record in bad:
        print(record)

# Expected output (with the sample_log.log file as below)
# Requested fields from the filtered and valid records found:
# [94, 'NU.US.amazon.com', 'REST.PUT.OBJECT', 'AWS:Q5JCJLQJT2EF05UO6VP14']
# [54, 'ALPHA.US.amazon.com', 'REST.PUT.OBJECT', 'AWS:M4QWXUQMTRB59SPH5LMLP']
# [93, 'PHI.IE.amazon.com', 'REST.PUT.OBJECT', 'AWS:HNPD8TNTPZM0NOCCCWG0T']
# [30, 'OMICRON.US.amazon.com', 'REST.PUT.OBJECT', 'AWS:84AFKQV0WN7ASW2UEU90I']
# [51, 'BETA.CA.amazon.com', 'REST.PUT.OBJECT', 'AWS:BEUB332P7QMQVV4MCF066']
# Invalid records found:
# ['Wrong number of lines', ['EndTime=Sun Jul 31 23:09:12 2016', 'StartTime=1470020952.03', 'Time=17 msecs', 'Hostname=ZETA.IE.amazon.com', 'index=f3a430000000000333b52000f084', 'objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1', 'host=fubar.comcast.com', 'cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8', "requestId=F08C5EE16DF7DBD3'", 'requesterID=AWS:I16UVHQTF365AW8VRXJP9', 'objectkey=fubar', 'userAgent=NoAgentHere']]

# sample_log.log file
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.03
# Time=94 msecs
# Hostname=NU.US.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.PUT.OBJECT
# REMOTE_ADDR=10.51.71.65
# Program=NVWRLDCBNFR1
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=US
# Marketplace=NMRN
# Merchant=external
# Operation=REST.PUT.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:Q5JCJLQJT2EF05UO6VP14
# objectkey=fubar
# userAgent=NoAgentHere
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.03
# Time=54 msecs
# Hostname=ALPHA.US.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.PUT.OBJECT
# REMOTE_ADDR=10.83.12.26
# Program=IR9KDHQO7CQE
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=US
# Marketplace=8C43
# Merchant=external
# Operation=REST.PUT.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:M4QWXUQMTRB59SPH5LMLP
# objectkey=fubar
# userAgent=NoAgentHere
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.03
# Time=93 msecs
# Hostname=PHI.IE.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.PUT.OBJECT
# REMOTE_ADDR=10.99.74.85
# Program=PNLPI0B933EF
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=IE
# Marketplace=2OGL
# Merchant=external
# Operation=REST.PUT.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:HNPD8TNTPZM0NOCCCWG0T
# objectkey=fubar
# userAgent=NoAgentHere
# 
# 
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.03
# Time=30 msecs
# Hostname=OMICRON.US.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.PUT.OBJECT
# REMOTE_ADDR=10.18.75.53
# Program=7BQTU0LIPZ61
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=US
# Marketplace=7070
# Merchant=external
# Operation=REST.PUT.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:84AFKQV0WN7ASW2UEU90I
# objectkey=fubar
# userAgent=NoAgentHere
# 
# 
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.03
# Time=69 msecs
# Hostname=BETA.IE.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.GET.OBJECT
# REMOTE_ADDR=10.61.16.83
# Program=IIXT07ATWR0C
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=IE
# Marketplace=7BXC
# Merchant=external
# Operation=REST.GET.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:GY8DM0JPIR5N65WN3C6B3
# objectkey=fubar
# userAgent=NoAgentHere
# 
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.03
# Time=17 msecs
# Hostname=ZETA.IE.amazon.com
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:I16UVHQTF365AW8VRXJP9
# objectkey=fubar
# userAgent=NoAgentHere
# 
# 
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.04
# Time=14 msecs
# Hostname=ETA.SG.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.DEL.OBJECT
# REMOTE_ADDR=10.20.60.93
# Program=BPQ10L1HQ73K
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=SG
# Marketplace=KES5
# Merchant=external
# Operation=REST.DEL.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:KGWCGHGZMQUJGM6J48U0N
# objectkey=fubar
# userAgent=NoAgentHere
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.04
# Time=96 msecs
# Hostname=RHO.CA.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.DEL.OBJECT
# REMOTE_ADDR=10.81.50.74
# Program=XK30MV0WGS6P
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=CA
# Marketplace=YEM2
# Merchant=external
# Operation=REST.DEL.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:8CG49ZPLAK1CAKZ05D1GZ
# objectkey=fubar
# userAgent=NoAgentHere
# 
# 
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.04
# Time=51 msecs
# Hostname=BETA.CA.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.PUT.OBJECT
# REMOTE_ADDR=10.25.74.93
# Program=5GVTU4LP74GP
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=CA
# Marketplace=KBLC
# Merchant=external
# Operation=REST.PUT.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:BEUB332P7QMQVV4MCF066
# objectkey=fubar
# userAgent=NoAgentHere
# 
# 
# EndTime=Sun Jul 31 23:09:12 2016
# StartTime=1470020952.04
# Time=70 msecs
# Hostname=ZETA.CA.amazon.com
# Timing=Authenticate:Latency:5/1,VerifyAccessToProduct:Latency:5/1,AuthClient:Authenticate:5/1,AuthClient:AuthenticateUser:5/1,AuthClient:ParsePolicies:0/4,AuthClient:SubscriptionCheck:4/1,Object.get:36/2,ObjectNodePicker.select:0/2
# Counters=Authenticate:Availability=1,VerifyAccessToProduct:Availability=1,AuthClient:TotalPolicies=4,AuthClient:AuthenticateSuccess=1,AuthClient:SubscriptionCacheHit=0,AuthClient:SubscriptionValid=1,auth.v25=1,bandwithBatchClientRecordQueueSize=1,batchClientRecordQueueSize=1,batchMetered.count=1
# Info=REST.DEL.OBJECT
# REMOTE_ADDR=10.58.6.97
# Program=00LHIMMIKM9Q
# History=start:1387387980848,s-checkThrottling:0,e-checkThrottling:0,e-receive-performance-metrics:0,s-deserialize-performance-metrics:0,e-deserialize-performance-metrics:0,e-get.data:0,s-batchReportBytesTransferred:2,e-batchReportBytesTransferred:0,s-dataTransferReportBytesTransferred:0,TRUNCATED
# HostGroup=CA
# Marketplace=RHW2
# Merchant=external
# Operation=REST.DEL.OBJECT
# Status=200
# actor=XYZAIC5JEGYM3UDNX7SQ/XYZAIWZT7XKU2VJCA2K4Y
# next-server-endpoint=10.93.93.180:4545
# index=f3a430000000000333b52000f084
# objectOwner=943fe22315790b2fc01e730a95de6a6d94972c06441f57ad0980032ea0da99c1
# host=fubar.comcast.com
# cache-endpoints=10.34.81.31-5397-tcp-dub3,10.165.33.45-5397-tcp-dub8
# requestId=F08C5EE16DF7DBD3'
# requesterID=AWS:CK1OZ5BCM0PRN2MZ8TR7Y
# objectkey=fubar
# userAgent=NoAgentHere
# 
# 
# 