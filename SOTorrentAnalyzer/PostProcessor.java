import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.*;
import java.util.ArrayList;

public class PostProcessor {
    public static void main(String[] args) {
        try{
            System.out.println("The program has been initiated.");
            FileReader fileReader = new FileReader("/home/Dreamteam/acceptedWithVersionAnswer.txt");
            BufferedReader bufferedReader = new BufferedReader(fileReader);
            Path path = Paths.get("/home/Dreamteam/acceptedWithVersionAnswer.txt");
            long countLine = Files.lines(path).count();
            String dbUrl = "jdbc:mysql://localhost:3306/sotorrent?autoReconnect=true&useSSL=false";
            String username = "root";
            String password = "1234";
            Connection connection = DriverManager.getConnection(dbUrl, username, password);
            Statement statement =connection.createStatement();
            System.out.println("Connected to the database successfully!\nBeginning querying process...\nThe number of queries initiated: "+countLine);
            long count = 0;
            String s;
            ArrayList<Post> posts = new ArrayList<Post>();
            while((s = bufferedReader.readLine()) != null){    
                String query = "select PostHistoryId, MostRecentVersion from PostBlockVersion where PostId = "+s+" group by PostHistoryId, MostRecentVersion order by PostHistoryId desc;";
                // String query = "select PostHistoryId, MostRecentVersion from PostBlockVersion where PostId = 43807 group by PostHistoryId, MostRecentVersion order by PostHistoryId desc;";
                ResultSet resultSet = statement.executeQuery(query);
                Post post = new Post(Integer.parseInt(s));
                while(resultSet.next()){
                    int postHistoryId = resultSet.getInt("PostHistoryId");
                    int MostRecentVersion = resultSet.getInt("MostRecentVersion");
                    PostHistory postHistory = new PostHistory(postHistoryId);
                    if(MostRecentVersion == 1) {
                        postHistory.setIsMostRecent(true);
                    }
                    else {
                        postHistory.setIsMostRecent(false);
                    }                    
                    if(post.getPostHistoriesSize() > 0) {
                        //postHistory.setPreviousPostHistoryId(post.getPostHistories().getLast().getPostHistoryId());
                        post.getPostHistories().getLast().setPreviousPostHistoryId(postHistoryId);
                    }
                    post.addPostHistory(postHistory);
                }
                posts.add(post);
                count++;
                if(count%1000 == 0) System.out.println(count+" queries has been processed. There are "+(countLine-count)+" queries left.");
                // break;
                // break;
            }
             String fileName = "postsWithPostHistoryVersion.txt";
             String directory = "/home/Dreamteam/";
             FileWriter fileWriter = new FileWriter(directory+fileName);
             BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);
             for(Post post : posts) {
                //  for(PostHistory postHistory : post.getPostHistories()){
                //     System.out.println("PostHistoryId:"+postHistory.getPostHistoryId()+" PreviousPostHistoryId:"+postHistory.getPreviousPostHistoryId()+" IsMostRecent:"+postHistory.isMostRecent());
                //  }
                 bufferedWriter.write(post.toString()+"\n");
             }
             bufferedWriter.close();
             fileWriter.close();
            System.out.println("The program is done! Check the file at: "+directory+fileName);
            bufferedReader.close();
            fileReader.close();
        }
        catch (SQLException | FileNotFoundException throwables) {
            throwables.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
