## Data Lakehouse using Apache Iceberg 

**A data lakehouse is a modern data management architecture that combines the best features of data lakes and data warehouses.**

* It was introduced to bridge the gap between these two traditional architectures, offering both the flexibility of data lakes and the performance and reliability of data warehouses.

* The key innovation of data lakehouses is their ability to enforce data structure and schema while maintaining the cost-effectiveness and scalability of object storage.

* This is achieved through specialized table formats and metadata management systems that provide ACID transactions, schema enforcement, and efficient query optimization – all while working directly with files stored in object storage. 


## What Is a Table Format?
A key enabler of the data lakehouse architecture is the table format – a specification that defines how data files are organized, tracked, and managed to form a logical table.

While file formats like Parquet and ORC handle how data is encoded within individual files, table formats operate at a higher level, managing collections of files as tables with features like schema evolution, partitioning, and transaction management. 

These table formats provide the crucial metadata layer that enables database-like capabilities on top of simple object storage systems, effectively bridging the gap between data lakes and data warehouses. 

Several table formats have emerged to address these needs, including **Apache Hudi**, **Delta Lake**, and **Apache Iceberg**. Among these, Apache
Iceberg stands out for its robust architecture and feature set.

Developed at Netflix and later donated to the Apache Software Foundation, Iceberg provides a table format that ensures reliable, scalable data management with features like schema evolution, hidden partitioning, time travel, and ACID compliance, making it particularly well-suited for large-scale data lake implementations. 
