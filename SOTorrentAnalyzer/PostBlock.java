import java.io.Serializable;
import java.util.*;
public class PostBlock implements Serializable {
    private int postBlockId;
    private boolean isCodeBlock;
    private int localId;
    private int precedingPostHistoryId;
    private int precedingLocalId;
    private int precedingPostBlockId;
    private boolean isEqualToPrecedingBlock;
    private double precedingSimilarity;

    public PostBlock (int postBlockId) {
        this.postBlockId = postBlockId;
    }

    public PostBlock (int postBlockId, boolean isCodeBlock, int localId, int precedingPostHistoryId, int precedingLocalId, int precedingPostBlockId, boolean isEqualToPrecedingBlock, double precedingSimilarity) {
        this.postBlockId = postBlockId;
        this.isCodeBlock = isCodeBlock;
        this.localId = localId;
        this.precedingPostHistoryId = precedingPostHistoryId;
        this.precedingLocalId = precedingLocalId;
        this.precedingPostBlockId = precedingPostBlockId;
        this.isEqualToPrecedingBlock = isEqualToPrecedingBlock;
        this.precedingSimilarity = precedingSimilarity;
    }

    public int getPostBlockId() {
        return postBlockId;
    }

    public void setPostBlockId(int postBlockId) {
        this.postBlockId = postBlockId;
    }

    public boolean isCodeBlock() {
        return isCodeBlock;
    }

    public void setIsCodeBlock(boolean isCodeBlock) {
        this.isCodeBlock = isCodeBlock;
    }

    public int getLocalId() {
        return localId;
    }

    public void setLocalId(int localId) {
        this.localId = localId;
    }

    public int getPrecedingPostHistoryId() {
        return precedingPostHistoryId;
    }

    public void setPrecedingPostHistoryId(int precedingPostHistoryId) {
        this.precedingPostHistoryId = precedingPostHistoryId;
    }

    public int getPrecedingLocalId() {
        return precedingLocalId;
    }

    public void setPrecedingLocalId(int precedingLocalId) {
        this.precedingLocalId = precedingLocalId;
    }

    public int getPrecedingPostBlockId() {
        return precedingPostBlockId;
    }

    public void setPrecedingPostBlockId(int precedingPostBlockId) {
        this.precedingPostBlockId = precedingPostBlockId;
    }

    public boolean isEqualToPrecedingBlock() {
        return isEqualToPrecedingBlock;
    }

    public void setIsEqualToPrecedingBlock(boolean isEqualToPrecedingBlock) {
        this.isEqualToPrecedingBlock = isEqualToPrecedingBlock;
    }

    public double getPrecedingSimilarity() {
        return precedingSimilarity;
    }

    public void setPrecedingSimilarity(double precedingSimilarity) {
        this.precedingSimilarity = precedingSimilarity;
    }
}