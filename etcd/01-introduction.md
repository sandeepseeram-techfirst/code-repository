## etcd 
A distributed, reliable key-value store for the most critical data of a distributed system. 

etcd is a strongly consistent, distributed key-value store that provides a reliable way to store data that needs to be accessed by a distributed system or cluster of machines. It gracefully handles leader elections during network partitions and can tolerate machine failure, even in the leader node.

* It is most famous as the primary brain and source of truth for Kubernetes, which stores all cluster state, pod specs, secrets, and deployment configurations directly in etcd.