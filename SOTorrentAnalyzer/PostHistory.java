import java.util.*;
public class PostHistory {
    private int postHistoryId;
    private int previousPostHistoryId;
    private boolean isMostRecent;
    private LinkedList<PostBlock> postBlocks;


    public PostHistory (int postHistoryId) {
        this.postHistoryId = postHistoryId;
        postBlocks = new LinkedList<PostBlock>();
    }

    public int getPostHistoryId() {
        return postHistoryId;
    }

    public void setPostHistoryId(int postHistoryId) {
        this.postHistoryId = postHistoryId;
    }

    public int getPreviousPostHistoryId() {
        return previousPostHistoryId;
    }

    public void setPreviousPostHistoryId(int previousPostHistoryId) {
        this.previousPostHistoryId = previousPostHistoryId;
    }

    public boolean isMostRecent() {
        return isMostRecent;
    }

    public void setIsMostRecent(boolean isMostRecent) {
        this.isMostRecent = isMostRecent;
    }

    public LinkedList<PostBlock> getPostBlocks () {
        return postBlocks;
    }

    public void addPostBlock(PostBlock postBlock) {
        postBlocks.add(postBlock);
    }

    public PostBlock getPostBlock (int postBlockId) {
        for (int i = 0; i < postBlocks.size(); i++) {
            if(postBlocks.get(i).getPostBlockId() == postBlockId) {
                // System.out.println("Found the postblock!");
                return postBlocks.get(i);
            }
        }
        // System.out.println("Will return null - from PostHistory");
        return null;
    }
}
