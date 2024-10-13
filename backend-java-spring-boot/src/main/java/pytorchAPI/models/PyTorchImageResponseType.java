package pytorchAPI.models;

import java.util.List;

public class PyTorchImageResponseType {
    private List<Double> scores;
    private List<String> classes;
    private List<List<Double>> boxes;
    private List<Integer> labels;

    // Getters and Setters
    public List<Double> getScores() {
        return scores;
    }

    public void setScores(List<Double> scores) {
        this.scores = scores;
    }

    public List<String> getClasses() {
        return classes;
    }

    public void setClasses(List<String> classes) {
        this.classes = classes;
    }

    public List<List<Double>> getBoxes() {
        return boxes;
    }

    public void setBoxes(List<List<Double>> boxes) {
        this.boxes = boxes;
    }

    public List<Integer> getLabels() {
        return labels;
    }

    public void setLabels(List<Integer> labels) {
        this.labels = labels;
    }
}
