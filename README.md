# StackOverflowStudy
**How to generate your ssh key**

This method is very important. You will obtain a pair of public and private key. These keys are essential to access to the remote server via ssh.
1. Go to terminal
2. Type `ssh-keygen`. Then, you will be prompted to locate where your public and private keys will be stored. The default location is Users/YOURHOME/.ssh/. If you want to change it, you can do it at this step.
3. You will be asked to put paraphrase. You can leave it blank, or type whatever you want.
4. Then, you will get a pair of public and private keys. The `id-rsa` is your private key and `id-rsa.pub` is your public key.
5. You *must* provide your public key to the person in charge of the remote server. So, they can authorize you for the access to the remote server.

**How to access to the remote server via ssh**
1. Go to Terminal
2. Using command `ssh -i private-key 34.87.136.79` where the private key is provided privately. For example `ssh -i /Desktop/my-private-key 34.87.136.79`.
3. Once you're in the server, you're good to go!

**How to use MySQL server on the remote server**
1. On the remote server, use command `mysql -u root -p`.
2. You will be asked for a password. Please use the password provided in order to access to the MySQL server.
3. After that you will be allowed to access to MySQL server as root.
4. There is only one database available which is `sotorrent`. Please use `use sotorrent` command to select the database.
5. There are two data tables available in the database which are `PostBlockVersion` and `PostBlockDiff`.
6. You may use SQL command to query for data such as `select`, `insert`, `delete` etc.

**How to compile and run Java program on the remote server**
