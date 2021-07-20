public class PostBlockStat {
    private int postId;
    private int uniqueId;
    private int postBlockType;
    private int revisions;
    private double minSim;
    private double maxSim;
    private double avgSim;

    public PostBlockStat(int postId, int uniqueId, int postBlockType, int revisions, double minSim, double maxSim, double avgSim) {
        this.postId = postId;
        this.uniqueId = uniqueId;
        this.postBlockType = postBlockType;
        this.revisions = revisions;
        this.minSim = minSim;
        this.maxSim = maxSim;
        this.avgSim = avgSim;
    }
 
    public String toCSV() {
        return postId+","+uniqueId+","+postBlockType+","+revisions+","+minSim+","+maxSim+","+avgSim+"\n";
    }
}
