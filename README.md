# StackOverflowStudy
**How to access to the remote server via ssh browser on GCP**
1. Go to GCP console, and login with jarvan-experiment Google account.
2. On the navigation panel on the left side, select `Compute Engine` under `VIRTUAL MACHINES` menu, select `VM instances`.
3. You will see `jarvan-exp-1` machine. On the connect column select the drop down arrow and select `Open in browser window`
4. There you go, you will have the access to the remote server.

**How to use MySQL server on the remote server**
1. On the remote server, use command `mysql -u root -p`.
2. You will be asked for a password. Please use the password provided in order to access to the MySQL server.
3. After that you will be allowed to access to MySQL server as root.
4. There is only one database available which is `sotorrent`. Please use `use sotorrent` command to select the database.
5. There are two data tables available in the database which are `PostBlockVersion` and `PostBlockDiff`.
6. You may use SQL command to query for data such as `select`, `insert`, `delete` etc.

**How to compile and run Java program on the remote server**
1. On the remote server, the Java program is located in `/StackOverflowStudy/SOTOrrentAnalyzer/`. You may run this command `cd StackOverflowStudy/SOTOrrentAnalyzer/` to change directory to here.
2. There will be several java files, but there is only one with the main class for running which is `PostBlockProcessor.java`.
3. Run the following command to compile the java program `javac PostBlockProcessor.java`. You may need to change the location of the SO answer file in the code.
4. Add the MySQL connector to the Java CLASSPATH `export CLASSPATH=$CLASSPATH:/usr/share/java/mysql-connector-java-8.0.27.jar`.
5. In the `PostBlockProcessor.java` file, in line 84-95 are the options where you may select the program to do. There are 4 options currently. You may find what they can do in the file.
6. Run the following command to execute the java program `java PostBlockProcessor`.

**Diff File Naming Convention**
For diff files, there is a pattarn of file naming which is `PostId-PostHistoryId-LocalId-CurrentPostBlockId-PreviousPostBlockId-PostBlockTypeId.txt` where `PostBlockTypeId` can be either 0 or 1, 0 is Text block and 1 is Code block.

Remark: Sometimes, you may encounter error while compiling the Java program. The error is that the compiler cannot find .jar for SQL. Please run this command `export CLASSPATH=$CLASSPATH:/usr/share/java/mysql-connector-java.jar` to bypass the error.
