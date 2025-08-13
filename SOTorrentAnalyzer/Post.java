import java.io.Serializable;
import java.util.*;
public class Post implements Serializable {
    private int postId;
    private LinkedList<PostHistory> postHistories;

    public Post (int postId) {
        this.postId = postId;
        postHistories = new LinkedList<PostHistory>();
    }

    public void addPostHistory(PostHistory postHistory){
        postHistories.add(postHistory);
    }

    public PostHistory getPostHistory(int postHistoryId){
        for(int i = 0; i < postHistories.size(); i++){
            if(postHistories.get(i).getPostHistoryId() == postHistoryId){
                // System.out.println("Found the posthistory!");
                return postHistories.get(i);
            }
        }
        // System.out.println("Will return null - from Post");
        return null;
    }

    public LinkedList<PostHistory> getPostHistories() {
        return postHistories;
    }

    public int getPostHistoriesSize() {
        return postHistories.size();
    }

    public int getPostId(){
        return this.postId;
    }

    @Override
    public String toString(){
        StringBuilder toText = new StringBuilder();
        toText.append(postId+"("+postHistories.size()+")"+":");
        for(PostHistory postHistory : postHistories){
            toText.append(postHistory.getPostHistoryId()+"[");
            for(PostBlock postBlock : postHistory.getPostBlocks()){
                toText.append(postBlock.getPostBlockId());
                if(postBlock == postHistory.getPostBlocks().getLast()) {
                    toText.append("]");
                }
                else{
                    toText.append(",");
                }
            }
            if(postHistory != postHistories.getLast()) {
                toText.append("->");
            }
        }
        return toText.toString();
    }
}
