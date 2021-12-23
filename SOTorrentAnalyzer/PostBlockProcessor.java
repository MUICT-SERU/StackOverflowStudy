import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.*;
import java.util.*;


public class PostBlockProcessor {
    private static String home = "/mnt/disks/data/so_study/StackOverflowStudy/";
    private static double minSimilarity = 0.8;
    private static double maxSimilarity = 0.9;

    public static void main(String[] args) {
        String answerFilePath = home + "files/acceptedWithVersionAnswer.txt";
        try {
            //Connect the program with MySQL DB
            System.out.println("The program has been initiated.");
            FileReader fileReader = new FileReader(answerFilePath);
            BufferedReader bufferedReader = new BufferedReader(fileReader);
            Path path = Paths.get(answerFilePath);
            long countLine = Files.lines(path).count();
            String dbUrl = "jdbc:mysql://localhost:3306/sotorrent?autoReconnect=true&useSSL=false";
            String username = "sotorrent";
            String password = "stackoverflow";
            try {
                // The newInstance() call is a work around for some
                // broken Java implementations
                Class.forName("com.mysql.cj.jdbc.Driver").newInstance();
            } catch (Exception ex) {
                // handle the error
                ex.printStackTrace();
            }
            Connection connection = DriverManager.getConnection(dbUrl, username, password);
            Statement statement = connection.createStatement();
            Statement statement2 = connection.createStatement();
            System.out.println("Connected to the database successfully!\nBeginning querying process..." +
                    "\nThe number of queries initiated: " + countLine);

            // Processing Post by creating Post objects
            long count = 0;
            String s;
            ArrayList<Post> posts = new ArrayList<Post>();
            while ((s = bufferedReader.readLine()) != null) {
                String query = "select PostHistoryId, MostRecentVersion from PostBlockVersion where PostId = " + s +
                        " group by PostHistoryId, MostRecentVersion order by PostHistoryId desc;";
                ResultSet resultSet = statement.executeQuery(query);
                Post post = new Post(Integer.parseInt(s));
                while (resultSet.next()) {
                    int postHistoryId = resultSet.getInt("PostHistoryId");
                    int MostRecentVersion = resultSet.getInt("MostRecentVersion");
                    PostHistory postHistory = new PostHistory(postHistoryId);
                    if (MostRecentVersion == 1) {
                        postHistory.setIsMostRecent(true);
                    } else {
                        postHistory.setIsMostRecent(false);
                    }
                    if (post.getPostHistoriesSize() > 0) {
                        post.getPostHistories().getLast().setPreviousPostHistoryId(postHistoryId);
                    }

                    String query2 = "select Id, PostBlockTypeId, LocalId, PredPostHistoryId, PredPostBlockVersionId, " +
                            "PredLocalId, PredEqual, PredSimilarity from PostBlockVersion where PostHistoryId = "
                            + postHistoryId + " order by LocalId;";
                    ResultSet resultSet2 = statement2.executeQuery(query2);
                    while (resultSet2.next()) {
                        int postBlockId = resultSet2.getInt("Id");
                        int postBlockTypeId = resultSet2.getInt("PostBlockTypeId");
                        int localId = resultSet2.getInt("LocalId");
                        int precedingPostHistoryId = resultSet2.getInt("PredPostHistoryId");
                        int precedingPostBlockId = resultSet2.getInt("PredPostBlockVersionId");
                        int precedingLocalId = resultSet2.getInt("PredLocalId");
                        int predEqual = resultSet2.getInt("PredEqual");
                        double precedingSimilarity = resultSet2.getDouble("PredSimilarity");

                        boolean isCodeBlock;
                        if (postBlockTypeId == 2) isCodeBlock = true;
                        else isCodeBlock = false;
                        boolean isEqualToPrecedingBlock;
                        if (predEqual == 1) isEqualToPrecedingBlock = true;
                        else isEqualToPrecedingBlock = false;

                        PostBlock postBlock = new PostBlock(postBlockId, isCodeBlock, localId, precedingPostHistoryId,
                                precedingLocalId, precedingPostBlockId, isEqualToPrecedingBlock, precedingSimilarity);
                        postHistory.addPostBlock(postBlock);
                    }
                    post.addPostHistory(postHistory);
                }
                posts.add(post);
                count++;
                if (count % 1000 == 0) {
                    System.out.println(count + " queries has been processed. There are " +
                            (countLine - count) + " queries left.");
                }
            }
            System.out.println("Finished importing the data.");

            //Write Post objects with PostHistory+PostBlock in to text file
            // writeOutTextFile(posts);

            //Calculate for changes in Posts #No File is written out
            // calculatePostChanges(posts);

            //Calculate for Min, Max, Avg of similarity of each post
            calculateSimilarity(posts);

            //Write out Diff files of each post in each postHistory
            //writeDiffFiles(posts, statement3);

            bufferedReader.close();
            fileReader.close();
        } catch (SQLException | FileNotFoundException throwables) {
            throwables.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void writeOutTextFile(ArrayList<Post> posts) {
        System.out.println("Start writing out text file...");
        String fileName = "postsWithPostHistoryVersion.txt";
        String directory = PostBlockProcessor.home;
        try {
            FileWriter fileWriter = new FileWriter(directory + fileName);
            BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);
            for (Post post : posts) {
                bufferedWriter.write(post.toString() + "\n");
            }
            bufferedWriter.close();
            fileWriter.close();
            System.out.println("The program is done! Check the file at: " + directory + fileName);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void calculatePostChanges(ArrayList<Post> posts) {
        System.out.println("Start calculating Post changes...");
        //variables for counting
        int codeChanges = 0;
        int textChanges = 0;
        int bothChanges = 0;

        for (Post post : posts) {
            LinkedList<PostHistory> postHistories = post.getPostHistories();
            PostHistory postHistory = post.getPostHistories().getFirst();
            boolean codeChange = false;
            boolean textChange = false;
            for (int i = 0; i < postHistory.getPostBlocks().size(); i++) {
                if (checkSimilarity(post, postHistory, postHistory.getPostBlocks().get(i).getPostBlockId()) == false) {
                    if (postHistory.getPostBlocks().get(i).isCodeBlock()) {
                        codeChange = true;
                    } else {
                        textChange = true;
                    }
                }
                if (codeChange && textChange) break;
            }
            if (codeChange && textChange) {
                bothChanges++;
            } else {
                if (codeChange) codeChanges++;
                if (textChange) textChanges++;
            }
        }
        System.out.print("The program is done! ");
        System.out.println("Code changes: " + codeChanges + ", Text changes: " + textChanges
                + ", BothChanges: " + bothChanges);
    }

    private static boolean checkSimilarity(Post post, PostHistory postHistory, int postBlockId) {
        PostBlock postBlock = postHistory.getPostBlock(postBlockId);
        if (postBlock != null) {
            if (postBlock.isEqualToPrecedingBlock() == true) {
                if (postBlock.getPrecedingPostBlockId() == 0) {
                    return true;
                } else {
                    return checkSimilarity(post, post.getPostHistory(postHistory.getPreviousPostHistoryId()),
                            postBlock.getPrecedingPostBlockId());
                }
            } else {
                return false;
            }
        } else {
            return true;
        }
    }

    private static void calculateSimilarity(ArrayList<Post> posts) {
        System.out.println("Start calculating for similarity...");
        String fileName = "similarity.csv";
        String directory = PostBlockProcessor.home;
        try {
            FileWriter fileWriter = new FileWriter(directory + fileName);
            BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);
            bufferedWriter.write("PostId,UniqueId,PostBlockType,Revisions,MinSim,MaxSim,AvgSim\n");
            for (Post post : posts) {
                Set<Integer> doneSet = new HashSet<Integer>();
                for (int i = 0; i < post.getPostHistoriesSize(); i++) {
                    PostHistory postHistory = post.getPostHistories().get(i);
                    int previousPostHistoryId = postHistory.getPreviousPostHistoryId();
                    for (int y = 0; y < postHistory.getPostBlocks().size(); y++) {
                        PostBlock postBlock = postHistory.getPostBlocks().get(y);
                        ArrayList<Double> thisSim = new ArrayList<Double>();
                        int currentPostBlockId = 0;
                        int currentPostHistoryId = 0;
                        int precedingPostBlockId = postBlock.getPostBlockId();
                        int precedingPostHistoryId = postHistory.getPostHistoryId();
                        do {
                            currentPostBlockId = precedingPostBlockId;
                            currentPostHistoryId = precedingPostHistoryId;
                            if (!doneSet.contains(currentPostBlockId)) {
                                thisSim.add(post.getPostHistory(currentPostHistoryId).
                                        getPostBlock(currentPostBlockId).getPrecedingSimilarity());
                                doneSet.add(currentPostBlockId);
                            }
                            precedingPostBlockId = post.getPostHistory(currentPostHistoryId).
                                    getPostBlock(currentPostBlockId).getPrecedingPostBlockId();
                            precedingPostHistoryId = post.getPostHistory(currentPostHistoryId).
                                    getPostBlock(currentPostBlockId).getPrecedingPostHistoryId();
                        } while (precedingPostBlockId != 0);
                        if (thisSim.size() > 0) {
                            double min = 1.0;
                            double max = 0.0;
                            double avg = 0.0;
                            for (int x = 0; x < thisSim.size() - 1; x++) {
                                if (thisSim.get(x).doubleValue() < min) min = thisSim.get(x).doubleValue();
                                if (thisSim.get(x).doubleValue() > max) max = thisSim.get(x).doubleValue();
                                avg = avg + thisSim.get(x).doubleValue();
                            }
                            // write the value out only when it is within the selected similarity range
                            if (avg != 0.0 && (avg >= minSimilarity) && (avg <= maxSimilarity)) {
                                System.out.println("The avg. similarity value is in the range: " + avg);
                                PostBlockStat postBlockStat;
                                if (postBlock.isCodeBlock()) {
                                    postBlockStat = new PostBlockStat(post.getPostId(), postBlock.getPostBlockId(),
                                            1, thisSim.size() - 1,
                                            min, max, (avg / (thisSim.size() - 1)));
                                } else {
                                    postBlockStat = new PostBlockStat(post.getPostId(), postBlock.getPostBlockId(),
                                            0, thisSim.size() - 1,
                                            min, max, (avg / (thisSim.size() - 1)));
                                }
                                bufferedWriter.write(postBlockStat.toCSV());
                            } else {
                                PostBlockStat postBlockStat;
                                if (postBlock.isCodeBlock()) {
                                    postBlockStat = new PostBlockStat(post.getPostId(), postBlock.getPostBlockId(),
                                            1, 0, 0, 0, 0);
                                } else {
                                    postBlockStat = new PostBlockStat(post.getPostId(), postBlock.getPostBlockId(),
                                            0, 0, 0, 0, 0);
                                }
                                bufferedWriter.write(postBlockStat.toCSV());
                            }
                        }
                    }
                }
            }
            System.out.println("The program is done! Check the file at: " + directory + fileName);
            bufferedWriter.close();
            fileWriter.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void writeDiffFiles(ArrayList<Post> posts, Statement statement) {
        System.out.println("Start writing diff files...");
        String directory = PostBlockProcessor.home + "diff/";
        try {
            for (Post post : posts) {
                Set<Integer> doneSet = new HashSet<Integer>();
                int runningBlockNumber = 1;
                for (int i = 0; i < post.getPostHistoriesSize(); i++) {
                    PostHistory postHistory = post.getPostHistories().get(i);
                    int previousPostHistoryId = postHistory.getPreviousPostHistoryId();
                    for (int y = 0; y < postHistory.getPostBlocks().size(); y++) {
                        PostBlock postBlock = postHistory.getPostBlocks().get(y);
                        ArrayList<Double> thisSim = new ArrayList<Double>();
                        int currentPostBlockId = 0;
                        int currentPostHistoryId = 0;
                        int precedingPostBlockId = postBlock.getPostBlockId();
                        int precedingPostHistoryId = postHistory.getPostHistoryId();
                        do {
                            currentPostBlockId = precedingPostBlockId;
                            currentPostHistoryId = precedingPostHistoryId;
                            if (!doneSet.contains(currentPostBlockId)) {
                                String query = "select count(*) as num from PostBlockDiff where PostBlockVersionId = "
                                        + post.getPostHistory(currentPostHistoryId).
                                        getPostBlock(currentPostBlockId).getPostBlockId() + ";";
                                ResultSet resultSet = statement.executeQuery(query);
                                resultSet.next();
                                if (resultSet.getInt("num") > 0) {
                                    int isCodeBlock = 0;
                                    if (post.getPostHistory(currentPostHistoryId).
                                            getPostBlock(currentPostBlockId).isCodeBlock()) {
                                        isCodeBlock = 1;
                                    }
                                    File file = new File(directory + post.getPostId() + "/" +
                                            post.getPostId() + "-" + post.getPostHistory(currentPostHistoryId).
                                            getPostHistoryId() + "-" + post.getPostHistory(currentPostHistoryId).
                                            getPostBlock(currentPostBlockId).getLocalId() + "-" +
                                            post.getPostHistory(currentPostHistoryId).getPostBlock(currentPostBlockId).
                                                    getPostBlockId() + "-" + post.getPostHistory(currentPostHistoryId).
                                            getPostBlock(currentPostBlockId).getPrecedingPostBlockId() + "-" +
                                            isCodeBlock + ".txt");
                                    file.getParentFile().mkdirs();
                                    FileWriter fileWriter = new FileWriter(file);
                                    BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);
                                    StringBuilder theFile = new StringBuilder();
                                    query = "select * from PostBlockDiff where PostBlockVersionId = " +
                                            post.getPostHistory(currentPostHistoryId).getPostBlock(currentPostBlockId).
                                                    getPostBlockId() + ";";
                                    resultSet = statement.executeQuery(query);
                                    while (resultSet.next()) {
                                        String[] stringSet = resultSet.getString("Text").split("\n");
                                        int operation = resultSet.getInt("PostBlockDiffOperationId");
                                        for (String s : stringSet) {
                                            if (operation == 0) theFile.append("   ");
                                            else if (operation == 1) theFile.append(" - ");
                                            else if (operation == -1) theFile.append(" + ");
                                            theFile.append(s + "\n");
                                        }
                                    }
                                    bufferedWriter.write(theFile.toString());
                                    bufferedWriter.close();
                                    fileWriter.close();
                                    runningBlockNumber++;
                                }
                                doneSet.add(currentPostBlockId);
                            }
                            precedingPostBlockId = post.getPostHistory(currentPostHistoryId).
                                    getPostBlock(currentPostBlockId).getPrecedingPostBlockId();
                            precedingPostHistoryId = post.getPostHistory(currentPostHistoryId).
                                    getPostBlock(currentPostBlockId).getPrecedingPostHistoryId();
                        } while (precedingPostBlockId != 0);
                    }
                }
            }
            System.out.println("The program is done! Check the files at: " + directory);
        } catch (IOException e) {
            e.printStackTrace();
        } catch (SQLException throwables) {
            throwables.printStackTrace();
        }
    }
}
